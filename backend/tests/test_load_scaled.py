"""AC-07-08 แบบย่อส่วน (T-09) ย่อจากผู้ใช้ 500 คน เป็น 20 คำขอพร้อมกัน (บันทึกใน ac-results.md)
ฉบับวัดได้จริงรอ CR-02 (quality-requirements.md) ผลบนเครื่องนักศึกษาเป็นเพียงสัญญาณ ไม่ใช่ผลตรวจรับจริง"""
import time
from concurrent.futures import ThreadPoolExecutor

from tests.conftest import NOW, H


# รองรับ AC-07-08 (REQ-QA-003) ฉบับย่อส่วน
def test_AC_07_08_search_under_load_scaled(client, db, seed):
    url = f"/technicians?category=ประปา&address_id={seed['addr'].id}&now={NOW.isoformat()}"
    headers = H("customer", seed["somchai"].id)  # CR-11: การค้นหาต้องเข้าสู่ระบบ

    def timed_get(_):
        t0 = time.perf_counter()
        r = client.get(url, headers=headers)
        return r.status_code == 200, time.perf_counter() - t0

    # Given ลูกค้า 20 คน (ย่อจาก 500) ส่งคำขอค้นหาช่างพร้อมกัน
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(timed_get, range(20)))
    # Then ทุกคำขอได้รายการช่างครบ
    assert all(ok for ok, _ in results)
    # Then 19 ใน 20 (ย่อจาก 95 ใน 100) ใช้เวลาไม่เกิน 2 วินาที
    fast = [sec for _, sec in results if sec <= 2.0]
    assert len(fast) >= 19
