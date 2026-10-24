"""CR-11 ตรรกะของ OTP และ session (specs/006-identity/rules.md BR-09, MD-STM-03)
REQ-SEC-013: OTP 6 หลัก หมดอายุ 5 นาที ลองผิดได้ 5 ครั้ง ขอใหม่ได้เมื่อครบ 60 วินาที ไม่เกิน 5 ครั้งต่อเบอร์ต่อชั่วโมง
REQ-SEC-014: token สุ่ม 32 ไบต์ เก็บเฉพาะค่าแฮช อายุ 30 วัน (ลูกค้า) 12 ชั่วโมง (ช่าง) ออกจากระบบแล้วใช้ไม่ได้ทันที
รหัส OTP และ token ไม่ลงฐานข้อมูลเป็นค่าจริง ไม่ลง log (REQ-PRV-002 ใช้กับเบอร์โทรด้วย)"""
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select, func

from app import config
from app.db.models import Account, OtpChallenge, AuthSession, Customer, ServiceAddress, Technician
from app.notify.queue import Notifier, NotifierTimeout
from app.privacy import get_logger, log_event

log = get_logger(__name__)

ROLES = ("customer", "technician")
# ข้อความ OTP ที่ส่งทาง IF-02 (รายการ "ต้องตรง" ของ UI-02-01 อ้างข้อความนี้) อยู่ที่นี่ที่เดียว
OTP_TEXT = "รหัส OTP บ้านพร้อม {code} ใช้ได้ {minutes} นาที ห้ามบอกรหัสนี้กับผู้อื่น รวมทั้งเจ้าหน้าที่"


class AuthError(Exception):
    """reason: invalid_phone / too_soon / too_many / wrong_code / expired / locked / used / not_verified /
    already_registered / notify_down ผู้เรียกแปลงเป็นรหัส HTTP ใน router.py"""
    def __init__(self, reason: str, **extra):
        self.reason, self.extra = reason, extra


@dataclass
class Actor:
    role: str
    subject_id: int
    session_id: int


def normalize_phone(phone: str) -> str:
    """ตัดทุกอย่างที่ไม่ใช่ตัวเลข เบอร์ไทยต้องขึ้นต้นด้วย 0 ยาว 9 หรือ 10 หลัก"""
    digits = re.sub(r"\D", "", phone or "")
    if not re.fullmatch(r"0\d{8,9}", digits):
        raise AuthError("invalid_phone")
    return digits


def format_phone(digits: str) -> str:
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _code_hash(challenge_id: int, code: str) -> str:
    return _hash(f"{challenge_id}:{code}")


def account_of(db, role: str, phone_norm: str) -> Account | None:
    return db.scalars(select(Account).where(Account.role == role, Account.phone_norm == phone_norm,
                                            Account.disabled_at.is_(None))).first()


def request_otp(db, role: str, phone: str, now: datetime, notifier: Notifier) -> tuple[OtpChallenge, str | None]:
    """REQ-SEC-013 ขั้นขอ OTP คืน (คำขอ, รหัส) รหัสคืนให้ผู้เรียกเฉพาะเพื่อ test และโหมด development (router ตัดสิน)
    ตอบเหมือนกันทุกกรณีที่เบอร์ถูกรูปแบบ ช่างที่ไม่มีบัญชีได้คำขอที่ไม่ส่งข้อความ (sent = False)"""
    if role not in ROLES:
        raise AuthError("invalid_role")
    phone_norm = normalize_phone(phone)
    recent = db.scalars(select(OtpChallenge).where(OtpChallenge.phone_norm == phone_norm, OtpChallenge.role == role,
                                                   OtpChallenge.created_at > now - timedelta(hours=1))
                        .order_by(OtpChallenge.id.desc())).all()
    if recent and (now - recent[0].created_at).total_seconds() < config.OTP_RESEND_SECONDS:
        wait = config.OTP_RESEND_SECONDS - int((now - recent[0].created_at).total_seconds())
        raise AuthError("too_soon", retry_after_seconds=max(wait, 1))
    if len(recent) >= config.OTP_MAX_PER_HOUR:
        raise AuthError("too_many")
    for old in recent:  # คำขอใหม่ทำให้รหัสเก่าที่ยังไม่ใช้ใช้ไม่ได้ (เหลือรหัสที่ใช้ได้ทีละหนึ่ง)
        if old.used_at is None and old.replaced_at is None:
            old.replaced_at = now
    send = role == "customer" or account_of(db, role, phone_norm) is not None
    code = f"{secrets.randbelow(10 ** config.OTP_DIGITS):0{config.OTP_DIGITS}d}"
    ch = OtpChallenge(role=role, phone_norm=phone_norm, code_hash="", sent=send, created_at=now,
                      expires_at=now + timedelta(minutes=config.OTP_TTL_MINUTES), wrong_attempts=0)
    db.add(ch)
    db.flush()
    ch.code_hash = _code_hash(ch.id, code)
    if send:
        try:
            notifier.send_otp(format_phone(phone_norm), OTP_TEXT.format(code=code, minutes=config.OTP_TTL_MINUTES),
                              timeout_seconds=config.NOTIFY_TIMEOUT_SECONDS)
        except NotifierTimeout:
            db.rollback()
            raise AuthError("notify_down")
    db.commit()
    log_event(log, "otp_requested", role=role, challenge_id=ch.id)  # ไม่มีเบอร์และรหัส
    return ch, (code if send else None)


def _usable(ch: OtpChallenge | None, now: datetime) -> OtpChallenge:
    if ch is None or ch.replaced_at is not None:
        raise AuthError("expired")
    if ch.used_at is not None:
        raise AuthError("used")
    if ch.wrong_attempts >= config.OTP_MAX_WRONG_ATTEMPTS:
        raise AuthError("locked")
    if now >= ch.expires_at:
        raise AuthError("expired")
    return ch


def verify_otp(db, challenge_id: int, code: str, now: datetime) -> OtpChallenge:
    """REQ-SEC-013 ตรวจรหัส ผิดนับหนึ่งครั้ง ครบ 5 ครั้งล็อกคำขอนี้ (ต้องขอรหัสใหม่) ถูกแล้วบันทึก verified_at"""
    ch = _usable(db.get(OtpChallenge, challenge_id), now)
    if ch.verified_at is not None:
        return ch
    ok = ch.sent and hmac.compare_digest(ch.code_hash, _code_hash(ch.id, (code or "").strip()))
    if not ok:
        ch.wrong_attempts += 1
        db.commit()
        log_event(log, "otp_wrong", role=ch.role, challenge_id=ch.id, attempts=ch.wrong_attempts)
        left = config.OTP_MAX_WRONG_ATTEMPTS - ch.wrong_attempts
        if left <= 0:
            raise AuthError("locked")
        raise AuthError("wrong_code", attempts_left=left)
    ch.verified_at = now
    db.commit()
    return ch


def issue_session(db, account: Account, now: datetime, lifetime: timedelta | None = None) -> tuple[str, AuthSession]:
    if lifetime is None:
        lifetime = (timedelta(days=config.SESSION_DAYS_CUSTOMER) if account.role == "customer"
                    else timedelta(hours=config.SESSION_HOURS_TECHNICIAN))
    token = secrets.token_urlsafe(32)
    sess = AuthSession(token_hash=_hash(token), account_id=account.id, role=account.role,
                       subject_id=account.subject_id, created_at=now, expires_at=now + lifetime)
    db.add(sess)
    db.commit()
    log_event(log, "session_issued", role=account.role, actor_id=account.subject_id)
    return token, sess


def login(db, ch: OtpChallenge, now: datetime) -> tuple[str, AuthSession] | None:
    """หลังยืนยัน OTP: มีบัญชีแล้ว ออก session (ใช้คำขอนี้ไปแล้ว) | ลูกค้าใหม่ คืน None ให้ลงทะเบียนต่อ"""
    account = account_of(db, ch.role, ch.phone_norm)
    if account is None:
        return None
    ch.used_at = now
    return issue_session(db, account, now)


def register_customer(db, challenge_id: int, name: str, address_text: str, lat: float, lng: float,
                      now: datetime) -> tuple[str, AuthSession, Customer]:
    """REQ-FN-058 ลูกค้าใหม่: ต้องยืนยัน OTP ของคำขอนี้แล้ว และทำให้เสร็จภายใน REGISTRATION_WINDOW_MINUTES"""
    ch = db.get(OtpChallenge, challenge_id)
    if ch is None or ch.role != "customer":
        raise AuthError("not_verified")
    if ch.used_at is not None:
        raise AuthError("used")
    if ch.verified_at is None:
        raise AuthError("not_verified")
    if now >= ch.verified_at + timedelta(minutes=config.REGISTRATION_WINDOW_MINUTES):
        raise AuthError("expired")
    if account_of(db, "customer", ch.phone_norm) is not None:
        raise AuthError("already_registered")
    customer = Customer(name=name.strip(), phone=format_phone(ch.phone_norm))
    db.add(customer)
    db.flush()
    db.add(ServiceAddress(customer_id=customer.id, text=address_text.strip(), lat=lat, lng=lng))
    account = Account(role="customer", subject_id=customer.id, phone_norm=ch.phone_norm, created_at=now)
    db.add(account)
    ch.used_at = now
    db.flush()
    token, sess = issue_session(db, account, now)
    log_event(log, "customer_registered", customer_id=customer.id)
    return token, sess, customer


def create_technician_account(db, technician_id: int, phone: str, now: datetime) -> Account:
    """REQ-FN-060 บัญชีช่างออกโดยบ้านพร้อม (Ops หลัง SH-06 ตรวจเอกสารตัวตนของช่าง) ช่างไม่ลงทะเบียนเอง"""
    phone_norm = normalize_phone(phone)
    if db.get(Technician, technician_id) is None:
        raise AuthError("not_found")
    existing = db.scalars(select(Account).where(Account.role == "technician", Account.subject_id == technician_id,
                                                Account.disabled_at.is_(None))).first()
    if existing is not None:
        existing.phone_norm = phone_norm
        db.commit()
        return existing
    if account_of(db, "technician", phone_norm) is not None:
        raise AuthError("already_registered")
    acc = Account(role="technician", subject_id=technician_id, phone_norm=phone_norm, created_at=now)
    db.add(acc)
    db.commit()
    return acc


def actor_from_token(db, token: str | None, now: datetime) -> Actor | None:
    """REQ-SEC-014 ตัวตนมาจาก token เท่านั้น session หมดอายุหรือถูกยกเลิกแล้วคืน None"""
    if not token:
        return None
    sess = db.scalars(select(AuthSession).where(AuthSession.token_hash == _hash(token))).first()
    if sess is None or sess.revoked_at is not None or now >= sess.expires_at:
        return None
    return Actor(role=sess.role, subject_id=sess.subject_id, session_id=sess.id)


def logout(db, actor: Actor, now: datetime) -> None:
    sess = db.get(AuthSession, actor.session_id)
    if sess is not None and sess.revoked_at is None:
        sess.revoked_at = now
        db.commit()


def revoke_customer(db, customer_id: int, now: datetime) -> None:
    """REQ-PRV-010 กับ REQ-SEC-014: ลูกค้าขอลบข้อมูล ลบบัญชี (เบอร์) และยกเลิก session ทุกตัวของลูกค้าคนนี้"""
    for s in db.scalars(select(AuthSession).where(AuthSession.role == "customer", AuthSession.subject_id == customer_id,
                                                  AuthSession.revoked_at.is_(None))).all():
        s.revoked_at = now
    for a in db.scalars(select(Account).where(Account.role == "customer", Account.subject_id == customer_id)).all():
        db.delete(a)


def count_active_sessions(db, role: str, subject_id: int, now: datetime) -> int:
    return db.scalar(select(func.count()).select_from(AuthSession).where(
        AuthSession.role == role, AuthSession.subject_id == subject_id, AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > now)) or 0
