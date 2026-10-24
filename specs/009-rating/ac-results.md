# ตารางผล AC หลังรัน test ทั้งชุด (specs/000-shared/test-run.txt)

รันวันที่ 10 ธ.ค. 2569 (วันในเคส) จาก export สะอาด Python 3.11 และ 3.12 และ vitest

| AC หรือ UI | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-11-01 | REQ-FN-068 | test_AC_11_01_rate_done_job, UI-11-01.test.jsx | T-01, T-04 | ผ่าน | |
| AC-11-02 | REQ-FN-068 | test_AC_11_02_not_done_cannot_rate, test_AC_11_02_stars_must_be_1_to_5 (0 และ 6) | T-01 | ผ่าน | พิสูจน์ชั้น 3 ใน T-01 |
| AC-11-03 | REQ-FN-068 | test_AC_11_03_only_once_per_job, UI-11-01.test.jsx | T-01 | ผ่าน | |
| AC-11-04 | REQ-FN-068 | test_AC_11_04_window_14_days | T-01 | ผ่าน | ขอบ 14 วันพอดีและเกิน 1 วินาที |
| AC-11-05 | REQ-SEC-010 | test_AC_11_05_other_customer_denied | T-01 | ผ่าน | |
| AC-11-06 | REQ-FN-069 | test_AC_11_06_average_shown_not_used_for_order, AC-11-06.test.jsx | T-02 | ผ่าน | |
| AC-11-07 | REQ-PRV-012 | test_AC_11_07_comment_masked_and_private | T-03 | ผ่าน | |
| AC-11-08 | REQ-FN-068, REQ-PRV-012 | test_AC_11_08_self_review_not_counted_and_erasure | T-01, T-03 | ผ่าน | |
| UI-11-01 | REQ-FN-068 | UI-11-01.test.jsx (2 test) | T-04 | ผ่าน | |
| AC เดิม | | test เดิม | | ผ่าน | ไม่มี test เดิมต้องแก้เพราะ CR-15 (ผลค้นหามีช่องใหม่ test เดิมไม่ได้เทียบทั้งก้อน) |
