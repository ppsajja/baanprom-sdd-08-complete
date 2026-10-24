"""AC-07-20 ถึง AC-07-24 จาก booking.feature v1.6 (CR-08 อนุมัติใน EV-051)
REQ-FN-064 ลูกค้าเลือกช่างคนเดิม (BR-08, Q-66) | REQ-FN-065 เส้นทาง A1 ไม่มีช่างว่างใน 7 วัน (Q-28 คิวรอเป็น Won't)"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import Job, SecurityEvent, ServiceAddress, Technician, TimeSlot, set_status
from tests.conftest import NOW, TOMORROW_14, H, book

LAST_MONTH = NOW - timedelta(days=20)


def q(now=NOW):
    return f"?now={now.isoformat()}"


@pytest.fixture()
def past_job(client, db, seed):
    """Given สมชายเคยใช้ช่าง "ประสิทธิ์" งานประปาเสร็จสิ้นเมื่อ 20 วันก่อน (สร้างตรงในฐานข้อมูล ไม่ผ่านการจอง)"""
    slot = TimeSlot(technician_id=seed["prasit"].id, start=LAST_MONTH, end=LAST_MONTH + timedelta(hours=2), state="booked")
    db.add(slot); db.flush()
    job = Job(customer_id=seed["somchai"].id, technician_id=seed["prasit"].id, slot_id=slot.id, address_id=seed["addr"].id,
              category="ประปา", status="done", deposit_amount=350, scheduled_start=LAST_MONTH, created_at=LAST_MONTH)
    db.add(job); db.commit()
    return job


def slots_of(client, seed, tech_id, category="ประปา", address_id=None, who=None):
    address_id = address_id or seed["addr"].id
    who = who or seed["somchai"].id
    return client.get(f"/me/past-technicians/{tech_id}/slots?category={category}&address_id={address_id}&now={NOW.isoformat()}",
                      headers=H("customer", who))


# รองรับ AC-07-20 (REQ-FN-064, BR-08 ข้อ 1 และ 2)
def test_AC_07_20_book_past_technician_when_free(client, db, seed, past_job, gateway):
    me = H("customer", seed["somchai"].id)
    # When สมชายเปิดรายการ "ช่างที่เคยใช้"
    past = client.get(f"/me/past-technicians{q()}", headers=me).json()
    # Then เห็นช่าง "ประสิทธิ์" จากงานที่เสร็จสิ้น
    assert [p["name"] for p in past] == ["ประสิทธิ์"] and past[0]["last_job_id"] == past_job.id
    # When เลือกช่าง "ประสิทธิ์" Then เห็นช่วงเวลาว่างของช่างคนนั้นใน 7 วัน
    out = slots_of(client, seed, seed["prasit"].id).json()
    assert out["available"] is True and out["slots"][0]["start"] == (TOMORROW_14 - timedelta(hours=3)).isoformat()
    assert {s["slot_id"] for s in out["slots"]} == {s.id for s in seed["slots"][:4]}
    # When จองช่วงแรก Then จองตามกฎเดิมทุกข้อ (ล็อก มัดจำ ยืนยันแล้ว)
    r = book(client, customer_id=seed["somchai"].id, slot_id=out["slots"][0]["slot_id"], address_id=seed["addr"].id)
    assert r.status_code == 201 and r.json()["technician_id"] == seed["prasit"].id and r.json()["deposit_amount"] == 350


# รองรับ AC-07-21 (REQ-FN-064, BR-08 ข้อ 3, Q-66): ช่างคนเดิมไม่ว่างใน 7 วัน ไม่มีคิวรอ ให้ค้นหาช่างอื่น
def test_AC_07_21_past_technician_not_free_in_7_days(client, db, seed, past_job):
    for s in seed["slots"][:4]:
        s.state = "booked"
    db.commit()
    out = slots_of(client, seed, seed["prasit"].id).json()
    assert out["available"] is False and out["reason"] == "no_slots" and out["slots"] == []
    assert out["message"] == "ช่าง ประสิทธิ์ ยังไม่มีช่วงเวลาว่างใน 7 วันข้างหน้า กรุณาค้นหาช่างคนอื่น"


# รองรับ AC-07-22 (REQ-FN-064, BR-03): ช่างคนเดิมอยู่นอกระยะ 15 กม. ของที่อยู่ที่เลือก
def test_AC_07_22_past_technician_out_of_range_for_chosen_address(client, db, seed, past_job):
    far_home = ServiceAddress(customer_id=seed["somchai"].id, text="บ้านต่างจังหวัด", lat=14.2000, lng=100.5300)
    db.add(far_home); db.commit()
    out = slots_of(client, seed, seed["prasit"].id, address_id=far_home.id).json()
    assert out["available"] is False and out["reason"] == "out_of_range" and "นอกพื้นที่ให้บริการ" in out["message"]
    # และงานประเภทที่ช่างไม่รับ
    skill = slots_of(client, seed, seed["prasit"].id, category="แอร์").json()
    assert skill["reason"] == "no_skill"


# รองรับ AC-07-23 (REQ-FN-064, REQ-SEC-010): ช่างที่ไม่เคยทำงานให้ หรือเคยแต่ยังไม่เสร็จ ไม่อยู่ในรายการ และเปิดดูไม่ได้
def test_AC_07_23_only_own_done_jobs_count(client, db, seed, past_job):
    # Given ลูกค้า "คนอื่น" ไม่เคยใช้ช่างคนไหน และสมชายมีงานของ "ไกลมาก" ที่ยกเลิก
    r = book(client, customer_id=seed["somchai"].id, slot_id=seed["slots"][4].id, address_id=seed["addr"].id)
    assert r.status_code == 201
    job = db.get(Job, r.json()["job_id"]); set_status(db, job, "cancelled", NOW); db.commit()
    assert client.get(f"/me/past-technicians{q()}", headers=H("customer", seed["other"].id)).json() == []
    assert [p["name"] for p in client.get(f"/me/past-technicians{q()}", headers=H("customer", seed["somchai"].id)).json()] == ["ประสิทธิ์"]
    # When ลูกค้า "คนอื่น" ขอช่วงเวลาของ "ประสิทธิ์" ผ่านช่องทางช่างคนเดิม Then 403 และบันทึก
    denied = slots_of(client, seed, seed["prasit"].id, address_id=seed["addr_other"].id, who=seed["other"].id)
    assert denied.status_code == 403
    assert db.scalars(select(SecurityEvent)).first().endpoint == "GET /me/past-technicians/{technician_id}/slots"
    # And งานที่เสร็จนานกว่า 12 เดือนไม่นับ
    past_job.scheduled_start = NOW - timedelta(days=400); db.commit()
    assert client.get(f"/me/past-technicians{q()}", headers=H("customer", seed["somchai"].id)).json() == []


# รองรับ AC-07-24 (REQ-FN-065, UC-07 A1, Q-28): ไม่มีช่างว่างใน 7 วัน ระบบตอบรายการว่าง และมีเลขโทร call center ให้หน้าจอ
def test_AC_07_24_no_technician_in_7_days(client, db, seed):
    for s in db.scalars(select(TimeSlot)).all():
        s.state = "booked"
    db.commit()
    r = client.get(f"/technicians?category=ประปา&address_id={seed['addr'].id}&now={NOW.isoformat()}",
                   headers=H("customer", seed["somchai"].id))
    assert r.status_code == 200 and r.json() == [] and r.headers["x-result-count"] == "0"
    assert client.get("/contact").json() == {"call_center_tel": "02-000-0000"}
