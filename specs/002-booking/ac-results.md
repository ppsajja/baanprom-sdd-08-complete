# ตารางผล AC หลังรัน test ทั้งชุด (specs/002-booking/test-run.txt)

รอบที่ 1 และ 2 รันวันที่ 4 ต.ค. 2569 รอบที่ 3 และ 4 รันวันที่ 11 ต.ค. 2569 (หลัง CR-03 และ CR-04) | คำสั่ง: cd backend && pytest -v -k "AC_" | cd frontend && npm test
สถานะที่ใช้: ผ่าน | ไม่ผ่าน | ยังไม่มี test | รอ Q-xx

## รอบที่ 1 (ก่อนแก้ GAP-07)

| AC ID | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-07-01 | REQ-FN-008 | test_AC_07_01_booking_success | T-04 | ผ่าน | หลังเพิ่ม assert จำนวน Payment (GAP-06) |
| AC-07-02 | REQ-FN-008, BR-02, BR-03 | test_AC_07_02_slot_not_rebookable | T-03 | ผ่าน | |
| AC-07-03 | REQ-FN-012 | test_AC_07_03_notify_both_within_60s | T-07 | ผ่าน | |
| AC-07-04 | REQ-FN-041 (CR-01) | test_AC_07_04_no_charge_when_slot_taken | T-02, T-04 | ผ่าน | พิสูจน์ชั้น 3: เปลี่ยน ALTERNATIVE_WINDOW_HOURS เป็น 1 แล้ว test พัง |
| AC-07-04 (หน้าจอ) | REQ-FN-041 | AC-07-04.test.jsx | T-10 | ผ่าน | |
| AC-07-05 | REQ-IF-001, REQ-IF-005 | test_AC_07_05_payment_timeout | T-05 | ไม่ผ่าน | assert timeout 30 วินาที แต่ config ใช้ 60 (GAP-07 สาเหตุ spec) |
| AC-07-06 | REQ-IF-001 | test_AC_07_06_payment_declined | T-05 | ผ่าน | |
| AC-07-07 | REQ-IF-005 | test_AC_07_07_inquiry_approved_no_double_charge | T-05 | ผ่าน | |
| AC-07-08 | REQ-QA-003 | ไม่มี | T-09 | ยังไม่มี test | ต้องการผู้ใช้ 500 คน ทดสอบย่อส่วนตามที่ทีมตัดสิน ดู CR-02 |
| AC-07-09 | REQ-SEC-004, REQ-PRV-002 | test_AC_07_09_phone_hidden_until_2h | T-08 | ผ่าน | พิสูจน์ชั้น 3: เปลี่ยน PHONE_REVEAL_HOURS เป็น 3 แล้ว test พัง |
| AC-07-10 R1, R2, R4, R5, R6 | REQ-BR-001 | test_AC_07_10_refund (parametrize), _R6_not_allowed | T-06 | ผ่าน | |
| AC-07-10 R3 | REQ-BR-001 | test_AC_07_10_refund_R3 (skip) | T-06 | รอ Q-14 | พฤติกรรมชั่วคราวตรวจด้วย _R3_temporary_behaviour ผ่าน |

สรุปรอบที่ 1: AC ทั้งหมด 10 ข้อ | มี test 9 | ผ่าน 8 | ไม่ผ่าน 1 | ยังไม่มี test 1 | รอ Q 1 (R3 ของ AC-07-10)
ไม่ผ่านเพราะสเปก 1 (GAP-07) | เพราะ AI 0 | เพราะ test 0
สเปกคุม AI ได้: 8 ใน 9 AC ที่มี test จุดที่หลุดคือ timeout ของ gateway ที่สเปก (30 วินาที) กับ Interface Contract IF-01 ที่ AI อ่าน (60 วินาที) บอกไม่ตรงกัน

## รอบที่ 2 (หลังตั้ง GATEWAY_TIMEOUT_SECONDS ตาม spec ข้อ 9 = 30 และเพิ่ม test ย่อส่วน T-09) (4 ต.ค. 2569 ผลตอนตั้ง Baseline B1 + CR-01)

| AC ID | ผล | เปลี่ยนจากรอบ 1 |
|---|---|---|
| AC-07-05 | ผ่าน | แก้ config ให้ตรง spec (ค่าจริงรอ Q-19) |
| AC-07-08 | ผ่าน (ย่อส่วน 20 จาก 500, 19 ใน 20 ไม่เกิน 2 วินาที) | เพิ่ม test_AC_07_08_search_under_load_scaled ไม่ใช่ผลตรวจรับจริง รอ CR-02 |
| อื่น ๆ | เหมือนรอบ 1 | |

สรุปรอบที่ 2: AC ทั้งหมด 10 ข้อ | มี test 10 | ผ่าน 9 (1 ข้อเป็นแบบย่อส่วน) | ไม่ผ่าน 0 | รอ Q 1 (R3)
pytest: 15 passed, 1 skipped | vitest: 1 passed

## รอบที่ 3 (11 ต.ค. 2569 รันทั้งชุดครั้งแรกหลัง /implement T-12 ถึง T-15) = test-run-round3.txt

รอบนี้คือการรันซ้ำทั้งชุดหลังการเปลี่ยนแปลง ดูสองอย่าง: AC ใหม่ผ่านไหม และ AC ที่เคยผ่านยังผ่านอยู่ไหม

| AC หรือ UI | test | ผล | เปลี่ยนจากรอบ 2 | หมายเหตุ |
|---|---|---|---|---|
| AC-07-11 (หลังบ้าน) | test_AC_07_11_deposit_shown_equals_charged (3 ประเภทงาน), _unknown_category_has_no_guessed_deposit | ผ่าน | ใหม่ (CR-03, T-12) | พิสูจน์ชั้น 3: ให้ GET /deposit-quote ตอบเกิน 10 บาท test พัง 3 ตัว |
| AC-07-11 (หน้าจอ) | AC-07-11.test.jsx | ผ่าน | ใหม่ (T-13) | ใช้ยอด 370 บาทที่ไม่มีในตาราง เพื่อพิสูจน์ว่าหน้าจอไม่ได้พิมพ์ยอดไว้เอง |
| AC-07-06 (หน้าจอ) | AC-07-06.test.jsx | ผ่าน | ใหม่ (T-13 ปิด F-04) | |
| UI-07-01 | UI-07-01.test.jsx (4 ตัว) | ผ่าน | ใหม่ (T-14) | |
| UI-07-02 | UI-07-02.test.jsx (5 ตัว) | ผ่าน | ใหม่ (T-13) | |
| UI-07-03 | UI-07-03.test.jsx | **ไม่ผ่าน** | ใหม่ (T-15) | หาข้อความ "3 ผลการจอง" ไม่เจอ หน้าผลการจองไม่มีแถบขั้นตอน (GAP-17 สาเหตุ ai) |
| AC-07-04 (หน้าจอ) | AC-07-04.test.jsx | **ไม่ผ่าน** | **เคยผ่าน** ในรอบ 2 | ปุ่มยืนยันกดไม่ได้ เพราะข้อมูลตั้งต้นของ test ไม่มียอดมัดจำ ซึ่งหน้ายืนยันแบบใหม่ต้องรับจากระบบ (GAP-16 สาเหตุ spec: ตารางผลกระทบของ CR-03 ไล่ไม่ถึง test นี้) |
| AC-07-01 ถึง AC-07-10 (หลังบ้าน) | 16 ตัวเดิม | ผ่าน 15 ข้าม 1 | เหมือนรอบ 2 | |

สรุปรอบที่ 3: pytest 19 passed, 1 skipped | vitest 12 passed, 2 failed
ของใหม่ไม่ผ่าน 1 (UI-07-03) | **ของเดิมที่เคยผ่านแล้วไม่ผ่าน 1 (AC-07-04 หน้าจอ)**
ไม่ผ่านเพราะสเปก 1 (GAP-16) | เพราะ AI 1 (GAP-17) | เพราะ test 0

สิ่งที่ทีมทำกับ 2 ข้อนี้
- AC-07-04 (หน้าจอ): ไม่แก้ assert เพราะ AC ไม่ได้เปลี่ยน กลับไปเพิ่มแถวในตารางผลกระทบของ CR-03 ก่อน แล้วจึงเพิ่มข้อมูลตั้งต้น 2 ช่อง (depositAmount, holdExpiresAt) ในส่วน Given ของ test ตามกติกา Baseline ข้อ 7
- UI-07-03: ไม่แก้ test เพราะ test ตรงกับรายการ "ต้องตรง" ในสเปก สั่ง AI แก้หน้าจอให้มีแถบขั้นตอน

## รอบที่ 4 (11 ต.ค. 2569 หลังแก้ GAP-16 และ GAP-17) = test-run.txt ปัจจุบัน

| AC ID | REQ ที่พิสูจน์ | test | task | ผล | เทียบรอบ 2 |
|---|---|---|---|---|---|
| AC-07-01 | REQ-FN-008 | test_AC_07_01_booking_success | T-04 | ผ่าน | เหมือนเดิม |
| AC-07-02 | REQ-FN-008, BR-02, BR-03 | test_AC_07_02_slot_not_rebookable | T-03 | ผ่าน | เหมือนเดิม |
| AC-07-03 | REQ-FN-012 | test_AC_07_03_notify_both_within_60s | T-07 | ผ่าน | เหมือนเดิม |
| AC-07-04 | REQ-FN-041 | test_AC_07_04_no_charge_when_slot_taken | T-02, T-04 | ผ่าน | เหมือนเดิม |
| AC-07-04 (หน้าจอ) | REQ-FN-041 | AC-07-04.test.jsx | T-10, T-13 | ผ่าน | เหมือนเดิม (แก้เฉพาะ Given ตาม CR-03) |
| AC-07-05 | REQ-IF-001, REQ-IF-005 | test_AC_07_05_payment_timeout | T-05 | ผ่าน | เหมือนเดิม |
| AC-07-06 | REQ-IF-001 | test_AC_07_06_payment_declined | T-05 | ผ่าน | เหมือนเดิม |
| AC-07-06 (หน้าจอ) | REQ-IF-001 | AC-07-06.test.jsx | T-13 | ผ่าน | ใหม่ |
| AC-07-07 | REQ-IF-005 | test_AC_07_07_inquiry_approved_no_double_charge | T-05 | ผ่าน | เหมือนเดิม |
| AC-07-08 | REQ-QA-003 | test_AC_07_08_search_under_load_scaled | T-09 | ผ่าน (ย่อส่วน 20 จาก 500) | เหมือนเดิม ยังไม่ใช่ผลตรวจรับ รอ CR-02 (แก้ GAP-15 ให้รันได้บน Python 3.12 ขึ้นไป) |
| AC-07-09 | REQ-SEC-004, REQ-PRV-002 | test_AC_07_09_phone_hidden_until_2h | T-08 | ผ่าน | เหมือนเดิม |
| AC-07-10 R1, R2, R4, R5, R6 | REQ-BR-001 | test_AC_07_10_refund (parametrize), _R6_not_allowed | T-06 | ผ่าน | เหมือนเดิม |
| AC-07-10 R3 | REQ-BR-001 | test_AC_07_10_refund_R3 (skip) | T-06 | รอ Q-14 | เหมือนเดิม |
| AC-07-11 | REQ-BR-002 | test_AC_07_11 (4 ตัว) | T-12 | ผ่าน | ใหม่ |
| AC-07-11 (หน้าจอ) | REQ-BR-002 | AC-07-11.test.jsx (2 ตัว) | T-13 | ผ่าน | ใหม่ |

รายการ "ต้องตรง" ของหน้าจอ (ไม่ใช่ AC แต่อยู่ใน Baseline B2)

| UI ID | test | task | ผล test | ผลตรวจด้วยคน 6 ข้อ |
|---|---|---|---|---|
| UI-07-01 | UI-07-01.test.jsx (4 ตัว) | T-14 | ผ่าน | ตรง 6 จาก 6 |
| UI-07-02 | UI-07-02.test.jsx (5 ตัว) | T-13 | ผ่าน | ตรง 6 จาก 6 |
| UI-07-03 | UI-07-03.test.jsx (1 ตัว) | T-15 | ผ่าน | ตรง 6 จาก 6 |

ผลตรวจด้วยคนอยู่ใน ui-review/ui-review.md

สรุปรอบที่ 4: AC ทั้งหมด 11 ข้อ | มี test 11 | ผ่าน 10 (1 ข้อเป็นแบบย่อส่วน) | ไม่ผ่าน 0 | รอ Q 1 (R3 ของ AC-07-10)
pytest: 19 passed, 1 skipped | vitest: 14 passed (6 ไฟล์)

## เทียบก่อนและหลังการเปลี่ยนแปลง

| | รอบที่ 2 (ก่อน CR-03) | รอบที่ 3 (รันซ้ำครั้งแรก) | รอบที่ 4 (หลังแก้) |
|---|---|---|---|
| AC ในสเปก | 10 | 11 | 11 |
| test หลังบ้าน | 15 ผ่าน 1 ข้าม | 19 ผ่าน 1 ข้าม | 19 ผ่าน 1 ข้าม |
| test หน้าจอ | 1 ผ่าน | 12 ผ่าน 2 ไม่ผ่าน | 14 ผ่าน |
| ของเดิมที่พังเพราะการเปลี่ยนแปลง | | 1 (AC-07-04 หน้าจอ) | 0 |
| ข้อค้นพบใน rtm.md ที่เปิดอยู่ | ยังไม่ได้ตามรอย | | 4 จาก 8 (F-05 ถึง F-08) |

สรุปสามบรรทัด
1. สิ่งที่ขอเปลี่ยนทำครบไหม: ครบ AC-07-11 ผ่านทั้งหลังบ้านและหน้าจอ และหน้าจอ 3 หน้าตรงกับรายการ "ต้องตรง" ทั้ง test และตาคน
2. ของเดิมพังไหม: พัง 1 ข้อในรอบที่ 3 (AC-07-04 หน้าจอ) เพราะตารางผลกระทบของ CR-03 ไล่ไม่ถึง test หน้าจอเดิม แก้ที่ CR ก่อนแล้วจึงแก้ Given ของ test รอบที่ 4 ผ่านครบ
3. ยังเหลืออะไร: R3 ของ BR-01 (Q-14) AC-07-08 ฉบับวัดได้ (CR-02) และข้อค้นพบ F-05 ถึง F-08 ซึ่ง test ทั้งชุดมองไม่เห็น เพราะเป็นเรื่องที่ยังไม่มี AC

## รอบ CR-07 (24 ต.ค. 2569 หลัง T-17 ถึง T-27) = specs/000-shared/test-run.txt

รอบนี้รันทั้งโครงการครั้งเดียว ผลอยู่ที่ specs/000-shared/test-run.txt (Python 3.11, 3.12 จาก export สะอาด และ 3.13) รอบแรกหลังแก้โค้ดก่อนแก้ test เดิมอยู่ที่ specs/000-shared/test-run-cr07-round1.txt
แถว AC-07-01 ถึง 11 ที่ไม่มีหมายเหตุ ผลเหมือนรอบที่ 4 และ test ไม่ถูกแตะ

| AC ID | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-07-01 ถึง AC-07-04 | REQ-FN-008, REQ-FN-012, REQ-FN-041 | test_booking.py 4 ตัว | T-02 ถึง T-07 | ผ่าน | ไม่แตะ test AC-07-04 ยังผ่านแม้มีเพดานล็อก เพราะตรวจ slot_taken ก่อนเพดาน |
| AC-07-05, AC-07-06, AC-07-07 | REQ-IF-001, REQ-IF-005 | test_payment.py 3 ตัว | T-05 | ผ่าน | ไม่แตะ AC-07-05 ไม่ต้องแก้ตาม CR-07 ข้อ ข5 |
| AC-07-08 | REQ-QA-003 | test_AC_07_08_search_under_load_scaled | T-09 | ผ่าน (ย่อส่วน 20 จาก 500) | ยังไม่ใช่ผลตรวจรับ รอ CR-02 |
| AC-07-09 | REQ-SEC-004, REQ-PRV-002 | test_AC_07_09_phone_hidden_until_2h | T-08 | ผ่าน | ไม่แตะ log ของ technician-view เปลี่ยนเป็น log_event แล้วยังไม่มีเบอร์ |
| AC-07-10 R1, R2, R4, R5, R6, R3 ชั่วคราว | REQ-BR-001 | test_refund.py 6 ตัว (R3 ข้าม 1 ตัว) | T-06, T-21 | ผ่าน | helper ส่วน When เปลี่ยนตาม CR-07 ข้อ ข4 (GAP-23) Given Then และตัวเลขไม่เปลี่ยน |
| AC-07-11 | REQ-BR-002 | test_AC_07_11_deposit_shown_equals_charged x3, AC-07-11.test.jsx | T-12, T-13 | ผ่าน | ไม่แตะ |
| AC-07-12 | REQ-QA-010 | test_AC_07_12_gateway_unreachable_keeps_hold_as_pending | T-18 | ผ่าน | ใหม่ ผ่านตั้งแต่รันครั้งแรก |
| AC-07-12, AC-07-13 (หน้าจอ) | REQ-QA-010 | AC-07-12.test.jsx (2 test) | T-26 | ผ่าน | ใหม่ |
| AC-07-13 | REQ-QA-010, REQ-IF-005 | test_AC_07_13_retry_uses_same_reference_no_double_charge | T-18 | ผ่าน | ใหม่ เหตุการณ์ B ในรูป test |
| AC-07-14 | REQ-SEC-011 | test_AC_07_14_second_hold_rejected, AC-07-14.test.jsx | T-19, T-26 | ผ่าน | ใหม่ รันครั้งแรกพัง 500 (GAP-27) แก้แล้ว พิสูจน์ชั้น 3: เพดาน 2 ช่วง test พัง |
| AC-07-15 | REQ-SEC-010, REQ-SEC-004 | test_AC_07_15_technician_view_other_job_forbidden_and_logged | T-20 | ผ่าน | ใหม่ |
| AC-07-16 | REQ-SEC-010, REQ-SEC-012 | test_AC_07_16_legacy_cancel_endpoint_closed | T-21 | ผ่าน | ใหม่ รันครั้งแรกพังเพราะ test อ่าน app.routes ซึ่งรุ่น FastAPI นี้ไม่แสดง route ของ router ที่ include (ข้อผิดของ test ไม่ใช่โค้ด) แก้ให้อ่าน /openapi.json |
| AC-07-17 | REQ-PRV-010 | test_AC_07_17_erasure_removes_phone_keeps_anonymous_history, test_AC_07_17_erasure_waits_for_active_job | T-22 | ผ่าน | ใหม่ ค้นเบอร์ในทุกตารางของ SQLite |
| AC-07-18 | REQ-PRV-010, REQ-OP-007 | test_AC_07_18_restore_does_not_bring_back_erased_data | T-23 | ผ่าน | ใหม่ บนไฟล์ SQLite ระบบจริงต้องซ้อมบน PostgreSQL |

สรุปสามบรรทัด
1. สิ่งที่ขอทำครบไหม: ครบ AC-07-12 ถึง 18 ผ่านทั้งหมด และ AC ข้ามทุก feature (AC-00-01 ถึง 08) ผ่านใน specs/000-shared/ac-results.md
2. ของเดิมพังไหม: รอบแรกพัง 8 ตัว ทั้งหมดเป็น test ที่ CR-07 ระบุไว้ก่อนว่าพฤติกรรมเปลี่ยน แก้เฉพาะบรรทัดตามตาราง "test เดิมที่เปลี่ยน" ของ CR-07 test อื่นไม่ถูกแตะและผ่าน
3. ยังเหลืออะไร: R3 (Q-14), AC-07-08 ฉบับวัดได้ (CR-02), mockup ของสถานะใหม่ (GAP-26), GET /jobs/{id} ยังไม่ตรวจสิทธิ์ (GAP-24)

## รอบ CR-10 (3 พ.ย. 2569)

ผลของ AC ที่ CR-10 และ CR-02 เพิ่มหรือแก้ อยู่ในตารางรวมที่ specs/000-shared/ac-results.md ส่วน "รอบ CR-10 และ CR-02" AC อื่นของ feature นี้ผลเท่ารอบก่อน และ test ไม่ถูกแตะ ผลระหว่างตรวจรับ R1 อยู่ใน docs/acceptance/acceptance-record-r1.md

## รอบตรวจรับ R1 รอบสอง (16 พ.ย. 2569)

ผลของ DEF-01 (UI-07-02) และผลทดสอบโหลดเต็มรูปของ AC-07-08 อยู่ในตารางรวมที่ specs/000-shared/ac-results.md ส่วน "รอบตรวจรับ R1 รอบสอง"

## รอบ R2 ส่วน A (23 พ.ย. 2569 รันจริงจาก export สะอาด specs/000-shared/test-run.txt)

| AC | REQ | test | ผล | หมายเหตุ |
|---|---|---|---|---|
| AC-07-01 ถึง AC-07-19 | | test เดิม | ผ่าน | test เดิมเปลี่ยนเฉพาะการบอกผู้ส่งตามตารางของ CR-11 รอบแรกก่อนแก้ test ไม่ผ่านเพราะ 401 (test-run-cr11-round1.txt) |
| AC-07-02 | REQ-FN-008 | test_AC_07_02_slot_not_rebookable | ผ่าน | บรรทัด When ใหม่ (ค้นด้วยที่อยู่ของผู้ค้น) |
| AC-07-08 (ย่อส่วน) | REQ-QA-003 | test_AC_07_08_search_under_load_scaled | ผ่าน | ตรวจถดถอย |
| AC-07-08 (ฉบับ Q-68) | REQ-QA-003 | load_test.py --rate 50 --duration 300 | ผ่าน บนเครื่องทดสอบ | 15000 จาก 15000 p95 0.023 วินาที docs/acceptance/load-test-r2.md |
| AC-07-20 ถึง AC-07-23 | REQ-FN-064 | test_booking_cr08.py | ผ่าน | |
| AC-07-24 | REQ-FN-065 | test_AC_07_24_no_technician_in_7_days | ผ่าน | |
| AC-07-20, 21, 24 (หน้าจอ) | REQ-FN-064, REQ-FN-065 | AC-07-20.test.jsx | ผ่าน | |
| UI-07-01 รายการต้องตรงเดิม | | UI-07-01.test.jsx | ผ่าน | ไม่แก้ test |
