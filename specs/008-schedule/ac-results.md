# ตารางผล AC หลังรัน test ทั้งชุด (specs/000-shared/test-run.txt)

รันวันที่ 10 ธ.ค. 2569 (วันในเคส) จาก export สะอาด Python 3.11 และ 3.12 และ vitest

| AC หรือ UI | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-04-01 | REQ-FN-066 | test_AC_04_01_add_slot_visible_in_search, UI-04-01.test.jsx | T-02, T-05 | ผ่าน | รอบแรกไม่ผ่านเพราะ test คาดผิด (GAP-45) |
| AC-04-02 | REQ-FN-066 | test_AC_04_02_rules_reject 6 แถว | T-02 | ผ่าน | |
| AC-04-03 | REQ-FN-066 | test_AC_04_03_close_free_slot_hidden_everywhere | T-03 | ผ่าน | พิสูจน์ชั้น 3 ใน T-03 |
| AC-04-04 | REQ-FN-066 | test_AC_04_04_cannot_close_booked_or_held | T-02 | ผ่าน | |
| AC-04-05 | REQ-FN-067 | test_AC_04_05_day_off_hides_slots_and_rematch | T-04 | ผ่าน | |
| AC-04-06 | REQ-FN-067 | test_AC_04_06_day_off_refused_when_booked, UI-04-01.test.jsx | T-04 | ผ่าน | |
| AC-04-07 | REQ-FN-067 | test_AC_04_07_remove_day_off_reopens_only_its_slots | T-04 | ผ่าน | |
| AC-04-08 | REQ-SEC-010 | test_AC_04_08_other_technician_and_customer_denied | T-02 | ผ่าน | |
| UI-04-01 | REQ-FN-066, REQ-FN-067 | UI-04-01.test.jsx (3 test) | T-05 | ผ่าน | ตรวจหน้าจอจริงเทียบ mockup ในการเดินซ้อม UAT (S-22) |
| AC เดิมของ 002 ถึง 007 | | test เดิม | | ผ่าน | ไม่มี test เดิมตัวไหนต้องแก้เพราะ CR-14 |
