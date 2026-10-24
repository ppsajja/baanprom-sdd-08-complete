"""CR-12 endpoint ของ UC-12 และ UC-05 (specs/007-accept-rematch/plan.md ข้อ 4) และ CR-08 ช่างคนเดิม (specs/002-booking)
POST /jobs/{id}/accept, POST /jobs/{id}/reject (ช่าง) | POST /jobs/{id}/decline-substitute (ลูกค้า)
GET /me/past-technicians, GET /me/past-technicians/{id}/slots (ลูกค้า) ทุกตัวตรวจสิทธิ์ด้วย ops/audit.py (REQ-SEC-010)"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import current_customer, current_technician
from app.auth.service import Actor
from app.clock import get_now
from app.db.models import ServiceAddress
from app.db.session import get_db
from app.jobstatus.service import technician_job_view
from app.matching import service
from app.matching.service import MatchError
from app.ops import audit
from app.payments.gateway import get_gateway
from app.refund.service import refund_message

router = APIRouter()


class RejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


def match_error(e: MatchError) -> JSONResponse:
    return JSONResponse({"reason": e.reason, "message": e.message}, status_code=409)


@router.post("/jobs/{job_id}/accept")
def accept(job_id: int, actor: Actor = Depends(current_technician), db: Session = Depends(get_db),
           now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-061 (UC-12 รับงาน)
    job = audit.job_of_technician(db, job_id, actor.subject_id, "POST /jobs/{job_id}/accept", now)
    try:
        service.accept(db, job, now)
    except MatchError as e:
        return match_error(e)
    return technician_job_view(job, now, db)


@router.post("/jobs/{job_id}/reject")
def reject(job_id: int, body: RejectIn | None = None, actor: Actor = Depends(current_technician),
           db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-061, REQ-FN-062 (UC-12 ปฏิเสธ แล้ว UC-05 จับคู่ช่างใหม่ทันที)
    job = audit.job_of_technician(db, job_id, actor.subject_id, "POST /jobs/{job_id}/reject", now)
    try:
        service.reject(db, job, now, reason=body.reason if body else None)
    except MatchError as e:
        return match_error(e)
    return {"job_id": job.id, "released": True}


@router.post("/jobs/{job_id}/decline-substitute")
def decline_substitute(job_id: int, actor: Actor = Depends(current_customer), db: Session = Depends(get_db),
                       now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-063 (BR-01 R4 ลูกค้าปฏิเสธช่างแทน คืนมัดจำเต็ม)
    job = audit.job_of_customer(db, job_id, actor.subject_id, "POST /jobs/{job_id}/decline-substitute", now)
    try:
        d, refund = service.decline_substitute(db, job, now, get_gateway())
    except MatchError as e:
        return match_error(e)
    return {"job_id": job.id, "status": job.status, "rule": d.rule, "refund_amount": refund.amount if refund else 0,
            "refund_result": refund.result if refund else None, "refund_message": refund_message(refund)}


@router.get("/me/past-technicians")
def past_technicians(actor: Actor = Depends(current_customer), db: Session = Depends(get_db),
                     now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-064 (CR-08, BR-08 ข้อ 1)
    return service.past_technicians(db, actor.subject_id, now)


@router.get("/me/past-technicians/{technician_id}/slots")
def past_technician_slots(technician_id: int, category: str, address_id: int, actor: Actor = Depends(current_customer),
                          db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-064 (BR-08 ข้อ 2 ถึง 4) ช่างที่ไม่เคยทำงานให้ลูกค้าคนนี้ ตอบ 403 และบันทึก (REQ-SEC-010)
    endpoint = "GET /me/past-technicians/{technician_id}/slots"
    address = db.get(ServiceAddress, address_id)
    if not address:
        raise HTTPException(404, "ไม่พบที่อยู่ให้บริการ")
    if address.customer_id != actor.subject_id:
        raise audit.deny(db, "customer", actor.subject_id, None, endpoint, now)
    try:
        out = service.past_technician_slots(db, actor.subject_id, technician_id, category, address, now)
    except service.NotPastTechnician:
        raise audit.deny(db, "customer", actor.subject_id, None, endpoint, now)
    db.commit()
    return out
