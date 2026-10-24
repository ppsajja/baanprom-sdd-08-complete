"""AC-09-11 ถึง AC-09-14 จาก job-status.feature v1.1 (CR-07, T-08 ถึง T-11 ของ 003)
QAS-1, QAS-2, QAS-3 ใน specs/003-job-status/quality-requirements.md และ REQ-SEC-010"""
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import config
from app.db.models import Job, TimeSlot, Technician, Customer, ServiceAddress, SecurityEvent
from app.notify.queue import queue, FakeNotifier
from tests.conftest import NOW, TOMORROW_14, book
from tests.test_job_status import confirmed_job, change, history


# รองรับ AC-09-11 (QAS-1, REQ-FN-053, Q-38)
def test_AC_09_11_messages_accepted_by_if02_within_60s(client, db, seed):
    # Given ช่างเปลี่ยนสถานะงาน และ IF-02 ทำงานปกติ (ย่อส่วน: งาน 1 งาน 3 ครั้ง แทน 100 ครั้งในหนึ่งวัน)
    job = confirmed_job(client, db, seed)
    queue.clear()
    notifier = FakeNotifier()
    times = [TOMORROW_14 - timedelta(hours=1), TOMORROW_14, TOMORROW_14 + timedelta(hours=2)]
    for at, to in zip(times, ("en_route", "in_progress", "done")):
        assert change(client, job.id, seed["prasit"].id, to, at).status_code == 200
        # When ตัวส่งข้อความทำงานรอบถัดไป (ทุก 1 นาที ในที่นี้ 30 วินาทีหลังกด)
        queue.deliver_due(notifier, at + timedelta(seconds=30))
    msgs = [m for m in queue.for_job(job.id) if m.to_role == "customer"]
    # Then อย่างน้อย 95 ใน 100 ข้อความถูก IF-02 ตอบรับภายใน 60 วินาทีนับจากเวลาที่ช่างกด (ย่อส่วน: 3 ใน 3)
    on_time = [m for m in msgs if m.delivered_at and m.delivered_at - m.created_at <= timedelta(seconds=60)]
    assert len(msgs) == 3 and len(on_time) == 3
    assert notifier.last_timeout_seconds == config.NOTIFY_TIMEOUT_SECONDS == 10


# รองรับ AC-09-12 (QAS-2, REQ-OP-001, Q-39) ย่อส่วน 10 จาก 50
def test_AC_09_12_status_change_under_load_scaled(client, db, seed):
    # Given ช่าง 10 คน (ย่อจาก 50) มีงาน "ยืนยันแล้ว" คนละ 1 งาน
    jobs = []
    for i in range(10):
        tech = Technician(name=f"ช่าง{i}", skills="ประปา", base_lat=13.7050, base_lng=100.5300)
        cust = Customer(name=f"ลูกค้า{i}", phone=f"080-000-00{i:02d}")
        db.add_all([tech, cust]); db.flush()
        addr = ServiceAddress(customer_id=cust.id, text="ทดสอบ", lat=13.74, lng=100.53)
        slot = TimeSlot(technician_id=tech.id, start=TOMORROW_14, end=TOMORROW_14 + timedelta(hours=2))
        db.add_all([addr, slot]); db.commit()
        r = book(client, customer_id=cust.id, slot_id=slot.id, address_id=addr.id)
        assert r.status_code == 201
        jobs.append((r.json()["job_id"], tech.id))
    at = TOMORROW_14 - timedelta(hours=1)

    def timed(pair):
        t0 = time.perf_counter()
        r = change(client, pair[0], pair[1], "en_route", at)
        return r.status_code, time.perf_counter() - t0

    # When ทุกคนส่ง POST /jobs/{id}/status ไป "ช่างกำลังเดินทาง" พร้อมกัน
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(timed, jobs))
    # Then ทุกคำขอได้ 200 และประวัติมีแถวใหม่ครบ
    assert all(code == 200 for code, _ in results)
    for jid, _ in jobs:
        h = history(client, db.get(Job, jid)).json()["history"]
        assert h[-1]["to_status"] == "en_route"
    # Then 95 ใน 100 ไม่เกิน 1 วินาที (ย่อส่วน: 10 ใน 10)
    assert sum(1 for _, sec in results if sec <= 1.0) == 10


# รองรับ AC-09-13 (QAS-3, REQ-QA-010 บรรทัดที่ 4, Q-40)
def test_AC_09_13_if02_down_status_saved_message_resent_once(client, db, seed):
    # Given IF-02 จำลองถูกสั่งให้ไม่ตอบ และช่างมีงานสถานะ "ยืนยันแล้ว"
    job = confirmed_job(client, db, seed)
    queue.clear()
    notifier = FakeNotifier(mode="down")
    at = TOMORROW_14 - timedelta(hours=1)
    # When ช่างกด "ออกเดินทาง" แล้วเดินนาฬิกาจำลองทีละ 1 นาทีเป็นเวลา 20 นาที แล้วสั่งให้ IF-02 กลับมาตอบ
    r = change(client, job.id, seed["prasit"].id, "en_route", at)
    for minute in range(0, 20):
        queue.deliver_due(notifier, at + timedelta(minutes=minute))
    notifier.mode = "ok"
    for minute in range(20, 31):
        queue.deliver_due(notifier, at + timedelta(minutes=minute))
    # Then สถานะงานเป็น "ช่างกำลังเดินทาง" และประวัติมี 1 แถวตั้งแต่ตอนกด
    assert r.status_code == 200
    h = history(client, job).json()["history"]
    assert [x for x in h if x["to_status"] == "en_route"] == [{"from_status": "confirmed", "to_status": "en_route", "at": at.isoformat()}]
    # Then ข้อความถึงลูกค้าถูกส่งสำเร็จ 1 ข้อความ ไม่มีข้อความซ้ำ และลองส่งไม่เกิน 6 ครั้ง ห่างกัน 5 นาที
    msg = [m for m in queue.for_job(job.id) if m.to_role == "customer"][0]
    # CR-13 (Q-67): คิวอยู่ในฐานข้อมูล ข้อความที่อ่านคืนเป็นวัตถุใหม่ทุกครั้ง จึงเทียบด้วยเลขข้อความแทน "is"
    assert len(notifier.sent) == 1 and notifier.sent[0].id == msg.id
    assert msg.attempts == 5 and msg.delivered_at == at + timedelta(minutes=20)


# รองรับ AC-09-13 กรณีไม่ตอบเกินรอบส่งซ้ำ (EV-045): ครบ 6 ครั้งแล้วหยุด ทำเครื่องหมายให้คนเวรตาม
def test_AC_09_13_if02_down_beyond_retries_gives_up_after_6(client, db, seed):
    job = confirmed_job(client, db, seed)
    queue.clear()
    notifier = FakeNotifier(mode="down")
    at = TOMORROW_14 - timedelta(hours=1)
    change(client, job.id, seed["prasit"].id, "en_route", at)
    for minute in range(0, 61):
        queue.deliver_due(notifier, at + timedelta(minutes=minute))
    msg = [m for m in queue.for_job(job.id) if m.to_role == "customer"][0]
    assert msg.attempts == config.NOTIFY_MAX_ATTEMPTS == 6 and msg.gave_up and msg.delivered_at is None
    assert notifier.calls == 6


# รองรับ AC-09-14 (REQ-SEC-010 บรรทัดที่ 2)
def test_AC_09_14_denied_status_change_logged_without_leaking_existence(client, db, seed):
    job = confirmed_job(client, db, seed)
    # When ช่าง "ไกลมาก" ขอเปลี่ยนงานของช่าง "ประสิทธิ์" และงานเลขที่ไม่มีอยู่
    a = change(client, job.id, seed["far"].id, "en_route")
    b = change(client, 99999, seed["far"].id, "en_route")
    # Then ทั้งสองได้ 403 คำตอบเหมือนกัน
    assert a.status_code == b.status_code == 403 and a.json() == b.json()
    # And งานยังเป็น "ยืนยันแล้ว" และมีบันทึกความพยายาม 2 รายการ
    db.refresh(db.get(Job, job.id)); assert db.get(Job, job.id).status == "confirmed"
    rows = db.scalars(select(SecurityEvent).where(SecurityEvent.kind == "denied")).all()
    assert [(r.actor_id, r.job_id, r.endpoint) for r in rows] == [
        (seed["far"].id, job.id, "POST /jobs/{job_id}/status"), (seed["far"].id, 99999, "POST /jobs/{job_id}/status")]
