"""R2 (CR-11, CR-12, CR-13): ตารางใหม่ accounts, otp_challenges, auth_sessions, job_assignments, notification_messages,
scheduler_leases, metric_minutes (create_all สร้างให้ เพราะ models.py มีครบ) ไม่มีคอลัมน์ใหม่ในตารางเดิม
CR-13 (Q-68): เพิ่ม index ของตารางเดิมที่คำค้นหาช่างและการตรวจสิทธิ์ใช้ทุกคำขอ ใช้ CREATE INDEX IF NOT EXISTS
ซึ่งใช้ได้ทั้ง PostgreSQL และ SQLite รันซ้ำได้ เรียก m003 ก่อนเพื่อให้ฐานข้อมูลเก่าได้ครบทุกขั้น"""
from sqlalchemy import text

from app.db.migrations import m003_cr09

INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_time_slots_tech_start ON time_slots (technician_id, start)",
    "CREATE INDEX IF NOT EXISTS ix_time_slots_state ON time_slots (state)",
    "CREATE INDEX IF NOT EXISTS ix_jobs_slot_status ON jobs (slot_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_jobs_customer ON jobs (customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_jobs_technician ON jobs (technician_id)",
    "CREATE INDEX IF NOT EXISTS ix_job_status_history_job ON job_status_history (job_id)",
    "CREATE INDEX IF NOT EXISTS ix_security_events_kind_at ON security_events (kind, at)",
    "CREATE INDEX IF NOT EXISTS ix_notification_messages_pending ON notification_messages (delivered_at, gave_up)",
)


def upgrade(engine) -> None:
    m003_cr09.upgrade(engine)  # create_all ของ m002 สร้างตารางใหม่ของ R2 ให้ด้วย
    with engine.begin() as conn:
        for sql in INDEXES:
            conn.execute(text(sql))
