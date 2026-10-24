# ตารางผล AC หลังรัน test ทั้งชุด (specs/000-shared/test-run.txt)

รันวันที่ 10 ธ.ค. 2569 (วันในเคส) จาก export สะอาด Python 3.11 และ 3.12 และ vitest

| AC หรือ UI | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-10-01 | REQ-FN-072 | test_AC_10_01_default_sms | T-01 | ผ่าน | รอบแรกไม่ผ่าน (GAP-47) |
| AC-10-02 | REQ-FN-072 | test_AC_10_02_link_and_choose_line, UI-10-01.test.jsx | T-02 | ผ่าน | |
| AC-10-03 | REQ-FN-072 | test_AC_10_03_line_requires_valid_link, UI-10-01.test.jsx | T-02 | ผ่าน | |
| AC-10-04 | REQ-FN-073 | test_AC_10_04_line_down_falls_back_to_sms | T-03 | ผ่าน | พิสูจน์ชั้น 3 ใน T-03 |
| AC-10-05 | REQ-FN-072 | test_AC_10_05_otp_always_sms | T-01 | ผ่าน | รอบแรก test คาดเบอร์ผิดรูปแบบ (GAP-47) |
| AC-10-06 | REQ-FN-072 | test_AC_10_06_technician_line_and_new_job_text | T-01 | ผ่าน | F-20 ปิด |
| AC-10-07 | REQ-FN-073, REQ-PRV-010 | test_AC_10_07_erasure_and_no_pii_in_delivery_log | T-03 | ผ่าน | |
| UI-10-01 | REQ-FN-072 | UI-10-01.test.jsx (2 test) | T-05 | ผ่าน | |
