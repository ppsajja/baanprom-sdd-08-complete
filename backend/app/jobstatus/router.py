"""GET /technicians/{id}/jobs, POST /jobs/{id}/status, GET /jobs/{id}/history (specs/003-job-status/plan.md ข้อ 4)
CR-07: REQ-SEC-010 (POST status ตอบ 403 เมื่อไม่ใช่งานของช่างหรือไม่มีงาน และบันทึก AC-09-06, AC-09-14)
และบันทึกทุกครั้งที่ส่งเบอร์ลูกค้าให้ช่าง log ผ่าน log_event เท่านั้น (REQ-OP-005 บรรทัดที่ 3)
CR-11 (R2): ช่างมาจาก token ช่างเปิดรายการงานของช่างคนอื่นไม่ได้ (403 และบันทึก) GET /jobs/{id}/history ตรวจสิทธิ์แล้ว (GAP-24 ปิด)"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Job, Technician, JOB_STATUSES
from app.jobstatus import service
from app.clock import get_now
from app.privacy import get_logger, log_event
from app.ops import audit
from app.auth.deps import current_technician, current_reader, Reader
from app.auth.service import Actor

router = APIRouter()
log = get_logger(__name__)  # REQ-PRV-002 ทุก log ของโมดูลนี้ผ่านตัวกรองเบอร์โทร


class StatusIn(BaseModel):
    technician_id: int | None = None  # CR-11: ไม่ใช้แล้ว ช่างมาจาก token
    to_status: str


@router.get("/technicians/{technician_id}/jobs")
def technician_jobs(technician_id: int, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
                    now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-050, REQ-SEC-004 | CR-11: เปิดได้เฉพาะรายการของตัวเอง (REQ-SEC-010)
    if technician_id != actor.subject_id:
        raise audit.deny(db, "technician", actor.subject_id, None, "GET /technicians/{technician_id}/jobs", now)
    if not db.get(Technician, technician_id):
        raise HTTPException(404, "ไม่พบช่าง")
    data = service.list_jobs_for_technician(db, technician_id, now)
    _record_phones(db, technician_id, data, "GET /technicians/{technician_id}/jobs", now)
    # GAP-22: เดิม log ทั้งรายการ (ชื่อลูกค้าหลุดลง log ได้) ตอนนี้ log เฉพาะรหัสและจำนวน
    log_event(log, "technician_jobs_listed", technician_id=technician_id, count=len(data))
    return data


def _record_phones(db, technician_id: int, views: list[dict], endpoint: str, now: datetime) -> None:
    # REQ-SEC-010 บรรทัดที่ 4: บันทึกว่าช่างคนไหนได้เบอร์ของงานไหนเมื่อไร ไม่เก็บตัวเบอร์
    for v in views:
        if "customer_phone" in v:
            audit.record_phone_revealed(db, technician_id, v["job_id"], endpoint, now)
    db.commit()


@router.post("/jobs/{job_id}/status")
def change_status(job_id: int, body: StatusIn, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
                  now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-051, REQ-DAT-002, REQ-FN-053
    # รองรับ REQ-SEC-010 (CR-07, Q-47): ไม่ใช่งานของช่างคนนี้ และไม่มีงานเลขนี้ ตอบ 403 เหมือนกัน แล้วบันทึกความพยายาม
    technician_id = actor.subject_id
    job = audit.job_of_technician(db, job_id, technician_id, "POST /jobs/{job_id}/status", now)
    if body.to_status not in JOB_STATUSES:
        raise HTTPException(422, "ไม่รู้จักสถานะ")
    try:
        service.change_status(db, job, technician_id, body.to_status, now)
    except service.TransitionNotAllowed as e:
        return JSONResponse({"reason": "transition_not_allowed", "from_status": e.from_status,
                             "to_status": e.to_status, "message": "เปลี่ยนสถานะนี้ไม่ได้"}, status_code=409)
    log_event(log, "job_status_changed", job_id=job.id, status=job.status, technician_id=technician_id)
    view = service.technician_job_view(job, now, db)
    _record_phones(db, technician_id, [view], "POST /jobs/{job_id}/status", now)
    return view


@router.get("/jobs/{job_id}/history")
def history(job_id: int, reader: Reader = Depends(current_reader), db: Session = Depends(get_db),
            now: datetime = Depends(get_now)):
    # รองรับ REQ-DAT-002, REQ-FN-052 (ลูกค้าและ call center อ่านจากที่เดียวกับช่าง)
    # CR-11 (GAP-24 ปิด): เจ้าของงาน ช่างผู้รับมอบหมาย หรือ call center ไม่ใช่ตอบ 403 และบันทึก (REQ-SEC-010)
    job = audit.job_for_reader(db, job_id, reader.actor, reader.ops, "GET /jobs/{job_id}/history", now)
    return {"job_id": job.id, "status": job.status, "history": service.history_for(db, job)}
