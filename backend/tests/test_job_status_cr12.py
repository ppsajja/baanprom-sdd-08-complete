"""AC-09-16 จาก job-status.feature v1.3 (CR-12, Q-32 ปิดใน EV-051) รายการงานของช่างแสดงงานที่ปิดแล้วย้อนหลัง 30 วัน"""
from datetime import timedelta

from app.db.models import Job, TimeSlot
from tests.conftest import NOW, H


# รองรับ AC-09-16 (REQ-FN-050 ฉบับ CR-12)
def test_AC_09_16_closed_jobs_shown_30_days_back(client, db, seed):
    tech = seed["prasit"].id
    rows = []
    for days, status in ((31, "done"), (29, "done"), (40, "cancelled"), (40, "confirmed")):
        at = NOW - timedelta(days=days)
        slot = TimeSlot(technician_id=tech, start=at, end=at + timedelta(hours=2), state="booked")
        db.add(slot); db.flush()
        job = Job(customer_id=seed["somchai"].id, technician_id=tech, slot_id=slot.id, address_id=seed["addr"].id,
                  category="ประปา", status=status, deposit_amount=350, scheduled_start=at, created_at=at)
        db.add(job); db.flush(); rows.append(job)
    db.commit()
    # When ช่างเปิดรายการงาน
    ids = [j["job_id"] for j in client.get(f"/technicians/{tech}/jobs?now={NOW.isoformat()}", headers=H("technician", tech)).json()]
    # Then เห็นงานที่ปิดแล้วไม่เกิน 30 วัน และงานที่ยังไม่ปิดทุกงาน ไม่เห็นงานที่ปิดเกิน 30 วัน
    assert rows[1].id in ids and rows[3].id in ids
    assert rows[0].id not in ids and rows[2].id not in ids
