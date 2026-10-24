"""REQ-BR-001 ยกเลิกงานและสร้างรายการคืนมัดจำตาม BR-01
CR-06 (specs/004-cancel-refund): ฟังก์ชันเดียวนี้ใช้ทั้งทางลูกค้า (UC-08) และทางระบบ (UC-07 R4, R5)
เพิ่ม: ส่งคำขอคืนเงินผ่าน Payment Gateway รายเดิม (REQ-IF-010, REQ-CON-003) ปล่อยช่วงเวลา (REQ-DAT-003)
และแจ้งลูกค้ากับช่างภายใน 60 วินาที (REQ-FN-055)
CR-07 (REQ-QA-010, Q-41, AC-08-08): gateway ไม่ตอบคำขอคืนเงินภายใน 30 วินาที บันทึก result = unknown พร้อม reference เดิม
ไม่ส่งซ้ำเอง แจ้งลูกค้าว่ากำลังตรวจสอบ Finance ปิดรายการภายใน 1 วันทำการตามคู่มือเหตุการณ์ที่ 1"""
from datetime import datetime

from sqlalchemy import select

from app.db.models import Job, Refund, Payment, set_status, SLOT_FREE
from app.refund.rules import decide, Decision
from app import config
from app.payments.gateway import Gateway, GatewayTimeout
from app.notify.queue import queue
from app.privacy import get_logger, log_event

log = get_logger(__name__)  # REQ-PRV-002


class CancelRejected(Exception):
    def __init__(self, decision: Decision, message: str):
        self.decision, self.message = decision, message


# ข้อความที่หน้าจอแสดงเมื่อยกเลิกไม่ได้ (UI-08-01 รายการ "ต้องตรง") อยู่ที่นี่ที่เดียว
# CR-10: MSG_R3_PENDING ไม่ถูกใช้แล้ว (Q-14 ปิด R3 ยกเลิกได้) คงชื่อไว้เพราะเป็นข้อความในบันทึกเดิมของ B4
MSG_R3_PENDING = "ยกเลิกขณะช่างกำลังเดินทางยังไม่เปิดให้ทำ กรุณาติดต่อ call center (รอ Q-14)"
MSG_R6_NOT_ALLOWED = "งานที่กำลังดำเนินงานหรือเสร็จสิ้นแล้วยกเลิกไม่ได้ กรุณาใช้กระบวนการร้องเรียน"
MSG_ALREADY_CLOSED = "งานนี้ถูกยกเลิกไปแล้ว"
# CR-07 (AC-08-08): ข้อความถึงลูกค้าเมื่อ gateway ไม่ตอบคำขอคืนเงิน
MSG_REFUND_CHECKING = "กำลังตรวจสอบการคืนเงิน"
# CR-10 (Q-34, AC-08-11): gateway ปฏิเสธคำขอคืนเงิน งานยังเป็น "ยกเลิก" ไม่ส่งซ้ำเอง Finance ติดตามภายใน 1 วันทำการ
MSG_REFUND_DECLINED = (f"การคืนเงินต้องตรวจสอบเพิ่ม เจ้าหน้าที่จะติดต่อคุณภายใน "
                       f"{config.REFUND_FOLLOWUP_BUSINESS_DAYS} วันทำการ")
# CR-10 (Q-14, AC-08-12): ข้อความใต้ยอดคืนเมื่อยกเลิกขณะช่างกำลังเดินทาง (UI-08-01) ตัวเลขมาจาก config ที่เดียว
MSG_R3_NOTE = f"หักค่าเดินทางของช่าง {config.TRAVEL_FEE_BAHT} บาท ตามเงื่อนไขการยกเลิกขณะช่างกำลังเดินทาง"


def refund_message(refund: "Refund | None") -> str:
    """CR-10 (Q-34, Q-41): ข้อความเรื่องเงินคืนที่หน้าผลการยกเลิกแสดง ว่างเมื่อ gateway ตอบรับ"""
    if refund is None or refund.result in ("approved", "not_sent"):
        return ""
    if refund.result == "unknown":
        return f"{MSG_REFUND_CHECKING} {refund.amount} บาท"
    return MSG_REFUND_DECLINED


def note_for(d: Decision) -> str:
    return MSG_R3_NOTE if d.rule == "R3" and d.outcome == "cancelled" else ""


def quote(job: Job, cancelled_by: str, now: datetime, substitute_declined: bool = False) -> Decision:
    """REQ-FN-054 (AC-08-01): ยอดคืนที่จะได้ถ้ายกเลิกตอนนี้ คิดจากตาราง BR-01 ตัวเดียวกับที่ใช้ยกเลิกจริง"""
    return decide(job.status, cancelled_by, job.scheduled_start, now, job.deposit_amount, substitute_declined)


def cancel_job(db, job: Job, cancelled_by: str, now: datetime,
               gateway: Gateway | None = None, substitute_declined: bool = False) -> tuple[Decision, Refund | None]:
    if job.status in ("cancelled", "auto_cancelled"):
        # AC-08-04: ยกเลิกซ้ำไม่ได้ และต้องไม่ส่งคำขอคืนเงินซ้ำ
        raise CancelRejected(Decision("R6", "not_allowed", None), MSG_ALREADY_CLOSED)
    d = quote(job, cancelled_by, now, substitute_declined)
    was_rematching = job.status == "rematching"
    if d.outcome == "pending_question":
        raise CancelRejected(d, MSG_R3_PENDING)
    if d.outcome == "not_allowed":
        raise CancelRejected(d, MSG_R6_NOT_ALLOWED)
    set_status(db, job, d.outcome, now)  # REQ-DAT-002 บันทึกประวัติ "ยกเลิก"
    # รองรับ REQ-DAT-003: ช่วงเวลาที่ผูกกับงานกลับเป็น "ว่าง"
    if job.slot and job.slot.state != SLOT_FREE:
        job.slot.state, job.slot.held_by_customer_id, job.slot.hold_expires_at = SLOT_FREE, None, None
    refund = None
    if d.refund_amount:  # R5 คืน 0 = ไม่มีรายการคืน เพราะไม่เคยตัดเงิน
        refund = Refund(job_id=job.id, amount=d.refund_amount, rule=d.rule, result="not_sent")
        # รองรับ REQ-IF-010 / REQ-CON-003: คืนเงินผ่าน interface Gateway ตัวเดิม ด้วย reference ของการชำระที่สำเร็จ
        payment = db.scalars(select(Payment).where(Payment.job_id == job.id, Payment.result == "success")).first()
        if gateway is not None and payment is not None:
            refund.gateway_ref = payment.gateway_ref
            try:
                result = gateway.refund(payment.gateway_ref, d.refund_amount,
                                        timeout_seconds=config.GATEWAY_TIMEOUT_SECONDS)
                refund.result = result.status
            except GatewayTimeout:
                refund.result = "unknown"  # CR-07 REQ-QA-010: ไม่รู้ผล ไม่ส่งซ้ำเอง (Q-41)
            log_event(log, "refund_sent", job_id=job.id, rule=d.rule, amount=d.refund_amount, result=refund.result)
        db.add(refund)
    # รองรับ REQ-FN-055: แจ้งลูกค้าและช่างภายใน 60 วินาที (IF-02) ไม่รอผลส่ง
    refund_text = f" คืนมัดจำ {d.refund_amount} บาท" if d.refund_amount else ""
    if refund is not None and refund.result == "unknown":
        refund_text = f" {MSG_REFUND_CHECKING} {d.refund_amount} บาท"
    if refund is not None and refund.result == "declined":
        # CR-10 (Q-34): ห้ามบอกลูกค้าว่าคืนแล้ว เมื่อ gateway ปฏิเสธ
        refund_text = f" {MSG_REFUND_DECLINED}"
    queue.enqueue("customer", job.customer_id, f"งาน #{job.id} ถูกยกเลิก{refund_text}", job.id, now, db=db)
    tech_text = f"งาน #{job.id} ถูกยกเลิก ช่วงเวลากลับเป็นว่าง"
    if d.rule == "R3":
        # CR-10 (Q-14): ช่างรู้ว่าลูกค้ายกเลิกระหว่างเดินทาง ค่าเดินทางเหมาจ่ายผ่าน Finance (นอกระบบใน R1)
        tech_text = f"งาน #{job.id} ลูกค้ายกเลิกระหว่างที่คุณกำลังเดินทาง ได้ค่าเดินทาง {config.TRAVEL_FEE_BAHT} บาท ผ่าน Finance"
    if not was_rematching:  # CR-12: ระหว่างหาช่างใหม่ ช่างคนเดิมปฏิเสธไปแล้วและได้ข้อความแล้ว ไม่ต้องแจ้งซ้ำ
        queue.enqueue("technician", job.technician_id, tech_text, job.id, now, db=db)
    db.commit()
    return d, refund
