"""CR-07 REQ-OP-001 และ REQ-OP-005: /health (ระบบยังมีชีวิต) /ready (พร้อมรับงาน ต่อฐานข้อมูลได้) /metrics (ตัวนับต่อ endpoint ต่อนาที)
/health และ /ready เปิดให้ระบบเฝ้าดูเรียกได้โดยไม่มีข้อมูลภายใน /metrics เป็นของ ops (REQ-SEC-012)"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ops.guard import require_ops
from app.ops.metrics import metrics

router = APIRouter()


@router.get("/health")
def health():
    # REQ-OP-001: ระบบเฝ้าดูเรียกทุก 1 นาที นาทีที่เรียกไม่สำเร็จนับเป็นเวลาล่ม (AC-00-04)
    return {"ok": True}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    # REQ-OP-001 / คู่มือเหตุการณ์ที่ 2: แยก "ระบบยังตอบ" ออกจาก "ฐานข้อมูลใช้ได้"
    # CR-18 REQ-OP-009: เลือกตัวจริงของระบบภายนอกแล้วแต่ตั้งค่าไม่ครบ ตอบ 503 พร้อมชื่อระบบ (ไม่บอกค่าของกุญแจ)
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"ok": False, "database": "unavailable"}, status_code=503)
    from app.integrations import status
    rows = status()
    broken = [r["kind"] for r in rows if not r["configured"]]
    if broken:
        return JSONResponse({"ok": False, "database": "ok", "integrations_not_configured": broken}, status_code=503)
    return {"ok": True, "database": "ok"}  # รายการตัวจำลองที่ยังใช้อยู่ดูที่ /ops/integrations


@router.get("/ops/integrations", dependencies=[Depends(require_ops)])
def integrations():
    # CR-18 REQ-OP-009: ระบบภายนอกแต่ละตัวใช้ตัวไหน (รายการก่อนเปิดใช้จริงใน docs/handover/mocks-and-limits.md)
    from app.integrations import status
    return status()


@router.get("/metrics", dependencies=[Depends(require_ops)])
def read_metrics(db: Session = Depends(get_db)):
    # CR-13 (REQ-OP-008): ยอดรวมทุก process (ตาราง metric_minutes) บวกนาทีปัจจุบันของ process ที่ตอบ
    from app.ops.metrics import combined
    return combined(db, metrics).as_dicts()


@router.get("/ops/refunds/follow-up", dependencies=[Depends(require_ops)])
def refunds_follow_up(db: Session = Depends(get_db)):
    # CR-10 (Q-34 และ Q-41, AC-08-11): รายการคืนเงินที่ Finance ต้องปิดเองภายใน 1 วันทำการ
    # gateway ปฏิเสธ (declined) หรือไม่ทราบผล (unknown) ระบบไม่ส่งซ้ำเอง ไม่มีข้อมูลส่วนบุคคลในคำตอบ
    from sqlalchemy import select
    from app.db.models import Refund
    rows = db.scalars(select(Refund).where(Refund.result.in_(("declined", "unknown"))).order_by(Refund.id)).all()
    return [{"job_id": r.job_id, "amount": r.amount, "rule": r.rule, "result": r.result,
             "gateway_ref": r.gateway_ref} for r in rows]
