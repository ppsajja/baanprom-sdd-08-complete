"""CR-17 (UC-10, specs/011-notifications) IF-02 แยกเป็นสองช่องทาง SMS และ LINE ผ่าน interface ที่สลับเป็นของจริงได้
ChannelRouter คือ Notifier ตัวที่ระบบใช้จริง: อ่านช่องทางที่ผู้รับเลือก (REQ-FN-072) ส่งทาง LINE ถ้าเชื่อมแล้ว
LINE ไม่สำเร็จ ส่ง SMS แทนในรอบเดียวกัน (REQ-FN-073) OTP ส่ง SMS เสมอ (REQ-SEC-013 รุ่น 1.4)
บันทึกผลทุกครั้งใน notification_deliveries (ช่องทาง ผล fallback) ไม่บันทึกข้อความ เบอร์ หรือรหัส LINE (REQ-PRV-002)
ตัวจำลอง MockSms MockLine เก็บข้อความในหน่วยความจำ (outbox) ไว้ให้ test และเครื่องทดสอบดู ไม่ส่งถึงโทรศัพท์จริง"""
import json
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from app.notify.queue import Message, Notifier, NotifierTimeout


class SmsSender:
    name = "none"

    def send(self, phone: str, text: str, timeout_seconds: int) -> None:
        raise NotImplementedError

    def request_erasure(self, customer_id: int, timeout_seconds: int) -> str:
        raise NotImplementedError


class LineSender:
    name = "none"

    def push(self, line_user_id: str, text: str, timeout_seconds: int) -> None:
        raise NotImplementedError


def _keep(box: deque, m: dict) -> None:
    """เก็บในหน่วยความจำ และถ้าเครื่องทดสอบตั้ง MOCK_OUTBOX_PATH เขียนต่อท้ายไฟล์ด้วย (หลาย process เห็นกล่องเดียวกัน)"""
    box.append(m)
    path = os.getenv("MOCK_OUTBOX_PATH")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")


def read_outbox_file() -> list[dict] | None:
    path = os.getenv("MOCK_OUTBOX_PATH")
    if not path:
        return None
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


@dataclass
class MockSms(SmsSender):
    name: str = "mock"
    mode: str = "ok"                      # ok | down (ไม่ตอบ)
    outbox: deque = field(default_factory=lambda: deque(maxlen=500))
    erasures: list[int] = field(default_factory=list)

    def send(self, phone, text, timeout_seconds):
        if self.mode == "down":
            raise NotifierTimeout()
        _keep(self.outbox, {"channel": "sms", "to": phone, "text": text, "at": datetime.now().isoformat()})

    def request_erasure(self, customer_id, timeout_seconds):
        if self.mode == "down":
            raise NotifierTimeout()
        self.erasures.append(customer_id)
        return "accepted"


@dataclass
class MockLine(LineSender):
    name: str = "mock"
    mode: str = "ok"                      # ok | down
    outbox: deque = field(default_factory=lambda: deque(maxlen=500))

    def push(self, line_user_id, text, timeout_seconds):
        if self.mode == "down":
            raise NotifierTimeout()
        _keep(self.outbox, {"channel": "line", "to": line_user_id, "text": text, "at": datetime.now().isoformat()})


def phone_of(db, role: str, subject_id: int) -> str:
    """เบอร์ของผู้รับ ลูกค้าใช้เบอร์ในตาราง customers (ลบแล้วเป็นค่าว่าง) ช่างใช้เบอร์ของบัญชีที่บ้านพร้อมออกให้"""
    from sqlalchemy import select
    from app.db.models import Account, Customer
    if role == "customer":
        c = db.get(Customer, subject_id)
        return c.phone if c is not None else ""
    acc = db.scalars(select(Account).where(Account.role == role, Account.subject_id == subject_id)).first()
    return acc.phone_norm if acc is not None else ""


class ChannelRouter(Notifier):
    """Notifier ของระบบจริง wants_db = True คิวส่ง session ที่กำลังส่งมาให้ บันทึกผลในธุรกรรมเดียวกับการส่ง"""
    wants_db = True

    def __init__(self, sms: SmsSender, line: LineSender):
        self.sms, self.line = sms, line

    def send(self, msg: Message, timeout_seconds: int, db=None) -> None:
        from app.db import session as db_session
        own = db is None
        s = db_session.SessionLocal() if own else db
        try:
            self._send(s, msg, timeout_seconds)
            if own:
                s.commit()
        finally:
            if own:
                s.close()

    def _send(self, db, msg: Message, timeout_seconds: int) -> None:
        from app.notify.preferences import preference_of
        from app.db.models import NotificationDelivery

        def record(channel, result, fallback=False):
            db.add(NotificationDelivery(message_id=msg.id, to_role=msg.to_role, to_id=msg.to_id, channel=channel,
                                        result=result, fallback=fallback, at=datetime.now()))

        pref = preference_of(db, msg.to_role, msg.to_id)
        fallback = False
        if pref is not None and pref.channel == "line" and pref.line_user_id:
            try:
                self.line.push(pref.line_user_id, msg.text, timeout_seconds)
                record("line", "sent")
                return
            except Exception:  # LINE ไม่ตอบหรือปฏิเสธ (เช่น ผู้ใช้บล็อกบัญชี) ส่ง SMS แทนในรอบนี้
                record("line", "failed")
                fallback = True
        phone = phone_of(db, msg.to_role, msg.to_id)
        if not phone:
            record("sms", "no_contact", fallback)  # ไม่มีเบอร์ (ลูกค้าขอลบข้อมูลแล้ว) ไม่มีทางส่ง ไม่ส่งซ้ำ
            return
        try:
            self.sms.send(phone, msg.text, timeout_seconds)
        except NotifierTimeout:
            record("sms", "failed", fallback)
            raise  # คิวส่งซ้ำทุก 5 นาทีตามเดิม (REQ-QA-010)
        record("sms", "sent", fallback)

    def send_otp(self, phone: str, text: str, timeout_seconds: int) -> None:
        self.sms.send(phone, text, timeout_seconds)  # OTP ไม่ส่งทาง LINE (REQ-SEC-013 รุ่น 1.4)

    def request_erasure(self, customer_id: int, timeout_seconds: int) -> str:
        # LINE ไม่มีบริการลบข้อมูลของผู้ใช้ ระบบลบรหัส LINE ของลูกค้าในฐานข้อมูลเอง (preferences.erase)
        return self.sms.request_erasure(customer_id, timeout_seconds)


def build_from_config() -> ChannelRouter:
    """REQ-IF-012: SMS_ADAPTER และ LINE_ADAPTER = mock (ค่าตั้งต้น) หรือ http (ตัวจริง ต้องตั้ง URL และกุญแจ)
    เครื่องทดสอบตั้งพฤติกรรมของตัวจำลองได้ด้วย MOCK_SMS_MODE MOCK_LINE_MODE = ok | down (ซ้อม OAT-5) ระบบจริงต้องไม่ใช้ตัวจำลอง"""
    import os
    from app.integrations import choice
    if choice("sms") == "http":
        from app.integrations.http_messaging import HttpSmsSender
        sms = HttpSmsSender()
    else:
        sms = MockSms(mode=os.getenv("MOCK_SMS_MODE", "ok"))
    if choice("line") == "http":
        from app.integrations.http_messaging import LineMessagingSender
        line = LineMessagingSender()
    else:
        line = MockLine(mode=os.getenv("MOCK_LINE_MODE", "ok"))
    return ChannelRouter(sms, line)
