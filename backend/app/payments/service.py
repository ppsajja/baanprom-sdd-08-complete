"""REQ-IF-001 authorize แล้ว capture | REQ-IF-005 timeout แล้ว status-inquiry ด้วย ref เดิม (MD-SEQ-07-05)
CR-07 REQ-QA-010: ถ้า gateway ไม่ตอบทั้ง authorize และ status-inquiry (ไม่ตอบเลย) ไม่ตัดสินแทน gateway
บันทึกการชำระเป็น pending พร้อม reference เดิม งานคงเป็น "รอชำระเงิน" และช่วงเวลายังล็อกจนครบ 10 นาที (REQ-FN-041)
ลูกค้ากดยืนยันซ้ำ ระบบถามสถานะด้วย reference เดิม ไม่ authorize ใหม่ ไม่สร้างงานใหม่ (AC-07-12, AC-07-13)"""
from datetime import datetime
import uuid

from sqlalchemy import select

from app import config
from app.db.models import Payment, Job
from app.payments.gateway import Gateway, GatewayTimeout, GatewayResult
from app.privacy import get_logger, log_event

log = get_logger(__name__)


def charge_deposit(db, job: Job, gateway: Gateway, now: datetime) -> Payment:
    """คืน Payment ที่ result เป็น success / failed / timeout / pending
    กติกา: authorize เรียกได้ครั้งเดียวต่อ ref (REQ-IF-005 ห้ามตัดเงินซ้ำ)"""
    ref = f"BP-{job.id}-{uuid.uuid4().hex[:8]}"
    try:
        # รอได้ไม่เกิน GATEWAY_TIMEOUT_SECONDS (Q-19 ค่าชั่วคราว 30 วินาที ตาม spec ข้อ 9)
        result = gateway.authorize(ref, job.deposit_amount, timeout_seconds=config.GATEWAY_TIMEOUT_SECONDS)
    except GatewayTimeout:
        # รองรับ REQ-IF-005: ไม่ตอบใน gateway-timeout ให้ถามสถานะด้วย ref เดิม ไม่ authorize ซ้ำ
        log_event(log, "gateway_timeout", job_id=job.id, reason="status_inquiry")
        try:
            result = gateway.status_inquiry(ref)
        except GatewayTimeout:
            # CR-07 REQ-QA-010 บรรทัดที่ 3: gateway ไม่ตอบเลย (GAP-21 เดิมโค้ดพังเป็น 500 ตรงนี้)
            log_event(log, "gateway_unreachable", job_id=job.id, result="pending")
            payment = Payment(job_id=job.id, amount=job.deposit_amount, gateway_ref=ref,
                              result="pending", authorized_at=now)
            db.add(payment)
            return payment
    payment = Payment(job_id=job.id, amount=job.deposit_amount, gateway_ref=ref, result="", authorized_at=now)
    db.add(payment)
    return settle(payment, result, gateway)


def settle(payment: Payment, result: GatewayResult, gateway: Gateway) -> Payment:
    """ตั้งผลของการชำระจากคำตอบของ gateway (ใช้ทั้งครั้งแรกและตอนถามซ้ำด้วย reference เดิม)"""
    if result.status == "approved":
        gateway.capture(payment.gateway_ref)  # D-07-03 capture หลัง approved เท่านั้น
        payment.result = "success"
    elif result.status == "declined":
        payment.result = "failed"
    else:
        # unknown หลัง inquiry: ถือว่าไม่สำเร็จ และ void กันวงเงินที่อาจค้าง (BR-01 R5 ต้องไม่มีการตัดเงิน)
        gateway.void(payment.gateway_ref)
        payment.result = "timeout"
    return payment


def pending_payment_of(db, job: Job) -> Payment | None:
    return db.scalars(select(Payment).where(Payment.job_id == job.id, Payment.result == "pending")).first()


def retry_pending(db, payment: Payment, gateway: Gateway) -> Payment:
    """CR-07 REQ-QA-010 บรรทัดที่ 2: ลองใหม่ด้วย reference เดิมเท่านั้น ถามสถานะ ไม่ authorize ใหม่"""
    try:
        result = gateway.status_inquiry(payment.gateway_ref)
    except GatewayTimeout:
        log_event(log, "gateway_unreachable", job_id=payment.job_id, result="pending")
        return payment
    return settle(payment, result, gateway)


def settle_on_hold_expiry(db, job: Job, slot, gateway: Gateway, now: datetime) -> bool:
    """CR-07 (EV-045 คำตอบของ Ops lead กับ SH-01): ล็อกครบ 10 นาทีแล้วการชำระยังเป็น pending
    ถามสถานะด้วย reference เดิมอีกครั้ง approved = ยืนยันงาน คืน True | อย่างอื่น = ยกเลิกอัตโนมัติตาม UC-07 E1 คืน False
    ใช้กับงานที่ยังเป็น "รอชำระเงิน" และมีการชำระ pending เท่านั้น"""
    from app.db.models import set_status, SLOT_BOOKED, SLOT_FREE
    from app.notify.queue import queue
    payment = pending_payment_of(db, job)
    if payment is None:
        return False
    try:
        result = gateway.status_inquiry(payment.gateway_ref)
    except GatewayTimeout:
        result = GatewayResult("unknown", payment.gateway_ref)
    settle(payment, result, gateway)
    if payment.result == "success":
        set_status(db, job, "confirmed", now)
        slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_BOOKED, None, None
        from app.matching.service import offer  # CR-12 REQ-FN-061
        offer(db, job, now)
        queue.enqueue("customer", job.customer_id, f"จองสำเร็จ งาน #{job.id} {slot.start:%d/%m %H:%M}", job.id, now, db=db)
        queue.enqueue("technician", slot.technician_id, f"มีงานใหม่ #{job.id} {slot.start:%d/%m %H:%M} กดรับงานหรือปฏิเสธภายใน {config.TECH_RESPONSE_MINUTES} นาที", job.id, now, db=db)
        return True
    set_status(db, job, "auto_cancelled", now)
    slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_FREE, None, None
    queue.enqueue("customer", job.customer_id, f"ชำระมัดจำไม่สำเร็จ งาน #{job.id} ถูกยกเลิก", job.id, now, db=db)
    log_event(log, "pending_payment_expired", job_id=job.id, result=payment.result)
    return False
