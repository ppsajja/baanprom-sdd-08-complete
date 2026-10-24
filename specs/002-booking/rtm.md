# rtm.md ตารางตามรอยของ feature จองงานบริการซ่อมบำรุง (UC-07)

รุ่น: 2.0 | วันที่: 2569-10-11 | ผู้ตรวจ: สมาชิก A, C (กลุ่ม X) | อ้างอิง: spec.md 1.4, booking.feature v1.3, plan v2, tasks v2, test-run.txt รอบที่ 4
รุ่น 1.0 (6 ก.ย. 2569, บทเรียน Living Specification) ตามรอยถึง AC เท่านั้น รุ่นนี้ต่อไปจนถึง test task โค้ด และหน้าจอ
ร่างครั้งแรกด้วย AI จากตารางใน plan.md ข้อ 6 และท้าย tasks.md (prompt-log.md #35) ทีมตรวจทุกแถวเทียบไฟล์จริง และเขียนช่อง "ทีมตัดสิน" เอง

วิธีอ่าน: หนึ่งแถวต่อหนึ่ง REQ ไล่จากซ้ายไปขวาคือ "ทำไมต้องมี" ไปจนถึง "อยู่ตรงไหนในของที่สร้าง" ช่องไหนว่างคือสายขาด ต้องมีรหัสข้อค้นพบ F-nn กำกับ

## 1. ตามรอยไปข้างหน้า (หลักฐาน ถึง ของที่สร้าง)

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ |
|---|---|---|---|---|---|---|---|
| REQ-FN-008 จองงานจากช่างที่ว่างใน 7 วัน | EV-004, EV-009 | ใช่ | AC-07-01, AC-07-02 | test_AC_07_01_booking_success, test_AC_07_02_slot_not_rebookable, UI-07-01.test.jsx, UI-07-03.test.jsx | T-03, T-04, T-10, T-11, T-14, T-15 | technicians/service.py, booking/service.py (create_booking), UI-07-01, UI-07-03 | ขาดบางส่วน: เส้นทาง A1 ไม่มี AC (F-05) และ "เลือกที่อยู่ให้บริการ" ไม่มีบนหน้าจอ (F-06) |
| REQ-FN-041 ล็อกช่วงเวลา 10 นาที | MD-ACT-07 (derived), EV-041 | ใช่ | AC-07-04 | test_AC_07_04_no_charge_when_slot_taken, AC-07-04.test.jsx, UI-07-01.test.jsx, UI-07-02.test.jsx | T-02, T-04, T-10, T-13, T-14 | booking/service.py (hold_slot), UI-07-01, UI-07-02 | ครบ (F-03 ปิดแล้ว) ค่า 10 นาทียังรอ Q-18 |
| REQ-FN-012 แจ้งสองฝ่ายใน 60 วินาที | EV-012 | ใช่ | AC-07-03 | test_AC_07_03_notify_both_within_60s, UI-07-03.test.jsx | T-07, T-15 | notify/queue.py, UI-07-03 | ครบ |
| REQ-BR-001 คืนมัดจำตาม BR-01 | EV-023 | ใช่ | AC-07-10 | test_AC_07_10_refund (R1, R2, R4, R5), test_AC_07_10_refund_R6_not_allowed, test_AC_07_10_refund_R3 (ข้าม), UI-07-02.test.jsx (ข้อความเงื่อนไข) | T-06, T-13 | refund/rules.py, refund/service.py, UI-07-02 (แสดงเงื่อนไข) | ครบ ยกเว้น R3 รอ Q-14 |
| REQ-BR-002 ยอดมัดจำตามตารางราคาประเมิน | Finance (data dictionary) | **ไม่** (ถึงรุ่น 1.2) และ ใช่ (ตั้งแต่รุ่น 1.3) | ไม่มี (ถึง v1.2) และ AC-07-11 (ตั้งแต่ v1.3) | test_AC_07_11_deposit_shown_equals_charged, test_AC_07_11_unknown_category_has_no_guessed_deposit, AC-07-11.test.jsx, UI-07-03.test.jsx | T-12, T-13, T-15 | config.DEPOSIT_BY_CATEGORY, booking/service.py (deposit_for), GET /deposit-quote, UI-07-02, UI-07-03 | ครบหลัง CR-03 (F-01, F-02 ปิดแล้ว) สัดส่วนต่อราคาประเมินรอ Q-26 |
| REQ-IF-001 ตัดมัดจำผ่าน gateway | สัญญา gateway | ใช่ | AC-07-05, AC-07-06 | test_AC_07_05_payment_timeout, test_AC_07_06_payment_declined, AC-07-06.test.jsx | T-04, T-05, T-13 | payments/service.py, payments/gateway.py, UI-07-02 | ครบ (F-04 ปิดแล้ว) |
| REQ-IF-005 status-inquiry ด้วย reference เดิม | MD-SEQ-07-05 (derived) | ใช่ | AC-07-05, AC-07-07 | test_AC_07_05_payment_timeout, test_AC_07_07_inquiry_approved_no_double_charge | T-05 | payments/service.py | ครบ ค่า timeout รอ Q-19 |
| REQ-QA-003 ค้นหาไม่เกิน 2 วินาที ที่ 500 คน | EV-007 | ใช่ | AC-07-08 | test_AC_07_08_search_under_load_scaled (ย่อส่วน 20 จาก 500) | T-09 | tests/test_load_scaled.py | ย่อส่วน ไม่ใช่ผลตรวจรับ รอ CR-02 |
| REQ-SEC-004 ช่างเห็นเบอร์ 2 ชั่วโมงก่อนนัด | EV-019 | ใช่ | AC-07-09 | test_AC_07_09_phone_hidden_until_2h | T-08 | booking/service.py (technician_view) | ครบ |
| REQ-PRV-002 เบอร์โทรห้ามลง log (Constraint กลาง) | PDPA | ใช่ | AC-07-09 | test_AC_07_09_phone_hidden_until_2h | T-01, T-08 | privacy.py | ครบ |
| REQ-DAT-002 สถานะงาน 8 สถานะ ประวัติ 24 เดือน | Operations | ใช่ | **ไม่มี** (spec เขียนว่า "ตรวจผ่าน T-01") | **ไม่มีในชุด test** | T-01 | db/models.py (jobs.status, job_status_history) | ขาด: ไม่มี AC และไม่มี test (F-08) |
| REQ-CON-001 R1 8 สัปดาห์ ทีม 4 คน (Constraint กลาง) | แผนโครงการ | ส่วน 8 (บรรทัดอ้าง) | ไม่ใช้ AC ตรวจตามวิธีในไฟล์กลาง | ไม่มี (ตรวจด้วยการอ่าน plan.md ข้อ 7) | ทุก task | plan.md ข้อ 7 ตัด A2 | ครบ |
| REQ-CON-003 gateway รายเดิม (Constraint กลาง) | สัญญา | ส่วน 8 (บรรทัดอ้าง) | ไม่ใช้ AC ตรวจตามวิธีในไฟล์กลาง | ไม่มี (ตรวจด้วยการอ่านโค้ด) | T-04 | payments/gateway.py (interface Gateway ตัวเดียว) | ครบ |

แหล่งข้อมูลของแต่ละคอลัมน์: ที่มา จาก docs/srs/catalogue.md | AC จาก spec ส่วน 4 และ booking.feature | test จาก plan.md ข้อ 6 และ test-run.txt | task จากตารางท้าย tasks.md | โค้ด จากคอมเมนต์ "รองรับ REQ-xx" ในไฟล์

## 2. ตามรอยย้อนกลับ (ของที่สร้าง ถึง ความต้องการ)

| ของที่มีอยู่จริง | อ้าง REQ หรือ AC ข้อไหน | ข้อค้นพบ |
|---|---|---|
| GET /technicians | REQ-FN-008, BR-02, BR-03 | ไม่มี |
| POST /slots/{id}/hold | REQ-FN-041 | ไม่มี |
| GET /deposit-quote | REQ-BR-002 (AC-07-11) | ไม่มี (เพิ่มตาม CR-03) |
| POST /bookings | REQ-FN-008, REQ-IF-001, REQ-IF-005, REQ-BR-002 | ไม่มี |
| GET /jobs/{id} และ /technician-view | REQ-FN-008, REQ-SEC-004 | ไม่มี |
| POST /jobs/{id}/cancel | REQ-BR-001 | ไม่มี |
| GET /notifications/queue | REQ-FN-012 (ใช้ตรวจใน test) | ไม่มี |
| GET /health | **ไม่อ้าง REQ ข้อใด** | F-07 |
| test หลังบ้าน 20 ตัว และ test หน้าจอ 14 ตัว | ทุกตัวมีรหัส AC หรือ UI ในชื่อ | ไม่มี |
| หน้าจอ 3 หน้า และปุ่มที่ทำงานกับข้อมูล (ค้นหา เลือกช่วงเวลา ยืนยัน เลือกช่วงใกล้เคียง) | UI-07-01 ถึง UI-07-03, REQ-FN-008, REQ-FN-041, REQ-IF-001, AC-07-04 | ไม่มี |
| ตัวเลขในโค้ดหน้าจอ ก่อน CR-03 | ตารางมัดจำ 350 / 400 / 500 ใน ConfirmBooking.jsx และข้อความ "10 นาที" | F-02, F-03 |
| ตัวเลขในโค้ดหน้าจอ หลัง CR-03 | "7 วัน" (REQ-FN-008), "24 ชั่วโมง" (BR-01), "60 วินาที" (REQ-FN-012) อยู่ในรายการ "ต้องตรง" ทั้งหมด | ไม่มี |
| ค่า 300 บาทใน deposit_for (ก่อน CR-03) | **ไม่มีที่มา** ไม่อยู่ในตารางราคาประเมิน | F-02 |

## 3. ตรวจความครบของสเปกเอง

| ตรวจ | ผล | ข้อค้นพบ |
|---|---|---|
| REQ ทุกข้อใน catalogue ที่เกี่ยวกับ UC-07 อยู่ใน spec ส่วน 4 | 13 จาก 14 ข้ออยู่ในส่วน 4 ส่วน 8 หรือ Non-goals ขาด REQ-BR-002 | F-01 |
| ทุกเส้นทางใน UC-07 มี AC | main, E1, E2 มี A2 เลื่อนไป R2 (D-07-02) E3 อยู่ใน Non-goals A1 **ไม่มี** | F-05 |
| ทุกแถวของ BR-01 มี example | R1 ถึง R6 ครบใน AC-07-10 | ไม่มี |
| AC ที่ Then บอกว่า "แจ้ง" หรือ "เสนอ" มี test หน้าจอ (หลักใน plan.md ข้อ 6) | AC-07-04 มี AC-07-06 **ไม่มี** | F-04 |
| Constraint กลางทุกข้ออยู่ในตารางตรวจ Constraints ของ plan.md | ครบ 8 ข้อ (หลัง CR-04) | ไม่มี |
| สิ่งที่ REQ บอกให้ผู้ใช้ทำได้ มีบนหน้าจอครบ | REQ-FN-008: ประเภทงาน ช่าง ช่วงเวลา มี ที่อยู่ให้บริการ **ไม่มี** | F-06 |
| รหัสที่เอกสารสองฉบับอ้าง หมายถึงสิ่งเดียวกัน | รหัส REQ, AC, BR, UI และ T ที่ spec, plan, tasks และไฟล์นี้อ้างถึงกัน ตรงกันทุกจุด (รอบนี้ยังไม่ได้ไล่รหัส Q และ AS ข้ามไฟล์ จะทำตอนปิดคำถามเปิดรอบถัดไป) | ไม่มี |

## 4. ข้อค้นพบ

| F-ID | ชนิด | พบอะไร อยู่ที่ไหน | สาเหตุ | ทีมตัดสิน | ปิดด้วย |
|---|---|---|---|---|---|
| F-01 | REQ ไม่อยู่ใน spec | REQ-BR-002 เป็น Approved ใน catalogue ตั้งแต่ B1 แต่ไม่อยู่ใน spec ส่วน 4 ไม่มี AC ไม่มี test ทั้งที่โค้ด (deposit_for) อ้างรหัสนี้อยู่ | spec | เพิ่มเข้า spec และเขียน AC-07-11 | CR-03, T-12 ปิดแล้ว |
| F-02 | ตัวเลขซ้ำสองที่ | ตารางมัดจำอยู่ทั้งใน booking/service.py และ ConfirmBooking.jsx (ทีมอนุญาต "ชั่วคราว" ใน prompt-log.md #32) และ deposit_for คืน 300 บาทเมื่อไม่รู้จักประเภทงาน โดยไม่มีที่มา | spec และ ai | ย้ายตารางไป config.py ที่เดียว หน้าจอรับยอดจาก API ตัดค่า 300 ออก (AS-10) | CR-03, D-00-05, T-12, T-13 ปิดแล้ว |
| F-03 | ตัวเลขซ้ำสองที่ | หน้ายืนยันพิมพ์ "ล็อกไว้ให้คุณ 10 นาที" ตายตัว ทั้งที่ HOLD_MINUTES ยังรอ Q-18 ถ้าคำตอบเป็น 15 นาที หน้าจอจะบอกผิด | ai | แสดงเวลาสิ้นสุดการล็อกจาก hold_expires_at ที่ระบบส่งมา | CR-03, T-13 ปิดแล้ว |
| F-04 | AC ไม่มี test | AC-07-06 Then "ระบบแจ้งลูกค้าว่าชำระไม่สำเร็จ" มี test หลังบ้านอย่างเดียว ไม่มี test หน้าจอ ขัดกับหลักใน plan.md ข้อ 6 | test | เพิ่ม AC-07-06.test.jsx | T-13 ปิดแล้ว |
| F-05 | เส้นทางไม่มี AC | UC-07 A1 (ไม่มีช่างว่างใน 7 วัน เสนอช่วงถัดไปหรือเข้าคิวรอ) ไม่มี scenario ทั้งที่ spec ส่วน 6 เขียนว่าครบทุก path | spec | ยังตอบไม่ได้ว่าต้องทำแค่ไหน เป็นคำถามถึง SH-01 | Q-28 ยังเปิด |
| F-06 | REQ ทำไม่ครบบนหน้าจอ | REQ-FN-008 ให้ลูกค้าเลือกที่อยู่ให้บริการ แต่หน้าจอใช้ที่อยู่คงที่ (App.jsx ส่ง addressId = 1) test ทุกตัวผ่าน เพราะไม่มี AC ข้อไหนตรวจการเลือกที่อยู่ | spec | เป็นคำถามว่าเลือกที่หน้านี้หรือที่ feature จัดการที่อยู่ | Q-29 ยังเปิด |
| F-07 | โค้ดไม่มี REQ | GET /health ใน main.py ไม่มี REQ รองรับ (REQ-OP-001 ยังเป็นแค่ข้อเสนอใน quality-requirements.md) | ai | คงไว้ก่อน เพราะบทเรียนข้อกำหนดด้านปฏิบัติการจะตัดสินว่า REQ-OP-001 เข้า catalogue หรือไม่ ถ้าไม่เข้าให้ลบ | ยังเปิด |
| F-08 | REQ ไม่มี AC | REQ-DAT-002 ไม่มี AC และไม่มี test ในชุด (prompt-log.md #23 บอกว่ามี test พื้นฐาน แต่ไม่มีไฟล์นั้นใน repo) ส่วน "เก็บประวัติ 24 เดือน" จึงไม่มีอะไรตรวจ | spec และ test | ต้องเปิด CR เพิ่ม AC ของลำดับสถานะและประวัติ ไม่ทำในรอบนี้เพราะไม่เกี่ยวกับหน้าจอ | ยังเปิด (CR-05 ยังไม่เปิด) |

## 5. สรุป

REQ ที่เกี่ยวกับ UC-07 ทั้งหมด 13 ข้อ | ตามรอยครบถึง test หรือวิธีตรวจ 10 ข้อ | ขาดบางส่วน 2 ข้อ (REQ-FN-008, REQ-DAT-002) | ย่อส่วน 1 ข้อ (REQ-QA-003)
ของเกิน 1 รายการ (GET /health)
ข้อค้นพบ 8 ข้อ: ปิดแล้ว 4 (F-01 ถึง F-04 ด้วย CR-03) | เปิดอยู่ 4 (F-05, F-06 เป็น Q-28, Q-29 | F-07, F-08 รอการตัดสิน)
สาเหตุ: spec 5 | ai 3 | test 2 (ข้อที่มีสองสาเหตุนับทั้งสอง)

สิ่งที่ได้เรียนจากตารางนี้: รอบที่แล้ว test ผ่าน 9 จาก 10 AC แต่ REQ สองข้อไม่มี AC เลย (F-01, F-08) และอีกหนึ่งข้อทำไม่ครบบนหน้าจอ (F-06) test ที่ผ่านบอกได้แค่ว่าสิ่งที่มี AC ถูกทำตรง ไม่ได้บอกว่าทุก REQ มี AC

## 3. แถวที่เพิ่มตาม CR-07 (24 ต.ค. 2569)

AI ร่าง ทีมตรวจทุกแถวและเขียนช่อง "ทีมตัดสิน" เอง ข้อในไฟล์กลางที่ไม่เป็นของ feature ใด อยู่ใน specs/000-shared/rtm.md

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-QA-010 (IF-01 ตัดมัดจำ) | เหตุการณ์ B, EV-045 | ตารางข้อของไฟล์กลาง | AC-07-12, AC-07-13 | test_AC_07_12, test_AC_07_13, AC-07-12.test.jsx | T-18, T-26 | payments/service.py, booking/service.py, booking/router.py, technicians/service.py, ConfirmBooking.jsx | ครบ | รับ |
| REQ-SEC-011 | TH-03, EV-045 | ตารางข้อของไฟล์กลาง | AC-07-14 | test_AC_07_14, AC-07-14.test.jsx | T-19, T-26 | booking/service.py, booking/router.py, config.py, TechnicianPicker.jsx | ครบ | รับ |
| REQ-SEC-010 (มุมมองช่าง และ endpoint ยกเลิกเดิม) | MU-01, เหตุการณ์ C, EV-045 | ตารางข้อของไฟล์กลาง | AC-07-15, AC-07-16 | test_AC_07_15, test_AC_07_16 | T-20, T-21 | ops/audit.py, booking/router.py, main.py (ไม่ include refund/router.py) | ขาดบางส่วน: GET /jobs/{id} ยังไม่ตรวจ (GAP-24) | รับความเสี่ยงตาม SH-01 จนถึง UC-02 |
| REQ-PRV-010 | PDPA, EV-045 (SH-05) | ตารางข้อของไฟล์กลาง | AC-07-17, AC-07-18 | test_AC_07_17 x2, test_AC_07_18 | T-22, T-23 | erasure/service.py, erasure/router.py, ops/backup.py | ครบ (การส่งคำขอลบไป IF-02 จริงรอข้อตกลงกับผู้ให้บริการ) | รับ |

ตามรอยย้อนกลับที่เพิ่ม

| ของที่มีอยู่จริง | อ้าง REQ หรือ AC ข้อไหน | ข้อค้นพบ |
|---|---|---|
| คำตอบ 202 payment_pending ของ POST /bookings | REQ-QA-010, AC-07-12 | ไม่มี |
| คำตอบ 409 hold_limit ของ POST /slots/{id}/hold | REQ-SEC-011, AC-07-14 | ไม่มี |
| ตาราง security_events | REQ-SEC-010 บรรทัดที่ 2 และ 4 | ไม่มี |
| POST /ops/erasure-requests | REQ-PRV-010 | ไม่มี |
| ข้อความใหม่บน UI-07-01 และ UI-07-02 | AC-07-12, AC-07-14 (รายการ "ต้องตรง" ที่ CR-07 เพิ่ม) | mockup ยังไม่มีภาพของสถานะนี้ (GAP-26) |
| POST /jobs/{id}/cancel | ไม่มีแล้ว (ปิดตาม CR-07) | ปิด F-12 เดิมของ 004 ไม่ต้องตามต่อ endpoint นี้ |

## 4. แถวที่เพิ่มหรือเปลี่ยนตาม CR-10 และ CR-02 (3 พ.ย. 2569)

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-057 แสดงราคาประเมิน | UC-07 ขั้น 4, EV-048 | ใช่ (1.6) | AC-07-19 | test_AC_07_19, AC-07-19.test.jsx, UI-07-02.test.jsx | T-28, T-29 | config.ESTIMATE_BY_CATEGORY, booking/service.py (estimate_for), GET /deposit-quote, UI-07-02 | ครบ | รับ |
| REQ-BR-002 (ข้อความใหม่ 50 ใน 100) | Finance, EV-048 | ใช่ | AC-07-11, AC-07-19 | test_AC_07_11, test_AC_07_19 | T-12, T-28 | config.DEPOSIT_BY_CATEGORY คำนวณจากราคาประเมิน | ครบ Q-26 ปิด | รับ |
| REQ-BR-001 แถว R3 | EV-048, DR-02 | ใช่ | AC-07-10 R3, AC-08-12 | test_AC_07_10_refund_R3, test_AC_08_12 | T-30, T-13 ของ 004 | refund/rules.py, refund/service.py | ครบ ไม่มี test ข้าม | รับ |
| REQ-FN-041, REQ-IF-005 (Approved) | EV-041, EV-048 | ใช่ | AC-07-04, AC-07-05, AC-07-07 | เดิม | เดิม | config ไม่เปลี่ยน | ครบ Q-18 Q-19 ปิด (GAP-07 ปิด) | รับ |
| REQ-QA-003 (ฉบับ CR-02) | EV-007, EV-048 | ใช่ | AC-07-08 | test_AC_07_08_search_under_load_scaled (ย่อส่วน) | T-09 | ไม่มีโค้ดใหม่ | ย่อส่วน ผลตรวจรับต้องมาจากการยิงโหลดบนเครื่องทดสอบ | รับ เป็นเกณฑ์จบข้อ 4 ของแผนตรวจรับ |

ข้อค้นพบใหม่: ไม่มี ข้อค้นพบที่ปิด: F-01 ถึง F-04 ปิดไปแล้วตั้งแต่ CR-03 รอบนี้ไม่มีสายขาดใหม่ F-05 (A1) และ F-06 (เลือกที่อยู่) ยังเปิด ย้ายไป R2 กับ Q-28 Q-29

## รอบตรวจรับ R1 (EV-049 EV-050)

| REQ | ที่มา | ใน Baseline | AC หรือ UI | test | task | โค้ด | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-041 ล็อกช่วงเวลา (ทางเข้าจากช่วงใกล้เคียง) | EV-049 (U-03 DEF-01) | ใช่ (B5) | UI-07-02, AC-07-04 | UI-07-02-DEF-01.test.jsx | T-32 | frontend/src/App.jsx (onPickAlternative), pages/ConfirmBooking.jsx | ครบ SH-01 ตรวจซ้ำ U-03 | รับ |
| REQ-QA-003 (เต็มรูป) | EV-007, EV-050 | ใช่ (B5) | AC-07-08 | backend/load_test.py | ตรวจรับ ค3 | ไม่มีโค้ดใหม่ | ไม่ผ่านบนเครื่องทดสอบ (Should) ผ่านถึงราว 200 คน | SH-01 รับ R1 ย้ายเกณฑ์ไปก่อนเปิดใช้จริง (Q-68) |

ข้อค้นพบใหม่: ไม่มี GAP-36 บันทึกที่ gaps.md

## แถวที่เพิ่มตาม R2 ส่วน A (CR-11, CR-08, CR-13 วันที่ 23 พ.ย. 2569)

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-064 ช่างคนเดิม | EV-049, EV-051 | ใช่ (1.7) | AC-07-20 ถึง AC-07-23 | test_booking_cr08.py 4 ตัว, AC-07-20.test.jsx | T-34, T-35 | matching/service.py, matching/router.py, TechnicianPicker.jsx, UI-07-01 | ครบ | รับ ทบทวนการใช้จริงใน hypercare (CR-08) |
| REQ-FN-065 A1 เลขโทร call center | EV-051 (Q-28) | ใช่ (1.7) | AC-07-24 | test_AC_07_24, AC-07-20.test.jsx | T-35, T-36 | technicians/router.py (GET /contact), TechnicianPicker.jsx | ครบ ปิด F-05 F-14 | รับ |
| REQ-SEC-014 (feature นี้) | EV-051 | ส่วน 4 (บรรทัดอ้าง) | AC เดิมทุกข้อ AC-07-02 (When ใหม่) | test เดิมตามตาราง CR-11 | T-03 ของ 006 | booking/router.py, technicians/router.py | ครบ ปิด F-06 (ที่อยู่คงที่) | รับ |
| REQ-QA-003 (ฉบับ Q-68) | EV-007, EV-051, EV-052 | ใช่ | AC-07-08 (Given ใหม่) | backend/load_test.py --rate 50 --duration 300, test_load_scaled.py | T-37 | technicians/service.py, ops/serve.py, db/session.py | ผ่านบนเครื่องทดสอบ (p95 0.023 วินาที) ยังไม่ได้วัดบนเครื่องขนาดจริง | รับเป็นหลักฐานของโค้ด เกณฑ์ตรวจรับยังอยู่ก่อนเปิดใช้จริง |
| REQ-OP-008 | EV-049 (OAT-3), EV-051 | ส่วน 4 (บรรทัดอ้าง) | AC-00-09 ถึง AC-00-11 | test_cross_cutting_cr13.py | T-37 | notify/queue.py, ops/lease.py, ops/metrics.py | ครบ ปิด GAP-38 | รับ |

ข้อค้นพบ: F-05 ปิด (A1 มี AC แล้ว AC-07-24) | F-06 ปิด (ที่อยู่มาจากการเข้าสู่ระบบ เลือกได้ AC-02-10) | F-14 ปิด (คิวรอไม่มีรหัส UC และไม่ใช้ UC-08 Q-33 ปิด) ไม่มี F ใหม่
