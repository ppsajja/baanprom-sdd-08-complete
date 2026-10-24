"""CR-14 endpoint ของ UC-04 (specs/008-schedule/plan.md ข้อ 4) ช่างมาจาก token เท่านั้น (REQ-SEC-014)
GET /me/schedule, POST /me/slots, POST /me/slots/{id}/close, POST /me/days-off, DELETE /me/days-off/{day}
ช่วงเวลาของช่างคนอื่น ตอบ 403 และบันทึกความพยายาม (REQ-SEC-010)"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import current_technician
from app.auth.service import Actor
from app.clock import get_now
from app.db.models import TimeSlot
from app.db.session import get_db
from app.ops import audit
from app.privacy import get_logger, log_event
from app.schedule import service

router = APIRouter()
log = get_logger(__name__)
STATUS = {"has_jobs": 409, "overlap": 409, "not_free": 409, "day_off": 409, "already_day_off": 409, "not_day_off": 404}


class SlotIn(BaseModel):
    start: datetime


class DayOffIn(BaseModel):
    day: date


def error(e: service.ScheduleError) -> JSONResponse:
    return JSONResponse({"reason": e.reason, "message": e.message, **e.extra}, status_code=STATUS.get(e.reason, 422))


@router.get("/me/schedule")
def my_schedule(days: int | None = None, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
                now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-066 (UI-04-01)
    return service.schedule_view(db, actor.subject_id, now, days)


@router.post("/me/slots", status_code=201)
def add_slot(body: SlotIn, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
             now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-066 BR-10 ข้อ 1 ถึง 4
    try:
        slot, reopened = service.add_slot(db, actor.subject_id, body.start.replace(tzinfo=None), now)
    except service.ScheduleError as e:
        return error(e)
    log_event(log, "slot_added", technician_id=actor.subject_id, slot_id=slot.id)
    return {"slot_id": slot.id, "start": slot.start.isoformat(), "end": slot.end.isoformat(), "state": slot.state,
            "reopened": reopened}


@router.post("/me/slots/{slot_id}/close")
def close_slot(slot_id: int, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
               now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-066 BR-10 ข้อ 5 | REQ-SEC-010 ช่วงของช่างคนอื่นตอบ 403 แบบเดียวกับช่วงที่ไม่มี
    slot = db.get(TimeSlot, slot_id, with_for_update=True)
    if slot is None or slot.technician_id != actor.subject_id:
        raise audit.deny(db, "technician", actor.subject_id, None, "POST /me/slots/{id}/close", now)
    try:
        slot = service.close_slot(db, slot, now)
    except service.ScheduleError as e:
        return error(e)
    log_event(log, "slot_closed", technician_id=actor.subject_id, slot_id=slot.id)
    return {"slot_id": slot.id, "state": slot.state}


@router.post("/me/days-off", status_code=201)
def add_day_off(body: DayOffIn, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
                now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-067 BR-10 ข้อ 6 และ 7
    try:
        row, n = service.add_day_off(db, actor.subject_id, body.day, now)
    except service.ScheduleError as e:
        return error(e)
    log_event(log, "day_off_added", technician_id=actor.subject_id, count=n)
    return {"day": body.day.isoformat(), "closed_slots": n}


@router.delete("/me/days-off/{day}")
def remove_day_off(day: date, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
                   now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-067 BR-10 ข้อ 8
    try:
        n = service.remove_day_off(db, actor.subject_id, day, now)
    except service.ScheduleError as e:
        return error(e)
    return {"day": day.isoformat(), "reopened_slots": n}
