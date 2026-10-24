"""REQ-FN-041 ล็อกช่วงเวลา | REQ-FN-008 สร้างงาน | UC-07 ขั้น 3, 5, 6 รวม E1, E2"""
from datetime import datetime, timedelta

from sqlalchemy import select

from app import config
from app.db.models import (TimeSlot, Job, Customer, ServiceAddress, set_status,
                           SLOT_FREE, SLOT_HELD, SLOT_BOOKED)
from app.payments.gateway import Gateway
from app.payments.service import charge_deposit, pending_payment_of, retry_pending
from app.notify.queue import queue
from app.technicians.service import release_expired_holds, find_alternatives, unavailable


class SlotTaken(Exception):
    """UC-07 E2 ช่วงเวลาถูกลูกค้าอื่นจองหรือล็อกไปก่อน"""
    def __init__(self, alternatives: list[dict]):
        self.alternatives = alternatives


class HoldLimitReached(Exception):
    """CR-07 REQ-SEC-011: ลูกค้าคนนี้ถือล็อกที่ยังไม่หมดอายุอยู่ครบ HOLD_LIMIT_PER_CUSTOMER ช่วงแล้ว"""
    def __init__(self, held: list[TimeSlot]):
        self.held = held


class PaymentPending(Exception):
    """CR-07 REQ-QA-010: gateway ไม่ตอบทั้ง authorize และ status-inquiry งานยังเป็น "รอชำระเงิน" ช่วงเวลายังล็อกอยู่"""
    def __init__(self, job: Job, slot: TimeSlot):
        self.job, self.slot = job, slot


class PaymentFailed(Exception):
    """UC-07 E1 ชำระไม่สำเร็จ หรือ gateway ไม่ตอบและสอบถามแล้วไม่สำเร็จ"""
    def __init__(self, job_id: int, reason: str):
        self.job_id, self.reason = job_id, reason


def hold_slot(db, slot: TimeSlot, customer_id: int, now: datetime) -> TimeSlot:
    # รองรับ REQ-FN-041: ล็อก HOLD_MINUTES นาที (Q-18) ถ้าคนอื่นล็อกอยู่ให้ปฏิเสธ
    release_expired_holds(db, now)
    if unavailable(slot.state, slot.held_by_customer_id, customer_id):  # CR-14: ช่วงที่ช่างปิดก็ล็อกไม่ได้
        raise SlotTaken(find_alternatives(db, slot, now, customer_id))
    # รองรับ REQ-SEC-011 (CR-07): ล็อกช่วงอื่นที่ยังไม่หมดอายุของลูกค้าคนนี้ นับรวมแล้วต้องไม่เกินเพดาน
    others = db.scalars(select(TimeSlot).where(TimeSlot.state == SLOT_HELD,
                                               TimeSlot.held_by_customer_id == customer_id,
                                               TimeSlot.id != slot.id)).all()
    if len(others) >= config.HOLD_LIMIT_PER_CUSTOMER:
        raise HoldLimitReached(others)
    slot.state = SLOT_HELD
    slot.held_by_customer_id = customer_id
    slot.hold_expires_at = now + timedelta(minutes=config.HOLD_MINUTES)
    db.commit()
    return slot


# CR-10 (Q-26) ข้อความใต้ราคาประเมินบนหน้ายืนยัน (UI-07-02 รายการ "ต้องตรง") อยู่ที่นี่ที่เดียว
MSG_ESTIMATE_NOTE = "ค่าบริการเบื้องต้น ยังไม่รวมค่าอะไหล่ ช่างแจ้งราคาจริงก่อนเริ่มงาน"


class UnknownCategory(Exception):
    """ประเภทงานที่ไม่อยู่ในตารางราคาประเมิน (AS-10) ไม่มียอดมัดจำ จึงจองไม่ได้"""


def deposit_for(category: str) -> int:
    """REQ-BR-002: ยอดมัดจำจากตารางราคาประเมิน (config.DEPOSIT_BY_CATEGORY) ปัดขึ้นหลักสิบ
    ประเภทงานที่ไม่อยู่ในตาราง ไม่เดายอดให้ (CR-03 ตัดค่า 300 ที่ไม่มีที่มาออก ดู F-02)"""
    if category not in config.DEPOSIT_BY_CATEGORY:
        raise UnknownCategory(category)
    base = config.DEPOSIT_BY_CATEGORY[category]
    return -(-base // 10) * 10


def estimate_for(category: str) -> int:
    """CR-10 REQ-FN-057 (Q-26): ราคาประเมิน (ค่าบริการเบื้องต้น ไม่รวมค่าอะไหล่) จาก config.ESTIMATE_BY_CATEGORY
    ยอดมัดจำของ deposit_for มาจากตารางเดียวกันนี้ (REQ-BR-002 ฉบับ CR-10) ประเภทที่ไม่อยู่ในตารางไม่เดายอด"""
    if category not in config.ESTIMATE_BY_CATEGORY:
        raise UnknownCategory(category)
    return config.ESTIMATE_BY_CATEGORY[category]


def create_booking(db, customer: Customer, slot: TimeSlot, address: ServiceAddress,
                   category: str, gateway: Gateway, now: datetime) -> Job:
    """UC-07 ขั้น 5 ถึง 6: ตรวจล็อก สร้างงาน รอชำระเงิน ตัดมัดจำ แล้วยืนยันหรือยกเลิกอัตโนมัติ"""
    release_expired_holds(db, now)
    # รองรับ REQ-QA-010 บรรทัดที่ 2 (CR-07, AC-07-13): ลูกค้ากดยืนยันซ้ำระหว่างที่การชำระยัง pending
    # ใช้งานเดิมและ reference เดิม ไม่สร้างงานใหม่ ไม่ authorize ใหม่ (เหตุการณ์ B ตัดเงินซ้ำเพราะสร้างคำขอใหม่)
    existing = db.scalars(select(Job).where(Job.customer_id == customer.id, Job.slot_id == slot.id,
                                            Job.status == "pending_payment")).first()
    if existing is not None and (payment := pending_payment_of(db, existing)) is not None:
        return _finish_payment(db, existing, slot, customer, retry_pending(db, payment, gateway), now)
    # รองรับ AC-07-04 (E2): ถ้า slot ไม่ได้ล็อกโดยลูกค้าคนนี้ ไม่ตัดเงิน และเสนอช่วงใกล้เคียง
    if unavailable(slot.state, slot.held_by_customer_id, customer.id):  # CR-14: รวมช่วงที่ช่างปิด
        raise SlotTaken(find_alternatives(db, slot, now, customer.id))
    if slot.state == SLOT_FREE:
        hold_slot(db, slot, customer.id, now)  # กดยืนยันโดยไม่ได้ล็อกก่อน ให้ล็อกให้ทันที

    job = Job(customer_id=customer.id, technician_id=slot.technician_id, slot_id=slot.id,
              address_id=address.id, category=category, status="pending_payment",
              deposit_amount=deposit_for(category), scheduled_start=slot.start, created_at=now)
    db.add(job)
    db.flush()
    set_status(db, job, "pending_payment", now)

    payment = charge_deposit(db, job, gateway, now)  # REQ-IF-001, REQ-IF-005
    return _finish_payment(db, job, slot, customer, payment, now)


def _finish_payment(db, job: Job, slot: TimeSlot, customer: Customer, payment, now: datetime) -> Job:
    """ผลของการชำระ: สำเร็จ = ยืนยัน | pending = คงล็อกไว้ (CR-07) | ไม่สำเร็จ = ยกเลิกอัตโนมัติ (UC-07 E1)"""
    if payment.result == "pending":
        # รองรับ REQ-QA-010 บรรทัดที่ 3 (AC-07-12): ไม่ปล่อยช่วงเวลา ไม่ยกเลิก ไม่ต่ออายุล็อก (ครบ 10 นาทีตาม REQ-FN-041)
        db.commit()
        raise PaymentPending(job, slot)
    if payment.result == "success":
        # รองรับ REQ-FN-008 ขั้น 6: งานยืนยันแล้ว ช่วงเวลาจองแล้ว
        set_status(db, job, "confirmed", now)
        slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_BOOKED, None, None
        # CR-12 REQ-FN-061: มอบงานให้ช่าง ช่างต้องรับหรือปฏิเสธภายใน 30 นาที (UC-12)
        from app.matching.service import offer
        offer(db, job, now)
        # รองรับ REQ-FN-012: วางข้อความถึงสองฝ่ายลงคิว ไม่รอผลส่ง CR-17 (F-20): ข้อความถึงช่างบอกเวลาที่ต้องตอบรับ
        queue.enqueue("customer", customer.id, f"จองสำเร็จ งาน #{job.id} {slot.start:%d/%m %H:%M}", job.id, now, db=db)
        queue.enqueue("technician", slot.technician_id, f"มีงานใหม่ #{job.id} {slot.start:%d/%m %H:%M} กดรับงานหรือปฏิเสธภายใน {config.TECH_RESPONSE_MINUTES} นาที", job.id, now, db=db)
        db.commit()
        return job

    # UC-07 E1 / BR-01 R5: ยกเลิกอัตโนมัติ ไม่มีการตัดเงิน ช่วงเวลากลับว่าง แจ้งลูกค้า
    set_status(db, job, "auto_cancelled", now)
    slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_FREE, None, None
    queue.enqueue("customer", customer.id, f"ชำระมัดจำไม่สำเร็จ งาน #{job.id} ถูกยกเลิก", job.id, now, db=db)
    db.commit()
    raise PaymentFailed(job.id, payment.result)


def technician_view(job: Job, now: datetime) -> dict:
    """REQ-SEC-004: มุมมองช่าง ใส่ customer_phone เฉพาะช่วง 2 ชั่วโมงก่อนนัดจนปิดงาน"""
    reveal_from = job.scheduled_start - timedelta(hours=config.PHONE_REVEAL_HOURS)
    data = {"job_id": job.id, "status": job.status, "category": job.category,
            "scheduled_start": job.scheduled_start.isoformat(), "customer_name": job.customer.name}
    if reveal_from <= now and job.status not in ("done", "cancelled", "auto_cancelled"):
        data["customer_phone"] = job.customer.phone
    return data


# ---- CR-09 REQ-FN-056 เลื่อนนัดของลูกค้า ตาม BR-06 (specs/005-ai-assistant/rules.md) ----
# ผู้ช่วย (UC-14) เรียกฟังก์ชันนี้ผ่านเครื่องมือ "เลื่อนนัด" ด้วยสิทธิ์ของลูกค้า ไม่มีทางเลื่อนนัดทางอื่น (REQ-AI-011 บรรทัดที่ 3)
from app.db.models import JobReschedule  # noqa: E402

# ข้อความถึงลูกค้าเมื่อไม่ผ่าน BR-06 อยู่ที่นี่ที่เดียว (ผู้ช่วยและ API ใช้ข้อความเดียวกัน)
RESCHEDULE_MESSAGES = {
    "not_confirmed": "เลื่อนนัดได้เฉพาะงานที่สถานะ ยืนยันแล้ว",
    "limit_reached": "งานนี้เลื่อนนัดครบ {max} ครั้งแล้ว",
    "too_late": "เหลือเวลาก่อนนัดเดิมน้อยกว่า {hours} ชั่วโมง เลื่อนเองไม่ได้",
    "other_technician": "เลื่อนได้เฉพาะช่วงเวลาของช่างคนเดิม",
    "out_of_window": "เวลาใหม่ต้องเริ่มอย่างน้อย {hours} ชั่วโมงจากตอนนี้ และอยู่ภายใน {days} วันข้างหน้า",
    "slot_taken": "ช่วงเวลานี้ไม่ว่างแล้ว",
}
BEYOND_RULE = ("not_confirmed", "limit_reached", "too_late", "other_technician", "out_of_window")


class RescheduleRejected(Exception):
    """BR-06 ไม่ผ่าน reason เป็นรหัสใน RESCHEDULE_MESSAGES ข้อ 1 ถึง 5 คือเกินกรอบ (ส่งต่อคน) slot_taken คือข้อ 6"""
    def __init__(self, reason: str):
        self.reason = reason
        self.message = RESCHEDULE_MESSAGES[reason].format(max=config.RESCHEDULE_MAX_PER_JOB,
                                                         hours=config.RESCHEDULE_MIN_HOURS_BEFORE,
                                                         days=config.SEARCH_DAYS_AHEAD)

    @property
    def beyond_rule(self) -> bool:
        return self.reason in BEYOND_RULE


def reschedules_used(db, job: Job) -> int:
    # CR-18 (GAP-31, Q-62): การเลื่อนกลับโดย call center ไม่นับเป็นครั้งของ BR-06 ข้อ 2
    return len(db.scalars(select(JobReschedule).where(JobReschedule.job_id == job.id,
                                                      JobReschedule.by_role != "call_center")).all())


def reschedule_window(now: datetime) -> tuple[datetime, datetime]:
    """BR-06 ข้อ 5: เริ่มไม่น้อยกว่า 12 ชั่วโมงจากตอนนี้ และอยู่ในช่วงที่ค้นได้ตาม REQ-FN-008 (ถึงสิ้นวันที่ 7 นับจากพรุ่งนี้)"""
    earliest = now + timedelta(hours=config.RESCHEDULE_MIN_HOURS_BEFORE)
    first_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return earliest, first_day + timedelta(days=config.SEARCH_DAYS_AHEAD)


def check_reschedule(db, job: Job, new_slot: TimeSlot | None, now: datetime) -> None:
    """ตรวจ BR-06 จากบนลงล่าง ข้อแรกที่ไม่ผ่านคือเหตุ new_slot = None ตรวจเฉพาะข้อ 1 ถึง 3 (ใช้ก่อนเสนอช่วงว่าง)"""
    if job.status != "confirmed":
        raise RescheduleRejected("not_confirmed")
    if reschedules_used(db, job) >= config.RESCHEDULE_MAX_PER_JOB:
        raise RescheduleRejected("limit_reached")
    if job.scheduled_start - now < timedelta(hours=config.RESCHEDULE_MIN_HOURS_BEFORE):
        raise RescheduleRejected("too_late")
    if new_slot is None:
        return
    if new_slot.technician_id != job.technician_id:
        raise RescheduleRejected("other_technician")
    earliest, latest = reschedule_window(now)
    if not (earliest <= new_slot.start < latest):
        raise RescheduleRejected("out_of_window")
    release_expired_holds(db, now)
    if new_slot.state != SLOT_FREE or new_slot.id == job.slot_id:
        raise RescheduleRejected("slot_taken")


def free_slots_for_reschedule(db, job: Job, now: datetime) -> list[TimeSlot]:
    """ช่วงว่างของช่างคนเดิมที่อยู่ในกรอบ BR-06 ข้อ 5 (เครื่องมือ "อ่านช่วงเวลาว่างของช่างคนเดิม" REQ-AI-010)"""
    release_expired_holds(db, now)
    earliest, latest = reschedule_window(now)
    return db.scalars(select(TimeSlot).where(TimeSlot.technician_id == job.technician_id, TimeSlot.state == SLOT_FREE,
                                             TimeSlot.start >= earliest, TimeSlot.start < latest,
                                             TimeSlot.id != job.slot_id).order_by(TimeSlot.start)).all()


def reschedule_job(db, job: Job, new_slot: TimeSlot, now: datetime, reference: str | None = None) -> JobReschedule:
    """REQ-FN-056 / BR-06 ลำดับ 1 ถึง 4 ในธุรกรรมเดียว reference เดิมที่ทำสำเร็จแล้ว คืนแถวเดิม ไม่เลื่อนซ้ำ"""
    if reference is not None:
        done = db.scalars(select(JobReschedule).where(JobReschedule.reference == reference)).first()
        if done is not None:
            return done
    check_reschedule(db, job, new_slot, now)
    old_slot = db.get(TimeSlot, job.slot_id)
    record = JobReschedule(job_id=job.id, from_slot_id=old_slot.id, to_slot_id=new_slot.id,
                           from_start=job.scheduled_start, to_start=new_slot.start, reference=reference,
                           by_role="customer", at=now)
    old_slot.state, old_slot.held_by_customer_id, old_slot.hold_expires_at = SLOT_FREE, None, None   # ลำดับ 1
    new_slot.state, new_slot.held_by_customer_id, new_slot.hold_expires_at = SLOT_BOOKED, None, None  # ลำดับ 2
    job.slot_id, job.scheduled_start = new_slot.id, new_slot.start
    db.add(record)                                                                                     # ลำดับ 3
    text = f"งาน #{job.id} เลื่อนนัดเป็น {new_slot.start:%d/%m %H:%M}"
    queue.enqueue("customer", job.customer_id, text, job.id, now, db=db)                                     # ลำดับ 4
    queue.enqueue("technician", job.technician_id, text, job.id, now, db=db)
    db.commit()
    return record
