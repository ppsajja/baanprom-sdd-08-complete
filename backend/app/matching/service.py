"""CR-12 UC-12 และ UC-05 ตาม BR-07 (specs/007-accept-rematch/rules.md) และ MD-STM-01 ลูกศร "ยืนยันแล้ว ไปยัง กำลังหาช่างใหม่"
- REQ-FN-061 ช่างรับหรือปฏิเสธงานภายใน 30 นาที ไม่ตอบถือว่าปฏิเสธ กด "ออกเดินทาง" ถือว่ารับแล้ว
- REQ-FN-062 ช่างปฏิเสธ งานเป็น "กำลังหาช่างใหม่" ระบบจับคู่ช่างใหม่ด้วยกฎ (ไม่ใช่การแนะนำอัตโนมัติ REQ-AI-002 ยัง Won't)
- REQ-FN-063 ได้ช่างแทน ลูกค้าปฏิเสธช่างแทนได้ คืนมัดจำเต็ม หาไม่ได้ภายใน 2 ชั่วโมง ยกเลิกและคืนเต็ม (BR-01 R4)
CR-08 REQ-FN-064 ช่างคนเดิม (BR-08) อยู่ท้ายไฟล์"""
from datetime import datetime, timedelta

from sqlalchemy import select

from app import config
from app.db.models import (Job, JobAssignment, JobStatusHistory, ServiceAddress, Technician, TimeSlot, set_status,
                           SLOT_FREE, SLOT_BOOKED)
from app.notify.queue import queue
from app.privacy import get_logger, log_event
from app.technicians.service import distance_km, release_expired_holds, slot_visible_to

log = get_logger(__name__)

# ข้อความถึงลูกค้าและช่าง และข้อความบนหน้าจอ (รายการ "ต้องตรง" ของ UI-09-01 และ UI-02-03) อยู่ที่นี่ที่เดียว
RESPONSE_LABELS = {"accept": "รับงาน", "reject": "ปฏิเสธงาน"}
MSG_REMATCHING = "ช่างไม่สะดวกรับงาน #{job} ระบบกำลังหาช่างใหม่ให้ในเวลาเดิม ภายใน {hours} ชั่วโมง"
MSG_SUBSTITUTE = ("งาน #{job} ได้ช่างใหม่ {name} เวลาเดิม {when} ถ้าไม่ต้องการช่างแทน กดไม่รับช่างแทน "
                  "ได้มัดจำคืนเต็มจำนวน")
MSG_TECH_NEW = "มีงานใหม่ #{job} {when} กดรับงานหรือปฏิเสธภายใน {minutes} นาที"
MSG_TECH_RELEASED = "งาน #{job} ส่งต่อช่างคนอื่นแล้ว เพราะ{why}"
WHY = {"rejected": "คุณปฏิเสธงาน", "no_response": "ไม่ได้ตอบรับภายใน {minutes} นาที"}

MATCH_ERRORS = {
    "not_pending": "งานนี้ตอบรับหรือปฏิเสธไปแล้ว",
    "not_confirmed": "รับหรือปฏิเสธได้เฉพาะงานที่สถานะ ยืนยันแล้ว",
    "not_substitute": "งานนี้ไม่ได้ใช้ช่างแทน",
}


class MatchError(Exception):
    def __init__(self, reason: str):
        self.reason, self.message = reason, MATCH_ERRORS[reason]


# ---- UC-12 ----

def assignments_of(db, job: Job) -> list[JobAssignment]:
    return db.scalars(select(JobAssignment).where(JobAssignment.job_id == job.id).order_by(JobAssignment.id)).all()


def current_assignment(db, job: Job) -> JobAssignment | None:
    rows = [a for a in assignments_of(db, job) if a.technician_id == job.technician_id]
    return rows[-1] if rows else None


def released_from(db, job: Job, technician_id: int) -> bool:
    """ช่างคนนี้ปฏิเสธหรือไม่ตอบงานนี้แล้ว (ต้องไม่เห็นงานและเบอร์ลูกค้าอีก แม้ job.technician_id ยังเป็นคนเดิมระหว่างหาช่างใหม่)"""
    rows = [a for a in assignments_of(db, job) if a.technician_id == technician_id]
    return bool(rows) and rows[-1].response in ("rejected", "no_response")


def offer(db, job: Job, now: datetime, via_rematch: bool = False) -> JobAssignment:
    """REQ-FN-061 มอบงานให้ช่างของ job ตอนงานเป็น "ยืนยันแล้ว" ช่างต้องตอบภายใน TECH_RESPONSE_MINUTES"""
    a = JobAssignment(job_id=job.id, technician_id=job.technician_id, slot_id=job.slot_id, via_rematch=via_rematch,
                      offered_at=now, respond_by=now + timedelta(minutes=config.TECH_RESPONSE_MINUTES),
                      response="pending")
    db.add(a)
    db.flush()
    return a


def response_actions(db, job: Job) -> list[dict]:
    """ปุ่มที่ช่างกดได้ (UI-09-01) รับงานได้เมื่อยังไม่ตอบ ปฏิเสธได้จนกว่าจะออกเดินทาง (BR-07 ข้อ 1)"""
    if job.status != "confirmed":
        return []
    a = current_assignment(db, job)
    if a is None:
        return []
    if a.response == "pending":
        return [{"action": "accept", "label": RESPONSE_LABELS["accept"]},
                {"action": "reject", "label": RESPONSE_LABELS["reject"]}]
    if a.response == "accepted":
        return [{"action": "reject", "label": RESPONSE_LABELS["reject"]}]
    return []


def assignment_view(db, job: Job) -> dict | None:
    a = current_assignment(db, job)
    if a is None:
        return None
    return {"response": a.response, "respond_by": a.respond_by.isoformat(), "via_rematch": a.via_rematch}


def accept(db, job: Job, now: datetime) -> JobAssignment:
    if job.status != "confirmed":
        raise MatchError("not_confirmed")
    a = current_assignment(db, job)
    if a is None or a.response not in ("pending", "accepted"):
        raise MatchError("not_pending")
    if a.response == "pending":
        a.response, a.responded_at = "accepted", now
        db.commit()
        log_event(log, "job_accepted", job_id=job.id, technician_id=job.technician_id)
    return a


def mark_accepted_on_departure(db, job: Job, now: datetime) -> None:
    """BR-07 ข้อ 2: ช่างกด "ออกเดินทาง" โดยยังไม่กดรับ ถือว่ารับงาน (ผู้เรียก commit)"""
    a = current_assignment(db, job)
    if a is not None and a.response == "pending":
        a.response, a.responded_at = "accepted", now


def reject(db, job: Job, now: datetime, reason: str | None = None, response: str = "rejected") -> Job:
    """REQ-FN-061 / REQ-FN-062: ปฏิเสธ (หรือไม่ตอบ) งานไป "กำลังหาช่างใหม่" ช่วงเวลาเดิมกลับเป็น "ว่าง" แล้วลองจับคู่ทันที"""
    if job.status != "confirmed":
        raise MatchError("not_confirmed")
    a = current_assignment(db, job)
    if a is None or a.response not in ("pending", "accepted"):
        raise MatchError("not_pending")
    a.response, a.responded_at, a.reason = response, now, (reason or "")[:200] or None
    old_tech = job.technician_id
    set_status(db, job, "rematching", now)
    slot = db.get(TimeSlot, job.slot_id)
    if slot is not None and slot.state != SLOT_FREE:
        slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_FREE, None, None  # REQ-DAT-003
    why = WHY[response].format(minutes=config.TECH_RESPONSE_MINUTES)
    queue.enqueue("technician", old_tech, MSG_TECH_RELEASED.format(job=job.id, why=why), job.id, now, db=db)
    log_event(log, "job_rejected", job_id=job.id, technician_id=old_tech, result=response)
    if not rematch(db, job, now):
        queue.enqueue("customer", job.customer_id, MSG_REMATCHING.format(job=job.id, hours=config.REMATCH_HOURS),
                      job.id, now, db=db)
    db.commit()
    return job


# ---- UC-05 ----

def candidate_slots(db, job: Job, now: datetime) -> list[tuple[float, TimeSlot]]:
    """BR-07 ข้อ 3: ช่วงเวลาที่ "ว่าง" เริ่มเวลาเดียวกับนัดเดิม ของช่างที่มีทักษะตรงประเภทงาน อยู่ในระยะ 15 กม. (BR-03)
    และยังไม่เคยได้รับงานนี้ เรียงจากใกล้ไปไกล ถ้าเท่ากันเรียงตามรหัสช่าง (ผลเดิมทุกครั้งที่ข้อมูลเดิม)"""
    release_expired_holds(db, now)
    address = db.get(ServiceAddress, job.address_id)
    tried = {a.technician_id for a in assignments_of(db, job)}
    out = []
    for slot in db.scalars(select(TimeSlot).where(TimeSlot.start == job.scheduled_start, TimeSlot.state == SLOT_FREE)):
        tech = db.get(Technician, slot.technician_id)
        if tech is None or tech.id in tried:
            continue
        if job.category not in [s.strip() for s in tech.skills.split(",")]:
            continue
        d = distance_km(tech.base_lat, tech.base_lng, address.lat, address.lng)
        if d > config.MAX_SERVICE_DISTANCE_KM:
            continue
        out.append((d, slot))
    out.sort(key=lambda x: (round(x[0], 3), x[1].technician_id))
    return out


def rematch(db, job: Job, now: datetime) -> bool:
    """REQ-FN-062 ได้ช่างใหม่: ช่วงเวลาใหม่ "จองแล้ว" งานกลับเป็น "ยืนยันแล้ว" มอบงานแบบช่างแทน แจ้งลูกค้าและช่างใหม่"""
    if job.status != "rematching":
        return False
    if job.scheduled_start - now < timedelta(hours=config.REMATCH_MIN_HOURS_BEFORE):
        return False
    found = candidate_slots(db, job, now)
    if not found:
        return False
    _, slot = found[0]
    slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_BOOKED, None, None
    job.technician_id, job.slot_id = slot.technician_id, slot.id
    job.slot = slot
    set_status(db, job, "confirmed", now)
    offer(db, job, now, via_rematch=True)
    tech = db.get(Technician, slot.technician_id)
    when = f"{slot.start:%d/%m %H:%M}"
    queue.enqueue("customer", job.customer_id, MSG_SUBSTITUTE.format(job=job.id, name=tech.name, when=when),
                  job.id, now, db=db)
    queue.enqueue("technician", tech.id, MSG_TECH_NEW.format(job=job.id, when=when,
                                                             minutes=config.TECH_RESPONSE_MINUTES), job.id, now, db=db)
    log_event(log, "job_rematched", job_id=job.id, technician_id=tech.id)
    return True


def rematch_started_at(db, job: Job) -> datetime | None:
    row = db.scalars(select(JobStatusHistory).where(JobStatusHistory.job_id == job.id,
                                                    JobStatusHistory.to_status == "rematching")
                     .order_by(JobStatusHistory.id.desc())).first()
    return row.at if row else None


def process_due(db, now: datetime, gateway=None) -> dict:
    """งานเบื้องหลังทุก 1 นาที (ops/scheduler.py): (1) ช่างไม่ตอบภายใน 30 นาที ถือว่าปฏิเสธ
    (2) งานที่ยังหาช่างใหม่ ลองจับคู่อีกครั้ง (3) ครบ 2 ชั่วโมง หรือใกล้เวลานัดเกินจับคู่ได้ ยกเลิกและคืนเต็ม (BR-01 R4)"""
    from app.refund.service import cancel_job
    from app.payments.gateway import get_gateway
    out = {"no_response": 0, "rematched": 0, "cancelled": 0}
    pending = db.scalars(select(JobAssignment).where(JobAssignment.response == "pending",
                                                     JobAssignment.respond_by <= now)).all()
    for a in pending:
        job = db.get(Job, a.job_id)
        if job is None or job.status != "confirmed" or job.technician_id != a.technician_id:
            continue
        reject(db, job, now, response="no_response")
        out["no_response"] += 1
    for job in db.scalars(select(Job).where(Job.status == "rematching")).all():
        if rematch(db, job, now):
            db.commit()
            out["rematched"] += 1
            continue
        started = rematch_started_at(db, job) or now
        too_late = job.scheduled_start - now < timedelta(hours=config.REMATCH_MIN_HOURS_BEFORE)
        if now >= started + timedelta(hours=config.REMATCH_HOURS) or too_late:
            cancel_job(db, job, "system", now, gateway or get_gateway())
            log_event(log, "rematch_failed", job_id=job.id)
            out["cancelled"] += 1
    return out


def decline_substitute(db, job: Job, now: datetime, gateway):
    """REQ-FN-063 ลูกค้าไม่รับช่างแทน: ยกเลิกตาม BR-01 R4 คืนมัดจำเต็ม ทำได้ก่อนช่างแทนออกเดินทางเท่านั้น"""
    from app.refund.service import cancel_job
    a = current_assignment(db, job)
    if a is None or not a.via_rematch:
        raise MatchError("not_substitute")
    if job.status != "confirmed":
        raise MatchError("not_confirmed")
    return cancel_job(db, job, "customer", now, gateway, substitute_declined=True)


def customer_job_view(db, job: Job) -> dict:
    """มุมมองลูกค้าต่องานของตัวเอง (UI-02-03 งานของฉัน) ไม่มีข้อมูลส่วนบุคคลของช่างนอกจากชื่อ"""
    tech = db.get(Technician, job.technician_id)
    a = current_assignment(db, job)
    substitute = bool(a and a.via_rematch)
    return {"job_id": job.id, "status": job.status, "category": job.category,
            "scheduled_start": job.scheduled_start.isoformat(),
            "technician_name": tech.name if tech and job.status != "rematching" else None,
            "substitute": substitute, "can_decline_substitute": substitute and job.status == "confirmed"}


# ---- CR-08 ช่างคนเดิม (REQ-FN-064, BR-08) ----

class NotPastTechnician(Exception):
    """ช่างคนนี้ไม่อยู่ในรายการช่างที่เคยใช้ของลูกค้าคนนี้ (ตอบ 403 และบันทึกเหมือน REQ-SEC-010)"""


def past_technicians(db, customer_id: int, now: datetime) -> list[dict]:
    """BR-08 ข้อ 1: ช่างของงานที่ "เสร็จสิ้น" ของลูกค้าคนนี้ใน 12 เดือนที่ผ่านมา ไม่ซ้ำคน ล่าสุดก่อน ไม่เกิน 3 คน"""
    since = now - timedelta(days=30 * config.PAST_TECHNICIAN_MONTHS)
    jobs = db.scalars(select(Job).where(Job.customer_id == customer_id, Job.status == "done",
                                        Job.scheduled_start >= since).order_by(Job.scheduled_start.desc())).all()
    out, seen = [], set()
    for j in jobs:
        if j.technician_id in seen:
            continue
        seen.add(j.technician_id)
        tech = db.get(Technician, j.technician_id)
        out.append({"technician_id": tech.id, "name": tech.name, "last_job_id": j.id, "last_category": j.category,
                    "last_scheduled_start": j.scheduled_start.isoformat()})
        if len(out) >= config.PAST_TECHNICIAN_MAX:
            break
    return out


# ข้อความเมื่อช่างคนเดิมจองไม่ได้ (UI-07-01 รายการ "ต้องตรง" ที่เพิ่มโดย CR-08) อยู่ที่นี่ที่เดียว
PAST_REASONS = {
    "no_skill": "ช่าง {name} ไม่รับงานประเภท {category} กรุณาค้นหาช่างคนอื่น",
    "out_of_range": "ที่อยู่นี้อยู่นอกพื้นที่ให้บริการของช่าง {name} กรุณาค้นหาช่างคนอื่น",
    "no_slots": "ช่าง {name} ยังไม่มีช่วงเวลาว่างใน {days} วันข้างหน้า กรุณาค้นหาช่างคนอื่น",
}


def past_technician_slots(db, customer_id: int, technician_id: int, category: str, address: ServiceAddress,
                          now: datetime) -> dict:
    """BR-08 ข้อ 2 ถึง 4: กฎเดิมของการจองใช้ครบ (ทักษะ BR-03 BR-02 ช่วง 7 วัน) ไม่มีคิวรอ"""
    if technician_id not in {t["technician_id"] for t in past_technicians(db, customer_id, now)}:
        raise NotPastTechnician()
    tech = db.get(Technician, technician_id)
    out = {"technician_id": tech.id, "name": tech.name, "available": False, "reason": None, "message": "", "slots": []}
    fmt = {"name": tech.name, "category": category, "days": config.SEARCH_DAYS_AHEAD}
    if category not in [s.strip() for s in tech.skills.split(",")]:
        out.update(reason="no_skill", message=PAST_REASONS["no_skill"].format(**fmt))
        return out
    if distance_km(tech.base_lat, tech.base_lng, address.lat, address.lng) > config.MAX_SERVICE_DISTANCE_KM:
        out.update(reason="out_of_range", message=PAST_REASONS["out_of_range"].format(**fmt))
        return out
    release_expired_holds(db, now)
    day_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=config.SEARCH_DAYS_AHEAD)
    slots = db.scalars(select(TimeSlot).where(TimeSlot.technician_id == tech.id, TimeSlot.start >= day_start,
                                              TimeSlot.start < day_end).order_by(TimeSlot.start)).all()
    free = [s for s in slots if slot_visible_to(s, customer_id)]
    if not free:
        out.update(reason="no_slots", message=PAST_REASONS["no_slots"].format(**fmt))
        return out
    out.update(available=True, slots=[{"slot_id": s.id, "start": s.start.isoformat(), "end": s.end.isoformat()}
                                      for s in free])
    return out
