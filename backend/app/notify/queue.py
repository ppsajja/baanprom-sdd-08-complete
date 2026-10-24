"""REQ-FN-012 คิวข้อความแจ้งเตือน API แค่วางลงคิว ไม่รอผลส่ง (IF-02)
R1 เป็นคิวในหน่วยความจำ (ทีมเลือกเอง) CR-13 (R2, Q-67) ย้ายไปตาราง notification_messages ในฐานข้อมูลเดิม (REQ-OP-008)
CR-07 (REQ-QA-010 บรรทัดที่ 1 และ 4, AC-09-11, AC-09-13): ตัวส่งข้อความ deliver_due() เรียก IF-02 ด้วย timeout 10 วินาที
ถ้า IF-02 ไม่ตอบ ข้อความค้างในคิวและส่งซ้ำทุก 5 นาที ไม่เกิน 6 ครั้ง ส่งสำเร็จแล้วบันทึก delivered_at และไม่ส่งอีก"""
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta

from app import config


@dataclass
class Message:
    to_role: str        # customer / technician
    to_id: int
    text: str
    job_id: int
    created_at: datetime
    due_at: datetime    # ต้องส่งก่อนเวลานี้ (REQ-FN-012: created_at + 60 วินาที)
    # CR-07: สถานะการส่งจริง (QAS-1 ของ 003 วัด "ถึงจริง" จาก delivered_at)
    attempts: int = 0
    last_attempt_at: datetime | None = None
    delivered_at: datetime | None = None
    gave_up: bool = False
    id: int | None = None   # CR-13 เลขแถวใน notification_messages


class NotifierTimeout(Exception):
    """IF-02 ไม่ตอบภายใน NOTIFY_TIMEOUT_SECONDS"""


class Notifier:
    """IF-02 ระบบส่งข้อความ ระบบจริงเขียน class ที่เรียก HTTP ของผู้ให้บริการ ตอน test ใช้ FakeNotifier"""
    def send(self, msg: Message, timeout_seconds: int) -> None:
        raise NotImplementedError

    def request_erasure(self, customer_id: int, timeout_seconds: int) -> str:  # REQ-PRV-010 บรรทัดที่ 3
        raise NotImplementedError

    def send_otp(self, phone: str, text: str, timeout_seconds: int) -> None:
        """CR-11 REQ-SEC-013: ส่ง OTP ตรงไปที่ IF-02 ทันที ไม่ผ่านคิว (รหัสห้ามอยู่ในฐานข้อมูลและ log)"""
        raise NotImplementedError


@dataclass
class FakeNotifier(Notifier):
    """mode = ok | down (ไม่ตอบ) | sent เก็บข้อความที่ส่งสำเร็จ | erasures เก็บคำขอลบที่ส่งสำเร็จ
    otps เก็บ (เบอร์, ข้อความ) ของ OTP ที่ส่ง ใช้ใน test และโหมด development เท่านั้น (ของจริงส่งเป็น SMS)"""
    mode: str = "ok"
    sent: list[Message] = field(default_factory=list)
    erasures: list[int] = field(default_factory=list)
    otps: list[tuple[str, str]] = field(default_factory=list)
    calls: int = 0
    last_timeout_seconds: int | None = None

    def send(self, msg, timeout_seconds):
        self.calls += 1
        self.last_timeout_seconds = timeout_seconds
        if self.mode == "down":
            raise NotifierTimeout()
        self.sent.append(msg)

    def request_erasure(self, customer_id, timeout_seconds):
        self.last_timeout_seconds = timeout_seconds
        if self.mode == "down":
            raise NotifierTimeout()
        self.erasures.append(customer_id)
        return "accepted"

    def send_otp(self, phone, text, timeout_seconds):
        self.last_timeout_seconds = timeout_seconds
        if self.mode == "down":
            raise NotifierTimeout()
        self.otps.append((phone, text))


class NotificationQueue:
    """CR-13 (Q-67 ปิดใน EV-051, REQ-OP-008): คิวอยู่ในตาราง notification_messages ไม่ใช่หน่วยความจำ
    ผู้เรียกส่ง db มาด้วย ข้อความจึงถูกเขียนในธุรกรรมเดียวกับการเปลี่ยนงาน (งานเปลี่ยนแต่ข้อความหาย หรือกลับกัน เกิดไม่ได้)
    ถ้าไม่ส่ง db มา (โค้ดเดิม หรือเรียกจาก test) ใช้ session ของตัวเองแล้ว commit ทันที
    หน้าตาเดิมของคิว (enqueue, items, for_job, as_dicts, clear, deliver_due) ไม่เปลี่ยน ผู้ใช้เดิมจึงไม่ต้องแก้"""

    @staticmethod
    def _session():
        from app.db import session as db_session  # อ่านทุกครั้ง test เปลี่ยน SessionLocal เป็นฐานในหน่วยความจำ
        return db_session.SessionLocal()

    @staticmethod
    def _to_message(row) -> Message:
        return Message(id=row.id, to_role=row.to_role, to_id=row.to_id, text=row.text, job_id=row.job_id,
                       created_at=row.created_at, due_at=row.due_at, attempts=row.attempts,
                       last_attempt_at=row.last_attempt_at, delivered_at=row.delivered_at, gave_up=row.gave_up)

    # รองรับ REQ-FN-012: ทุกข้อความมีกำหนดส่งภายใน NOTIFY_WITHIN_SECONDS
    def enqueue(self, to_role: str, to_id: int, text: str, job_id: int, now: datetime, db=None) -> Message:
        from app.db.models import NotificationMessage
        row = NotificationMessage(to_role=to_role, to_id=to_id, text=text, job_id=job_id, created_at=now,
                                  due_at=now + timedelta(seconds=config.NOTIFY_WITHIN_SECONDS),
                                  attempts=0, gave_up=False)
        if db is not None:
            db.add(row)
            db.flush()  # ได้เลขข้อความ ผู้เรียก commit พร้อมงาน
            return self._to_message(row)
        s = self._session()
        try:
            s.add(row)
            s.commit()
            return self._to_message(row)
        finally:
            s.close()

    def _load(self, job_id: int | None = None) -> list[Message]:
        from sqlalchemy import select
        from app.db.models import NotificationMessage
        s = self._session()
        try:
            q = select(NotificationMessage).order_by(NotificationMessage.id)
            if job_id is not None:
                q = q.where(NotificationMessage.job_id == job_id)
            return [self._to_message(r) for r in s.scalars(q).all()]
        finally:
            s.close()

    @property
    def items(self) -> list[Message]:
        return self._load()

    def for_job(self, job_id: int) -> list[Message]:
        return self._load(job_id)

    def as_dicts(self) -> list[dict]:
        out = []
        for m in self._load():
            d = asdict(m)
            d.pop("id", None)
            out.append(d)
        return out

    def clear(self) -> None:
        from sqlalchemy import delete, inspect
        from app.db.models import NotificationMessage
        s = self._session()
        try:
            if inspect(s.get_bind()).has_table("notification_messages"):
                s.execute(delete(NotificationMessage))
                s.commit()
        finally:
            s.close()

    # รองรับ REQ-QA-010 บรรทัดที่ 4: ส่งข้อความที่ยังไม่ถึง ครั้งแรกทันที ครั้งต่อไปทุก NOTIFY_RETRY_MINUTES นาที
    # CR-13: อ่านจากตาราง และบันทึกผลกลับทีละข้อความ ข้อความที่ค้างก่อนหลังบ้านเริ่มใหม่จึงถูกส่งต่อ (AC-00-09)
    # บน PostgreSQL ล็อกแถวที่กำลังส่ง (SKIP LOCKED) ถ้ามีสอง process เรียกพร้อมกันจะไม่ส่งข้อความเดียวกันซ้ำ (AC-00-10)
    def deliver_due(self, notifier: Notifier, now: datetime) -> int:
        from sqlalchemy import select
        from app.db.models import NotificationMessage
        delivered = 0
        retry_gap = timedelta(minutes=config.NOTIFY_RETRY_MINUTES)
        s = self._session()
        try:
            q = (select(NotificationMessage)
                 .where(NotificationMessage.delivered_at.is_(None), NotificationMessage.gave_up.is_(False))
                 .order_by(NotificationMessage.id))
            if s.get_bind().dialect.name == "postgresql":
                q = q.with_for_update(skip_locked=True)
            for row in s.scalars(q).all():
                if row.last_attempt_at and now - row.last_attempt_at < retry_gap:
                    continue
                row.attempts += 1
                row.last_attempt_at = now
                try:
                    # CR-17: ตัวส่งที่เลือกช่องทาง (ChannelRouter) บันทึกผลในธุรกรรมเดียวกันกับคิว
                    if getattr(notifier, "wants_db", False):
                        notifier.send(self._to_message(row), timeout_seconds=config.NOTIFY_TIMEOUT_SECONDS, db=s)
                    else:
                        notifier.send(self._to_message(row), timeout_seconds=config.NOTIFY_TIMEOUT_SECONDS)
                except NotifierTimeout:
                    if row.attempts >= config.NOTIFY_MAX_ATTEMPTS:
                        row.gave_up = True  # คนเวรเห็นจากจำนวน gave_up ใน GET /notifications/queue (คู่มือเหตุการณ์ที่ 4)
                    continue
                row.delivered_at = now
                delivered += 1
            s.commit()
        finally:
            s.close()
        return delivered


queue = NotificationQueue()

# CR-17 (UC-10): ตัวส่งของระบบคือ ChannelRouter (SMS หรือ LINE ตามที่ผู้รับเลือก) สร้างตอนเรียกครั้งแรกจากค่าตั้ง
# test ที่ต้องการดูข้อความเองยังสลับเป็น FakeNotifier ได้ด้วย set_notifier เหมือนเดิม
_notifier: Notifier | None = None


def get_notifier() -> Notifier:
    global _notifier
    if _notifier is None:
        from app.notify.channels import build_from_config
        _notifier = build_from_config()
    return _notifier


def set_notifier(n: Notifier) -> None:
    global _notifier
    _notifier = n
