"""AC-09-09 จาก job-status.feature (specs/003-job-status, CR-05)
REQ-SEC-004 เบอร์ลูกค้าในรายการงานของช่าง เห็นเฉพาะ 2 ชั่วโมงก่อนนัดจนปิดงาน | REQ-PRV-002 log ไม่มีเบอร์"""
import logging
from datetime import timedelta

from tests.conftest import TOMORROW_14, H
from tests.test_job_status import confirmed_job, change


def jobs_of(client, technician_id, now):
    return client.get(f"/technicians/{technician_id}/jobs?now={now.isoformat()}", headers=H("technician", technician_id)).json()


# รองรับ AC-09-09 (REQ-SEC-004, REQ-PRV-002)
def test_AC_09_09_phone_in_job_list_only_from_2h_until_closed(client, db, seed, caplog):
    caplog.set_level(logging.INFO)
    # Given งานสถานะ ยืนยันแล้ว นัดเวลา 14:00
    job = confirmed_job(client, db, seed)
    tech = seed["prasit"].id
    # When ช่างเปิดรายการงานเวลา 11:30 Then ไม่เห็นเบอร์โทรของลูกค้า
    j = jobs_of(client, tech, TOMORROW_14 - timedelta(hours=2, minutes=30))[0]
    assert j["job_id"] == job.id and "customer_phone" not in j
    # When ช่างเปิดรายการงานเวลา 12:00 Then เห็นเบอร์โทรของลูกค้า
    j = jobs_of(client, tech, TOMORROW_14 - timedelta(hours=2))[0]
    assert j["customer_phone"] == "081-234-5678"
    # And เมื่อช่างออกเดินทางและถึงหน้างาน ยังเห็นเบอร์
    change(client, job.id, tech, "en_route", TOMORROW_14 - timedelta(hours=1))
    r = change(client, job.id, tech, "in_progress", TOMORROW_14)
    assert r.json().get("customer_phone") == "081-234-5678"
    # When ช่างปิดงาน (เสร็จสิ้น) Then ไม่เห็นเบอร์โทรอีก
    r = change(client, job.id, tech, "done", TOMORROW_14 + timedelta(hours=2))
    assert "customer_phone" not in r.json()
    j = jobs_of(client, tech, TOMORROW_14 + timedelta(hours=3))[0]
    assert j["status"] == "done" and "customer_phone" not in j
    # And ไม่มีเบอร์โทรของลูกค้าปรากฏใน log ของระบบ (router พยายาม log ทั้งรายการ ตัวกรอง privacy.py ต้องกันไว้)
    assert "081-234-5678" not in caplog.text
    assert "0812345678" not in caplog.text
