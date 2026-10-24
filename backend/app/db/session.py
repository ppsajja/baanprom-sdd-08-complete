"""สร้าง engine และ session ของ SQLAlchemy (ทีมเลือกเอง ดู D-00-02 ในไฟล์กลาง)"""
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from app import config


class Base(DeclarativeBase):
    pass


def make_engine(url: str = config.DATABASE_URL):
    # SQLite ในหน่วยความจำต้องใช้ connection เดียวร่วมกันทุก session ไม่งั้นตารางหาย
    if url.startswith("sqlite"):
        return create_engine(
            url, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    # CR-13 (GAP-42): ขนาด pool เท่ากับจำนวนเธรดที่ FastAPI ใช้รัน endpoint (40) คำขอที่ได้เธรดแล้วไม่ต้องรอ connection
    # ระบบจริงปรับได้ด้วย DB_POOL_SIZE (จำนวน process คูณค่านี้ต้องไม่เกิน max_connections ของ PostgreSQL)
    import os
    size = int(os.getenv("DB_POOL_SIZE", "40"))
    return create_engine(url, pool_size=size, max_overflow=0, pool_pre_ping=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# GAP-15: SQLite ใช้ connection เดียวร่วมกันทุกเธรด (StaticPool) ถ้าหลายคำขอเข้าพร้อมกันจะชนกันบน Python 3.12 ขึ้นไป
# จึงให้คำขอที่ใช้ SQLite เข้าฐานข้อมูลทีละคำขอ ส่วนระบบจริงใช้ PostgreSQL (D-00-02) ไม่ผ่านเงื่อนไขนี้
_sqlite_gate = threading.Lock()


def get_db():
    db = SessionLocal()
    one_at_a_time = db.get_bind().dialect.name == "sqlite"
    if one_at_a_time:
        _sqlite_gate.acquire()
    try:
        yield db
    finally:
        db.close()
        if one_at_a_time:
            _sqlite_gate.release()
