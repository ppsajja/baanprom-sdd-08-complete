# ตารางผล AC หลังรัน test ทั้งชุด (specs/000-shared/test-run.txt)

รันวันที่ 23 พ.ย. 2569 (วันในเคส) จาก export สะอาด Python 3.11 และ 3.12 และ vitest คำสั่งเดิมของโครงการ
สถานะที่ใช้: ผ่าน | ไม่ผ่าน | ยังไม่มี test

| AC หรือ UI | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-02-01 | REQ-FN-058, REQ-SEC-013, REQ-PRV-011 | test_AC_02_01_new_customer_registers_with_phone_and_otp | T-02 | ผ่าน | |
| AC-02-02 | REQ-FN-059, REQ-SEC-014 | test_AC_02_02_registered_customer_logs_in | T-02 | ผ่าน | |
| AC-02-03 | REQ-SEC-013 | test_AC_02_03_otp_expires_after_5_minutes | T-01 | ผ่าน | ขอบ 5 นาทีพอดีและก่อน 1 วินาที |
| AC-02-04 | REQ-SEC-013 | test_AC_02_04_five_wrong_codes_lock_the_challenge | T-01 | ผ่าน | พิสูจน์ชั้น 3: ตั้ง 6 ครั้ง test นี้พัง |
| AC-02-05 | REQ-SEC-013 | test_AC_02_05_resend_limits_and_old_code_replaced | T-01 | ผ่าน | |
| AC-02-06 | REQ-SEC-014 | test_AC_02_06_identity_comes_from_token_only, AC-02-06.test.jsx (4 ตัว) | T-03, T-07 | ผ่าน | |
| AC-02-07 | REQ-SEC-010 | test_AC_02_07_job_and_history_need_owner_assignee_or_call_center | T-04 | ผ่าน | ปิด GAP-24 |
| AC-02-08 | REQ-SEC-013, REQ-PRV-002 | test_AC_02_08_no_code_or_phone_in_log_or_db | T-01 | ผ่าน | |
| AC-02-09 | REQ-PRV-010, REQ-SEC-014 | test_AC_02_09_erasure_removes_account_and_sessions | T-05 | ผ่าน | |
| AC-02-10 | REQ-FN-058 | test_AC_02_10_multiple_addresses_choose_when_searching, AC-07-20.test.jsx | T-02, T-07 | ผ่าน | หน้าจอเพิ่มที่อยู่มีแล้วใน R2 ส่วน B (UI-02-04 ปิด F-17) |
| AC-02-11 | REQ-SEC-012, REQ-SEC-013 | test_AC_02_11_production_never_returns_the_code | T-02 | ผ่าน | |
| AC-01-01 | REQ-FN-060 | test_AC_01_01_technician_logs_in_with_issued_account | T-06 | ผ่าน | |
| AC-01-02 | REQ-FN-060, REQ-SEC-013 | test_AC_01_02_unknown_technician_phone_gets_same_answer_but_no_sms | T-06 | ผ่าน | |
| AC-01-03 | REQ-SEC-010, REQ-SEC-014 | test_AC_01_03_technician_token_limited_to_own_menu_and_jobs, AC-02-06.test.jsx | T-03 | ผ่าน | |
| UI-02-01 | | UI-02-01.test.jsx (4 ตัว) | T-07 | ผ่าน | |
| UI-02-02 | | UI-02-02.test.jsx (2 ตัว) | T-07 | ผ่าน | |
| UI-02-03 | | UI-02-03.test.jsx (2 ตัว) | T-07 | ผ่าน | ใช้ร่วมกับ 007 |
| UI-01-01 | | UI-01-01.test.jsx | T-07 | ผ่าน | รอบแรกไม่ผ่าน (test ผิด GAP-43) |

ตรวจหน้าจอด้วยคน: ยังไม่ได้เปิดหน้าจอจริงเทียบ mockup กับ SH-01 (ส่วน B ของ R2 ทำพร้อมงวดตรวจรับ) ภาพ .png ของ mockup สร้างจาก .html

## R2 ส่วน B (CR-18) ผลจาก specs/000-shared/test-run.txt รอบสุดท้าย (Python 3.11 และ 3.12 และ vitest)

| AC | REQ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-02-12 | REQ-FN-074, REQ-PRV-011 | test_AC_02_12_add_address_geocoded, UI-02-04.test.jsx | T-09 | ผ่าน | |
| AC-02-13 | REQ-FN-074, REQ-QA-010 | test_AC_02_13_address_not_found_or_map_down, UI-02-04.test.jsx | T-09 | ผ่าน | |
| AC-02-14 | REQ-FN-074, REQ-SEC-010 | test_AC_02_14_delete_address_rules | T-09 | ผ่าน | |
| UI-02-04 | | UI-02-04.test.jsx | T-09 | ผ่าน | |
| UI-02-02 (แก้) | | UI-02-02.test.jsx เดิม ไม่แก้ | T-09 | ผ่าน | หน้าลงทะเบียนเลิกส่งพิกัด |

ตรวจหน้าจอด้วยคน: เดินซ้อม UAT R2 (docs/acceptance/uat-r2.md S-20 และ S-21) เปิดหน้าที่อยู่จริงเทียบภาพ UI-02-04

