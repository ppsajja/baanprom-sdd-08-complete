"""AC-04-01 ถึง AC-04-08 จาก schedule.feature (specs/008-schedule, CR-14) UC-04 ช่างจัดตารางเวลาว่างและวันหยุด
BR-10 ช่วงละ 2 ชั่วโมง ตรงชั่วโมง 08:00 ถึง 20:00 ล่วงหน้าไม่เกิน 30 วัน ไม่ซ้อน ช่วงที่ปิดไม่ปรากฏในการค้นหา การจอง และการจับคู่"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import Job, SecurityEvent, Technician, TimeSlot, SLOT_CLOSED, SLOT_FREE
from tests.conftest import NOW, TOMORROW_14, H, book


def q(now=NOW):
    return f"?now={now.isoformat()}"


def tech_h(seed):
    return H("technician", seed["prasit"].id)


def search(client, seed, now=NOW):
    r = client.get(f"/technicians{q(now)}&category=ประปา&address_id={seed['addr'].id}", headers=H("customer", seed["somchai"].id))
    assert r.status_code == 200
    return [s["slot_id"] for t in r.json() for s in t["slots"]]


def add(client, seed, start, headers=None):
    return client.post(f"/me/slots{q()}", json={"start": start.isoformat()}, headers=headers or tech_h(seed))


# รองรับ AC-04-01 (REQ-FN-066): ช่างเพิ่มช่วงเวลาว่าง ลูกค้าค้นหาเห็นช่วงนั้น
def test_AC_04_01_add_slot_visible_in_search(client, db, seed):
    start = (NOW + timedelta(days=2)).replace(hour=9, minute=0)
    r = add(client, seed, start)
    assert r.status_code == 201 and r.json()["state"] == "free"
    assert r.json()["end"] == (start + timedelta(hours=2)).isoformat()
    assert r.json()["slot_id"] in search(client, seed)
    view = client.get(f"/me/schedule{q()}", headers=tech_h(seed)).json()
    day = next(d for d in view["days"] if d["date"] == start.date().isoformat())
    # วันนั้นมีช่วง 14:00 จากข้อมูลตั้งต้นอยู่แล้ว ช่วงใหม่ 09:00 ต้องมาก่อน (เรียงตามเวลา) สถานะ "ว่าง"
    assert [(s["start"], s["state_th"]) for s in day["slots"]][0] == (start.isoformat(), "ว่าง")


# รองรับ AC-04-02 (BR-10 ข้อ 1 ถึง 4): ช่วงที่ผิดกฎถูกปฏิเสธ ไม่มีแถวใหม่
@pytest.mark.parametrize("start,reason,code", [
    ((NOW + timedelta(days=2)).replace(hour=9, minute=30), "not_on_hour", 422),
    ((NOW + timedelta(days=2)).replace(hour=7), "outside_hours", 422),
    ((NOW + timedelta(days=2)).replace(hour=19), "outside_hours", 422),
    (NOW.replace(hour=10, minute=0), "too_soon", 422),
    ((NOW + timedelta(days=31)).replace(hour=9), "too_far", 422),
    (TOMORROW_14 + timedelta(hours=1), "overlap", 409),
], ids=["not_on_hour", "before_8", "ends_after_20", "too_soon", "too_far", "overlap"])
def test_AC_04_02_rules_reject(client, db, seed, start, reason, code):
    before = db.query(TimeSlot).count()
    r = add(client, seed, start)
    assert r.status_code == code and r.json()["reason"] == reason and r.json()["message"]
    assert db.query(TimeSlot).count() == before


# รองรับ AC-04-03 (REQ-FN-066 BR-10 ข้อ 5): ปิดช่วงที่ว่าง ลูกค้าไม่เห็น ล็อกไม่ได้ ระบบไม่ใช้จับคู่
def test_AC_04_03_close_free_slot_hidden_everywhere(client, db, seed):
    slot = seed["slots"][1]
    r = client.post(f"/me/slots/{slot.id}/close{q()}", headers=tech_h(seed))
    assert r.status_code == 200 and r.json()["state"] == SLOT_CLOSED
    assert slot.id not in search(client, seed)
    hold = client.post(f"/slots/{slot.id}/hold{q()}", json={}, headers=H("customer", seed["somchai"].id))
    assert hold.status_code == 409 and hold.json()["reason"] == "slot_taken"
    assert book(client, customer_id=seed["somchai"].id, slot_id=slot.id, address_id=seed["addr"].id).status_code == 409
    # เพิ่มช่วงเดิมอีกครั้ง = เปิดช่วงที่ปิดไว้ ไม่สร้างแถวซ้ำ
    again = add(client, seed, slot.start)
    assert again.status_code == 201 and again.json()["reopened"] is True and again.json()["slot_id"] == slot.id
    assert slot.id in search(client, seed)


# รองรับ AC-04-04 (BR-10 ข้อ 5): ช่วงที่จองแล้วหรือลูกค้ากำลังล็อก ปิดไม่ได้
def test_AC_04_04_cannot_close_booked_or_held(client, db, seed):
    assert book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id).status_code == 201
    r = client.post(f"/me/slots/{seed['slot'].id}/close{q()}", headers=tech_h(seed))
    assert r.status_code == 409 and r.json()["reason"] == "not_free"
    held = seed["slots"][1]
    assert client.post(f"/slots/{held.id}/hold{q()}", json={}, headers=H("customer", seed["other"].id)).status_code == 200
    r = client.post(f"/me/slots/{held.id}/close{q()}", headers=tech_h(seed))
    assert r.status_code == 409
    db.refresh(held)
    assert held.state == "held"


# รองรับ AC-04-05 (REQ-FN-067 BR-10 ข้อ 6): วันหยุดปิดช่วงว่างทั้งวัน ค้นหาไม่เห็น จับคู่ช่างใหม่ไม่เลือก เพิ่มช่วงในวันนั้นไม่ได้
def test_AC_04_05_day_off_hides_slots_and_rematch(client, db, seed):
    near = Technician(name="สมหมาย", skills="ประปา", base_lat=13.7200, base_lng=100.5300)
    db.add(near); db.flush()
    near_slot = TimeSlot(technician_id=near.id, start=TOMORROW_14, end=TOMORROW_14 + timedelta(hours=2))
    db.add(near_slot); db.commit()
    r = client.post(f"/me/days-off{q()}", json={"day": TOMORROW_14.date().isoformat()}, headers=H("technician", near.id))
    assert r.status_code == 201 and r.json()["closed_slots"] == 1
    db.refresh(near_slot)
    assert near_slot.state == SLOT_CLOSED and near_slot.id not in search(client, seed)
    assert add(client, seed, TOMORROW_14.replace(hour=9), headers=H("technician", near.id)).json()["reason"] == "day_off"
    # งานของสมชายกับประสิทธิ์ ช่างปฏิเสธ ระบบไม่จับคู่สมหมายที่หยุดวันนั้น
    job_id = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id).json()["job_id"]
    client.post(f"/jobs/{job_id}/reject{q()}", json={"reason": "ติดงาน"}, headers=tech_h(seed))
    job = db.get(Job, job_id); db.refresh(job)
    assert job.status == "rematching"


# รองรับ AC-04-06 (BR-10 ข้อ 7): วันที่มีงานจองแล้ว ประกาศวันหยุดไม่ได้ บอกเลขงาน
def test_AC_04_06_day_off_refused_when_booked(client, db, seed):
    job_id = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id).json()["job_id"]
    r = client.post(f"/me/days-off{q()}", json={"day": TOMORROW_14.date().isoformat()}, headers=tech_h(seed))
    assert r.status_code == 409 and r.json()["reason"] == "has_jobs" and r.json()["job_ids"] == [job_id]
    db.refresh(seed["slots"][1])
    assert seed["slots"][1].state == SLOT_FREE  # ช่วงอื่นของวันนั้นไม่ถูกปิด
    assert client.post(f"/me/days-off{q()}", json={"day": NOW.date().isoformat()}, headers=tech_h(seed)).json()["reason"] == "past_day"


# รองรับ AC-04-07 (BR-10 ข้อ 8): ยกเลิกวันหยุด ช่วงที่ปิดเพราะวันหยุดกลับเป็นว่าง ช่วงที่ช่างปิดเองก่อนหน้ายังปิด
def test_AC_04_07_remove_day_off_reopens_only_its_slots(client, db, seed):
    a, b = seed["slots"][1], seed["slots"][2]   # วันพรุ่งนี้ทั้งคู่
    client.post(f"/me/slots/{b.id}/close{q()}", headers=tech_h(seed))
    day = TOMORROW_14.date().isoformat()
    assert client.post(f"/me/days-off{q()}", json={"day": day}, headers=tech_h(seed)).json()["closed_slots"] == 2
    r = client.delete(f"/me/days-off/{day}{q()}", headers=tech_h(seed))
    assert r.status_code == 200 and r.json()["reopened_slots"] == 2
    for s in (seed["slot"], a, b):
        db.refresh(s)
    assert seed["slot"].state == SLOT_FREE and a.state == SLOT_FREE and b.state == SLOT_CLOSED
    assert client.delete(f"/me/days-off/{day}{q()}", headers=tech_h(seed)).status_code == 404


# รองรับ AC-04-08 (REQ-SEC-010 REQ-SEC-014): ช่างคนอื่นปิดช่วงของช่างคนนี้ไม่ได้ ลูกค้าเปิดตารางของช่างไม่ได้
def test_AC_04_08_other_technician_and_customer_denied(client, db, seed):
    r = client.post(f"/me/slots/{seed['slot'].id}/close{q()}", headers=H("technician", seed["far"].id))
    assert r.status_code == 403 and r.json()["detail"] == "ไม่มีสิทธิ์กับงานนี้"
    db.refresh(seed["slot"])
    assert seed["slot"].state == SLOT_FREE
    ev = db.scalars(select(SecurityEvent).where(SecurityEvent.kind == "denied")).all()
    assert [(e.actor_id, e.endpoint) for e in ev] == [(seed["far"].id, "POST /me/slots/{id}/close")]
    assert client.get(f"/me/schedule{q()}", headers=H("customer", seed["somchai"].id)).status_code == 403
    assert client.get(f"/me/schedule{q()}").status_code == 401
