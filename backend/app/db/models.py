"""ตารางตาม plan.md ข้อ 3 (MD-DOM-01) ชื่อสถานะตาม glossary.md"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# REQ-DAT-002 สถานะงาน 8 ค่า ตาม MD-STM-01
JOB_STATUSES = (
    "pending_payment",   # รอชำระเงิน
    "confirmed",         # ยืนยันแล้ว
    "auto_cancelled",    # ยกเลิกอัตโนมัติ
    "rematching",        # กำลังหาช่างใหม่
    "en_route",          # ช่างกำลังเดินทาง
    "in_progress",       # กำลังดำเนินงาน
    "done",              # เสร็จสิ้น
    "cancelled",         # ยกเลิก
)

# สถานะช่วงเวลา ตาม MD-DOM-01 TimeSlot.state
SLOT_FREE, SLOT_HELD, SLOT_BOOKED = "free", "held", "booked"


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))  # PII REQ-PRV-002 ห้ามลง log
    # CR-07 REQ-PRV-010: เวลาที่ลบเบอร์ ชื่อ ที่อยู่ และพิกัดแล้ว (None = ยังไม่ลบ) migration m002
    erased_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ServiceAddress(Base):
    __tablename__ = "service_addresses"  # AS-03 ลูกค้าหนึ่งคนมีได้หลายที่
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    text: Mapped[str] = mapped_column(String(200))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)


class Technician(Base):
    __tablename__ = "technicians"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    skills: Mapped[str] = mapped_column(String(200))  # คั่นด้วยจุลภาค เช่น "ประปา,ไฟฟ้า"
    base_lat: Mapped[float] = mapped_column(Float)    # BR-03 จุดตั้งต้นของช่าง
    base_lng: Mapped[float] = mapped_column(Float)


class TimeSlot(Base):
    __tablename__ = "time_slots"  # REQ-FN-041, BR-02
    id: Mapped[int] = mapped_column(primary_key=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"))
    start: Mapped[datetime] = mapped_column(DateTime)
    end: Mapped[datetime] = mapped_column(DateTime)
    state: Mapped[str] = mapped_column(String(10), default=SLOT_FREE)
    held_by_customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # AS-07
    technician: Mapped[Technician] = relationship()


class Job(Base):
    __tablename__ = "jobs"  # REQ-FN-008, REQ-DAT-002
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"))
    address_id: Mapped[int] = mapped_column(ForeignKey("service_addresses.id"))
    category: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending_payment")
    deposit_amount: Mapped[int] = mapped_column(Integer)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    customer: Mapped[Customer] = relationship()
    slot: Mapped[TimeSlot] = relationship()


class JobStatusHistory(Base):
    __tablename__ = "job_status_history"  # REQ-DAT-002 ประวัติ 24 เดือน
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20))
    at: Mapped[datetime] = mapped_column(DateTime)


class Payment(Base):
    __tablename__ = "payments"  # REQ-IF-001
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    amount: Mapped[int] = mapped_column(Integer)
    gateway_ref: Mapped[str] = mapped_column(String(50))
    result: Mapped[str] = mapped_column(String(10))  # success / failed / timeout / pending (CR-07 REQ-QA-010 gateway ไม่ตอบเลย)
    authorized_at: Mapped[datetime] = mapped_column(DateTime)


class Refund(Base):
    __tablename__ = "refunds"  # REQ-BR-001
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    amount: Mapped[int] = mapped_column(Integer)
    rule: Mapped[str] = mapped_column(String(5))  # R1..R6
    # CR-06 (REQ-IF-010): คำขอคืนเงินส่งผ่าน gateway ด้วย reference ของการชำระเดิม ผลเป็น approved / declined / not_sent
    # CR-07 (REQ-QA-010, Q-41): gateway ไม่ตอบคำขอคืนเงิน ผลเป็น unknown ไม่ส่งซ้ำเอง Finance ปิดภายใน 1 วันทำการ
    gateway_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result: Mapped[str | None] = mapped_column(String(10), nullable=True)


class SecurityEvent(Base):
    """CR-07 REQ-SEC-010: บันทึกคำขอที่ถูกปฏิเสธสิทธิ์ (kind = denied) และการส่งเบอร์ลูกค้าให้ช่าง (kind = phone_revealed)
    เก็บผู้ส่ง เลขงาน endpoint และเวลา ไม่เก็บเบอร์ ชื่อ หรือที่อยู่ (REQ-PRV-002)"""
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    actor_role: Mapped[str] = mapped_column(String(20))   # customer / technician
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # ไม่ใช่ foreign key เพราะเลขที่ขออาจไม่มีจริง
    endpoint: Mapped[str] = mapped_column(String(80))
    at: Mapped[datetime] = mapped_column(DateTime)


class ErasureRequest(Base):
    """CR-07 REQ-PRV-010: คำขอลบข้อมูลของลูกค้า กำหนดเสร็จ = requested_at + 30 วัน (ค่าของบริษัท)
    if02_* คือผลการส่งคำขอลบไปยังระบบส่งข้อความ (IF-02)"""
    __tablename__ = "erasure_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer)
    requested_at: Mapped[datetime] = mapped_column(DateTime)
    due_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    if02_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    if02_result: Mapped[str | None] = mapped_column(String(20), nullable=True)


def set_status(db, job: Job, to_status: str, now: datetime) -> None:
    """เปลี่ยนสถานะงานและบันทึกประวัติ (REQ-DAT-002) ที่เดียวทั้งระบบ"""
    assert to_status in JOB_STATUSES, to_status
    db.add(JobStatusHistory(job_id=job.id, from_status=job.status, to_status=to_status, at=now))
    job.status = to_status


# ---- CR-09 ผู้ช่วยตอบคำถามและเลื่อนนัด (UC-14) ตารางใหม่ทั้งหมด ไม่แก้ตารางเดิม (migration m003) ----

class JobReschedule(Base):
    """REQ-FN-056 / BR-06 ขั้น 3: บันทึกการเลื่อนนัด 1 แถวต่อ 1 ครั้ง นับแถวเพื่อตรวจ BR-06 ข้อ 2
    reference คือรหัสของคำขอ (เช่น P-12 จากข้อเสนอของผู้ช่วย) ใช้กันการเลื่อนซ้ำเมื่อเรียกซ้ำ (REQ-AI-012)"""
    __tablename__ = "job_reschedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    from_slot_id: Mapped[int] = mapped_column(Integer)
    to_slot_id: Mapped[int] = mapped_column(Integer)
    from_start: Mapped[datetime] = mapped_column(DateTime)
    to_start: Mapped[datetime] = mapped_column(DateTime)
    reference: Mapped[str | None] = mapped_column(String(40), nullable=True, unique=True)
    by_role: Mapped[str] = mapped_column(String(20))   # customer (ผ่าน API หรือผ่านผู้ช่วยด้วยสิทธิ์ของลูกค้า)
    at: Mapped[datetime] = mapped_column(DateTime)


class AssistantConversation(Base):
    """UC-14 บทสนทนา 1 ครั้ง ไม่จำข้ามบทสนทนา (Q-58) context_job_id คืองานที่กำลังคุยในบทสนทนานี้"""
    __tablename__ = "assistant_conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    context_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    declines: Mapped[int] = mapped_column(Integer, default=0)   # REQ-AI-012 เงื่อนไขที่ 3


class AssistantTurn(Base):
    """REQ-AI-013 บันทึกคำตอบ 1 แถวต่อ 1 ข้อความ เก็บพอที่จะสร้างคำตอบซ้ำได้ (REQ-AI-020 ชั้น 3)
    masked_text คือข้อความลูกค้าหลังปิดบังเบอร์โทร อีเมล เลขบัตร (Q-57) facts คือข้อมูลที่ค้นมา (ไม่มีข้อมูลส่วนบุคคลของลูกค้าตั้งแต่ต้น)"""
    __tablename__ = "assistant_turns"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("assistant_conversations.id"))
    customer_id: Mapped[int] = mapped_column(Integer)
    at: Mapped[datetime] = mapped_column(DateTime)
    masked_text: Mapped[str] = mapped_column(String(600))
    intent: Mapped[str] = mapped_column(String(30))
    outcome: Mapped[str] = mapped_column(String(30))       # answered / no_data / refused / handoff / not_found / proposal / clarify / limited / disabled
    facts: Mapped[str] = mapped_column(String(4000))        # JSON
    prompt_version: Mapped[str] = mapped_column(String(20))
    model_version: Mapped[str] = mapped_column(String(40))
    guard: Mapped[str] = mapped_column(String(200))         # ผลรั้วขาออก เช่น passed หรือ blocked:phone,ungrounded_time
    answer: Mapped[str] = mapped_column(String(2000))
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)


class AssistantProposal(Base):
    """REQ-AI-011 ข้อเสนอเลื่อนนัดที่รอลูกค้ายืนยัน (MD-STM-02) ค่าที่แสดงในสรุปคือค่าที่ส่ง API (D-14-03)
    status: pending / confirmed / declined / expired / unknown / failed"""
    __tablename__ = "assistant_proposals"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("assistant_conversations.id"))
    customer_id: Mapped[int] = mapped_column(Integer)
    job_id: Mapped[int] = mapped_column(Integer)
    technician_id: Mapped[int] = mapped_column(Integer)
    old_slot_id: Mapped[int] = mapped_column(Integer)
    new_slot_id: Mapped[int] = mapped_column(Integer)
    old_start: Mapped[datetime] = mapped_column(DateTime)
    new_start: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AssistantAction(Base):
    """REQ-AI-013 บันทึกการกระทำระดับ 2 แยกจากบันทึกคำตอบ ใช้ตอบ "ทำไมนัดฉันถูกเลื่อน" ได้ภายใน 1 นาที"""
    __tablename__ = "assistant_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int] = mapped_column(Integer)
    customer_id: Mapped[int] = mapped_column(Integer)
    masked_text: Mapped[str] = mapped_column(String(600))    # ข้อความที่ลูกค้าขอเลื่อน (ปิดบังแล้ว)
    interpretation: Mapped[str] = mapped_column(String(300))  # ผู้ช่วยตีความว่าอะไร
    tool: Mapped[str] = mapped_column(String(40))
    args: Mapped[str] = mapped_column(String(300))            # JSON ค่าที่ส่ง
    confirmed_at: Mapped[datetime] = mapped_column(DateTime)
    result: Mapped[str] = mapped_column(String(40))
    prompt_version: Mapped[str] = mapped_column(String(20))
    model_version: Mapped[str] = mapped_column(String(40))
    at: Mapped[datetime] = mapped_column(DateTime)


class AssistantTicket(Base):
    """REQ-AI-005 / REQ-AI-012 / REQ-AI-022 ตั๋วส่งต่อ call center (เหตุ: out_of_scope, unclear_intent, tool_error,
    declined_twice, beyond_rule, customer_request, complaint) reply_due_at ใช้กับคำร้องเรียน"""
    __tablename__ = "assistant_tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(Integer)
    customer_id: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(30))
    intent: Mapped[str] = mapped_column(String(30))
    turn_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    reply_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")


class AssistantSetting(Base):
    """REQ-AI-022 ค่าเปิดปิดผู้ช่วย อยู่ในฐานข้อมูล จึงปิดได้ทันทีโดยไม่ต้อง deploy"""
    __tablename__ = "assistant_settings"
    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))
    updated_at: Mapped[datetime] = mapped_column(DateTime)


# ---- R2 CR-11 ตัวตนของผู้ใช้ (UC-01 ช่างเข้าสู่ระบบ, UC-02 ลูกค้าลงทะเบียนและเข้าสู่ระบบ) specs/006-identity ----
# ตารางใหม่ทั้งหมด ไม่แก้ตารางเดิม (migration m004) เบอร์โทรเป็น PII (REQ-PRV-002) ห้ามลง log

class Account(Base):
    """บัญชีเข้าสู่ระบบ 1 แถวต่อ 1 คน role = customer / technician subject_id = customers.id หรือ technicians.id
    phone_norm คือเบอร์ที่ตัดเครื่องหมายออกเหลือตัวเลข (ใช้ค้นตอนขอ OTP) ลบทั้งแถวเมื่อลูกค้าขอลบข้อมูล (REQ-PRV-010)"""
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("role", "phone_norm", name="uq_accounts_role_phone"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[int] = mapped_column(Integer)
    phone_norm: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OtpChallenge(Base):
    """REQ-SEC-013 คำขอ OTP 1 ครั้ง (MD-STM-03) เก็บเฉพาะค่าแฮชของรหัส ไม่เก็บรหัสจริง
    sent = False เมื่อไม่มีบัญชีช่างของเบอร์นี้ (ไม่ส่งข้อความ แต่ตอบเหมือนกัน กันการเดาว่าเบอร์ไหนมีบัญชี)"""
    __tablename__ = "otp_challenges"
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    phone_norm: Mapped[str] = mapped_column(String(20), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    sent: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    wrong_attempts: Mapped[int] = mapped_column(Integer, default=0)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    replaced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuthSession(Base):
    """REQ-SEC-014 session ของผู้ที่เข้าสู่ระบบแล้ว เก็บค่าแฮชของ token (sha256) ไม่เก็บ token จริง"""
    __tablename__ = "auth_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    account_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---- R2 CR-12 ช่างรับหรือปฏิเสธงาน (UC-12) และจับคู่ช่างใหม่ (UC-05) specs/007-accept-rematch ----

class JobAssignment(Base):
    """REQ-FN-061 การมอบงานให้ช่าง 1 แถวต่อช่าง 1 คนต่องาน (MD-STM-04) response: pending / accepted / rejected / no_response
    via_rematch = True คือช่างแทนที่ระบบจับคู่ให้ (UC-05) ลูกค้าปฏิเสธช่างแทนได้ (BR-01 R4)"""
    __tablename__ = "job_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, index=True)
    technician_id: Mapped[int] = mapped_column(Integer)
    slot_id: Mapped[int] = mapped_column(Integer)
    via_rematch: Mapped[bool] = mapped_column(Boolean, default=False)
    offered_at: Mapped[datetime] = mapped_column(DateTime)
    respond_by: Mapped[datetime] = mapped_column(DateTime)
    response: Mapped[str] = mapped_column(String(20), default="pending")
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)


# ---- R2 CR-13 คิวข้อความในฐานข้อมูล และงานเบื้องหลังเมื่อรันหลาย process (Q-67) ----

class NotificationMessage(Base):
    """REQ-OP-008 ข้อความถึงลูกค้าและช่าง 1 แถวต่อ 1 ข้อความ เขียนในธุรกรรมเดียวกับการเปลี่ยนงาน จึงไม่หายเมื่อหลังบ้านเริ่มใหม่"""
    __tablename__ = "notification_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    to_role: Mapped[str] = mapped_column(String(20))
    to_id: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(500))
    job_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    due_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    gave_up: Mapped[bool] = mapped_column(Boolean, default=False)


class SchedulerLease(Base):
    """REQ-OP-008 งานเบื้องหลังที่ต้องทำที่เดียว (ส่งข้อความ ลบข้อมูล เตือนคนเวร จับคู่ช่างใหม่) ทำโดย process ที่ถือสิทธิ์อยู่"""
    __tablename__ = "scheduler_leases"
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    holder: Mapped[str] = mapped_column(String(80))
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class MetricMinute(Base):
    """REQ-OP-005 ตัวนับต่อ endpoint ต่อนาทีที่รวมจากทุก process (แต่ละ process ส่งยอดของนาทีที่จบแล้วเข้ามาบวก)"""
    __tablename__ = "metric_minutes"
    endpoint: Mapped[str] = mapped_column(String(120), primary_key=True)
    minute: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    requests: Mapped[int] = mapped_column(Integer, default=0)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    empty_results: Mapped[int] = mapped_column(Integer, default=0)
    total_ms: Mapped[float] = mapped_column(Float, default=0.0)
    max_ms: Mapped[float] = mapped_column(Float, default=0.0)


# ---- R2 ส่วน B (migration m005) ตารางใหม่ทั้งหมด ไม่แก้ตารางเดิม ----

# CR-14 (UC-04, specs/008-schedule): ช่วงเวลาที่ช่างปิดเอง หรือปิดเพราะวันหยุด ไม่ปรากฏในการค้นหา การจอง และการจับคู่ (BR-10)
SLOT_CLOSED = "closed"


class TechnicianDayOff(Base):
    """CR-14 REQ-FN-067 วันหยุดของช่าง 1 แถวต่อ 1 วัน ช่วงเวลาที่ "ว่าง" ของวันนั้นเป็น closed ทั้งหมด"""
    __tablename__ = "technician_days_off"
    __table_args__ = (UniqueConstraint("technician_id", "day", name="uq_days_off_tech_day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    technician_id: Mapped[int] = mapped_column(Integer, index=True)
    day: Mapped[datetime] = mapped_column(DateTime)       # เที่ยงคืนของวันนั้น
    created_at: Mapped[datetime] = mapped_column(DateTime)
    closed_slot_ids: Mapped[str] = mapped_column(String(2000), default="[]")  # JSON ช่วงที่ปิดเพราะวันหยุดนี้ (BR-10 ข้อ 8)


class Rating(Base):
    """CR-15 REQ-FN-068 (UC-11) คะแนนของลูกค้าต่องานที่เสร็จสิ้น 1 แถวต่อ 1 งาน (BR-11 ข้อ 3)
    comment เก็บหลังปิดบังเบอร์ อีเมล เลขบัตร (REQ-PRV-012) counted = False เมื่อเข้า BR-11 ข้อ 5 (เบอร์ของลูกค้าตรงกับช่าง)"""
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, unique=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    technician_id: Mapped[int] = mapped_column(Integer, index=True)
    stars: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(300), default="")
    counted: Mapped[bool] = mapped_column(Boolean, default=True)
    at: Mapped[datetime] = mapped_column(DateTime)


class ReconciliationRun(Base):
    """CR-16 REQ-FN-070 (UC-13) การกระทบยอด 1 ครั้งต่อรายงาน 1 ไฟล์ของ gateway (IF-01) report_sha256 กันการนำเข้าซ้ำโดยไม่รู้ตัว"""
    __tablename__ = "reconciliation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_date: Mapped[datetime] = mapped_column(DateTime)
    report_sha256: Mapped[str] = mapped_column(String(64))
    rows_in_report: Mapped[int] = mapped_column(Integer)
    matched: Mapped[int] = mapped_column(Integer, default=0)
    differences: Mapped[int] = mapped_column(Integer, default=0)
    at: Mapped[datetime] = mapped_column(DateTime)


class ReconciliationItem(Base):
    """CR-16 รายการต่าง 1 แถวต่อ 1 รายการ kind: missing_in_report / missing_in_system / amount_mismatch / status_mismatch
    / refund_unknown_resolved / refund_unknown_still ไม่มีข้อมูลส่วนบุคคล (มีแค่เลขงาน reference ยอด)"""
    __tablename__ = "reconciliation_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(30))
    entry_type: Mapped[str] = mapped_column(String(10))   # capture / refund
    reference: Mapped[str] = mapped_column(String(50))
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    system_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    report_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    system_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    report_status: Mapped[str | None] = mapped_column(String(20), nullable=True)


class RefundResolution(Base):
    """CR-16 REQ-FN-071 (Q-41): ผลคืนเงินที่เปลี่ยนจากรายงานของ gateway บันทึกเดิมไม่ถูกเขียนทับเงียบ ๆ"""
    __tablename__ = "refund_resolutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    refund_id: Mapped[int] = mapped_column(Integer, index=True)
    run_id: Mapped[int] = mapped_column(Integer)
    from_result: Mapped[str] = mapped_column(String(10))
    to_result: Mapped[str] = mapped_column(String(10))
    at: Mapped[datetime] = mapped_column(DateTime)


class NotificationPreference(Base):
    """CR-17 REQ-FN-072 (UC-10) ช่องทางรับข้อความของลูกค้าหรือช่าง channel: sms (ค่าตั้งต้น) / line
    line_user_id มาจากการเชื่อมบัญชี LINE (IF-02) เป็นข้อมูลส่วนบุคคล ลบเมื่อลูกค้าขอลบข้อมูล"""
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("role", "subject_id", name="uq_notify_pref"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(10), default="sms")
    line_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    link_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    link_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class NotificationDelivery(Base):
    """CR-17 REQ-FN-073 ข้อความ 1 ข้อความส่งทางช่องทางไหน result: sent / failed / no_contact fallback = True เมื่อ LINE ไม่สำเร็จแล้วส่ง SMS แทน"""
    __tablename__ = "notification_deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    to_role: Mapped[str] = mapped_column(String(20))
    to_id: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(10))
    result: Mapped[str] = mapped_column(String(20))
    fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    at: Mapped[datetime] = mapped_column(DateTime)
