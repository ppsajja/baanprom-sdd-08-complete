"""AC-12-01 ถึง AC-12-05 และ AC-05-01 ถึง AC-05-06 จาก accept-rematch.feature (specs/007-accept-rematch, CR-12)
UC-12 ช่างรับหรือปฏิเสธงาน | UC-05 จับคู่ช่างใหม่แบบกฎ BR-07 (MD-STM-01 ลูกศร ยืนยันแล้ว ไปยัง กำลังหาช่างใหม่)
BR-01 R4 หาไม่ได้ภายใน 2 ชั่วโมง หรือลูกค้าปฏิเสธช่างแทน คืนมัดจำเต็ม"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import config
from app.db.models import Job, JobAssignment, Refund, SecurityEvent, Technician, TimeSlot, SLOT_BOOKED, SLOT_FREE
from app.matching import service as matching
from app.notify.queue import queue
from tests.conftest import NOW, TOMORROW_14, H, book


def q(now=NOW):
    return f"?now={now.isoformat()}"


@pytest.fixture()
def others(db, seed):
    """ช่างเพิ่ม 3 คน มีช่วงเวลาเดียวกับนัดเดิม (พรุ่งนี้ 14:00) ห่างจากบ้านสมชาย ราว 2.2 กม. 5.5 กม. และช่างไฟฟ้าอย่างเดียว 1 กม."""
    near = Technician(name="สมหมาย", skills="ประปา", base_lat=13.7200, base_lng=100.5300)
    mid = Technician(name="วิชัย", skills="ประปา,แอร์", base_lat=13.6900, base_lng=100.5300)
    elec = Technician(name="ไฟฟ้าล้วน", skills="ไฟฟ้า", base_lat=13.7310, base_lng=100.5300)
    db.add_all([near, mid, elec]); db.flush()
    slots = {t.name: TimeSlot(technician_id=t.id, start=TOMORROW_14, end=TOMORROW_14 + timedelta(hours=2))
             for t in (near, mid, elec)}
    db.add_all(slots.values()); db.commit()
    return {"near": near, "mid": mid, "elec": elec, "slots": slots}


def confirmed_job(client, db, seed):
    r = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert r.status_code == 201
    job = db.get(Job, r.json()["job_id"]); db.refresh(job)
    return job


def jobs_of(client, tech_id, now=NOW):
    return client.get(f"/technicians/{tech_id}/jobs{q(now)}", headers=H("technician", tech_id))


def reject(client, job_id, tech_id, now=NOW):
    return client.post(f"/jobs/{job_id}/reject{q(now)}", json={"reason": "ติดงานอื่น"}, headers=H("technician", tech_id))


# รองรับ AC-12-01 (REQ-FN-061)
def test_AC_12_01_new_job_offered_with_accept_and_reject(client, db, seed):
    job = confirmed_job(client, db, seed)
    # When ช่าง "ประสิทธิ์" เปิดรายการงาน
    view = jobs_of(client, seed["prasit"].id).json()[0]
    # Then เห็นปุ่ม "รับงาน" และ "ปฏิเสธงาน" ต้องตอบภายใน 30 นาทีนับจากเวลาที่งานยืนยัน
    assert [r["label"] for r in view["responses"]] == ["รับงาน", "ปฏิเสธงาน"]
    assert view["assignment"]["response"] == "pending"
    assert view["assignment"]["respond_by"] == (NOW + timedelta(minutes=30)).isoformat()
    assert view["status"] == "confirmed"


# รองรับ AC-12-02 (REQ-FN-061): รับงานไม่เปลี่ยนสถานะงาน (MD-STM-01)
def test_AC_12_02_accept_keeps_status_and_hides_accept_button(client, db, seed):
    job = confirmed_job(client, db, seed)
    r = client.post(f"/jobs/{job.id}/accept{q(NOW + timedelta(minutes=5))}", headers=H("technician", seed["prasit"].id))
    assert r.status_code == 200
    assert r.json()["status"] == "confirmed" and r.json()["assignment"]["response"] == "accepted"
    assert [x["label"] for x in r.json()["responses"]] == ["ปฏิเสธงาน"]
    # กดรับซ้ำได้ผลเดิม
    assert client.post(f"/jobs/{job.id}/accept{q()}", headers=H("technician", seed["prasit"].id)).status_code == 200


# รองรับ AC-12-03 (REQ-FN-061, BR-07 ข้อ 2): กดออกเดินทางโดยไม่กดรับ ถือว่ารับแล้ว
def test_AC_12_03_departure_counts_as_accept(client, db, seed):
    job = confirmed_job(client, db, seed)
    r = client.post(f"/jobs/{job.id}/status{q(TOMORROW_14 - timedelta(hours=1))}", json={"to_status": "en_route"},
                    headers=H("technician", seed["prasit"].id))
    assert r.status_code == 200 and r.json()["responses"] == []
    a = matching.current_assignment(db, db.get(Job, job.id))
    db.refresh(a)
    assert a.response == "accepted"


# รองรับ AC-12-04 (REQ-SEC-010): ช่างคนอื่นรับหรือปฏิเสธงานนี้ไม่ได้
def test_AC_12_04_other_technician_cannot_respond(client, db, seed):
    job = confirmed_job(client, db, seed)
    far = H("technician", seed["far"].id)
    assert client.post(f"/jobs/{job.id}/accept{q()}", headers=far).status_code == 403
    assert client.post(f"/jobs/{job.id}/reject{q()}", json={}, headers=far).status_code == 403
    assert client.post(f"/jobs/{job.id}/accept{q()}", headers=H("customer", seed["somchai"].id)).status_code == 403
    db.refresh(job); assert job.status == "confirmed"
    assert len(db.scalars(select(SecurityEvent).where(SecurityEvent.kind == "denied")).all()) == 2


# รองรับ AC-12-05 (REQ-FN-061, BR-07 ข้อ 1): ปฏิเสธได้จนกว่าจะออกเดินทาง
def test_AC_12_05_cannot_reject_after_departure(client, db, seed):
    job = confirmed_job(client, db, seed)
    tech = H("technician", seed["prasit"].id)
    client.post(f"/jobs/{job.id}/status{q()}", json={"to_status": "en_route"}, headers=tech)
    r = reject(client, job.id, seed["prasit"].id)
    assert r.status_code == 409 and r.json()["reason"] == "not_confirmed"
    db.refresh(job); assert job.status == "en_route"


# รองรับ AC-05-01 (REQ-FN-062, BR-07 ข้อ 3, MD-STM-01)
def test_AC_05_01_reject_rematches_to_nearest_free_technician_same_time(client, db, seed, others):
    job = confirmed_job(client, db, seed)
    queue.clear()
    at = NOW + timedelta(minutes=10)
    # When ช่าง "ประสิทธิ์" ปฏิเสธงาน
    r = reject(client, job.id, seed["prasit"].id, at)
    assert r.status_code == 200
    # Then งานได้ช่าง "สมหมาย" (ทักษะตรง ใกล้ที่สุด ว่างเวลาเดิม) สถานะกลับเป็น "ยืนยันแล้ว" เวลานัดเดิม
    db.refresh(job)
    assert job.status == "confirmed" and job.technician_id == others["near"].id and job.scheduled_start == TOMORROW_14
    # And ช่วงเวลาของช่างเดิมกลับเป็น "ว่าง" ช่วงเวลาของช่างใหม่เป็น "จองแล้ว"
    old, new = db.get(TimeSlot, seed["slot"].id), others["slots"]["สมหมาย"]
    db.refresh(old); db.refresh(new)
    assert old.state == SLOT_FREE and new.state == SLOT_BOOKED
    # And ประวัติมีลูกศร ยืนยันแล้ว ไปยัง กำลังหาช่างใหม่ และ กำลังหาช่างใหม่ ไปยัง ยืนยันแล้ว
    h = client.get(f"/jobs/{job.id}/history{q(at)}", headers=H("customer", job.customer_id)).json()["history"]
    assert [(x["from_status"], x["to_status"]) for x in h[-2:]] == [("confirmed", "rematching"), ("rematching", "confirmed")]
    # And ลูกค้าได้ข้อความชื่อช่างใหม่ ช่างใหม่ได้งานให้ตอบภายใน 30 นาที ช่างเดิมได้ข้อความว่าส่งต่อแล้ว
    texts = {(m.to_role, m.to_id): m.text for m in queue.for_job(job.id)}
    assert "ได้ช่างใหม่ สมหมาย" in texts[("customer", seed["somchai"].id)]
    assert "30 นาที" in texts[("technician", others["near"].id)]
    assert "ส่งต่อช่างคนอื่นแล้ว" in texts[("technician", seed["prasit"].id)]
    assert all(m.due_at - m.created_at <= timedelta(seconds=60) for m in queue.for_job(job.id))
    # And ช่างเดิมไม่เห็นงานนี้อีก (รายการและหน้างาน) ช่างใหม่เห็นพร้อมปุ่มรับงาน
    assert jobs_of(client, seed["prasit"].id, at).json() == []
    assert client.get(f"/jobs/{job.id}/technician-view{q(at)}", headers=H("technician", seed["prasit"].id)).status_code == 403
    mine = jobs_of(client, others["near"].id, at).json()
    assert [j["job_id"] for j in mine] == [job.id] and mine[0]["assignment"]["via_rematch"] is True


# รองรับ AC-05-02 (REQ-FN-063, BR-01 R4, Q-50): หาไม่ได้ภายใน 2 ชั่วโมง ยกเลิกและคืนเต็ม
def test_AC_05_02_no_substitute_within_2_hours_cancels_with_full_refund(client, db, seed, gateway):
    job = confirmed_job(client, db, seed)   # ไม่มีช่างอื่นในระยะที่ว่างเวลาเดิม (ช่าง "ไกลมาก" อยู่ 40 กม.)
    queue.clear()
    at = NOW + timedelta(minutes=10)
    assert reject(client, job.id, seed["prasit"].id, at).status_code == 200
    db.refresh(job)
    # Then งานยังเป็น "กำลังหาช่างใหม่" ลูกค้าได้ข้อความว่ากำลังหาช่างใหม่ภายใน 2 ชั่วโมง
    assert job.status == "rematching"
    assert any("กำลังหาช่างใหม่" in m.text for m in queue.for_job(job.id) if m.to_role == "customer")
    # When งานเบื้องหลังทำงานก่อนครบ 2 ชั่วโมง Then ยังไม่ยกเลิก
    assert matching.process_due(db, at + timedelta(hours=1, minutes=59))["cancelled"] == 0
    # When ครบ 2 ชั่วโมง Then ยกเลิกตาม BR-01 R4 คืนมัดจำ 350 บาทเต็มผ่าน gateway
    out = matching.process_due(db, at + timedelta(hours=2))
    assert out["cancelled"] == 1
    db.refresh(job); assert job.status == "cancelled"
    refund = db.scalars(select(Refund).where(Refund.job_id == job.id)).one()
    assert refund.rule == "R4" and refund.amount == job.deposit_amount == 350 and refund.result == "approved"
    # And ช่างเดิมไม่ได้ข้อความยกเลิกซ้ำ (ปฏิเสธไปแล้ว)
    tech_msgs = [m.text for m in queue.for_job(job.id) if m.to_role == "technician"]
    assert len(tech_msgs) == 1 and "ส่งต่อช่างคนอื่นแล้ว" in tech_msgs[0]


# รองรับ AC-05-03 (REQ-FN-061): ช่างไม่ตอบภายใน 30 นาที ถือว่าปฏิเสธ แล้วจับคู่ใหม่
def test_AC_05_03_no_response_in_30_minutes_counts_as_reject(client, db, seed, others):
    job = confirmed_job(client, db, seed)
    assert matching.process_due(db, NOW + timedelta(minutes=29))["no_response"] == 0
    out = matching.process_due(db, NOW + timedelta(minutes=30))
    assert out["no_response"] == 1
    db.refresh(job)
    assert job.status == "confirmed" and job.technician_id == others["near"].id
    first = db.scalars(select(JobAssignment).where(JobAssignment.job_id == job.id).order_by(JobAssignment.id)).first()
    assert first.technician_id == seed["prasit"].id and first.response == "no_response"


# รองรับ AC-05-04 (REQ-FN-063, BR-01 R4): ลูกค้าไม่รับช่างแทน คืนมัดจำเต็ม แม้เหลือน้อยกว่า 24 ชั่วโมง
def test_AC_05_04_customer_declines_substitute_full_refund(client, db, seed, gateway, others):
    job = confirmed_job(client, db, seed)
    me = H("customer", seed["somchai"].id)
    # Given งานที่ยังเป็นช่างเดิม ปฏิเสธช่างแทนไม่ได้
    no = client.post(f"/jobs/{job.id}/decline-substitute{q()}", headers=me)
    assert no.status_code == 409 and no.json()["reason"] == "not_substitute"
    reject(client, job.id, seed["prasit"].id)
    view = [j for j in client.get(f"/me/jobs{q()}", headers=me).json() if j["job_id"] == job.id][0]
    assert view["substitute"] is True and view["can_decline_substitute"] is True and view["technician_name"] == "สมหมาย"
    # When ลูกค้ากด "ไม่รับช่างแทน" เมื่อเหลือ 20 ชั่วโมงก่อนนัด
    late = TOMORROW_14 - timedelta(hours=20)
    r = client.post(f"/jobs/{job.id}/decline-substitute{q(late)}", headers=me)
    # Then ยกเลิกตาม R4 ได้คืน 350 บาทเต็ม (ไม่ใช่ R2 50 ใน 100) ช่วงเวลาของช่างแทนกลับเป็นว่าง
    assert r.status_code == 200 and r.json()["rule"] == "R4" and r.json()["refund_amount"] == 350
    new = others["slots"]["สมหมาย"]; db.refresh(new)
    assert new.state == SLOT_FREE
    # And ลูกค้าคนอื่นกดแทนไม่ได้
    assert client.post(f"/jobs/{job.id}/decline-substitute{q(late)}", headers=H("customer", seed["other"].id)).status_code == 403


# รองรับ AC-05-05 (BR-07 ข้อ 3 และ 4): ไม่ส่งกลับไปหาช่างที่เคยปฏิเสธ เรียงตามระยะ ทักษะต้องตรง
def test_AC_05_05_order_by_distance_skip_tried_and_wrong_skill(client, db, seed, others):
    job = confirmed_job(client, db, seed)
    reject(client, job.id, seed["prasit"].id)
    db.refresh(job); assert job.technician_id == others["near"].id
    # When ช่าง "สมหมาย" ปฏิเสธต่อ Then ได้ "วิชัย" (ไกลกว่า) ไม่ใช่ "ไฟฟ้าล้วน" (ใกล้แต่ทักษะไม่ตรง) และไม่กลับไปที่ "ประสิทธิ์"
    reject(client, job.id, others["near"].id)
    db.refresh(job); assert job.technician_id == others["mid"].id and job.status == "confirmed"
    # When "วิชัย" ปฏิเสธอีก Then ไม่มีคนเหลือ งานรอหาช่างใหม่
    reject(client, job.id, others["mid"].id)
    db.refresh(job); assert job.status == "rematching"
    tried = [a.technician_id for a in db.scalars(select(JobAssignment).where(JobAssignment.job_id == job.id)
                                                  .order_by(JobAssignment.id))]
    assert tried == [seed["prasit"].id, others["near"].id, others["mid"].id]


# รองรับ AC-05-06 (BR-07 ข้อ 3, BR-03): ช่างที่อยู่นอกระยะ 15 กม. ไม่ถูกจับคู่ แม้ว่างเวลาเดิม และใกล้นัดเกินไปไม่จับคู่
def test_AC_05_06_out_of_range_and_too_close_to_start_not_matched(client, db, seed, gateway):
    job = confirmed_job(client, db, seed)
    at = TOMORROW_14 - timedelta(hours=1, minutes=30)
    reject(client, job.id, seed["prasit"].id, at)
    db.refresh(job)
    assert job.status == "rematching"   # ช่าง "ไกลมาก" ว่างเวลาเดิมแต่อยู่ 40 กม.
    far_slot = db.get(TimeSlot, seed["slots"][4].id); db.refresh(far_slot)
    assert far_slot.state == SLOT_FREE
    # When เหลือเวลาก่อนนัดน้อยกว่า 1 ชั่วโมง (ผ่านไปเพียง 31 นาทีหลังปฏิเสธ) Then ยกเลิกทันทีตาม R4 ไม่รอครบ 2 ชั่วโมง
    assert matching.process_due(db, TOMORROW_14 - timedelta(hours=1))["cancelled"] == 0
    near_start = TOMORROW_14 - timedelta(minutes=config.REMATCH_MIN_HOURS_BEFORE * 60 - 1)
    assert matching.process_due(db, near_start)["cancelled"] == 1
    db.refresh(job); assert job.status == "cancelled"
