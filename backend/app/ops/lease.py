"""CR-13 (Q-67 ปิดใน EV-051, REQ-OP-008): รันหลังบ้านหลาย process ได้ งานเบื้องหลังที่ต้องทำที่เดียว
(ส่งข้อความ ลบข้อมูล เตือนคนเวร จับคู่ช่างใหม่) ทำโดย process ที่ถือสิทธิ์ (lease) ในตาราง scheduler_leases
ถือสิทธิ์ได้ครั้งละหนึ่ง process ต่ออายุทุกนาที ถ้า process นั้นดับ ไม่ต่อภายใน 90 วินาที process อื่นรับต่อเอง
ใช้ UPDATE แถวเดียวที่มีเงื่อนไข จึงใช้ได้ทั้ง PostgreSQL และ SQLite ไม่ต้องมีบริการอื่นเพิ่ม"""
import os
import socket
from datetime import datetime, timedelta

from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError

from app import config
from app.db.models import SchedulerLease

TICK = "tick"


def holder_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def acquire(db, holder: str, now: datetime, name: str = TICK) -> bool:
    """คืน True เมื่อ process นี้ถือสิทธิ์ (ได้ใหม่หรือต่ออายุ) ในรอบนี้"""
    until = now + timedelta(seconds=config.SCHEDULER_LEASE_SECONDS)
    res = db.execute(update(SchedulerLease)
                     .where(SchedulerLease.name == name,
                            or_(SchedulerLease.holder == holder, SchedulerLease.expires_at < now))
                     .values(holder=holder, expires_at=until))
    if res.rowcount == 1:
        db.commit()
        return True
    if db.get(SchedulerLease, name) is None:
        try:
            db.add(SchedulerLease(name=name, holder=holder, expires_at=until))
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False
    db.commit()
    return False
