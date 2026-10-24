# Tasks: การจองงานบริการซ่อมบำรุง (UC-07)

Feature: SPEC-BOOKING | อ้างอิง: plan.md (plan v1) | สร้างด้วย /tasks วันที่ 2569-10-04 (tasks v1)
แก้รอบที่ 1 (ทีมสั่ง): T-06 เดิม AI ตั้ง "พร้อมทำ" ทั้งที่ R3 รอ Q-14 แก้เป็นทำเฉพาะ R1, R2, R4, R5, R6 ตาม D-07-04 และเพิ่มหมายเหตุ

tasks v2 (2569-10-11): เพิ่มช่อง "แบบหน้าจอ" ให้ทุก task และเพิ่ม T-12 ถึง T-16 ตาม CR-03 ด้วยข้อความสั่งในแชต **ไม่ได้รัน /tasks ใหม่** (prompt-log.md #40) เลขและสถานะของ T-01 ถึง T-11 ไม่เปลี่ยน

tasks v3 (2569-10-24): เพิ่ม T-17 ถึง T-27 ตาม CR-07 ด้วยข้อความสั่งในแชต **ไม่ได้รัน /tasks ใหม่** (prompt-log.md #70) เลขและสถานะของ T-01 ถึง T-16 ไม่เปลี่ยน งานที่ไม่ใช่ของ feature ใด (ops/, erasure/, audit.py) อยู่ที่ไฟล์นี้เพราะ CR-07 อยู่ใน changes/ ของ feature นี้

สรุป: 31 task (tasks v4 ดูท้ายไฟล์) | 0 task รอ Q-xx ทั้ง task (CR-10: T-06 ทำครบทุกแถวแล้ว เดิม R3 ใช้พฤติกรรมชั่วคราว)
สถานะปัจจุบัน: เสร็จ 27 (ทุก task ผ่านการตรวจ 5 ข้อแล้ว task หน้าจอของรอบสองผ่านการตรวจเทียบ mockup 6 ข้อด้วย T-26 ตรวจเฉพาะข้อความ เพราะสถานะใหม่ยังไม่มีภาพใน mockup)

### T-01 ตั้งโครงโปรเจกต์ ฐานข้อมูล และตาราง
- รองรับ: REQ-DAT-002, REQ-PRV-002, MD-DOM-01
- ตรวจด้วย: ไม่มี AC ตรง ๆ เป็นงานพื้นฐานของ T-02 ถึง T-08
- ไฟล์ที่แตะ: backend/requirements.txt, backend/pytest.ini, frontend/package.json, frontend/vite.config.js, backend/app/config.py, backend/app/db/session.py, backend/app/db/models.py, backend/app/db/migrations/m001_init.py, backend/app/main.py, backend/tests/conftest.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: pytest และ npm test รันได้ (ยังไม่มี test ของ AC) upgrade(engine) สร้างตาราง 8 ตารางได้ และ jobs.status รับได้เฉพาะ 8 ค่าตาม glossary
- สถานะ: เสร็จ

### T-02 ล็อกช่วงเวลาและหมดอายุอัตโนมัติ
- รองรับ: REQ-FN-041, AS-07, BR-02
- ตรวจด้วย: AC-07-04 (ส่วนล็อก) และ test พื้นฐาน hold หมดอายุใน 10 นาที
- ไฟล์ที่แตะ: backend/app/booking/service.py (hold_slot), backend/app/technicians/service.py (release_expired_holds), backend/app/booking/router.py (POST /slots/{id}/hold)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-01
- เสร็จเมื่อ: POST /slots/{id}/hold ตอบ hold_expires_at = now + HOLD_MINUTES และคนอื่นล็อกซ้ำได้ 409
- สถานะ: เสร็จ

### T-03 ค้นช่างว่างตามประเภทงาน ระยะทาง และช่วงที่ไม่ซ้อน
- รองรับ: REQ-FN-008, BR-02, BR-03, AS-06
- ตรวจด้วย: AC-07-02
- ไฟล์ที่แตะ: backend/app/technicians/service.py, backend/app/technicians/router.py, backend/app/clock.py, backend/tests/test_booking.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-01
- เสร็จเมื่อ: test_AC_07_02_slot_not_rebookable ผ่าน
- สถานะ: เสร็จ

### T-04 สร้าง endpoint จองงาน (POST /bookings) และตัดมัดจำแบบ authorize แล้ว capture
- รองรับ: REQ-FN-008, REQ-FN-041, REQ-IF-001, REQ-CON-003
- ตรวจด้วย: AC-07-01, AC-07-04
- ไฟล์ที่แตะ: backend/app/booking/service.py (create_booking), backend/app/booking/router.py, backend/app/payments/gateway.py, backend/app/payments/service.py, backend/tests/test_booking.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-02, T-03
- เสร็จเมื่อ: test_AC_07_01_booking_success และ test_AC_07_04_no_charge_when_slot_taken ผ่าน
- สถานะ: เสร็จ (ระหว่างทำพบ GAP-05 "ใกล้เคียง" ไม่มีตัวเลข เปิด CR-01 ก่อนจึงทำต่อ)

### T-05 gateway-timeout และ status-inquiry ด้วย reference เดิม
- รองรับ: REQ-IF-005, REQ-IF-001, MD-SEQ-07-05
- ตรวจด้วย: AC-07-05, AC-07-06, AC-07-07
- ไฟล์ที่แตะ: backend/app/payments/service.py, backend/app/payments/gateway.py (GatewayTimeout, status_inquiry), backend/tests/test_payment.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-04
- เสร็จเมื่อ: test_AC_07_05, test_AC_07_06, test_AC_07_07 ผ่าน และ authorize ถูกเรียกครั้งเดียวต่อ ref
- สถานะ: เสร็จ (รอบแรก test_AC_07_05 ไม่ผ่านเพราะ GAP-07 ค่า timeout ไม่ตรง แก้ config แล้วผ่าน)

### T-06 ยกเลิกงานและคืนมัดจำตาม BR-01 (เฉพาะ R1, R2, R4, R5, R6)
- รองรับ: REQ-BR-001, BR-01, MD-STM-01
- ตรวจด้วย: AC-07-10 (Scenario Outline ทุกแถวยกเว้น R3)
- ไฟล์ที่แตะ: backend/app/refund/rules.py, backend/app/refund/service.py, backend/app/refund/router.py, backend/tests/test_refund.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-04
- เสร็จเมื่อ: test_AC_07_10_refund ผ่านทุกแถวที่ไม่ใช่ R3 และ R3 ตอบ 409 ตามพฤติกรรมชั่วคราว
- สถานะ: เสร็จ (R3 รอ Q-14 test ข้ามไว้พร้อมเหตุผล)

### T-07 คิวแจ้งเตือนลูกค้าและช่างภายใน 60 วินาที
- รองรับ: REQ-FN-012, IF-02
- ตรวจด้วย: AC-07-03
- ไฟล์ที่แตะ: backend/app/notify/queue.py, backend/app/booking/service.py (enqueue), backend/app/main.py (GET /notifications/queue), backend/tests/test_booking.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-04
- เสร็จเมื่อ: test_AC_07_03_notify_both_within_60s ผ่าน
- สถานะ: เสร็จ

### T-08 มุมมองช่างซ่อนเบอร์ลูกค้าจนก่อนนัด 2 ชั่วโมง และตัวกรอง log
- รองรับ: REQ-SEC-004, REQ-PRV-002
- ตรวจด้วย: AC-07-09
- ไฟล์ที่แตะ: backend/app/privacy.py, backend/app/booking/service.py (technician_view), backend/app/booking/router.py (GET /jobs/{id}/technician-view), backend/tests/test_privacy.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-04
- เสร็จเมื่อ: test_AC_07_09_phone_hidden_until_2h ผ่าน และเมื่อแก้ PHONE_REVEAL_HOURS เป็น 3 test ต้องพัง (พิสูจน์ชั้น 3 แล้ว)
- สถานะ: เสร็จ

### T-09 test ย่อส่วนรับโหลดสำหรับ REQ-QA-003
- รองรับ: REQ-QA-003
- ตรวจด้วย: AC-07-08 (ฉบับย่อส่วน 20 คำขอ รอ CR-02 เป็นเกณฑ์ตรวจรับจริง)
- ไฟล์ที่แตะ: backend/tests/test_load_scaled.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-03
- เสร็จเมื่อ: test_AC_07_08_search_under_load_scaled รันได้และบันทึกวิธีย่อส่วนใน ac-results.md
- สถานะ: เสร็จ (ผลเป็นสัญญาณบนเครื่องนักศึกษา ไม่ใช่ผลตรวจรับ)

### T-10 หน้าจอเลือกช่าง ยืนยัน และผลการจอง (ใช้ API จำลอง)
- รองรับ: REQ-FN-008, REQ-FN-041, AC-07-04 (ส่วนแสดงผล)
- ตรวจด้วย: AC-07-04 (หน้าจอ)
- ไฟล์ที่แตะ: frontend/src/App.jsx, frontend/src/api/client.js, frontend/src/pages/TechnicianPicker.jsx, frontend/src/pages/ConfirmBooking.jsx, frontend/src/pages/BookingResult.jsx, frontend/src/__tests__/AC-07-04.test.jsx, frontend/src/setupTests.js, frontend/vite.config.js, frontend/package.json, frontend/index.html
- แบบหน้าจอ: ไม่มี (ทำก่อนมี mockup หน้าจอถูกปรับตามแบบใน T-13 ถึง T-15)
- ต้องทำหลัง: ไม่มี (ใช้สัญญา API ใน plan.md ข้อ 4)
- เสร็จเมื่อ: npm test ผ่าน AC-07-04.test.jsx
- สถานะ: เสร็จ

### T-11 ต่อหน้าจอกับ API จริง
- รองรับ: REQ-FN-008
- ตรวจด้วย: ไม่มี AC ตรง ๆ ตรวจด้วยตา: npm run dev + uvicorn แล้วจองได้จนเห็นหน้าผลการจอง
- ไฟล์ที่แตะ: frontend/vite.config.js (proxy /api), backend/seed_demo.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-03, T-04, T-05, T-10
- เสร็จเมื่อ: กดค้นหา เลือกช่วงเวลา ยืนยัน แล้วเห็น "งาน #1 สถานะ ยืนยันแล้ว" บนหน้าจอ
- สถานะ: เสร็จ

### T-12 ยอดมัดจำที่เดียว และ endpoint ขอยอดมัดจำ (CR-03)
- รองรับ: REQ-BR-002, D-00-05, AS-10
- ตรวจด้วย: AC-07-11
- ไฟล์ที่แตะ: backend/app/config.py (DEPOSIT_BY_CATEGORY), backend/app/booking/service.py (deposit_for), backend/app/booking/router.py (GET /deposit-quote และตรวจประเภทงานใน POST /bookings), backend/tests/test_deposit.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-04
- เสร็จเมื่อ: test_AC_07_11 ผ่านทั้ง 3 ประเภทงาน ประเภทงานนอกตารางได้ 422 และไม่มีค่า 300 เหลือในโค้ด
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: ให้ endpoint ตอบยอดเกินไป 10 บาท test พัง 3 ตัว แก้กลับแล้วผ่าน)

### T-13 หน้ายืนยันตามแบบ UI-07-02 (CR-03)
- รองรับ: REQ-BR-002, REQ-FN-041, REQ-IF-001, REQ-BR-001, D-07-05, D-00-05
- ตรวจด้วย: AC-07-11 (หน้าจอ), AC-07-06 (หน้าจอ), AC-07-04 (หน้าจอ เดิม) และรายการ "ต้องตรง" ของ UI-07-02
- ไฟล์ที่แตะ: frontend/src/pages/ConfirmBooking.jsx, frontend/src/components/Steps.jsx, frontend/src/App.jsx, frontend/src/__tests__/AC-07-11.test.jsx, frontend/src/__tests__/AC-07-06.test.jsx, frontend/src/__tests__/UI-07-02.test.jsx, frontend/src/__tests__/AC-07-04.test.jsx (เฉพาะข้อมูลตั้งต้น ตาม CR-03 ที่แก้เพิ่มหลัง GAP-16)
- แบบหน้าจอ: UI-07-02 mockups/UI-07-02-confirm.html
- ต้องทำหลัง: ไม่มี (ใช้ API จำลองตามสัญญาใน plan.md ข้อ 4)
- เสร็จเมื่อ: npm test ผ่าน AC-07-11.test.jsx, AC-07-06.test.jsx, UI-07-02.test.jsx และ AC-07-04.test.jsx ยังผ่าน
- สถานะ: เสร็จ (รันทั้งชุดครั้งแรก AC-07-04.test.jsx ไม่ผ่าน ดู GAP-16)

### T-14 หน้าเลือกช่างตามแบบ UI-07-01 (CR-03)
- รองรับ: REQ-FN-008, REQ-FN-041, REQ-BR-002, D-07-05
- ตรวจด้วย: รายการ "ต้องตรง" ของ UI-07-01 (AC-07-02 และ AC-07-04 ส่วนล็อก ตรวจที่หลังบ้านแล้ว)
- ไฟล์ที่แตะ: frontend/src/pages/TechnicianPicker.jsx, frontend/src/api/client.js (getDepositQuote), frontend/src/__tests__/UI-07-01.test.jsx
- แบบหน้าจอ: UI-07-01 mockups/UI-07-01-pick-technician.html
- ต้องทำหลัง: T-13 (ใช้ Steps.jsx)
- เสร็จเมื่อ: npm test ผ่าน UI-07-01.test.jsx และไม่มีปุ่มหรือข้อความของ Q-28, Q-29 บนหน้าจอ
- สถานะ: เสร็จ

### T-15 หน้าผลการจองตามแบบ UI-07-03 (CR-03)
- รองรับ: REQ-FN-008, REQ-FN-012, REQ-BR-002
- ตรวจด้วย: รายการ "ต้องตรง" ของ UI-07-03
- ไฟล์ที่แตะ: frontend/src/pages/BookingResult.jsx, frontend/src/App.jsx (ส่งชื่อช่าง), frontend/src/__tests__/UI-07-03.test.jsx
- แบบหน้าจอ: UI-07-03 mockups/UI-07-03-result.html
- ต้องทำหลัง: T-13 (ใช้ Steps.jsx)
- เสร็จเมื่อ: npm test ผ่าน UI-07-03.test.jsx
- สถานะ: เสร็จ (รอบแรก AI ไม่ได้ใส่แถบขั้นตอน test จับได้ ดู GAP-17)

### T-16 รัน test ทั้งชุด และตรวจหน้าจอจริงเทียบ mockup ด้วยคน (CR-03)
- รองรับ: REQ-FN-008, REQ-BR-002
- ตรวจด้วย: ทุก AC (รันซ้ำทั้งชุด) และรายการตรวจ 6 ข้อใน docs/mockup-guide.md ข้อ 9
- ไฟล์ที่แตะ: specs/002-booking/test-run.txt, test-run-round3.txt, ac-results.md, gaps.md, rtm.md, ui-review/ (ภาพหน้าจอจริงและ ui-review.md), docs/srs/baseline.md, backend/app/db/session.py (เฉพาะการแก้ GAP-15)
- แบบหน้าจอ: UI-07-01, UI-07-02, UI-07-03
- ต้องทำหลัง: T-12, T-13, T-14, T-15
- เสร็จเมื่อ: AC ที่เคยผ่านในรอบที่ 2 ยังผ่านทุกข้อ AC-07-11 ผ่าน และรายการตรวจหน้าจอ 6 ข้อ "ตรง" ครบ 3 หน้า
- สถานะ: เสร็จ

### T-17 ตารางและ migration ของ CR-07
- รองรับ: REQ-PRV-010, REQ-SEC-010, REQ-QA-010 (CR-07)
- ตรวจด้วย: ไม่มี AC ตรง ๆ เป็นงานพื้นฐานของ T-18 ถึง T-23
- ไฟล์ที่แตะ: backend/app/db/models.py (customers.erased_at, SecurityEvent, ErasureRequest, ค่า pending ของ payments.result), backend/app/db/migrations/m002_cr07.py (ใหม่), backend/app/main.py (เรียก m002)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-01
- เสร็จเมื่อ: test เดิมทั้งชุดผ่านบนฐานข้อมูลใหม่ และ m002 เพิ่มคอลัมน์ erased_at ให้ฐานข้อมูลเก่าได้
- สถานะ: เสร็จ

### T-18 gateway ไม่ตอบเลย คงล็อกเป็น "รอชำระเงิน" และลองใหม่ด้วย reference เดิม (CR-07)
- รองรับ: REQ-QA-010 บรรทัดที่ 2 และ 3, REQ-IF-005, REQ-FN-041, D-07-06
- ตรวจด้วย: AC-07-12, AC-07-13 (AC-07-05 และ AC-07-07 ต้องผ่านเหมือนเดิม)
- ไฟล์ที่แตะ: backend/app/payments/gateway.py (FakeGateway inquiry_answer = timeout), backend/app/payments/service.py (pending, settle, retry_pending, settle_on_hold_expiry), backend/app/booking/service.py (PaymentPending, ใช้งานเดิมเมื่อกดซ้ำ), backend/app/booking/router.py (202 payment_pending), backend/app/technicians/service.py (ปิดเรื่องเงินก่อนปล่อยล็อกที่หมดอายุ), backend/app/technicians/router.py (commit หลังค้นหา), backend/tests/test_booking_cr07.py
- แบบหน้าจอ: UI-07-02 (ทำใน T-26)
- ต้องทำหลัง: T-17
- เสร็จเมื่อ: test_AC_07_12 และ test_AC_07_13 ผ่าน authorize ถูกเรียก 1 ครั้งต่องานเสมอ และ status-inquiry ที่ไม่ตอบไม่ทำให้เกิด 500 อีก (GAP-21)
- สถานะ: เสร็จ

### T-19 จำกัดการล็อกช่วงเวลา 1 ช่วงต่อลูกค้า (CR-07)
- รองรับ: REQ-SEC-011, D-00-05
- ตรวจด้วย: AC-07-14
- ไฟล์ที่แตะ: backend/app/config.py (HOLD_LIMIT_PER_CUSTOMER), backend/app/booking/service.py (HoldLimitReached), backend/app/booking/router.py (409 hold_limit), backend/app/technicians/service.py (flush หลังปล่อยล็อก), backend/tests/test_booking_cr07.py
- แบบหน้าจอ: UI-07-01 (ทำใน T-26)
- ต้องทำหลัง: T-02
- เสร็จเมื่อ: test_AC_07_14 ผ่าน และพิสูจน์ชั้น 3: ตั้ง HOLD_LIMIT_PER_CUSTOMER = 2 แล้ว test พัง
- สถานะ: เสร็จ (พิสูจน์ชั้น 3 แล้ว test_AC_07_14 พัง 1 ตัว แก้กลับแล้วผ่าน)

### T-20 สิทธิ์ต่องาน 403 และบันทึกความพยายามที่มุมมองช่าง (CR-07)
- รองรับ: REQ-SEC-010 บรรทัดที่ 1, 2, 4, REQ-SEC-004
- ตรวจด้วย: AC-07-15 (AC-07-09 ต้องผ่านเหมือนเดิม)
- ไฟล์ที่แตะ: backend/app/ops/audit.py (ใหม่ ใช้ร่วมทุก feature), backend/app/booking/router.py (technician-view), backend/tests/test_booking_cr07.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-17
- เสร็จเมื่อ: test_AC_07_15 ผ่าน คำตอบของงานคนอื่นกับงานที่ไม่มีเหมือนกันทุกตัวอักษร
- สถานะ: เสร็จ

### T-21 ปิด POST /jobs/{id}/cancel (CR-07)
- รองรับ: REQ-SEC-010, REQ-SEC-012, D-07-07, MU-01
- ตรวจด้วย: AC-07-16 และ AC-07-10 ทุกแถว (test เปลี่ยนเฉพาะ helper ส่วน When ตามตาราง test เดิมที่เปลี่ยนใน CR-07)
- ไฟล์ที่แตะ: backend/app/refund/router.py (ลบ), backend/app/main.py (ไม่ include), backend/tests/test_refund.py (helper cancel), backend/tests/test_booking_cr07.py
- แบบหน้าจอ: ไม่มี (หน้าจอไม่เคยเรียก endpoint นี้)
- ต้องทำหลัง: T-06
- เสร็จเมื่อ: test_AC_07_16 ผ่าน และ AC-07-10 ผ่านทุกแถวด้วยตัวเลขเดิม
- สถานะ: เสร็จ

### T-22 คำขอลบข้อมูลลูกค้า (CR-07)
- รองรับ: REQ-PRV-010 บรรทัดที่ 1 ถึง 3, REQ-DAT-002
- ตรวจด้วย: AC-07-17
- ไฟล์ที่แตะ: backend/app/erasure/ (ใหม่: service.py, router.py), backend/app/notify/queue.py (Notifier.request_erasure), backend/app/config.py (ERASURE_DEADLINE_DAYS, erasure_ledger_path), backend/tests/test_erasure.py
- แบบหน้าจอ: ไม่มี (R1 รับคำขอผ่าน call center)
- ต้องทำหลัง: T-17
- เสร็จเมื่อ: test_AC_07_17 ทั้ง 2 ตัวผ่าน ค้นเบอร์ในทุกตารางไม่พบ
- สถานะ: เสร็จ

### T-23 สำรอง กู้คืน และลบซ้ำหลังกู้คืน (CR-07)
- รองรับ: REQ-OP-007, REQ-PRV-010 บรรทัดที่ 4
- ตรวจด้วย: AC-00-05, AC-07-18
- ไฟล์ที่แตะ: backend/app/ops/backup.py (ใหม่), backend/ops_backup.py (ใหม่ คำสั่งของคนเวร), backend/app/erasure/service.py (reapply_ledger), backend/tests/test_cross_cutting.py, backend/tests/test_erasure.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-22
- เสร็จเมื่อ: test_AC_00_05 และ test_AC_07_18 ผ่าน และลองคำสั่ง ops_backup.py backup แล้ว restore บนเครื่องว่างจริงได้ 1 รอบ
- สถานะ: เสร็จ (ซ้อมด้วยคำสั่งบนเครื่องพัฒนาแล้ว การซ้อมบน PostgreSQL ของระบบจริงยังไม่ทำ ดู operations.md)

### T-24 การเฝ้าดู /health /ready /metrics log มีโครงสร้าง และการตั้งค่าโหมด production (CR-07)
- รองรับ: REQ-OP-001, REQ-OP-005, REQ-SEC-010 บรรทัดที่ 3, REQ-SEC-012, REQ-PRV-002
- ตรวจด้วย: AC-00-01 ถึง AC-00-04, AC-00-06 ถึง AC-00-08 (AC-07-09 ต้องผ่านเหมือนเดิม)
- ไฟล์ที่แตะ: backend/app/ops/ (ใหม่: metrics.py, alerts.py, guard.py, router.py, scheduler.py), backend/app/main.py (create_app, middleware, งานเบื้องหลังทุก 1 นาที), backend/app/clock.py (now= เฉพาะโหมด test), backend/app/config.py, backend/app/privacy.py (log_event), router และ service ทุกตัวที่ log, backend/tests/conftest.py (APP_ENV = test), backend/tests/test_cross_cutting.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-20
- เสร็จเมื่อ: test_cross_cutting.py ผ่านทั้งไฟล์ และค้น log.info ใน backend/app ต้องไม่เหลือ (ใช้ log_event ทั้งหมด)
- สถานะ: เสร็จ

### T-25 คู่มือรับมือเหตุฉบับใช้จริง และบัญชี endpoint (CR-07)
- รองรับ: REQ-OP-006, REQ-OP-007, REQ-SEC-012
- ตรวจด้วย: ไม่มี AC ตรวจด้วย walkthrough (EV-045) และเทียบบัญชี endpoint กับ /openapi.json ของโหมด development
- ไฟล์ที่แตะ: docs/srs/operations.md
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-21, T-23, T-24
- เสร็จเมื่อ: เหตุการณ์ที่ 1 ถึง 3 ผ่าน walkthrough และบัญชี endpoint ตรงกับ /openapi.json ทุกแถว
- สถานะ: เสร็จ (เหตุการณ์ที่ 4 และ 5 ยังไม่ได้ walkthrough)

### T-26 หน้าจอรับคำตอบใหม่ของ CR-07 (UI-07-01, UI-07-02)
- รองรับ: REQ-SEC-011, REQ-QA-010, D-00-05
- ตรวจด้วย: AC-07-12 (หน้าจอ) AC-07-13 (หน้าจอ) AC-07-14 (หน้าจอ) และ test หน้าจอเดิมทั้งหมด
- ไฟล์ที่แตะ: frontend/src/pages/TechnicianPicker.jsx, frontend/src/pages/ConfirmBooking.jsx, frontend/src/__tests__/AC-07-12.test.jsx, frontend/src/__tests__/AC-07-14.test.jsx
- แบบหน้าจอ: UI-07-01, UI-07-02 (รายการ "ต้องตรง" ที่ CR-07 เพิ่ม ยังไม่มีภาพใน mockup GAP-26)
- ต้องทำหลัง: T-18, T-19
- เสร็จเมื่อ: npm test ผ่านทั้งหมด และไม่มีตัวเลขนาทีหรือเวลาพิมพ์ในหน้าจอ (ข้อความมาจาก API)
- สถานะ: เสร็จ

### T-27 รัน test ทั้งชุดหลัง CR-07
- รองรับ: ทุก REQ ของ CR-07
- ตรวจด้วย: ทุก AC ของ 002, 003, 004 และ AC-00-01 ถึง 08
- ไฟล์ที่แตะ: specs/000-shared/test-run.txt, specs/000-shared/test-run-cr07-round1.txt, ac-results.md ของทุก feature และ 000-shared, rtm.md ของทุก feature, specs/000-shared/gaps.md, docs/srs/baseline.md
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-17 ถึง T-26 และ T-08 ถึง T-11 ของ 003, T-07 ถึง T-10 ของ 004
- เสร็จเมื่อ: test เดิมที่ไม่อยู่ในตาราง "test เดิมที่เปลี่ยน" ของ CR-07 ผ่านโดยไม่ถูกแตะ และ test ใหม่ผ่านทั้งหมด
- สถานะ: เสร็จ

## ตารางตรวจความครบ

| AC ID | task ที่ตรวจ AC นี้ |
|---|---|
| AC-07-01 | T-04 |
| AC-07-02 | T-03 |
| AC-07-03 | T-07 |
| AC-07-04 | T-02, T-04, T-10 (หน้าจอ), T-13 (หน้าจอแบบใหม่) |
| AC-07-05 | T-05 |
| AC-07-06 | T-05 |
| AC-07-07 | T-05 |
| AC-07-08 | T-09 (ย่อส่วน รอ CR-02) |
| AC-07-09 | T-08 |
| AC-07-10 | T-06 (R3 รอ Q-14) |
| AC-07-11 | T-12 (หลังบ้าน), T-13 (หน้าจอ) |
| AC-07-06 (หน้าจอ) | T-13 |
| รายการ "ต้องตรง" ของ UI-07-01, UI-07-02, UI-07-03 | T-14, T-13, T-15 และ T-16 (ตรวจด้วยคน) |

| Constraint ID | task ที่ทำให้เป็นจริง |
|---|---|
| REQ-CON-003 | T-04 (interface Gateway ไม่เปลี่ยนราย) |
| REQ-CON-001 | ทุก task ตัด A2 ออก (D-07-02) |
| REQ-PRV-002 | T-01 (ไม่มีตาราง log), T-08 (privacy.py) |
| REQ-SEC-004 | T-08 |
| REQ-IF-001 | T-04 |
| REQ-IF-005 | T-05 |
| REQ-DAT-002 | T-01 |
| REQ-BR-002 | T-12, T-13 |
| D-00-01, D-00-02, D-00-03 | T-01 (โครงโปรเจกต์) |
| D-00-04 | ทุก task ที่มี test (ชื่อ test ตาม AC หรือ UI) |
| D-00-05 | T-12, T-13 |

## สิ่งที่ยังไม่ทำ

- Q-14 BR-01 R3: T-06 ทำแถวอื่นแล้ว R3 ใช้พฤติกรรมชั่วคราว "ไม่อนุญาต" ยังไม่ได้คำตอบ (เลื่อนเป็น 25 ต.ค.)
- Q-18 ระยะล็อก: ทำเป็น config HOLD_MINUTES = 10 ถ้าคำตอบต่าง แก้ config
- Q-19 gateway-timeout: config GATEWAY_TIMEOUT_SECONDS = 30 (ดู GAP-07)
- Q-22 geoPoint: เก็บแต่ไม่ส่งออก ยังไม่มี task เพราะไม่มี REQ รองรับ
- Q-23 ใครปลดล็อก: ใช้ AS-07 หมดอายุเอง (T-02) รอกลุ่มยืนยันกับเจ้าของ
- Q-26 ราคาประเมิน, Q-27 รูปแบบหมายเลขงาน, Q-28 UC-07 A1, Q-29 เลือกที่อยู่: ยังไม่มี task เพราะยังไม่มี REQ หรือ AC รองรับ หน้าจอใช้พฤติกรรมชั่วคราวตาม spec ส่วน 9

### ส่วนที่เพิ่มตาม CR-07 (tasks v3)

| AC | task |
|---|---|
| AC-07-12, AC-07-13 | T-18, T-26 (หน้าจอ) |
| AC-07-14 | T-19, T-26 (หน้าจอ) |
| AC-07-15 | T-20 |
| AC-07-16 | T-21 |
| AC-07-17 | T-22 |
| AC-07-18 | T-23 |
| AC-00-01 ถึง AC-00-04, AC-00-06 ถึง AC-00-08 | T-24 |
| AC-00-05 | T-23 |

| Constraint ID (รุ่น 1.1) | task ที่ทำให้เป็นจริง |
|---|---|
| REQ-OP-001 | T-24 |
| REQ-OP-005 | T-24 |
| REQ-OP-006 | T-25 |
| REQ-OP-007 | T-23, T-25 |
| REQ-QA-010 | T-18 (IF-01 ตัดมัดจำ) IF-02 อยู่ที่ T-08, T-10 ของ 003 IF-01 คืนเงินอยู่ที่ T-08 ของ 004 IF-03 ยังไม่เรียกจริง (ค่าใน config) |
| REQ-SEC-010 | T-20, T-21, T-24 (บรรทัดที่ 3) |
| REQ-SEC-011 | T-19 |
| REQ-SEC-012 | T-21, T-24, T-25 |
| REQ-PRV-010 | T-22, T-23 |
| REQ-CMP-001 | ไม่มี task (SH-05 ตรวจเอกสาร EV-045) |

### ส่วนที่เพิ่มตาม CR-10 และ CR-02 (tasks v4, 3 พ.ย. 2569)

tasks v4: เพิ่ม T-28 ถึง T-31 ด้วยข้อความสั่งในแชต **ไม่ได้รัน /tasks ใหม่** (prompt-log.md #81) เลขและสถานะของ T-01 ถึง T-27 ไม่เปลี่ยน รวม 31 task เสร็จ 31 (T-06 ทำครบทุกแถวแล้ว R3 ไม่ใช้พฤติกรรมชั่วคราวอีก)

### T-28 ราคาประเมินในตารางเดียว และ deposit-quote ส่งราคาประเมิน (CR-10)
- รองรับ: REQ-FN-057, REQ-BR-002, D-00-05
- ตรวจด้วย: AC-07-19, AC-07-11 (เดิม ไม่แก้)
- ไฟล์ที่แตะ: backend/app/config.py, backend/app/booking/service.py, backend/app/booking/router.py, backend/tests/test_booking_cr10.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: test_AC_07_19 ผ่าน และ test ของ AC-07-11 ผ่านโดยไม่แก้
- สถานะ: เสร็จ

### T-29 หน้ายืนยันแสดงราคาประเมิน และเงื่อนไขบรรทัดที่ 3 ตาม BR-01 รุ่น 1.1 (CR-10)
- รองรับ: REQ-FN-057, REQ-BR-001
- ตรวจด้วย: AC-07-19 (หน้าจอ), UI-07-02 (รายการ "ต้องตรง" ที่ CR-10 แก้)
- ไฟล์ที่แตะ: frontend/src/pages/TechnicianPicker.jsx, frontend/src/pages/ConfirmBooking.jsx, frontend/src/__tests__/AC-07-19.test.jsx, frontend/src/__tests__/UI-07-02.test.jsx (2 test ตามตาราง "test เดิมที่เปลี่ยน" ของ CR-10)
- แบบหน้าจอ: UI-07-02 รุ่น CR-10
- ต้องทำหลัง: T-28
- เสร็จเมื่อ: npm test ผ่าน และไม่มีตัวเลขราคาหรือค่าเดินทางพิมพ์ในหน้าจอ
- สถานะ: เสร็จ

### T-30 BR-01 แถว R3 (CR-10)
- รองรับ: REQ-BR-001
- ตรวจด้วย: AC-07-10 แถว R3 (ไม่ข้ามแล้ว)
- ไฟล์ที่แตะ: specs/002-booking/rules.md (รุ่น 1.1), backend/app/refund/rules.py, backend/tests/test_refund.py (ตาราง "test เดิมที่เปลี่ยน" ของ CR-10)
- แบบหน้าจอ: ไม่มี (หน้ายกเลิกอยู่ที่ T-13 ของ 004)
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: test_AC_07_10 ทุกแถวผ่าน ไม่มี test ข้าม
- สถานะ: เสร็จ

### T-31 ช่องทางถึงคนเวรผ่าน webhook (CR-10, GAP-28)
- รองรับ: REQ-OP-005 บรรทัดที่ 2
- ตรวจด้วย: AC-00-02 (test เดิมไม่แก้ เพิ่ม test ของ Pager ตัวจริง) และ OAT-2 บนเครื่องทดสอบ
- ไฟล์ที่แตะ: backend/app/config.py, backend/app/ops/alerts.py, backend/tests/test_cross_cutting_cr10.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: test ผ่าน และ OAT-2 ได้ข้อความถึงเครื่องรับภายใน 2 นาที
- สถานะ: เสร็จ

| AC หรือ Constraint (CR-10) | task |
|---|---|
| AC-07-08 (ฉบับ CR-02) | T-09 (ย่อส่วน เดิม) และการยิงโหลดตอนตรวจรับ (docs/acceptance) |
| AC-07-10 แถว R3 | T-30 |
| AC-07-19 | T-28, T-29 |
| REQ-OP-005 บรรทัดที่ 2 ช่องทางจริง | T-31 |

### ส่วนที่เพิ่มหลังตรวจรับรอบแรก (tasks v5, 16 พ.ย. 2569)

tasks v5: เพิ่ม T-32 และ T-33 จากข้อบกพร่องที่พบตอนตรวจรับ (docs/acceptance/acceptance-record-r1.md) ด้วยข้อความสั่งในแชต ไม่ได้รัน /tasks ใหม่ (prompt-log.md #86) ไม่มี REQ AC BR หรือ UI เปลี่ยน จึงไม่ต้องมี CR (แก้โค้ดให้ตรงสเปกเดิม) test เดิมเปลี่ยน 0 ตัว รวม 33 task เสร็จ 33

### T-32 แก้ DEF-01 ล็อกช่วงใกล้เคียงและแสดงเวลาหมดล็อก (GAP-36)
- รองรับ: REQ-FN-041
- ตรวจด้วย: UI-07-02 (รายการต้องตรง บรรทัดเวลาหมดล็อก) AC-07-04 (เดิม ไม่แก้)
- ไฟล์ที่แตะ: frontend/src/App.jsx, frontend/src/pages/ConfirmBooking.jsx, frontend/src/__tests__/UI-07-02-DEF-01.test.jsx (ใหม่)
- แบบหน้าจอ: UI-07-02 รุ่น CR-10 (ไม่เปลี่ยน)
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: test ใหม่ไม่ผ่านกับโค้ดก่อนแก้ แล้วผ่านหลังแก้ test เดิมผ่านโดยไม่แก้ SH-01 ตรวจซ้ำ U-03
- สถานะ: เสร็จ

### T-33 แก้ DEF-02 log ของแอปออก stdout ในระบบจริง (GAP-37)
- รองรับ: REQ-OP-005 บรรทัดที่ 3
- ตรวจด้วย: AC-00-03 (test เดิมไม่แก้ เพิ่ม test_AC_00_03_production_app_writes_structured_log_to_stdout) และ OAT-6 รอบสอง
- ไฟล์ที่แตะ: backend/app/main.py, backend/tests/test_cross_cutting_def02.py (ใหม่)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: test ใหม่ไม่ผ่านกับโค้ดก่อนแก้ แล้วผ่านหลังแก้ OAT-6 ผ่าน
- สถานะ: เสร็จ

tasks v6 (2569-11-23): เพิ่ม T-34 ถึง T-37 ตาม CR-08 และ CR-13 ด้วยข้อความสั่งในแชต (prompt-log.md #92) งานของ CR-11 และ CR-12 ที่แตะไฟล์ของ feature นี้อยู่ใน tasks.md ของ 006 และ 007

### T-34 ช่างคนเดิม หลังบ้าน (CR-08, BR-08)
- รองรับ: REQ-FN-064, BR-08, REQ-SEC-010
- ตรวจด้วย: AC-07-20, AC-07-21, AC-07-22, AC-07-23
- ไฟล์ที่แตะ: backend/app/matching/service.py (past_technicians, past_technician_slots), backend/app/matching/router.py, backend/app/config.py, backend/tests/test_booking_cr08.py (ใหม่)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-03 ของ 006 (ลูกค้ามาจาก token)
- เสร็จเมื่อ: test_AC_07_20 ถึง 23 ผ่าน
- สถานะ: เสร็จ

### T-35 ช่างคนเดิมและเส้นทาง A1 หน้าจอ (CR-08)
- รองรับ: REQ-FN-064, REQ-FN-065
- ตรวจด้วย: AC-07-20.test.jsx (AC-07-20, 21, 24 และ AC-02-10) UI-07-01.test.jsx เดิมผ่านโดยไม่แก้
- ไฟล์ที่แตะ: frontend/src/pages/TechnicianPicker.jsx, frontend/src/api/client.js, mockups/UI-07-01-pick-technician.html
- แบบหน้าจอ: UI-07-01 (แก้ เพิ่มสถานะที่ 4)
- สถานะ: เสร็จ

### T-36 เส้นทาง A1 หลังบ้าน เลขโทร call center (CR-08 Q-28)
- รองรับ: REQ-FN-065
- ตรวจด้วย: AC-07-24
- ไฟล์ที่แตะ: backend/app/technicians/router.py (GET /contact)
- สถานะ: เสร็จ

### T-37 คิวในฐานข้อมูล หลาย process และประสิทธิภาพของการค้นหา (CR-13)
- รองรับ: REQ-OP-008, REQ-QA-003
- ตรวจด้วย: AC-00-09, AC-00-10, AC-00-11, AC-07-08 (docs/acceptance/load-test-r2.md)
- ไฟล์ที่แตะ: backend/app/notify/queue.py, ops/lease.py (ใหม่), ops/metrics.py, ops/scheduler.py, ops/router.py, ops/serve.py (ใหม่), ops/nodelay.py (ใหม่), main.py, db/session.py, db/migrations/m004_r2.py, technicians/service.py, booking/router.py (with_for_update), auth/deps.py, backend/load_test.py, backend/tests/test_cross_cutting_cr13.py (ใหม่) test เดิม test_job_status_cr07.py 1 บรรทัดตามตารางของ CR-13
- เสร็จเมื่อ: test_AC_00_09 ถึง 11 ผ่าน ทดสอบโหลดบน PostgreSQL 2 process ไม่มีคำตอบ 5xx และบันทึกผลตรงตามที่วัดได้
- สถานะ: เสร็จ (พบ GAP-41 GAP-42 ระหว่างทดสอบโหลด แก้แล้ว)
