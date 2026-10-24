"""AC-07-09 จาก booking.feature (T-08): REQ-SEC-004 ซ่อนเบอร์จนก่อนนัด 2 ชั่วโมง และ REQ-PRV-002 ไม่มีเบอร์ใน log"""
import logging
from datetime import timedelta

from tests.conftest import TOMORROW_14, book, H


# รองรับ AC-07-09 (REQ-SEC-004, REQ-PRV-002)
def test_AC_07_09_phone_hidden_until_2h(client, db, seed, caplog):
    # Given งานสถานะ ยืนยันแล้ว นัดเวลา 14:00
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    job_id = res.json()["job_id"]
    tech = seed["prasit"].id
    caplog.set_level(logging.INFO)
    # When ช่างเปิดดูงานเวลา 11:30
    at_1130 = (TOMORROW_14 - timedelta(hours=2, minutes=30)).isoformat()
    r1 = client.get(f"/jobs/{job_id}/technician-view?technician_id={tech}&now={at_1130}", headers=H("technician", tech))
    # Then ไม่เห็นเบอร์โทรของลูกค้า
    assert r1.status_code == 200 and "customer_phone" not in r1.json()
    # When ช่างเปิดดูงานเวลา 12:00
    at_1200 = (TOMORROW_14 - timedelta(hours=2)).isoformat()
    r2 = client.get(f"/jobs/{job_id}/technician-view?technician_id={tech}&now={at_1200}", headers=H("technician", tech))
    # Then เห็นเบอร์โทรของลูกค้า
    assert r2.json().get("customer_phone") == "081-234-5678"
    # And ไม่มีเบอร์โทรของลูกค้าปรากฏใน log ของระบบ (router พยายาม log ทั้ง dict แต่ตัวกรองต้องกันไว้)
    assert "081-234-5678" not in caplog.text
    assert "0812345678" not in caplog.text
