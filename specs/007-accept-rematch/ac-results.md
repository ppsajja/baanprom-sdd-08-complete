# ตารางผล AC หลังรัน test ทั้งชุด (specs/000-shared/test-run.txt)

รันวันที่ 23 พ.ย. 2569 (วันในเคส) จาก export สะอาด Python 3.11 และ 3.12 และ vitest

| AC หรือ UI | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-12-01 | REQ-FN-061 | test_AC_12_01_new_job_offered_with_accept_and_reject, AC-12-01.test.jsx | T-01, T-06 | ผ่าน | |
| AC-12-02 | REQ-FN-061 | test_AC_12_02_accept_keeps_status_and_hides_accept_button, AC-12-01.test.jsx | T-02, T-06 | ผ่าน | |
| AC-12-03 | REQ-FN-061 | test_AC_12_03_departure_counts_as_accept | T-02 | ผ่าน | |
| AC-12-04 | REQ-SEC-010 | test_AC_12_04_other_technician_cannot_respond | T-02 | ผ่าน | |
| AC-12-05 | REQ-FN-061 | test_AC_12_05_cannot_reject_after_departure, AC-12-01.test.jsx | T-02, T-06 | ผ่าน | |
| AC-05-01 | REQ-FN-062 | test_AC_05_01_reject_rematches_to_nearest_free_technician_same_time, AC-12-01.test.jsx | T-03, T-06 | ผ่าน | |
| AC-05-02 | REQ-FN-063 | test_AC_05_02_no_substitute_within_2_hours_cancels_with_full_refund | T-04 | ผ่าน | |
| AC-05-03 | REQ-FN-061 | test_AC_05_03_no_response_in_30_minutes_counts_as_reject | T-04 | ผ่าน | |
| AC-05-04 | REQ-FN-063 | test_AC_05_04_customer_declines_substitute_full_refund, UI-02-03.test.jsx | T-05, T-06 | ผ่าน | |
| AC-05-05 | REQ-FN-062 | test_AC_05_05_order_by_distance_skip_tried_and_wrong_skill | T-03 | ผ่าน | พิสูจน์ชั้น 3: ตัดเงื่อนไขทักษะ test พัง 4 ตัว |
| AC-05-06 | REQ-FN-062, REQ-FN-063 | test_AC_05_06_out_of_range_and_too_close_to_start_not_matched | T-03, T-04 | ผ่าน | |
| AC-09-16 | REQ-FN-050 | test_AC_09_16_closed_jobs_shown_30_days_back | T-07 | ผ่าน | |
| AC เดิมของ 002 ถึง 005 | | test เดิม | ผ่าน | ไม่มี test เดิมตัวไหนต้องแก้เพราะ CR-12 (AC-09-05 แถว confirmed ไป rematching ยังได้ 409 ตาม D-12-01) |
