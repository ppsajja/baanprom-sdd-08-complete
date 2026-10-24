"""CR-18 เครื่องมือของ call center ด้วยกุญแจของตัวเอง (X-Call-Center-Token ปิด GAP-32)
- POST /call-center/assistant/switch หัวหน้า call center ปิดหรือเปิดผู้ช่วยเอง (REQ-AI-022 Q-60) ไม่ต้องสั่งคนเวร
- GET /call-center/assistant/tickets ตั๋วส่งต่อของผู้ช่วย
- POST /call-center/jobs/{id}/revert-reschedule เลื่อนกลับนัดที่ถูกเลื่อนผิด ไม่นับครั้งของ BR-06 (REQ-FN-075 ปิด GAP-31 Q-62)
ทุกตัวอยู่ในบัญชี endpoint ของ operations.md"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assistant import handoff, service as assistant
from app.auth.deps import require_call_center
from app.clock import get_now
from app.db.models import AssistantTicket, Job, JobReschedule, TimeSlot, SLOT_BOOKED, SLOT_FREE
from app.db.session import get_db
from app.notify.queue import queue
from app.privacy import get_logger, log_event

router = APIRouter(dependencies=[Depends(require_call_center)])
log = get_logger(__name__)

REVERT_MESSAGES = {
    "no_reschedule": "งานนี้ไม่มีการเลื่อนนัดที่เลื่อนกลับได้",
    "not_confirmed": "เลื่อนกลับได้เฉพาะงานที่สถานะ ยืนยันแล้ว",
    "slot_taken": "ช่วงเวลาเดิมไม่ว่างแล้ว กรุณาหาเวลาใหม่กับลูกค้า",
}


class SwitchIn(BaseModel):
    enabled: bool


@router.post("/call-center/assistant/switch")
def switch(body: SwitchIn, db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    assistant.set_enabled(db, body.enabled, now)
    log_event(log, "assistant_switched", actor_role="call_center", result="enabled" if body.enabled else "disabled")
    return {"enabled": body.enabled, "at": now.isoformat()}


@router.get("/call-center/assistant/tickets")
def tickets(db: Session = Depends(get_db)):
    rows = db.scalars(select(AssistantTicket).order_by(AssistantTicket.id)).all()
    return [handoff.ticket_view(db, t) for t in rows]


@router.post("/call-center/jobs/{job_id}/revert-reschedule")
def revert_reschedule(job_id: int, db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    """ย้อนการเลื่อนนัดครั้งล่าสุด (ของลูกค้าหรือผู้ช่วย) กลับไปช่วงเวลาเดิม ช่วงเดิมต้องยังว่าง แจ้งลูกค้าและช่าง"""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "ไม่พบงาน")
    last = db.scalars(select(JobReschedule).where(JobReschedule.job_id == job.id).order_by(JobReschedule.id.desc())).first()
    if last is None or last.by_role == "call_center":
        return JSONResponse({"reason": "no_reschedule", "message": REVERT_MESSAGES["no_reschedule"]}, status_code=409)
    if job.status != "confirmed":
        return JSONResponse({"reason": "not_confirmed", "message": REVERT_MESSAGES["not_confirmed"]}, status_code=409)
    back = db.get(TimeSlot, last.from_slot_id, with_for_update=True)
    if back is None or back.state != SLOT_FREE:
        return JSONResponse({"reason": "slot_taken", "message": REVERT_MESSAGES["slot_taken"]}, status_code=409)
    current = db.get(TimeSlot, job.slot_id)
    db.add(JobReschedule(job_id=job.id, from_slot_id=current.id, to_slot_id=back.id, from_start=job.scheduled_start,
                         to_start=back.start, reference=f"REVERT-{last.id}", by_role="call_center", at=now))
    current.state, current.held_by_customer_id, current.hold_expires_at = SLOT_FREE, None, None
    back.state, back.held_by_customer_id, back.hold_expires_at = SLOT_BOOKED, None, None
    job.slot_id, job.scheduled_start = back.id, back.start
    text = f"งาน #{job.id} เจ้าหน้าที่แก้นัดกลับเป็น {back.start:%d/%m %H:%M}"
    queue.enqueue("customer", job.customer_id, text, job.id, now, db=db)
    queue.enqueue("technician", job.technician_id, text, job.id, now, db=db)
    db.commit()
    log_event(log, "reschedule_reverted", actor_role="call_center", job_id=job.id)
    return {"job_id": job.id, "scheduled_start": job.scheduled_start.isoformat(), "slot_id": job.slot_id}
