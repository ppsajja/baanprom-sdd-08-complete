"""AC-07-12 ถึง AC-07-16 จาก booking.feature v1.4 (CR-07, T-18 ถึง T-21 ของ 002)
REQ-QA-010 gateway ไม่ตอบเลย และลองใหม่ด้วย reference เดิม | REQ-SEC-011 จำกัดการล็อก | REQ-SEC-010 สิทธิ์ต่องาน"""
from datetime import timedelta

from sqlalchemy import select

from app.db.models import Job, Payment, TimeSlot, SecurityEvent
from tests.conftest import NOW, TOMORROW_14, book, H


def hold(client, slot_id, customer_id, now=NOW):
    return client.post(f"/slots/{slot_id}/hold?now={now.isoformat()}", json={"customer_id": customer_id},
                       headers=H("customer", customer_id))


# รองรับ AC-07-12 (REQ-QA-010 บรรทัดที่ 3, REQ-FN-041)
def test_AC_07_12_gateway_unreachable_keeps_hold_as_pending(client, db, seed, gateway):
    # Given ลูกค้าล็อกช่วงเวลาไว้ และ Payment Gateway ไม่ตอบทั้งคำขอ authorize และ status-inquiry
    assert hold(client, seed["slot"].id, seed["somchai"].id).status_code == 200
    gateway.mode, gateway.inquiry_answer = "timeout", "timeout"
    # When ลูกค้ากดยืนยัน
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    # Then ระบบตอบว่ารับคำขอแล้วแต่ยังไม่รู้ผลการชำระ และบอกเวลาสิ้นสุดของล็อก
    assert res.status_code == 202, res.text
    body = res.json()
    assert body["reason"] == "payment_pending" and "ไม่ตัดเงินซ้ำ" in body["message"]
    assert body["hold_expires_at"] == (NOW + timedelta(minutes=10)).isoformat()
    # And งานมีสถานะ "รอชำระเงิน" และช่วงเวลายังถูกล็อกโดยลูกค้าคนนี้
    job = db.get(Job, body["job_id"]); db.refresh(job)
    assert job.status == "pending_payment"
    slot = db.get(TimeSlot, seed["slot"].id); db.refresh(slot)
    assert slot.state == "held" and slot.held_by_customer_id == seed["somchai"].id
    # And มีรายการชำระ 1 รายการสถานะ pending พร้อม reference
    pays = db.scalars(select(Payment).where(Payment.job_id == job.id)).all()
    assert [p.result for p in pays] == ["pending"] and pays[0].gateway_ref
    # When ครบ 10 นาทีแล้ว gateway ยังไม่ตอบ (ลูกค้าอีกคนค้นหา ระบบตรวจล็อกที่หมดอายุ)
    later = NOW + timedelta(minutes=10)
    client.get(f"/technicians?category=ประปา&address_id={seed['addr_other'].id}&now={later.isoformat()}",
               headers=H("customer", seed["other"].id))
    # Then งานเป็น "ยกเลิกอัตโนมัติ" ช่วงเวลาว่าง ไม่มีรายการชำระสำเร็จ และ void ด้วย reference เดิม
    db.refresh(job); db.refresh(slot)
    assert job.status == "auto_cancelled" and slot.state == "free"
    assert db.scalar(select(Payment).where(Payment.job_id == job.id, Payment.result == "success")) is None
    assert f"void:{pays[0].gateway_ref}" in gateway.calls


# รองรับ AC-07-13 (REQ-QA-010 บรรทัดที่ 2, REQ-IF-005) เหตุการณ์ B ในรูป test
def test_AC_07_13_retry_uses_same_reference_no_double_charge(client, db, seed, gateway):
    # Given การจองของลูกค้าค้างเป็น "รอชำระเงิน" เพราะ gateway ไม่ตอบ
    gateway.mode, gateway.inquiry_answer = "timeout", "timeout"
    first = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert first.status_code == 202
    job_id = first.json()["job_id"]
    # And gateway กลับมาตอบ และรายการเดิม approved ไปแล้วฝั่ง gateway
    gateway.mode, gateway.inquiry_answer = "approved", "approved"
    # When ลูกค้ากดยืนยันอีกครั้งภายในเวลาล็อก
    again = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id,
                 now=NOW + timedelta(minutes=3))
    # Then งานเดิมมีสถานะ "ยืนยันแล้ว" ไม่มีงานใหม่
    assert again.status_code == 201, again.text
    assert again.json()["job_id"] == job_id and again.json()["status"] == "confirmed"
    assert len(db.scalars(select(Job).where(Job.customer_id == seed["somchai"].id)).all()) == 1
    # And คำขอ authorize ถูกส่ง 1 ครั้งเท่านั้น การลองใหม่ใช้ status-inquiry ด้วย reference เดิม
    assert sum(1 for c in gateway.calls if c.startswith("authorize")) == 1
    refs = {c.split(":")[1] for c in gateway.calls if c.startswith(("authorize", "inquiry", "capture"))}
    assert len(refs) == 1
    # And มีรายการชำระสำเร็จ 1 รายการเท่านั้น
    pays = db.scalars(select(Payment).where(Payment.job_id == job_id)).all()
    assert [p.result for p in pays] == ["success"]


# รองรับ AC-07-14 (REQ-SEC-011)
def test_AC_07_14_second_hold_rejected(client, db, seed):
    # Given ลูกค้าล็อกช่วงเวลา พรุ่งนี้ 14:00-16:00 ไว้และยังไม่หมดอายุ
    first, second = seed["slots"][0], seed["slots"][1]
    assert hold(client, first.id, seed["somchai"].id).status_code == 200
    # When ลูกค้าคนเดิมขอล็อกช่วง พรุ่งนี้ 16:00-18:00
    r = hold(client, second.id, seed["somchai"].id, NOW + timedelta(minutes=2))
    # Then ระบบปฏิเสธ (409) และบอกว่าช่วงใดที่ยังถืออยู่
    assert r.status_code == 409 and r.json()["reason"] == "hold_limit"
    assert [h["slot_id"] for h in r.json()["held"]] == [first.id]
    # And ตาราง time_slots มีแถวที่ลูกค้าคนนี้ถือล็อกเพียง 1 แถว
    held = db.scalars(select(TimeSlot).where(TimeSlot.held_by_customer_id == seed["somchai"].id)).all()
    assert [s.id for s in held] == [first.id]
    # And เมื่อล็อกแรกหมดอายุ (10 นาที) ลูกค้าล็อกช่วงใหม่ได้
    assert hold(client, second.id, seed["somchai"].id, NOW + timedelta(minutes=11)).status_code == 200
    # And ล็อกช่วงเดิมซ้ำได้ ไม่นับเป็นช่วงที่สอง
    assert hold(client, second.id, seed["somchai"].id, NOW + timedelta(minutes=12)).status_code == 200


# รองรับ AC-07-15 (REQ-SEC-010 บรรทัดที่ 1, 2 และ 4)
def test_AC_07_15_technician_view_other_job_forbidden_and_logged(client, db, seed):
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    job_id = res.json()["job_id"]
    at_1200 = (TOMORROW_14 - timedelta(hours=2)).isoformat()
    # When ช่าง "ไกลมาก" เปิดดูงานของช่าง "ประสิทธิ์" และงานที่ไม่มีอยู่
    far = H("technician", seed["far"].id)
    other = client.get(f"/jobs/{job_id}/technician-view?technician_id={seed['far'].id}&now={at_1200}", headers=far)
    missing = client.get(f"/jobs/99999/technician-view?technician_id={seed['far'].id}&now={at_1200}", headers=far)
    # Then ทั้งสองคำขอได้ 403 ข้อความเดียวกัน ไม่บอกว่างานมีอยู่หรือไม่ และไม่มีเบอร์ลูกค้า
    assert other.status_code == missing.status_code == 403
    assert other.json() == missing.json()
    assert "081-234-5678" not in other.text
    # And มีบันทึกความพยายาม 2 รายการ พร้อมผู้ส่ง เวลา และเลขงานที่ขอ
    denied = db.scalars(select(SecurityEvent).where(SecurityEvent.kind == "denied")).all()
    assert [(e.actor_role, e.actor_id, e.job_id) for e in denied] == [
        ("technician", seed["far"].id, job_id), ("technician", seed["far"].id, 99999)]
    assert all(e.at.isoformat() == at_1200 for e in denied)
    # When ช่างเจ้าของงานเปิดดูในช่วง 2 ชั่วโมงก่อนนัด Then เห็นเบอร์ และมีบันทึกการส่งเบอร์ที่ไม่มีตัวเบอร์
    mine = client.get(f"/jobs/{job_id}/technician-view?technician_id={seed['prasit'].id}&now={at_1200}",
                      headers=H("technician", seed["prasit"].id))
    assert mine.json()["customer_phone"] == "081-234-5678"
    shown = db.scalars(select(SecurityEvent).where(SecurityEvent.kind == "phone_revealed")).all()
    assert [(e.actor_id, e.job_id) for e in shown] == [(seed["prasit"].id, job_id)]
    assert not hasattr(SecurityEvent, "phone")


# รองรับ AC-07-16 (REQ-SEC-010, OWASP API9:2023)
def test_AC_07_16_legacy_cancel_endpoint_closed(client, db, seed, gateway):
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    job_id = res.json()["job_id"]
    # When ใครก็ตามส่ง POST /jobs/{id}/cancel แบบเดิม (MU-01 ขั้นที่ 3)
    for body in ({"cancelled_by": "customer"}, {"cancelled_by": "system"}):
        r = client.post(f"/jobs/{job_id}/cancel?now={NOW.isoformat()}", json=body)
        # Then ไม่มี endpoint นี้แล้ว
        assert r.status_code in (404, 405)
    # And งานยังเป็น "ยืนยันแล้ว" และไม่มีคำขอคืนเงิน
    job = db.get(Job, job_id); db.refresh(job)
    assert job.status == "confirmed"
    assert not [c for c in gateway.calls if c.startswith("refund:")]
    # And บัญชี endpoint ของระบบมีทางยกเลิกของลูกค้าทางเดียว
    paths = set(client.get("/openapi.json").json()["paths"])
    assert "/jobs/{job_id}/cancel" not in paths and "/jobs/{job_id}/customer-cancel" in paths
