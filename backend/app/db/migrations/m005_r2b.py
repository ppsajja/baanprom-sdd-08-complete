"""R2 ส่วน B (CR-14 ถึง CR-18): ตารางใหม่ technician_days_off, ratings, reconciliation_runs, reconciliation_items,
refund_resolutions, notification_preferences, notification_deliveries (create_all สร้างให้ เพราะ models.py มีครบ)
ไม่มีคอลัมน์ใหม่ในตารางเดิม time_slots.state ได้ค่าใหม่ closed (คอลัมน์ข้อความเดิม ไม่ต้อง ALTER)
เรียก m004 ก่อนเพื่อให้ฐานข้อมูลเก่าได้ครบทุกขั้น รันซ้ำได้"""
from sqlalchemy import text

from app.db.migrations import m004_r2

INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_payments_job ON payments (job_id)",
    "CREATE INDEX IF NOT EXISTS ix_refunds_job ON refunds (job_id)",
    "CREATE INDEX IF NOT EXISTS ix_payments_ref ON payments (gateway_ref)",
)


def upgrade(engine) -> None:
    m004_r2.upgrade(engine)
    with engine.begin() as conn:
        for sql in INDEXES:
            conn.execute(text(sql))
