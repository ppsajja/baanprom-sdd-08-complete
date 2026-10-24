"""เตรียมฐานข้อมูล SQLite ในหน่วยความจำ, FakeGateway, และข้อมูลตั้งต้นตาม Background ใน booking.feature
ทุก test เริ่มจากสภาพเดียวกัน: ลูกค้า สมชาย, ช่าง ประสิทธิ์ (ประปา) มีช่วงเวลา พรุ่งนี้ 14:00-16:00 ว่าง"""
import os
from datetime import datetime, timedelta

# CR-07 REQ-SEC-012: ช่อง now= ใช้ได้เฉพาะโหมด test (ค่าตั้งต้นของระบบคือ production) ต้องตั้งก่อน import app
os.environ["APP_ENV"] = "test"
# CR-11: call center อ่านงานด้วยกุญแจของ Ops (X-Ops-Token) ซึ่งต้องตั้ง OPS_TOKEN ทุกโหมด test ที่ต้องการค่าอื่นตั้งเองด้วย monkeypatch
os.environ.setdefault("OPS_TOKEN", "ops-token-for-tests")
OPS = {"X-Ops-Token": os.environ["OPS_TOKEN"]}

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import config
from app.db import session as db_session
from app.db.models import Customer, ServiceAddress, Technician, TimeSlot
from app.db.migrations.m001_init import upgrade
from app.payments import gateway as gw
from app.notify.queue import queue as notify_queue

# เวลาตั้งต้นของทุก test (วันเสาร์ 4 ต.ค. 2569 10:00) ให้ "พรุ่งนี้ 14:00" คำนวณได้แน่นอน
NOW = datetime(2026, 10, 4, 10, 0, 0)
TOMORROW_14 = (NOW + timedelta(days=1)).replace(hour=14, minute=0)


@pytest.fixture()
def db():
    engine = db_session.make_engine("sqlite:///:memory:")
    upgrade(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db_session.SessionLocal = TestSession  # ให้ get_db ของ app ใช้ฐานข้อมูลนี้
    s = TestSession()
    yield s
    s.close()


@pytest.fixture()
def gateway():
    g = gw.FakeGateway(mode="approved")
    gw.set_gateway(g)
    return g


@pytest.fixture()
def client(db, gateway):
    from app.main import app
    notify_queue.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def seed(db):
    """ข้อมูลตาม Background ของ booking.feature"""
    somchai = Customer(name="สมชาย", phone="081-234-5678")
    other = Customer(name="คนอื่น", phone="089-999-0000")
    db.add_all([somchai, other])
    db.flush()
    addr = ServiceAddress(customer_id=somchai.id, text="บ้านเลขที่ 12 ซอยสุขใจ", lat=13.7400, lng=100.5300)
    addr_other = ServiceAddress(customer_id=other.id, text="หมู่บ้านริมคลอง", lat=13.7420, lng=100.5320)
    # ช่าง ประสิทธิ์ ห่างจากบ้านสมชายราว 4 กม. (BR-03 ผ่าน) ช่าง ไกลมาก อยู่ 40 กม. (BR-03 ไม่ผ่าน)
    prasit = Technician(name="ประสิทธิ์", skills="ประปา,ไฟฟ้า", base_lat=13.7050, base_lng=100.5300)
    far = Technician(name="ไกลมาก", skills="ประปา", base_lat=14.1000, base_lng=100.5300)
    db.add_all([addr, addr_other, prasit, far])
    db.flush()
    slots = [
        TimeSlot(technician_id=prasit.id, start=TOMORROW_14, end=TOMORROW_14 + timedelta(hours=2)),
        TimeSlot(technician_id=prasit.id, start=TOMORROW_14 + timedelta(hours=2), end=TOMORROW_14 + timedelta(hours=4)),
        TimeSlot(technician_id=prasit.id, start=TOMORROW_14 - timedelta(hours=3), end=TOMORROW_14 - timedelta(hours=1)),
        TimeSlot(technician_id=prasit.id, start=TOMORROW_14 + timedelta(days=1), end=TOMORROW_14 + timedelta(days=1, hours=2)),
        TimeSlot(technician_id=far.id, start=TOMORROW_14, end=TOMORROW_14 + timedelta(hours=2)),
    ]
    db.add_all(slots)
    db.commit()
    return {"somchai": somchai, "other": other, "addr": addr, "addr_other": addr_other,
            "prasit": prasit, "far": far, "slot": slots[0], "slots": slots}


def auth_headers(role: str, subject_id: int) -> dict:
    """CR-11 (R2): header Authorization ของลูกค้าหรือช่างที่เข้าสู่ระบบแล้ว สร้าง session ตรงในฐานข้อมูลของ test
    ไม่ผ่าน OTP (การเข้าสู่ระบบจริงตรวจใน test_identity.py) session ยาวพอสำหรับเวลาจำลองทุกตัวในชุด test
    เป็นทางเดียวที่ test เดิมใช้บอกว่า "ใครเป็นผู้ส่ง" แทน customer_id และ technician_id ที่เคยส่งใน body และ query"""
    from app.auth.service import issue_session, normalize_phone
    from app.db.models import Account
    s = db_session.SessionLocal()
    db_session._sqlite_gate.acquire()  # test ที่ยิงพร้อมกันหลายเธรดเรียก helper นี้ในเธรด (SQLite ใช้ connection เดียว)
    try:
        acc = s.query(Account).filter_by(role=role, subject_id=subject_id).first()
        if acc is None:
            obj = s.get(Customer if role == "customer" else Technician, subject_id)
            phone = getattr(obj, "phone", "") or ""
            try:
                phone_norm = normalize_phone(phone)
            except Exception:
                phone_norm = f"09{subject_id:08d}" if role == "customer" else f"08{subject_id:08d}"
            acc = Account(role=role, subject_id=subject_id, phone_norm=phone_norm, created_at=SESSION_FROM)
            s.add(acc)
            s.commit()
        token, _ = issue_session(s, acc, SESSION_FROM, lifetime=timedelta(days=3650 * 3))
        return {"Authorization": f"Bearer {token}"}
    finally:
        s.close()
        db_session._sqlite_gate.release()


# CR-11: session ของ test เริ่มก่อนเวลาจำลองทุกตัว (บาง test ย้อนเวลาไปก่อน NOW) และอยู่นาน (test โหมด production ใช้นาฬิกาจริง)
SESSION_FROM = NOW - timedelta(days=60)


H = auth_headers  # ชื่อสั้นสำหรับ test


def book(client, *, customer_id, slot_id, address_id, category="ประปา", now=NOW):
    """ช่วย POST /bookings ให้สั้น
    CR-11: ส่ง Authorization ของลูกค้าที่ระบุ ลูกค้ามาจาก token (customer_id ใน body ระบบไม่ใช้แล้ว คงไว้ให้ test อ่านง่าย)"""
    return client.post(f"/bookings?now={now.isoformat()}",
                       json={"customer_id": customer_id, "slot_id": slot_id,
                             "address_id": address_id, "category": category},
                       headers=auth_headers("customer", customer_id))
