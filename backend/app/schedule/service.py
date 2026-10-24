"""CR-14 (UC-04 specs/008-schedule) ช่างจัดตารางเวลาว่างของตัวเอง ตามกฎ BR-10
- เพิ่มช่วงเวลาว่าง ช่วงละ SLOT_HOURS ชั่วโมง เริ่มตรงชั่วโมง ระหว่าง 08:00 ถึง 20:00 ล่วงหน้าไม่เกิน 30 วัน ไม่ซ้อนกัน
- ปิดช่วงที่ว่าง (state closed) ช่วงที่ล็อกหรือจองแล้วปิดไม่ได้ ช่วงที่ปิดไม่ปรากฏในการค้นหา การจอง การจับคู่ และการเลื่อนนัด
- วันหยุด ปิดช่วงที่ว่างของวันนั้นทั้งหมด วันที่มีช่วงที่ล็อกหรือจองอยู่ ประกาศวันหยุดไม่ได้ (ช่างต้องปฏิเสธงานก่อนผ่าน UC-12)
- ยกเลิกวันหยุด ช่วงที่ปิดเพราะวันหยุดและยังไม่เริ่ม กลับเป็นว่าง
ไม่ลบแถวช่วงเวลา (งานเดิมอ้าง slot_id อยู่) ปิดด้วยการเปลี่ยน state เท่านั้น"""
import json
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app import config
from app.db.models import Job, TechnicianDayOff, TimeSlot, SLOT_BOOKED, SLOT_CLOSED, SLOT_FREE, SLOT_HELD
from app.technicians.service import release_expired_holds

# ข้อความที่หน้าจอ UI-04-01 แสดง (รายการ "ต้องตรง") อยู่ที่นี่ที่เดียว
MESSAGES = {
    "not_on_hour": "เวลาเริ่มต้องตรงชั่วโมง เช่น 09:00",
    "outside_hours": f"ช่วงเวลาต้องอยู่ระหว่าง {config.WORK_START_HOUR:02d}:00 ถึง {config.WORK_END_HOUR:02d}:00",
    "too_soon": f"ช่วงเวลาต้องเริ่มอย่างน้อย {config.SCHEDULE_MIN_LEAD_HOURS} ชั่วโมงจากตอนนี้",
    "too_far": f"เพิ่มช่วงเวลาได้ล่วงหน้าไม่เกิน {config.SCHEDULE_DAYS_AHEAD} วัน",
    "overlap": "ช่วงเวลานี้ซ้อนกับช่วงที่มีอยู่แล้ว",
    "day_off": "วันนี้เป็นวันหยุดของคุณ ยกเลิกวันหยุดก่อนเพิ่มช่วงเวลา",
    "not_free": "ปิดได้เฉพาะช่วงที่ว่าง ช่วงที่ลูกค้ากำลังจองหรือจองแล้ว ต้องปฏิเสธงานก่อน",
    "has_jobs": "วันนี้มีงานที่จองแล้วหรือกำลังจอง กรุณาปฏิเสธงานก่อนประกาศวันหยุด",
    "past_day": "ประกาศวันหยุดได้เฉพาะวันพรุ่งนี้เป็นต้นไป",
    "already_day_off": "วันนี้เป็นวันหยุดอยู่แล้ว",
    "not_day_off": "วันนี้ไม่ใช่วันหยุด",
}


class ScheduleError(Exception):
    def __init__(self, reason: str, **extra):
        self.reason, self.extra, self.message = reason, extra, MESSAGES[reason]


def _midnight(d: date | datetime) -> datetime:
    return datetime(d.year, d.month, d.day)


def day_off_of(db, technician_id: int, day: datetime) -> TechnicianDayOff | None:
    return db.scalars(select(TechnicianDayOff).where(TechnicianDayOff.technician_id == technician_id,
                                                     TechnicianDayOff.day == _midnight(day))).first()


def add_slot(db, technician_id: int, start: datetime, now: datetime) -> tuple[TimeSlot, bool]:
    """BR-10 ข้อ 1 ถึง 4 คืน (ช่วงเวลา, เปิดช่วงเดิมที่ปิดไว้หรือไม่)"""
    end = start + timedelta(hours=config.SLOT_HOURS)
    if start.minute or start.second or start.microsecond:
        raise ScheduleError("not_on_hour")
    if start.hour < config.WORK_START_HOUR or end > start.replace(hour=0) + timedelta(hours=config.WORK_END_HOUR):
        raise ScheduleError("outside_hours")
    if start < now + timedelta(hours=config.SCHEDULE_MIN_LEAD_HOURS):
        raise ScheduleError("too_soon")
    if start > now + timedelta(days=config.SCHEDULE_DAYS_AHEAD):
        raise ScheduleError("too_far")
    if day_off_of(db, technician_id, start) is not None:
        raise ScheduleError("day_off")
    same = db.scalars(select(TimeSlot).where(TimeSlot.technician_id == technician_id, TimeSlot.start == start)).first()
    if same is not None:
        if same.state == SLOT_CLOSED:   # เปิดช่วงที่ปิดไว้ (ไม่สร้างแถวซ้ำ)
            same.state = SLOT_FREE
            db.commit()
            return same, True
        raise ScheduleError("overlap")
    overlap = db.scalars(select(TimeSlot).where(TimeSlot.technician_id == technician_id, TimeSlot.state != SLOT_CLOSED,
                                                TimeSlot.start < end, TimeSlot.end > start)).first()
    if overlap is not None:
        raise ScheduleError("overlap")
    slot = TimeSlot(technician_id=technician_id, start=start, end=end, state=SLOT_FREE)
    db.add(slot)
    db.commit()
    return slot, False


def close_slot(db, slot: TimeSlot, now: datetime) -> TimeSlot:
    """BR-10 ข้อ 5 ปิดได้เฉพาะช่วงที่ว่าง ปิดซ้ำได้ผลเดิม"""
    release_expired_holds(db, now)
    if slot.state == SLOT_CLOSED:
        return slot
    if slot.state != SLOT_FREE:
        raise ScheduleError("not_free")
    slot.state = SLOT_CLOSED
    db.commit()
    return slot


def slots_of_day(db, technician_id: int, day: datetime) -> list[TimeSlot]:
    d0 = _midnight(day)
    return db.scalars(select(TimeSlot).where(TimeSlot.technician_id == technician_id, TimeSlot.start >= d0,
                                             TimeSlot.start < d0 + timedelta(days=1)).order_by(TimeSlot.start)).all()


def add_day_off(db, technician_id: int, day: date, now: datetime) -> tuple[TechnicianDayOff, int]:
    """BR-10 ข้อ 6 และ 7 คืน (วันหยุด, จำนวนช่วงที่ปิด)"""
    d0 = _midnight(day)
    if d0 <= _midnight(now):
        raise ScheduleError("past_day")
    if day_off_of(db, technician_id, d0) is not None:
        raise ScheduleError("already_day_off")
    release_expired_holds(db, now)
    slots = slots_of_day(db, technician_id, d0)
    busy = [s for s in slots if s.state in (SLOT_HELD, SLOT_BOOKED)]
    if busy:
        jobs = db.scalars(select(Job.id).where(Job.slot_id.in_([s.id for s in busy]),
                                               Job.status.in_(("pending_payment", "confirmed")))).all()
        raise ScheduleError("has_jobs", job_ids=sorted(jobs))
    closed = [s for s in slots if s.state == SLOT_FREE]
    for s in closed:
        s.state = SLOT_CLOSED
    row = TechnicianDayOff(technician_id=technician_id, day=d0, created_at=now,
                           closed_slot_ids=json.dumps([s.id for s in closed]))
    db.add(row)
    db.commit()
    return row, len(closed)


def remove_day_off(db, technician_id: int, day: date, now: datetime) -> int:
    """BR-10 ข้อ 8 ช่วงที่ปิดเพราะวันหยุดและยังไม่เริ่ม กลับเป็นว่าง ช่วงที่ช่างปิดเองก่อนประกาศวันหยุดยังปิด"""
    row = day_off_of(db, technician_id, _midnight(day))
    if row is None:
        raise ScheduleError("not_day_off")
    reopened = 0
    for sid in json.loads(row.closed_slot_ids or "[]"):
        s = db.get(TimeSlot, sid)
        if s is not None and s.state == SLOT_CLOSED and s.start > now:
            s.state = SLOT_FREE
            reopened += 1
    db.delete(row)
    db.commit()
    return reopened


STATE_TH = {SLOT_FREE: "ว่าง", SLOT_HELD: "ลูกค้ากำลังจอง", SLOT_BOOKED: "จองแล้ว", SLOT_CLOSED: "ปิด"}


def schedule_view(db, technician_id: int, now: datetime, days: int | None = None) -> dict:
    """ตารางของช่างคนนี้ วันพรุ่งนี้ถึง SCHEDULE_VIEW_DAYS วัน ไม่มีข้อมูลลูกค้า (มีแค่เลขงาน)"""
    release_expired_holds(db, now)
    db.commit()
    days = days or config.SCHEDULE_VIEW_DAYS
    first = _midnight(now)
    rows = db.scalars(select(TimeSlot).where(TimeSlot.technician_id == technician_id, TimeSlot.start >= first,
                                             TimeSlot.start < first + timedelta(days=days)).order_by(TimeSlot.start)).all()
    offs = {r.day for r in db.scalars(select(TechnicianDayOff).where(TechnicianDayOff.technician_id == technician_id))}
    job_of = {j.slot_id: j.id for j in db.scalars(select(Job).where(Job.slot_id.in_([s.id for s in rows]),
                                                                   Job.status.in_(("pending_payment", "confirmed"))))} if rows else {}
    out = []
    for i in range(days):
        d = first + timedelta(days=i)
        out.append({"date": d.date().isoformat(), "day_off": d in offs,
                    "slots": [{"slot_id": s.id, "start": s.start.isoformat(), "end": s.end.isoformat(), "state": s.state,
                               "state_th": STATE_TH[s.state], "job_id": job_of.get(s.id),
                               "can_close": s.state == SLOT_FREE}
                              for s in rows if d <= s.start < d + timedelta(days=1)]})
    return {"technician_id": technician_id, "days": out,
            "rules": {"slot_hours": config.SLOT_HOURS, "from": f"{config.WORK_START_HOUR:02d}:00",
                      "to": f"{config.WORK_END_HOUR:02d}:00", "days_ahead": config.SCHEDULE_DAYS_AHEAD}}
