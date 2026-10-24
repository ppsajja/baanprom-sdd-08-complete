"""CR-11 endpoint ของ UC-01 และ UC-02 (specs/006-identity/plan.md ข้อ 4) ทุกตัวอยู่ในบัญชี endpoint ของ operations.md
POST /auth/otp, POST /auth/verify, POST /auth/register, POST /auth/logout, GET /me, POST /me/addresses, GET /me/jobs
POST /ops/technicians/{id}/account (X-Ops-Token) ออกบัญชีช่าง"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.auth import service
from app.auth.deps import current_actor, current_customer
from app.auth.service import Actor, AuthError
from app.clock import get_now
from app.db.models import Customer, ServiceAddress, Technician, Job
from app.db.session import get_db
from app.notify.queue import get_notifier
from app.ops.guard import require_ops
from app.privacy import get_logger, log_event

router = APIRouter()
ops_router = APIRouter(dependencies=[Depends(require_ops)])
log = get_logger(__name__)

# ข้อความที่หน้าจอแสดง (รายการ "ต้องตรง" ของ UI-02-01 UI-02-02 UI-01-01) อยู่ที่นี่ที่เดียว
MESSAGES = {
    "invalid_phone": "เบอร์โทรไม่ถูกต้อง",
    "invalid_role": "ไม่รู้จักประเภทผู้ใช้",
    "too_soon": "ขอรหัสใหม่ได้อีกครั้งใน {retry_after_seconds} วินาที",
    "too_many": "ขอรหัสเกินจำนวนที่กำหนด กรุณาลองใหม่ในอีก 1 ชั่วโมง",
    "wrong_code": "รหัสไม่ถูกต้อง เหลืออีก {attempts_left} ครั้ง",
    "expired": "รหัสหมดอายุแล้ว กรุณาขอรหัสใหม่",
    "locked": "ใส่รหัสผิดครบ 5 ครั้ง กรุณาขอรหัสใหม่",
    "used": "รหัสนี้ใช้ไปแล้ว กรุณาขอรหัสใหม่",
    "not_verified": "กรุณายืนยันรหัส OTP ก่อน",
    "already_registered": "เบอร์นี้ลงทะเบียนแล้ว กรุณาเข้าสู่ระบบ",
    "notify_down": "ระบบส่งข้อความขัดข้อง กรุณาลองใหม่อีกครั้ง",
    "not_found": "ไม่พบช่าง",
}
STATUS = {"invalid_phone": 422, "invalid_role": 422, "too_soon": 429, "too_many": 429, "wrong_code": 401,
          "expired": 410, "locked": 410, "used": 410, "not_verified": 409, "already_registered": 409,
          "notify_down": 503, "not_found": 404}


def error(e: AuthError) -> JSONResponse:
    return JSONResponse({"reason": e.reason, "message": MESSAGES[e.reason].format(**e.extra), **e.extra},
                        status_code=STATUS[e.reason])


class OtpIn(BaseModel):
    phone: str
    role: str = "customer"


class VerifyIn(BaseModel):
    challenge_id: int
    code: str


class RegisterIn(BaseModel):
    challenge_id: int
    name: str = Field(min_length=1, max_length=100)
    address_text: str = Field(min_length=1, max_length=200)
    lat: float
    lng: float


class AddressIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    lat: float
    lng: float


class TechAccountIn(BaseModel):
    phone: str


def session_out(token: str, sess, name: str) -> dict:
    return {"token": token, "role": sess.role, "subject_id": sess.subject_id, "name": name,
            "expires_at": sess.expires_at.isoformat()}


def name_of(db, role: str, subject_id: int) -> str:
    obj = db.get(Customer if role == "customer" else Technician, subject_id)
    return obj.name if obj else ""


@router.post("/auth/otp", status_code=202)
def request_otp(body: OtpIn, db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-059, REQ-FN-060, REQ-SEC-013 ตอบแบบเดียวกันทั้งเบอร์ที่มีและไม่มีบัญชี
    try:
        ch, code = service.request_otp(db, body.role, body.phone, now, get_notifier())
    except AuthError as e:
        return error(e)
    out = {"challenge_id": ch.id, "expires_at": ch.expires_at.isoformat(),
           "resend_after_seconds": config.OTP_RESEND_SECONDS}
    # REQ-SEC-012: รหัสส่งกลับในคำตอบเฉพาะโหมด test และ development (ระบบส่งข้อความยังเป็นของจำลอง) ระบบจริงไม่มีทางเห็น
    if config.app_env() != "production" and code is not None:
        out["dev_code"] = code
    return out


@router.post("/auth/verify")
def verify(body: VerifyIn, db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-059, REQ-FN-060, REQ-SEC-013, REQ-SEC-014
    try:
        ch = service.verify_otp(db, body.challenge_id, body.code, now)
        issued = service.login(db, ch, now)
    except AuthError as e:
        return error(e)
    if issued is None:
        # ลูกค้าใหม่ (UC-02 ทางลงทะเบียน) ไปหน้ากรอกชื่อและที่อยู่ ใช้ challenge_id เดิม
        until = ch.verified_at + timedelta(minutes=config.REGISTRATION_WINDOW_MINUTES)
        return {"needs_registration": True, "challenge_id": ch.id, "register_before": until.isoformat()}
    token, sess = issued
    return session_out(token, sess, name_of(db, sess.role, sess.subject_id))


@router.post("/auth/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-058, REQ-PRV-011 (พิกัดเก็บเพื่อคำนวณระยะ BR-03 เท่านั้น)
    try:
        token, sess, customer = service.register_customer(db, body.challenge_id, body.name, body.address_text,
                                                          body.lat, body.lng, now)
    except AuthError as e:
        return error(e)
    return session_out(token, sess, customer.name)


@router.post("/auth/logout")
def logout(actor: Actor = Depends(current_actor), db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    # REQ-SEC-014: token ที่ออกจากระบบแล้วใช้ไม่ได้อีก
    service.logout(db, actor, now)
    return {"ok": True}


def addresses_of(db, customer_id: int) -> list[dict]:
    rows = db.scalars(select(ServiceAddress).where(ServiceAddress.customer_id == customer_id)
                      .order_by(ServiceAddress.id)).all()
    return [{"address_id": a.id, "text": a.text} for a in rows]  # พิกัดไม่ส่งกลับหน้าจอ (REQ-PRV-011)


@router.get("/me")
def me(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    out = {"role": actor.role, "subject_id": actor.subject_id, "name": name_of(db, actor.role, actor.subject_id)}
    if actor.role == "customer":
        out["addresses"] = addresses_of(db, actor.subject_id)
    return out


@router.post("/me/addresses", status_code=201)
def add_address(body: AddressIn, actor: Actor = Depends(current_customer), db: Session = Depends(get_db)):
    # รองรับ REQ-FN-058 (AS-03 ลูกค้าหนึ่งคนมีหลายที่อยู่ Q-29 เลือกบน UI-07-01)
    a = ServiceAddress(customer_id=actor.subject_id, text=body.text.strip(), lat=body.lat, lng=body.lng)
    db.add(a)
    db.commit()
    return {"address_id": a.id, "text": a.text}


@router.get("/me/jobs")
def my_jobs(actor: Actor = Depends(current_customer), db: Session = Depends(get_db)):
    # REQ-FN-052 ลูกค้าเห็นงานของตัวเองเท่านั้น (REQ-SEC-010) ช่างแทนที่ปฏิเสธได้ดูจาก can_decline_substitute (REQ-FN-063)
    from app.matching.service import customer_job_view
    jobs = db.scalars(select(Job).where(Job.customer_id == actor.subject_id).order_by(Job.scheduled_start.desc())).all()
    return [customer_job_view(db, j) for j in jobs]


@ops_router.post("/ops/technicians/{technician_id}/account", status_code=201)
def technician_account(technician_id: int, body: TechAccountIn, db: Session = Depends(get_db),
                       now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-060: บัญชีช่างออกโดยบ้านพร้อม (Ops) หลัง SH-06 ตรวจตัวตนของช่าง
    try:
        acc = service.create_technician_account(db, technician_id, body.phone, now)
    except AuthError as e:
        return error(e)
    log_event(log, "technician_account_created", technician_id=technician_id)
    return {"technician_id": technician_id, "account_id": acc.id}
