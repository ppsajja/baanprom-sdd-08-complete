"""AC-00-01 ถึง AC-00-08 จาก specs/000-shared/cross-cutting.feature (CR-07, Constraint กลางรุ่น 1.1 ส่วน 6)
ข้อกำหนดข้ามทุก feature: REQ-OP-001, REQ-OP-005, REQ-OP-007, REQ-SEC-010 บรรทัดที่ 3, REQ-SEC-012"""
import json
import logging
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app import config
from app.db.models import Job, SecurityEvent, TimeSlot, Customer, ServiceAddress
from app.db.migrations.m002_cr07 import upgrade
from app.ops import alerts, backup
from app.ops.metrics import Metrics, metrics
from tests.conftest import NOW, TOMORROW_14, book, H


@pytest.fixture()
def pager():
    p = alerts.FakePager()
    alerts.state.clear()
    yield p
    alerts.state.clear()


@pytest.fixture()
def production(monkeypatch, db, gateway):
    """แอปที่สร้างในโหมด production (ค่าตั้งต้นของระบบ) และมี OPS_TOKEN"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPS_TOKEN", "ops-secret-for-test")
    from app.main import create_app
    with TestClient(create_app()) as c:
        yield c


# รองรับ AC-00-01 (REQ-OP-005 บรรทัดที่ 1)
def test_AC_00_01_metrics_per_endpoint_per_minute(client, db, seed, gateway):
    metrics.clear()
    # Given ระบบรับคำขอค้นหา 3 ครั้ง จอง 1 ครั้ง และจองที่ชำระไม่สำเร็จ 1 ครั้ง
    for _ in range(3):
        client.get(f"/technicians?category=ประปา&address_id={seed['addr'].id}&now={NOW.isoformat()}")
    book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    gateway.mode = "declined"
    book(client, customer_id=seed["other"].id, slot_id=seed["slots"][1].id, address_id=seed["addr_other"].id)
    # When Ops lead อ่าน GET /metrics
    rows = client.get("/metrics").json()
    by = {}
    for r in rows:
        by.setdefault(r["endpoint"], [0, 0])
        by[r["endpoint"]][0] += r["requests"]; by[r["endpoint"]][1] += r["failures"]
    # Then มีจำนวนคำขอ คำขอที่ล้มเหลว และเวลาตอบ แยกตามแม่แบบ endpoint และนาที
    assert by["GET /technicians"] == [3, 0]
    assert by["POST /bookings"] == [2, 1]  # 402 ชำระไม่สำเร็จนับเป็นล้มเหลว
    assert all({"minute", "avg_ms", "max_ms"} <= set(r) for r in rows)
    assert not any("/jobs/1" in r["endpoint"] for r in rows)  # ไม่ใช้ path จริงที่มีเลขงาน


# รองรับ AC-00-02 (REQ-OP-005 บรรทัดที่ 2)
def test_AC_00_02_page_on_call_after_5_failing_minutes(db, pager):
    m = Metrics()
    start = datetime(2026, 10, 25, 9, 0)
    # Given endpoint ตอบล้มเหลว 10 ใน 100 ทุกนาที นาน 6 นาที
    pages_at = {}
    for minute in range(6):
        at = start + timedelta(minutes=minute)
        for i in range(100):
            m.record("POST /bookings", 500 if i < 10 else 201, 50.0, at)
        # When งานเบื้องหลังตรวจเกณฑ์ทุก 1 นาที (ต้นนาทีถัดไป)
        sent = alerts.evaluate(db, m, at + timedelta(minutes=1), pager)
        pages_at[minute + 1] = len(sent)
    # Then ไม่เตือนในนาทีที่ 1 ถึง 4 เตือน 1 ครั้งเมื่อครบ 5 นาที (ภายใน 2 นาทีหลังครบเกณฑ์) และไม่เตือนซ้ำ
    assert [pages_at[k] for k in range(1, 7)] == [0, 0, 0, 0, 1, 0]
    assert len(pager.sent) == 1 and pager.sent[0].kind == "failure_rate"
    assert pager.sent[0].at - (start + timedelta(minutes=5)) <= timedelta(minutes=config.ALERT_PAGE_WITHIN_MINUTES)
    # And ล้มเหลว 5 ใน 100 พอดี ไม่เกินเกณฑ์ ไม่เตือน
    m2 = Metrics(); alerts.state.clear(); p2 = alerts.FakePager()
    for minute in range(6):
        for i in range(100):
            m2.record("GET /technicians", 500 if i < 5 else 200, 10.0, start + timedelta(minutes=minute))
    assert alerts.evaluate(db, m2, start + timedelta(minutes=6), p2) == []


# รองรับ AC-00-03 (REQ-OP-005 บรรทัดที่ 3, REQ-PRV-002)
def test_AC_00_03_structured_log_without_pii(client, db, seed, caplog):
    caplog.set_level(logging.INFO)
    # Given ลูกค้าจอง ช่างดูงานในช่วงเห็นเบอร์ ช่างเปิดรายการงาน และช่างคนอื่นถูกปฏิเสธ
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    job_id = res.json()["job_id"]
    at = (TOMORROW_14 - timedelta(hours=1)).isoformat()
    prasit, far = H("technician", seed["prasit"].id), H("technician", seed["far"].id)  # CR-11 ผู้ส่งมาจาก token
    client.get(f"/jobs/{job_id}/technician-view?technician_id={seed['prasit'].id}&now={at}", headers=prasit)
    client.get(f"/technicians/{seed['prasit'].id}/jobs?now={at}", headers=prasit)
    client.get(f"/jobs/{job_id}/technician-view?technician_id={seed['far'].id}&now={at}", headers=far)
    lines = [r.getMessage() for r in caplog.records if r.name.startswith("app.")]
    # Then ทุกบรรทัดของ log เป็น JSON ที่มีช่อง event
    parsed = [json.loads(line) for line in lines]
    assert parsed and all("event" in p for p in parsed)
    # And ไม่มีเบอร์โทร ชื่อ ที่อยู่ และพิกัดของลูกค้า
    text = "\n".join(lines)
    for pii in ("081-234-5678", "0812345678", "สมชาย", "ซอยสุขใจ", "13.74", "100.53"):
        assert pii not in text, pii
    # And ช่องที่ไม่อยู่ในรายการที่อนุญาตถูกทิ้ง
    from app.privacy import log_event, get_logger
    rec = log_event(get_logger("app.test"), "x", job_id=1, address="บ้านเลขที่ 12", lat=13.74)
    assert rec == {"event": "x", "job_id": 1, "dropped": ["address", "lat"]}


# รองรับ AC-00-04 (REQ-OP-001)
def test_AC_00_04_health_and_ready(client, db):
    # When ระบบเฝ้าดูเรียก /health และ /ready
    assert client.get("/health").json() == {"ok": True}
    assert client.get("/ready").json() == {"ok": True, "database": "ok"}
    # And เมื่อฐานข้อมูลใช้ไม่ได้ /health ยังตอบ แต่ /ready ตอบ 503
    from app.main import app
    from app.db.session import get_db

    class Broken:
        def execute(self, *_):
            raise RuntimeError("disk full")

    app.dependency_overrides[get_db] = lambda: Broken()
    try:
        assert client.get("/health").status_code == 200
        r = client.get("/ready")
        assert r.status_code == 503 and r.json()["database"] == "unavailable"
    finally:
        app.dependency_overrides.clear()


# รองรับ AC-00-05 (REQ-OP-007)
def test_AC_00_05_backup_restore_drill_within_rpo(tmp_path, monkeypatch):
    monkeypatch.setenv("ERASURE_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    live = tmp_path / "live.db"
    eng = create_engine(f"sqlite:///{live}")
    upgrade(eng)
    s = sessionmaker(bind=eng, expire_on_commit=False)()
    c = Customer(name="ก", phone="080-000-0000"); s.add(c); s.flush()
    a = ServiceAddress(customer_id=c.id, text="x", lat=13.7, lng=100.5); s.add(a); s.flush()
    from app.db.models import Technician
    t = Technician(name="ช", skills="ประปา", base_lat=13.7, base_lng=100.5); s.add(t); s.flush()

    def add_job(at):
        sl = TimeSlot(technician_id=t.id, start=at, end=at + timedelta(hours=2), state="booked"); s.add(sl); s.flush()
        s.add(Job(customer_id=c.id, technician_id=t.id, slot_id=sl.id, address_id=a.id, category="ประปา",
                  status="confirmed", deposit_amount=350, scheduled_start=at, created_at=at)); s.commit()

    offsite = tmp_path / "offsite"
    t0 = datetime(2026, 10, 25, 9, 0)
    # Given สำรองทุก 15 นาที: 09:00 และ 09:15 ระหว่างนั้นมีการจองเข้ามา
    add_job(t0); backup.backup_sqlite(str(live), str(offsite), t0)
    add_job(t0 + timedelta(minutes=10)); backup.backup_sqlite(str(live), str(offsite), t0 + timedelta(minutes=15))
    # And มีการจองอีก 1 รายการที่ 09:20 แล้วเครื่องหลักเสียที่ 09:25
    add_job(t0 + timedelta(minutes=20))
    s.close(); eng.dispose()
    # When ซ้อมกู้คืนจากสำเนาล่าสุดบนเครื่องว่าง
    report = backup.restore_sqlite(str(offsite), str(tmp_path / "empty-machine.db"), t0 + timedelta(minutes=25))
    eng2 = create_engine(f"sqlite:///{tmp_path / 'empty-machine.db'}")
    s2 = sessionmaker(bind=eng2)()
    restored = s2.scalar(select(func.count()).select_from(Job))
    s2.close(); eng2.dispose()
    # Then ได้การจองครบถึงสำเนาล่าสุด หายเฉพาะรายการหลังสำเนา และอายุสำเนาไม่เกิน RPO 15 นาที
    assert restored == 2 and 3 - restored == 1
    assert report.backup_age_minutes <= config.BACKUP_INTERVAL_MINUTES == 15
    # And เวลากู้คืนที่บันทึกได้ต่ำกว่า RTO 4 ชั่วโมงมาก (เป็นเวลาในเครื่องทดสอบ ไม่ใช่ผลซ้อมจริง)
    assert report.seconds < config_rto_seconds()
    # And สำเนาที่เก่ากว่า 30 วันถูกลบ ส่วนสำเนาใหม่ยังอยู่
    old = backup.backup_sqlite(str(tmp_path / "empty-machine.db"), str(offsite), t0 - timedelta(days=31))
    removed = backup.prune(str(offsite), t0)
    assert removed == [old] and len(backup.list_backups(str(offsite))) == 2


def config_rto_seconds() -> int:
    return 4 * 3600


# รองรับ AC-00-06 (REQ-SEC-012 บรรทัดที่ 1 และ 2, OWASP API8:2023, API5:2023)
def test_AC_00_06_production_hides_docs_and_guards_ops_endpoints(production):
    # When ระบบรันในโหมด production
    # Then หน้าเอกสารที่ FastAPI เปิดให้เองไม่มี
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert production.get(path).status_code == 404, path
    # And endpoint ของ ops ตอบ 403 เมื่อไม่มีหรือส่งกุญแจผิด และตอบ 200 เมื่อกุญแจถูก
    for path in ("/notifications/queue", "/metrics"):
        assert production.get(path).status_code == 403
        assert production.get(path, headers={"X-Ops-Token": "wrong"}).status_code == 403
        assert production.get(path, headers={"X-Ops-Token": "ops-secret-for-test"}).status_code == 200
    assert production.post("/ops/erasure-requests", json={"customer_id": 1}).status_code == 403
    # And /health ยังเปิดให้ระบบเฝ้าดู
    assert production.get("/health").status_code == 200


# รองรับ AC-00-07 (REQ-SEC-012 บรรทัดที่ 3)
def test_AC_00_07_now_parameter_ignored_outside_test_mode(production, db, seed):
    # Given ระบบรันในโหมด production
    far_past = datetime(2020, 1, 1, 9, 0)
    before = datetime.now()
    # When ผู้เรียกส่ง now= เพื่อย้อนเวลาตอนล็อกช่วงเวลา
    r = production.post(f"/slots/{seed['slot'].id}/hold?now={far_past.isoformat()}", json={"customer_id": seed["somchai"].id},
                        headers=H("customer", seed["somchai"].id))
    # Then ระบบใช้นาฬิกาของเครื่อง ล็อกหมดอายุ 10 นาทีนับจากเวลาจริง ไม่ใช่จากค่าที่ส่งมา
    assert r.status_code == 200
    expires = datetime.fromisoformat(r.json()["hold_expires_at"])
    assert before + timedelta(minutes=10) <= expires <= datetime.now() + timedelta(minutes=10)


# รองรับ AC-00-08 (REQ-SEC-010 บรรทัดที่ 3, OWASP A09:2025)
def test_AC_00_08_page_when_one_actor_denied_over_20_in_10_minutes(db, pager):
    start = datetime(2026, 10, 25, 9, 0)
    # Given ช่างรหัส 7 ถูกปฏิเสธสิทธิ์ 20 ครั้งใน 10 นาที
    for i in range(20):
        db.add(SecurityEvent(kind="denied", actor_role="technician", actor_id=7, job_id=1000 + i,
                             endpoint="GET /jobs/{job_id}/technician-view", at=start + timedelta(seconds=25 * i)))
    db.commit()
    # Then 20 ครั้งยังไม่เกินเกณฑ์ ไม่เตือน
    assert alerts.evaluate(db, Metrics(), start + timedelta(minutes=9), pager) == []
    # When ถูกปฏิเสธครั้งที่ 21 ภายใน 10 นาทีเดียวกัน
    db.add(SecurityEvent(kind="denied", actor_role="technician", actor_id=7, job_id=2000,
                         endpoint="GET /jobs/{job_id}/technician-view", at=start + timedelta(minutes=9, seconds=30)))
    db.commit()
    sent = alerts.evaluate(db, Metrics(), start + timedelta(minutes=9, seconds=40), pager)
    # Then ส่งข้อความถึงคนเวร 1 ครั้ง ระบุบทบาทและรหัสผู้ส่ง ไม่มีข้อมูลลูกค้า
    assert [p.kind for p in sent] == ["denials"] and "technician รหัส 7" in sent[0].text
    assert alerts.evaluate(db, Metrics(), start + timedelta(minutes=9, seconds=50), pager) == []
