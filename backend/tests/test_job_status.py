"""AC-09-01 ถึง AC-09-08 และ AC-09-10 จาก job-status.feature (specs/003-job-status, CR-05)
UC-09 ช่างอัปเดตสถานะงาน: รายการงานของช่าง ลูกศรของ MD-STM-01 ประวัติ และการแจ้งลูกค้า"""
from datetime import timedelta

import pytest

from app import config
from app.db.models import Job, TimeSlot
from app.notify.queue import queue
from tests.conftest import NOW, TOMORROW_14, book, H, OPS


def confirmed_job(client, db, seed, slot=None):
    """Background: งานสถานะ ยืนยันแล้ว ของช่าง ประสิทธิ์ นัดพรุ่งนี้ 14:00"""
    slot = slot or seed["slot"]
    res = book(client, customer_id=seed["somchai"].id, slot_id=slot.id, address_id=seed["addr"].id)
    assert res.status_code == 201
    job = db.get(Job, res.json()["job_id"]); db.refresh(job)
    return job


def change(client, job_id, technician_id, to_status, now=NOW):
    # CR-11: technician_id คือผู้ส่ง ส่งเป็น token ของช่างคนนั้น (technician_id ใน body ระบบไม่ใช้แล้ว)
    return client.post(f"/jobs/{job_id}/status?now={now.isoformat()}",
                       json={"technician_id": technician_id, "to_status": to_status},
                       headers=H("technician", technician_id))


def history(client, job):
    # CR-11: อ่านประวัติในนามลูกค้าเจ้าของงาน (GET /jobs/{id}/history ต้องเข้าสู่ระบบแล้ว GAP-24 ปิด)
    return client.get(f"/jobs/{job.id}/history", headers=H("customer", job.customer_id))


# รองรับ AC-09-01 (REQ-FN-050)
def test_AC_09_01_technician_sees_only_own_jobs(client, db, seed):
    # Given ช่าง ประสิทธิ์ มีงาน 1 รายการ และช่าง ไกลมาก มีงาน 1 รายการ
    mine = confirmed_job(client, db, seed)
    far_slot = seed["slots"][4]
    theirs = book(client, customer_id=seed["other"].id, slot_id=far_slot.id, address_id=seed["addr_other"].id)
    assert theirs.status_code == 201
    # When ช่าง ประสิทธิ์ เปิดรายการงานของตัวเอง
    r = client.get(f"/technicians/{seed['prasit'].id}/jobs?now={NOW.isoformat()}", headers=H("technician", seed["prasit"].id))
    # Then เห็นเฉพาะงานของตัวเอง พร้อมสถานะ "ยืนยันแล้ว" และปุ่มถัดไปคือ ออกเดินทาง
    assert r.status_code == 200
    ids = [j["job_id"] for j in r.json()]
    assert ids == [mine.id]
    assert r.json()[0]["status"] == "confirmed"
    assert [n["status"] for n in r.json()[0]["next_statuses"]] == ["en_route"]
    # And ช่างที่ไม่มีในระบบได้ 404
    # CR-11: ช่าง ประสิทธิ์ ขอรายการของรหัสอื่นได้ 403 (ไม่ใช่รายการของตัวเอง REQ-SEC-010) จึงไม่รู้ว่ารหัสนั้นมีอยู่หรือไม่
    assert client.get(f"/technicians/999/jobs?now={NOW.isoformat()}", headers=H("technician", seed["prasit"].id)).status_code == 403


# รองรับ AC-09-02 (REQ-FN-051, REQ-DAT-002)
def test_AC_09_02_en_route_recorded(client, db, seed):
    # Given งานสถานะ ยืนยันแล้ว
    job = confirmed_job(client, db, seed)
    at = TOMORROW_14 - timedelta(hours=1)
    # When ช่างกด ออกเดินทาง
    r = change(client, job.id, seed["prasit"].id, "en_route", at)
    # Then งานมีสถานะ ช่างกำลังเดินทาง และประวัติมีแถว ยืนยันแล้ว ไปยัง ช่างกำลังเดินทาง
    assert r.status_code == 200 and r.json()["status"] == "en_route"
    h = history(client, job).json()["history"]
    assert h[-1] == {"from_status": "confirmed", "to_status": "en_route", "at": at.isoformat()}


# รองรับ AC-09-03 และ AC-09-04 (REQ-FN-051): ลูกศรถัดไปของ MD-STM-01 ทีละขั้น
def test_AC_09_03_check_in_then_AC_09_04_close(client, db, seed):
    job = confirmed_job(client, db, seed)
    tech = seed["prasit"].id
    assert change(client, job.id, tech, "en_route", TOMORROW_14 - timedelta(hours=1)).status_code == 200
    # AC-09-03 When ช่างกด ถึงหน้างาน Then กำลังดำเนินงาน
    r = change(client, job.id, tech, "in_progress", TOMORROW_14)
    assert r.status_code == 200 and r.json()["status"] == "in_progress"
    # AC-09-04 When ช่างกด ปิดงาน Then เสร็จสิ้น (AS-11 รอ Q-31) และไม่มีปุ่มถัดไป
    r = change(client, job.id, tech, "done", TOMORROW_14 + timedelta(hours=2))
    assert r.status_code == 200 and r.json()["status"] == "done"
    assert r.json()["next_statuses"] == []
    db.refresh(job); assert job.status == "done"


# รองรับ AC-09-05 (REQ-FN-051, Q-30): ลูกศรที่ไม่มีใน MD-STM-01 ถูกปฏิเสธ ไม่บันทึกประวัติ
@pytest.mark.parametrize("from_status,to_status", [
    ("confirmed", "done"),          # ข้ามขั้น
    ("confirmed", "in_progress"),   # ข้ามขั้น
    ("in_progress", "en_route"),    # ย้อนกลับ (Q-30)
    ("confirmed", "cancelled"),     # ยกเลิกเป็นของ UC-08 ไม่ใช่ปุ่มของช่าง
    ("confirmed", "rematching"),    # ช่างปฏิเสธและจับคู่ใหม่ อยู่ใน UC-05 (Non-goal)
])
def test_AC_09_05_transition_not_allowed(client, db, seed, from_status, to_status):
    from app.db.models import set_status
    job = confirmed_job(client, db, seed)
    set_status(db, job, from_status, NOW); db.commit()
    before = len(history(client, job).json()["history"])
    r = change(client, job.id, seed["prasit"].id, to_status)
    assert r.status_code == 409 and r.json()["reason"] == "transition_not_allowed"
    db.refresh(job); assert job.status == from_status
    assert len(history(client, job).json()["history"]) == before


# รองรับ AC-09-06 (REQ-FN-051): ช่างคนอื่นเปลี่ยนสถานะงานไม่ได้
def test_AC_09_06_other_technician_cannot_change(client, db, seed):
    job = confirmed_job(client, db, seed)
    r = change(client, job.id, seed["far"].id, "en_route")
    # CR-07 (Q-47, GAP-23): AC-09-06 บรรทัด Then แก้จาก "ไม่พบงานของช่างคนนี้" (404) เป็น "ไม่มีสิทธิ์กับงานนี้" (403)
    assert r.status_code == 403
    db.refresh(job); assert job.status == "confirmed"


# รองรับ AC-09-07 (REQ-FN-052): ลูกค้าและ call center เห็นสถานะเดียวกับที่ช่างเปลี่ยน
def test_AC_09_07_customer_and_call_center_see_same_status(client, db, seed):
    job = confirmed_job(client, db, seed)
    change(client, job.id, seed["prasit"].id, "en_route", TOMORROW_14 - timedelta(hours=1))
    # CR-11: ลูกค้าอ่านด้วย token ของตัวเอง call center อ่านด้วยกุญแจของ Ops (GAP-32 กุญแจแยกบทบาทยังเปิด)
    customer_view = client.get(f"/jobs/{job.id}", headers=H("customer", job.customer_id)).json()
    history_view = client.get(f"/jobs/{job.id}/history", headers=OPS).json()
    assert customer_view["status"] == "en_route" == history_view["status"]
    assert "customer_phone" not in customer_view  # มุมมองนี้ไม่มีเบอร์ (REQ-PRV-002 ไม่เกี่ยว แต่ไม่ส่งเกิน)


# รองรับ AC-09-08 (REQ-FN-053): แจ้งลูกค้าภายใน 60 วินาทีทุกครั้งที่สถานะเปลี่ยน
def test_AC_09_08_notify_customer_within_60s_on_each_change(client, db, seed):
    job = confirmed_job(client, db, seed)
    queue.clear()
    t1 = TOMORROW_14 - timedelta(hours=1)
    t2 = TOMORROW_14
    change(client, job.id, seed["prasit"].id, "en_route", t1)
    change(client, job.id, seed["prasit"].id, "in_progress", t2)
    msgs = [m for m in queue.for_job(job.id) if m.to_role == "customer"]
    assert len(msgs) == 2
    for m, t in zip(msgs, (t1, t2)):
        assert m.due_at <= t + timedelta(seconds=config.NOTIFY_WITHIN_SECONDS)


# รองรับ AC-09-10 (REQ-DAT-002): ประวัติครบทุกการเปลี่ยนตั้งแต่สร้างงาน เรียงตามเวลา
def test_AC_09_10_history_complete_in_order(client, db, seed):
    job = confirmed_job(client, db, seed)
    tech = seed["prasit"].id
    change(client, job.id, tech, "en_route", TOMORROW_14 - timedelta(hours=1))
    change(client, job.id, tech, "in_progress", TOMORROW_14)
    change(client, job.id, tech, "done", TOMORROW_14 + timedelta(hours=2))
    h = history(client, job).json()["history"]
    assert [(r["from_status"], r["to_status"]) for r in h] == [
        ("pending_payment", "pending_payment"), ("pending_payment", "confirmed"),
        ("confirmed", "en_route"), ("en_route", "in_progress"), ("in_progress", "done"),
    ]
    assert [r["at"] for r in h] == sorted(r["at"] for r in h)
