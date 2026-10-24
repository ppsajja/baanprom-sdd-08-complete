"""GET /jobs/{id}/refund-quote, POST /jobs/{id}/customer-cancel (specs/004-cancel-refund/plan.md ข้อ 4)
UC-08 ลูกค้ายกเลิกการจองและรับเงินคืน ใช้ตาราง BR-01 และ cancel_job ตัวเดียวกับ UC-07 (ไม่คัดลอกกฎ D-00-05)
CR-07: ช่องทางยกเลิกของลูกค้ามีช่องทางเดียวคือ endpoint นี้ (POST /jobs/{id}/cancel ของ 002 ถูกปิด OWASP API9:2023)
REQ-SEC-010: ไม่ใช่งานของลูกค้าคนนี้หรือไม่มีงาน ตอบ 403 เหมือนกันและบันทึกความพยายาม (MU-01, AC-08-10)
CR-11 (R2): ลูกค้ามาจาก token (REQ-SEC-014) customer_id ใน query และ body ไม่ใช้แล้ว"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Job
from app.refund import service
from app.clock import get_now
from app.payments.gateway import get_gateway
from app.privacy import get_logger, log_event
from app.ops import audit
from app.auth.deps import current_customer
from app.auth.service import Actor

router = APIRouter()
log = get_logger(__name__)  # REQ-PRV-002


class CustomerCancelIn(BaseModel):
    customer_id: int | None = None  # CR-11: ไม่ใช้แล้ว ลูกค้ามาจาก token


def _own_job(db: Session, job_id: int, customer_id: int, endpoint: str, now: datetime) -> Job:
    # รองรับ REQ-FN-054: ลูกค้าเห็นและยกเลิกได้เฉพาะงานของตัวเอง (การเข้าสู่ระบบจริงเลื่อนไป R2 จึงรับ customer_id ตรง ๆ)
    # CR-07 REQ-SEC-010 (Q-47): เดิมตอบ 404 ตอนนี้ตอบ 403 และบันทึกผู้ส่ง เวลา เลขงาน
    return audit.job_of_customer(db, job_id, customer_id, endpoint, now)


@router.get("/jobs/{job_id}/refund-quote")
def refund_quote(job_id: int, actor: Actor = Depends(current_customer), db: Session = Depends(get_db),
                 now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-054, REQ-BR-001 (AC-08-01): ยอดคืนที่แสดงมาจากตาราง BR-01 ตัวเดียวกับที่ใช้ยกเลิกจริง
    job = _own_job(db, job_id, actor.subject_id, "GET /jobs/{job_id}/refund-quote", now)
    if job.status in ("cancelled", "auto_cancelled"):
        return {"job_id": job.id, "status": job.status, "allowed": False, "rule": None,
                "refund_amount": 0, "message": service.MSG_ALREADY_CLOSED}
    d = service.quote(job, "customer", now)
    allowed = d.outcome in ("cancelled", "auto_cancelled")
    message = "" if allowed else (service.MSG_R3_PENDING if d.outcome == "pending_question" else service.MSG_R6_NOT_ALLOWED)
    # CR-10 (Q-14, AC-08-12): note บอกเหตุที่ยอดคืนถูกหัก (R3) ข้อความมาจากหลังบ้านที่เดียว
    return {"job_id": job.id, "status": job.status, "deposit_amount": job.deposit_amount,
            "scheduled_start": job.scheduled_start.isoformat(), "allowed": allowed, "rule": d.rule,
            "refund_amount": d.refund_amount or 0, "message": message, "note": service.note_for(d)}


@router.post("/jobs/{job_id}/customer-cancel")
def customer_cancel(job_id: int, body: CustomerCancelIn | None = None, actor: Actor = Depends(current_customer),
                    db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-054, REQ-BR-001, REQ-IF-010, REQ-DAT-002, REQ-DAT-003, REQ-FN-055
    job = _own_job(db, job_id, actor.subject_id, "POST /jobs/{job_id}/customer-cancel", now)
    try:
        d, refund = service.cancel_job(db, job, "customer", now, get_gateway())
    except service.CancelRejected as e:
        return JSONResponse({"rule": e.decision.rule, "outcome": e.decision.outcome, "message": e.message}, status_code=409)
    log_event(log, "customer_cancelled", customer_id=actor.subject_id, job_id=job.id, rule=d.rule)  # REQ-PRV-002
    # CR-10 (Q-34, AC-08-11): refund_message ไม่ว่างเมื่อ gateway ปฏิเสธหรือไม่ตอบ หน้าผลการยกเลิกแสดงแทนคำว่าคืนแล้ว
    return {"job_id": job.id, "status": job.status, "rule": d.rule,
            "refund_amount": refund.amount if refund else 0,
            "refund_result": refund.result if refund else None,
            "refund_message": service.refund_message(refund)}
