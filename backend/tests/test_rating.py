"""AC-11-01 ถึง AC-11-08 จาก rating.feature (specs/009-rating, CR-15) UC-11 ลูกค้าให้คะแนนช่างหลังงานเสร็จ
BR-11 (Q-20 ปิดใน EV-051): 1 ถึง 5 ดาว เฉพาะเจ้าของงาน งานเสร็จสิ้น งานละครั้ง ภายใน 14 วัน กันรีวิวตัวเอง
ค่าเฉลี่ยแสดงเมื่อมี 3 คะแนนขึ้นไป ไม่ใช้เรียงช่าง ความเห็นปิดบังข้อมูลติดต่อ ไม่แสดงต่อลูกค้าคนอื่นและช่าง (REQ-PRV-012)"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import Account, Job, Rating, SecurityEvent, Technician, TimeSlot
from tests.conftest import NOW, TOMORROW_14, OPS, H, book


def q(now):
    return f"?now={now.isoformat()}"


DONE_AT = TOMORROW_14 + timedelta(hours=1, minutes=30)


def done_job(client, db, seed, slot=None, customer=None):
    customer = customer or seed["somchai"]
    addr = seed["addr"] if customer is seed["somchai"] else seed["addr_other"]
    slot = slot or seed["slot"]
    job_id = book(client, customer_id=customer.id, slot_id=slot.id, address_id=addr.id).json()["job_id"]
    tech = seed["prasit"].id
    for to, at in (("en_route", slot.start - timedelta(minutes=30)), ("in_progress", slot.start), ("done", slot.start + timedelta(hours=1, minutes=30))):
        assert client.post(f"/jobs/{job_id}/status{q(at)}", json={"to_status": to}, headers=H("technician", tech)).status_code == 200
    return db.get(Job, job_id)


def rate(client, job, stars, comment="", customer_id=None, now=DONE_AT + timedelta(hours=2)):
    return client.post(f"/jobs/{job.id}/rating{q(now)}", json={"stars": stars, "comment": comment},
                       headers=H("customer", customer_id or job.customer_id))


# รองรับ AC-11-01 (REQ-FN-068): ลูกค้าให้ 5 ดาวงานที่เสร็จสิ้น
def test_AC_11_01_rate_done_job(client, db, seed):
    job = done_job(client, db, seed)
    mine = client.get(f"/me/jobs{q(DONE_AT + timedelta(hours=1))}", headers=H("customer", job.customer_id)).json()[0]
    assert mine["can_rate"] is True and mine["my_rating"] is None
    r = rate(client, job, 5, "ช่างตรงเวลา")
    assert r.status_code == 201 and r.json() == {"job_id": job.id, "stars": 5, "message": "ขอบคุณสำหรับคะแนน"}
    mine = client.get(f"/me/jobs{q(DONE_AT + timedelta(hours=3))}", headers=H("customer", job.customer_id)).json()[0]
    assert mine["can_rate"] is False and mine["my_rating"] == 5


# รองรับ AC-11-02 (BR-11 ข้อ 2) และ AC-11-03 (ข้อ 3) และขอบของดาว
def test_AC_11_02_not_done_cannot_rate(client, db, seed):
    job_id = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id).json()["job_id"]
    job = db.get(Job, job_id)
    r = rate(client, job, 4, now=NOW + timedelta(minutes=5))
    assert r.status_code == 409 and r.json()["reason"] == "not_done"
    assert db.query(Rating).count() == 0


@pytest.mark.parametrize("stars", [0, 6])
def test_AC_11_02_stars_must_be_1_to_5(client, db, seed, stars):
    job = done_job(client, db, seed)
    assert rate(client, job, stars).status_code == 422


def test_AC_11_03_only_once_per_job(client, db, seed):
    job = done_job(client, db, seed)
    assert rate(client, job, 4).status_code == 201
    r = rate(client, job, 1)
    assert r.status_code == 409 and r.json()["reason"] == "already_rated"
    assert [x.stars for x in db.query(Rating).all()] == [4]


# รองรับ AC-11-04 (BR-11 ข้อ 4): ภายใน 14 วันหลังช่างปิดงาน
def test_AC_11_04_window_14_days(client, db, seed):
    job = done_job(client, db, seed)
    assert rate(client, job, 3, now=DONE_AT + timedelta(days=14, seconds=1)).json()["reason"] == "window_passed"
    assert rate(client, job, 3, now=DONE_AT + timedelta(days=14)).status_code == 201


# รองรับ AC-11-05 (REQ-SEC-010): ลูกค้าคนอื่นให้คะแนนงานนี้ไม่ได้ ช่างให้คะแนนไม่ได้
def test_AC_11_05_other_customer_denied(client, db, seed):
    job = done_job(client, db, seed)
    r = rate(client, job, 1, customer_id=seed["other"].id)
    assert r.status_code == 403 and r.json()["detail"] == "ไม่มีสิทธิ์กับงานนี้"
    assert db.scalars(select(SecurityEvent).where(SecurityEvent.endpoint == "POST /jobs/{id}/rating")).all()
    r = client.post(f"/jobs/{job.id}/rating{q(DONE_AT)}", json={"stars": 5}, headers=H("technician", seed["prasit"].id))
    assert r.status_code == 403 and db.query(Rating).count() == 0


def _ratings(db, tech_id, stars_list, counted=True):
    for i, s in enumerate(stars_list):
        db.add(Rating(job_id=9000 + tech_id * 100 + i, customer_id=1, technician_id=tech_id, stars=s, comment="",
                      counted=counted, at=NOW))
    db.commit()


def search(client, seed):
    r = client.get(f"/technicians{q(NOW)}&category=ประปา&address_id={seed['addr'].id}", headers=H("customer", seed["somchai"].id))
    return r.json()


# รองรับ AC-11-06 (REQ-FN-069): ค่าเฉลี่ยในผลค้นหาเมื่อมี 3 คะแนนขึ้นไป ลำดับช่างไม่เปลี่ยนตามคะแนน
def test_AC_11_06_average_shown_not_used_for_order(client, db, seed):
    second = Technician(name="วิชัย", skills="ประปา", base_lat=13.7300, base_lng=100.5300)
    db.add(second); db.flush()
    db.add(TimeSlot(technician_id=second.id, start=TOMORROW_14, end=TOMORROW_14 + timedelta(hours=2))); db.commit()
    _ratings(db, seed["prasit"].id, [3, 3])          # 2 คะแนน ยังไม่แสดง
    _ratings(db, second.id, [5, 5, 4])               # 4.7
    rows = search(client, seed)
    assert [r["technician_id"] for r in rows] == [seed["prasit"].id, second.id]   # ตามรหัสช่างเหมือนเดิม
    assert rows[0]["rating"] == {"average": None, "count": 2}
    assert rows[1]["rating"] == {"average": 4.7, "count": 3}
    assert client.get("/me/rating", headers=H("technician", second.id)).json() == {"average": 4.7, "count": 3}


# รองรับ AC-11-07 (REQ-PRV-012): ความเห็นปิดบังข้อมูลติดต่อ ไม่อยู่ในผลค้นหาและมุมมองของช่าง หัวหน้าช่างอ่านได้ไม่มีชื่อลูกค้า
def test_AC_11_07_comment_masked_and_private(client, db, seed):
    job = done_job(client, db, seed)
    rate(client, job, 2, "ช่างมาสาย โทรกลับ 081-234-5678 หรือ a@b.co")
    stored = db.scalars(select(Rating)).one()
    assert "081-234-5678" not in stored.comment and "[phone]" in stored.comment and "[email]" in stored.comment
    assert "comment" not in str(search(client, seed)) and "มาสาย" not in str(search(client, seed))
    assert "มาสาย" not in str(client.get("/me/rating", headers=H("technician", seed["prasit"].id)).json())
    head = client.get(f"/ops/technicians/{seed['prasit'].id}/ratings", headers=OPS).json()
    assert head["ratings"][0]["job_id"] == job.id and "มาสาย" in head["ratings"][0]["comment"]
    assert "สมชาย" not in str(head) and "customer" not in str(head)


# รองรับ AC-11-08 (BR-11 ข้อ 5): บัญชีลูกค้าที่เบอร์ตรงกับบัญชีของช่างคนนั้น ไม่นับในค่าเฉลี่ย ลบข้อมูลแล้วความเห็นหาย ดาวคงอยู่
def test_AC_11_08_self_review_not_counted_and_erasure(client, db, seed):
    job = done_job(client, db, seed)
    customer_acc = db.scalars(select(Account).where(Account.role == "customer", Account.subject_id == job.customer_id)).one()
    db.add(Account(role="technician", subject_id=seed["prasit"].id, phone_norm=customer_acc.phone_norm, created_at=NOW))
    db.commit()
    assert rate(client, job, 5, "เยี่ยม").status_code == 201        # ตอบเหมือนปกติ ไม่บอกว่าไม่นับ
    assert db.scalars(select(Rating)).one().counted is False
    _ratings(db, seed["prasit"].id, [2, 2, 2])
    assert client.get("/me/rating", headers=H("technician", seed["prasit"].id)).json() == {"average": 2.0, "count": 3}
    client.post(f"/ops/erasure-requests{q(DONE_AT + timedelta(days=1))}", json={"customer_id": job.customer_id})
    db.expire_all()
    mine = db.scalars(select(Rating).where(Rating.job_id == job.id)).one()
    assert mine.comment == "" and mine.stars == 5
