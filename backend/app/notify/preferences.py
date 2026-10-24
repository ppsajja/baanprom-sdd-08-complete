"""CR-17 REQ-FN-072 ช่องทางรับข้อความของลูกค้าและช่าง (UC-10) และการเชื่อมบัญชี LINE (BR-12)
ขั้นการเชื่อม: ผู้ใช้กดเชื่อม ระบบให้รหัส 6 หลัก (อายุ 10 นาที) ผู้ใช้เพิ่มบัญชีทางการของบ้านพร้อมใน LINE แล้วพิมพ์รหัส
LINE ส่ง webhook มาพร้อมรหัสผู้ใช้ LINE ระบบตรวจลายเซ็นแล้วผูกรหัสนั้นกับบัญชี (POST /integrations/line/webhook)
ระบบเก็บแฮชของรหัสเชื่อม ไม่เก็บรหัสจริง รหัสผู้ใช้ LINE เป็นข้อมูลส่วนบุคคล ลบเมื่อขอลบข้อมูล (REQ-PRV-010)"""
import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select

from app import config
from app.db.models import NotificationPreference

MESSAGES = {
    "unknown_channel": "ไม่รู้จักช่องทางนี้",
    "line_not_linked": "กรุณาเชื่อมบัญชี LINE ก่อนเลือกรับข้อความทาง LINE",
}


class PreferenceError(Exception):
    def __init__(self, reason: str):
        self.reason, self.message = reason, MESSAGES[reason]


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def preference_of(db, role: str, subject_id: int) -> NotificationPreference | None:
    return db.scalars(select(NotificationPreference).where(NotificationPreference.role == role,
                                                           NotificationPreference.subject_id == subject_id)).first()


def _ensure(db, role: str, subject_id: int, now: datetime) -> NotificationPreference:
    p = preference_of(db, role, subject_id)
    if p is None:
        p = NotificationPreference(role=role, subject_id=subject_id, channel="sms", updated_at=now)
        db.add(p)
        db.flush()
    return p


def view(db, role: str, subject_id: int) -> dict:
    p = preference_of(db, role, subject_id)
    return {"channel": p.channel if p else "sms", "line_linked": bool(p and p.line_user_id),
            "channels": list(config.NOTIFY_CHANNELS)}


def set_channel(db, role: str, subject_id: int, channel: str, now: datetime) -> dict:
    if channel not in config.NOTIFY_CHANNELS:
        raise PreferenceError("unknown_channel")
    p = _ensure(db, role, subject_id, now)
    if channel == "line" and not p.line_user_id:
        raise PreferenceError("line_not_linked")
    p.channel, p.updated_at = channel, now
    db.commit()
    return view(db, role, subject_id)


def start_line_link(db, role: str, subject_id: int, now: datetime) -> tuple[str, datetime]:
    p = _ensure(db, role, subject_id, now)
    code = f"{secrets.randbelow(10 ** 6):06d}"
    p.link_code_hash, p.link_code_expires_at = _hash(code), now + timedelta(minutes=config.LINE_LINK_CODE_MINUTES)
    p.updated_at = now
    db.commit()
    return code, p.link_code_expires_at


def complete_line_link(db, code: str, line_user_id: str, now: datetime) -> NotificationPreference | None:
    """webhook ของ LINE: รหัสถูกและยังไม่หมดอายุ ผูกรหัสผู้ใช้ LINE ใช้รหัสได้ครั้งเดียว ไม่ถูกคืน None"""
    h = _hash(code.strip())
    p = db.scalars(select(NotificationPreference).where(NotificationPreference.link_code_hash == h)).first()
    if p is None or p.link_code_expires_at is None or p.link_code_expires_at < now:
        return None
    p.line_user_id, p.link_code_hash, p.link_code_expires_at, p.updated_at = line_user_id, None, None, now
    db.commit()
    return p


def unlink_line(db, role: str, subject_id: int, now: datetime) -> dict:
    p = _ensure(db, role, subject_id, now)
    p.line_user_id, p.channel, p.updated_at = None, "sms", now
    db.commit()
    return view(db, role, subject_id)


def erase(db, customer_id: int) -> None:
    """REQ-PRV-010: ลบรหัส LINE และรหัสเชื่อมของลูกค้า (เรียกจาก erasure.anonymize)"""
    p = preference_of(db, "customer", customer_id)
    if p is not None:
        p.line_user_id, p.link_code_hash, p.link_code_expires_at, p.channel = None, None, None, "sms"
