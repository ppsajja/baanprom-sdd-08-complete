"""CR-07: งานที่ต้องทำทุก 1 นาทีในระบบจริง (main.py เรียกในงานเบื้องหลัง ยกเว้นโหมด test ที่ test เรียก tick เอง)
ลำดับ: ปิดล็อกที่หมดอายุ (REQ-QA-010) ส่งข้อความที่ค้าง (REQ-QA-010) ทำคำขอลบ (REQ-PRV-010)
ลบบันทึกการส่งเบอร์ที่เก่ากว่า 90 วัน (REQ-SEC-010) แล้วตรวจเกณฑ์เตือน (REQ-OP-005, REQ-SEC-010)
CR-09: ลบบันทึกคำตอบและบันทึกการกระทำของผู้ช่วยที่อายุเกิน 180 วัน (REQ-AI-013)
CR-12: ช่างไม่ตอบรับภายใน 30 นาที จับคู่ช่างใหม่ซ้ำ และยกเลิกเมื่อหาไม่ได้ใน 2 ชั่วโมง (matching.process_due)
CR-13 (REQ-OP-008): tick ทำโดย process ที่ถือสิทธิ์ (ops/lease.py) เท่านั้น การเตือนอ่านตัวนับรวมทุก process"""
from datetime import datetime, timedelta

from app.technicians.service import release_expired_holds
from app.notify.queue import queue, get_notifier
from app.erasure.service import process_due
from app.ops import audit, alerts
from app.ops.metrics import metrics
from app.assistant import records as assistant_records
from app.matching import service as matching
from app.ops.metrics import combined


def tick(db, now: datetime) -> None:
    release_expired_holds(db, now)
    db.commit()
    queue.deliver_due(get_notifier(), now)
    process_due(db, now, get_notifier())
    audit.purge_phone_view_log(db, now)
    assistant_records.purge(db, now)
    matching.process_due(db, now)
    db.commit()
    alerts.evaluate(db, combined(db, metrics, now - timedelta(minutes=30)), now)
