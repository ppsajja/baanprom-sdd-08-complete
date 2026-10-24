"""CR-16 endpoint ของ UC-13 ด้วยกุญแจของ Finance (X-Finance-Token GAP-32 ปิด) ทุกตัวอยู่ในบัญชี endpoint ของ operations.md
POST /finance/reconciliations {report_date, csv} | GET /finance/reconciliations/{id} | GET /finance/refunds/follow-up"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_finance
from app.clock import get_now
from app.db.models import ReconciliationRun, Refund
from app.db.session import get_db
from app.reconciliation import service

router = APIRouter(dependencies=[Depends(require_finance)])


class ReportIn(BaseModel):
    report_date: date
    csv: str = Field(max_length=2_000_000)


@router.post("/finance/reconciliations", status_code=201)
def import_report(body: ReportIn, db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-070, REQ-FN-071 (Q-41)
    try:
        run, already = service.reconcile(db, body.report_date, body.csv, now)
    except service.ReportError as e:
        db.rollback()
        return JSONResponse({"reason": "bad_report", "line": e.line, "message": f"บรรทัด {e.line}: {e.message}"},
                            status_code=422)
    return JSONResponse(service.run_view(db, run, already), status_code=200 if already else 201)


@router.get("/finance/reconciliations/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(ReconciliationRun, run_id)
    if run is None:
        raise HTTPException(404, "ไม่พบผลกระทบยอด")
    return service.run_view(db, run)


@router.get("/finance/refunds/follow-up")
def follow_up(db: Session = Depends(get_db)):
    # รายการเดียวกับ /ops/refunds/follow-up (CR-10) Finance เปิดด้วยกุญแจของตัวเอง
    rows = db.scalars(select(Refund).where(Refund.result.in_(("declined", "unknown"))).order_by(Refund.id)).all()
    return [{"job_id": r.job_id, "amount": r.amount, "rule": r.rule, "result": r.result, "gateway_ref": r.gateway_ref}
            for r in rows]
