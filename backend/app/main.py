"""FastAPI app ของบ้านพร้อม R1: UC-07 (specs/002-booking), UC-09 (specs/003-job-status), UC-08 (specs/004-cancel-refund)
CR-09: UC-14 ผู้ช่วยตอบคำถามและเลื่อนนัด (specs/005-ai-assistant) app/assistant และ POST /jobs/{id}/reschedule
CR-07 (Constraint กลางรุ่น 1.1 ส่วน 6):
- REQ-SEC-012 โหมด production ปิด /docs /redoc /openapi.json และให้ /notifications/queue /metrics /ops/* ใช้ X-Ops-Token
- REQ-OP-005 ตัวนับคำขอต่อ endpoint ต่อนาที (middleware) และงานเบื้องหลังทุก 1 นาที (ops/scheduler.py)
- REQ-OP-001 /health และ /ready อยู่ใน ops/router.py
- OWASP API9:2023 บัญชี endpoint อยู่ใน docs/srs/operations.md ส่วน "บัญชี endpoint" POST /jobs/{id}/cancel ถูกปิด
  (router เดิมใน app/refund/router.py ถูกลบ การยกเลิกโดยลูกค้ามีทางเดียวคือ customer-cancel ของ 004)"""
import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime

from fastapi import Depends, FastAPI, Request

from app import config
from app.db.session import engine, SessionLocal
from app.db.migrations.m004_r2 import upgrade
from app.technicians.router import router as technicians_router
from app.booking.router import router as booking_router
from app.jobstatus.router import router as jobstatus_router
from app.cancel.router import router as cancel_router
from app.erasure.router import router as erasure_router
from app.ops.router import router as ops_router
from app.assistant.router import router as assistant_router, ops_router as assistant_ops_router
from app.ops.guard import require_ops
from app.ops.metrics import metrics, flush_to_db
from app.ops import scheduler, lease
from app.auth.router import router as auth_router, ops_router as auth_ops_router
from app.matching.router import router as matching_router
from app.notify.queue import queue


def minute_job(holder: str, now: datetime) -> bool:
    """CR-13 (REQ-OP-008): ทุก process ส่งตัวนับของนาทีที่จบแล้วเข้าตาราง แล้ว process ที่ถือสิทธิ์ทำ tick คืน True เมื่อทำ tick"""
    db = SessionLocal()
    try:
        flush_to_db(db, metrics, now)
        if lease.acquire(db, holder, now):
            scheduler.tick(db, now)
            return True
        return False
    finally:
        db.close()


async def _every_minute() -> None:
    # งานเบื้องหลังของระบบจริง (ไม่รันในโหมด test เพราะ test เรียก scheduler.tick เองด้วยเวลาจำลอง)
    # CR-13: เรียกในเธรดแยก ไม่ให้งานที่รอระบบภายนอก (IF-02 timeout 10 วินาที) ค้างลูปของคำขอ
    holder = lease.holder_id()
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.to_thread(minute_job, holder, datetime.now())
        except Exception:
            logging.getLogger("app.ops.scheduler").exception("minute_job_failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    upgrade(engine)  # T-01 สร้างตาราง m002 ของ CR-07 (T-17 ของ 002) m003 ของ CR-09 (T-01 ของ 005) และ m004 ของ R2 (T-01 ของ 006)
    task = None if config.app_env() == "test" else asyncio.create_task(_every_minute())
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def configure_logging() -> None:
    """DEF-02 (ตรวจรับ R1 OAT-6, GAP-37) รองรับ REQ-OP-005 บรรทัดที่ 3: log ของแอป (logger ชื่อ app) ออก stdout บรรทัดละ JSON
    ระดับ INFO ข้อความเป็น JSON จาก privacy.log_event อยู่แล้ว จึงใช้รูปแบบ %(message)s ไม่เพิ่มอะไร เรียกซ้ำได้ไม่ซ้อนตัวจัดการ
    ตัวจัดการผูกกับ sys.stdout ตอนเรียก ระบบจริงเก็บ stdout ของหลังบ้าน (journald หรือบริการ log ที่ Ops lead เลือก)"""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    for h in list(logger.handlers):
        if getattr(h, "_baanprom", False):
            logger.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._baanprom = True
    logger.addHandler(handler)


def create_app() -> FastAPI:
    configure_logging()
    production = config.app_env() == "production"
    app = FastAPI(title="บ้านพร้อม R2 - UC-01 UC-02 เข้าสู่ระบบ, UC-07 จองงาน, UC-09 สถานะงาน, UC-08 ยกเลิกและคืนเงิน, "
                        "UC-12 UC-05 รับงานและจับคู่ช่างใหม่, UC-14 ผู้ช่วย", lifespan=lifespan,
                  # รองรับ REQ-SEC-012 (AC-00-06): หน้าเอกสารที่ FastAPI เปิดให้เอง ปิดในระบบจริง
                  docs_url=None if production else "/docs",
                  redoc_url=None if production else "/redoc",
                  openapi_url=None if production else "/openapi.json")

    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        # รองรับ REQ-OP-005 บรรทัดที่ 1 (AC-00-01): นับตามแม่แบบของ path ไม่ใช่ path จริง
        t0 = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        endpoint = f"{request.method} {route.path}" if route is not None else f"{request.method} (ไม่มี route)"
        empty = endpoint == "GET /technicians" and response.headers.get("x-result-count") == "0"
        metrics.record(endpoint, response.status_code, (time.perf_counter() - t0) * 1000, datetime.now(), empty)
        return response

    app.include_router(ops_router)
    app.include_router(technicians_router)
    app.include_router(booking_router)
    app.include_router(jobstatus_router)   # CR-05 (specs/003-job-status)
    app.include_router(cancel_router)      # CR-06 (specs/004-cancel-refund)
    app.include_router(erasure_router)     # CR-07 REQ-PRV-010
    app.include_router(assistant_router)   # CR-09 (specs/005-ai-assistant) UC-14 ผู้ช่วย
    app.include_router(assistant_ops_router)  # CR-09 REQ-AI-022 ปุ่มหยุด และตั๋วของ call center (X-Ops-Token)
    app.include_router(auth_router)        # CR-11 (specs/006-identity) UC-01 UC-02
    app.include_router(auth_ops_router)    # CR-11 REQ-FN-060 ออกบัญชีช่าง (X-Ops-Token)
    app.include_router(matching_router)    # CR-12 (specs/007-accept-rematch) UC-12 UC-05 และ CR-08 ช่างคนเดิม

    @app.get("/notifications/queue", dependencies=[Depends(require_ops)])
    def notifications():
        # รองรับ REQ-FN-012 ใช้ตรวจใน test และหน้าแอดมิน | CR-07 REQ-SEC-012 ในระบบจริงต้องมี X-Ops-Token
        return queue.as_dicts()

    return app


app = create_app()
