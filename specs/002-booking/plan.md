# Plan: การจองงานบริการซ่อมบำรุง (UC-07)

อ้างอิง: spec.md SPEC-BOOKING v1.1 (B1 + v2 หลัง /clarify) | Updated: 2569-10-04 | สร้างด้วย /plan แล้วทีมตรวจแล้ว (plan v1)
หลังจากนั้น: ข้อ 5 เพิ่มแถว REQ-IF-005 "ใช้แล้ว" เมื่อ Q-19 มีค่าชั่วคราว (แก้โดยทีม 4 ต.ค.)
plan v2 (2569-10-11): แก้เฉพาะข้อ 2, 4, 5, 6, 7, 8 ตาม CR-03 และ CR-04 ด้วยข้อความสั่งในแชต **ไม่ได้รัน /plan ใหม่** (prompt-log.md #39) อ้างอิง spec.md 1.4 และ Constraint กลางรุ่น 1.0
plan v3 (2569-10-24): CR-07 อนุมัติ แก้เฉพาะตารางข้อ 5 ส่วน "รุ่น 1.1" และเพิ่มข้อ 9 ด้วยข้อความสั่งในแชต **ไม่ได้รัน /plan ใหม่** (prompt-log.md #70) อ้างอิง spec.md 1.5 และ Constraint กลางรุ่น 1.1

## 1. สรุปแนวทาง

- ลูกค้าค้นช่างว่างตามประเภทงานและที่อยู่ (BR-02, BR-03) ล็อกช่วงเวลา 10 นาที (REQ-FN-041) แล้วยืนยันพร้อมชำระมัดจำ
- หลังบ้านเป็น API (Python FastAPI) เก็บข้อมูลด้วย SQLAlchemy ต่อ PostgreSQL ในระบบจริง ตอน test ใช้ SQLite ในหน่วยความจำ
- การชำระเป็น authorize แล้ว capture (D-07-03) ถ้า gateway ไม่ตอบใน gateway-timeout ให้ status-inquiry ด้วย reference เดิม (REQ-IF-005) ก่อนตัดสิน
- การแจ้งเตือนไม่รอผล: API วางข้อความลงคิว ตัวส่งแยกทำงาน (REQ-FN-012 ภายใน 60 วินาที)
- ช่างเห็นเบอร์ลูกค้าผ่าน endpoint มุมมองช่างเท่านั้น ซึ่งซ่อนเบอร์จนถึง 2 ชั่วโมงก่อนนัด (REQ-SEC-004) และ log ของระบบไม่มีฟิลด์เบอร์โทร (REQ-PRV-002)
- คืนมัดจำตาม BR-01 เป็นตารางในโค้ด 1 ที่ (rules R1 ถึง R6) R3 ใช้พฤติกรรมชั่วคราวของ Q-14 ตาม spec ข้อ 9

## 2. เทคโนโลยีที่ใช้

| สิ่งที่เลือก | มาจาก | หมายเหตุ |
|---|---|---|
| Payment Gateway รายเดิม (IF-01) | REQ-CON-003 | ในโค้ดเป็น interface `Gateway` ตอน test ใช้ `FakeGateway` ที่สั่งให้ approved / declined / ไม่ตอบ ได้ |
| Python + FastAPI | D-00-01 (ทีมเลือกเอง บันทึกในไฟล์กลางตาม CR-04) | ทดสอบแล้วบน Python 3.11 ถึง 3.13 (GAP-15) |
| SQLAlchemy 2 + PostgreSQL 16 | D-00-02 (ทีมเลือกเอง) | ต่อฐานข้อมูลผ่านตัวแปร `DATABASE_URL` ตอน test ใช้ `sqlite:///:memory:` ไม่ต้องติดตั้งอะไรเพิ่ม |
| pytest + httpx (TestClient) | D-00-04 (ทีมเลือกเอง) | ทุก test ชื่อขึ้นต้น test_AC_07_xx |
| React 19 (Vite) + Tailwind CSS 4 | D-00-03 (ทีมเลือกเอง) | โครงเริ่มต้นอยู่ใน `frontend/` แล้ว |
| Vitest + React Testing Library | D-00-04 (ทีมเลือกเอง) | test หน้าจอใช้ API จำลอง ไม่ต้องรันหลังบ้าน ชื่อไฟล์ตาม AC หรือ UI |
| คิวในหน่วยความจำ (notify/queue.py) | ทีมเลือกเอง ไม่ได้มาจาก spec | ระบบจริงเปลี่ยนเป็น Redis ได้โดยแก้ไฟล์เดียว ตอน test อ่านคิวตรง ๆ |

library ทั้งหมดอยู่ใน `backend/requirements.txt`
รัน test หลังบ้าน: `cd backend && pytest -v -k "AC_"`
เปิดหลังบ้าน: `cd backend && uvicorn app.main:app --reload --port 8000` (หน้าจอเรียกผ่าน `/api` ซึ่ง Vite ส่งต่อให้)
รัน test หน้าจอ: `cd frontend && npm test` เปิดดูหน้าจอ: `cd frontend && npm run dev`

### โครงไฟล์

```
backend/
  requirements.txt
  pytest.ini
  app/
    main.py                     สร้าง FastAPI app รวม router และสร้างตารางตอนเริ่ม
    config.py                   DATABASE_URL, HOLD_MINUTES (Q-18), GATEWAY_TIMEOUT_SECONDS (Q-19), PHONE_REVEAL_HOURS, DEPOSIT_BY_CATEGORY (REQ-BR-002, CR-03)
    db/models.py                ตาราง customers, service_addresses, technicians, time_slots, jobs, job_status_history, payments, refunds
    db/session.py               engine, SessionLocal, get_db
    db/migrations/m001_init.py  ฟังก์ชัน upgrade(engine) สร้างทุกตาราง
    clock.py                    เวลาปัจจุบันที่ test กำหนดได้ (now=...)
    technicians/service.py      ค้นช่างว่าง (BR-02, BR-03, AS-06) และหาช่วงใกล้เคียง (AC-07-04)
    technicians/router.py       GET /technicians
    booking/service.py          ล็อกช่วงเวลา (REQ-FN-041) และสร้างงาน (REQ-FN-008)
    booking/router.py           POST /slots/{id}/hold, GET /deposit-quote (CR-03), POST /bookings, GET /jobs/{id}, GET /jobs/{id}/technician-view
    payments/gateway.py         interface Gateway + FakeGateway (IF-01)
    payments/service.py         authorize + timeout + status-inquiry + capture (REQ-IF-001, REQ-IF-005)
    refund/rules.py             ตาราง BR-01 R1 ถึง R6
    refund/service.py           ยกเลิกงานและสร้าง Refund (REQ-BR-001)
    refund/router.py            POST /jobs/{id}/cancel
    notify/queue.py             คิวข้อความและเวลาส่ง (REQ-FN-012)
    privacy.py                  ตัวกรอง log ไม่ให้มีเบอร์โทร (REQ-PRV-002)
  tests/
    conftest.py                 ฐานข้อมูลในหน่วยความจำ, FakeGateway, นาฬิกาจำลอง, ข้อมูลตั้งต้น (ช่าง ประสิทธิ์ ฯลฯ)
    test_booking.py             AC-07-01, 02, 03, 04
    test_payment.py             AC-07-05, 06, 07
    test_privacy.py             AC-07-09
    test_refund.py              AC-07-10 (R1, R2, R4, R5, R6; R3 ข้ามรอ Q-14)
    test_load_scaled.py         AC-07-08 แบบย่อส่วน (รอ CR-02 จึงยังเป็นฉบับทดลอง)
    test_deposit.py             AC-07-11 (CR-03)
frontend/
  src/api/client.js             เรียก API ตามสัญญาข้อ 4
  src/components/Steps.jsx         แถบขั้นตอน 3 ขั้น ใช้ร่วม 3 หน้า (CR-03)
  src/pages/TechnicianPicker.jsx   UI-07-01 เลือกประเภทงาน แล้วเลือกช่างและช่วงเวลา (ล็อก และขอยอดมัดจำ)
  src/pages/ConfirmBooking.jsx     UI-07-02 แสดงมัดจำจากระบบ เวลาสิ้นสุดการล็อก เงื่อนไข BR-01 แล้วกดยืนยัน รับ 409 และ 402
  src/pages/BookingResult.jsx      UI-07-03 แสดงหมายเลขงาน สถานะ และยอดมัดจำที่ชำระ
  src/__tests__/AC-07-04.test.jsx  test หน้าจอของ AC-07-04
  src/__tests__/AC-07-06.test.jsx  test หน้าจอของ AC-07-06 (CR-03 ปิด F-04)
  src/__tests__/AC-07-11.test.jsx  test หน้าจอของ AC-07-11 (CR-03)
  src/__tests__/UI-07-01.test.jsx, UI-07-02.test.jsx, UI-07-03.test.jsx  ตรวจรายการ "ต้องตรง" ของแต่ละหน้า (CR-03)
```

## 3. โมเดลข้อมูล

| ตาราง | ฟิลด์หลัก | รองรับ |
|---|---|---|
| customers | id, name, phone (PII) | REQ-PRV-002 |
| service_addresses | id, customer_id, text, lat, lng | AS-03, BR-03 |
| technicians | id, name, skills (คั่นด้วยจุลภาค), base_lat, base_lng | BR-03 |
| time_slots | id, technician_id, start, end, state (ว่าง / ล็อกชั่วคราว / จองแล้ว), held_by_customer_id, hold_expires_at | REQ-FN-041, BR-02, AS-07 |
| jobs | id, customer_id, technician_id, slot_id, address_id, category, status (8 ค่า), deposit_amount, scheduled_start, created_at | REQ-FN-008, REQ-DAT-002 |
| job_status_history | id, job_id, from_status, to_status, at | REQ-DAT-002 (ประวัติ 24 เดือน) |
| payments | id, job_id, amount, gateway_ref, result (สำเร็จ / ล้มเหลว / หมดเวลา), authorized_at | REQ-IF-001 |
| refunds | id, job_id, amount, rule (R1..R6) | REQ-BR-001 |

- ตาราง log ไม่มี ระบบใช้ logging ของ Python ผ่าน privacy.py ที่กรองรูปแบบเบอร์โทรออก (REQ-PRV-002)
- status ของ jobs ใช้ชื่อในโค้ดจาก glossary.md เท่านั้น (pending_payment, confirmed, auto_cancelled, rematching, en_route, in_progress, done, cancelled)

## 4. API / หน้าจอ

| รายการ | input / output หลัก | รองรับ |
|---|---|---|
| GET /technicians | in: category, address_id, customer_id / out: ช่างและช่วงเวลาที่ว่างใน 7 วัน (ไม่รวมช่วงที่จองแล้วหรือล็อกโดยคนอื่น) | REQ-FN-008, BR-02, BR-03, AS-06 |
| POST /slots/{slot_id}/hold | in: customer_id / out: hold_expires_at หรือ 409 ถ้าถูกล็อกโดยคนอื่น | REQ-FN-041 |
| GET /deposit-quote (CR-03) | in: category / out: {category, deposit_amount} จาก config.DEPOSIT_BY_CATEGORY ปัดขึ้นหลักสิบ หรือ 422 ถ้าประเภทงานไม่อยู่ในตาราง (AS-10) | REQ-BR-002, AC-07-11 |
| POST /bookings | in: customer_id, slot_id, address_id, category / out: 201 job (confirmed) หรือ 409 {reason: slot_taken, alternatives[]} หรือ 402 {reason: payment_failed} หรือ 422 ประเภทงานไม่อยู่ในตาราง (CR-03) | REQ-FN-008, REQ-IF-001, REQ-IF-005, REQ-BR-002, AC-07-04 |
| GET /jobs/{id} | out: งานและสถานะ (มุมมองลูกค้า) | REQ-FN-008 |
| GET /jobs/{id}/technician-view | in: technician_id, now / out: งาน; ฟิลด์ customer_phone มีเฉพาะเมื่ออยู่ในช่วง 2 ชั่วโมงก่อนนัดจนปิดงาน | REQ-SEC-004 |
| POST /jobs/{id}/cancel | in: cancelled_by (customer / system), now / out: สถานะใหม่ และ refund ถ้ามี หรือ 409 (R3 ชั่วคราว, R6) | REQ-BR-001 |
| GET /notifications/queue | out: ข้อความในคิว (ใช้ตรวจใน test และหน้าแอดมิน) | REQ-FN-012 |
| หน้าเลือกช่าง TechnicianPicker (UI-07-01, mockups/UI-07-01-pick-technician.html) | เรียก GET /technicians แล้ว POST /slots/{id}/hold แล้ว GET /deposit-quote ส่งยอดมัดจำและเวลาสิ้นสุดการล็อกไปหน้ายืนยัน (D-07-05) | REQ-FN-008, REQ-FN-041, REQ-BR-002 |
| หน้ายืนยัน ConfirmBooking (UI-07-02, mockups/UI-07-02-confirm.html) | แสดงยอดมัดจำที่รับมา เวลาสิ้นสุดการล็อก และเงื่อนไข BR-01 แล้ว POST /bookings ถ้าได้ 409 แสดง "ช่วงเวลาถูกจองแล้ว" และปุ่มช่วงใกล้เคียง ถ้าได้ 402 แสดง "ชำระมัดจำไม่สำเร็จ" | AC-07-04, AC-07-06, AC-07-11 |
| หน้าผลการจอง BookingResult (UI-07-03, mockups/UI-07-03-result.html) | แสดงหมายเลขงาน สถานะเป็นคำไทยตาม glossary และยอดมัดจำที่ชำระ | REQ-FN-008, REQ-FN-012, REQ-BR-002 |

สิ่งที่ mockup ร่างแรกมีแต่ spec ไม่ได้สั่ง ไม่อยู่ในตารางนี้ ไปอยู่ข้อ 8: ราคาประเมิน (Q-26) รูปแบบหมายเลขงาน (Q-27) เข้าคิวรอ (Q-28) เลือกที่อยู่ (Q-29)

## 5. ตารางตรวจ Constraints

| Constraint ID | ถูกนำไปใช้ที่ไหนใน plan | สถานะ |
|---|---|---|
| REQ-CON-003 | ข้อ 2: gateway รายเดิมอยู่หลัง interface `Gateway` ไม่เปลี่ยนราย | ใช้แล้ว |
| REQ-CON-001 | ข้อ 7: ลำดับงานตัด A2 ออก (D-07-02) ให้พอ 8 สัปดาห์ | ใช้แล้ว |
| REQ-PRV-002 | ข้อ 3: ไม่มีตาราง log ที่เก็บเบอร์ และ privacy.py กรอง log | ใช้แล้ว |
| REQ-SEC-004 | ข้อ 4: GET /jobs/{id}/technician-view ซ่อนเบอร์จนก่อนนัด 2 ชั่วโมง | ใช้แล้ว |
| REQ-IF-001 | ข้อ 4: POST /bookings authorize ก่อน capture | ใช้แล้ว |
| REQ-IF-005 | payments/service.py: timeout แล้ว status-inquiry ด้วย ref เดิม | ใช้แล้ว (ค่า timeout ชั่วคราว 30 วินาที รอ Q-19) |
| REQ-DAT-002 | ข้อ 3: jobs.status 8 ค่า + job_status_history | ใช้แล้ว |
| REQ-BR-002 (CR-03) | ข้อ 4: GET /deposit-quote และ POST /bookings ใช้ deposit_for ตัวเดียวกัน | ใช้แล้ว |

Constraint กลางจาก specs/000-shared/constraints.md รุ่น 1.0 (CR-04) REQ-CON-001, REQ-CON-003, REQ-PRV-002 อยู่ในตารางข้างบนแล้ว ที่เหลือคือการตัดสินใจทางเทคนิค

| Constraint ID | ถูกนำไปใช้ที่ไหนใน plan | สถานะ |
|---|---|---|
| D-00-01 | ข้อ 2: หลังบ้าน Python + FastAPI | ใช้แล้ว |
| D-00-02 | ข้อ 2 และข้อ 3: SQLAlchemy ต่อผ่าน DATABASE_URL ที่เดียว | ใช้แล้ว |
| D-00-03 | ข้อ 2: หน้าจอ React + Tailwind เรียกหลังบ้านผ่าน api/client.js | ใช้แล้ว |
| D-00-04 | ข้อ 6: ชื่อ test ตาม AC และ UI | ใช้แล้ว |
| D-00-05 | ข้อ 4: ยอดมัดจำและเวลาสิ้นสุดการล็อกมาจาก API ตัวเลขอยู่ใน config.py | ใช้แล้ว (T-12, T-13) |

ข้อเสนอ Constraint กลางรุ่น 1.1 (specs/000-shared/constraints.md ส่วน 6, CR-07 สถานะ Proposed) เพิ่มแถวไว้ให้ Impact Analysis มองเห็น ยังไม่มี task โค้ด หรือ test จนกว่า CR-07 จะอนุมัติ (เพิ่มในรอบ Failure Day ไม่ได้รัน /plan ใหม่)
plan v3: CR-07 อนุมัติแล้ว (24 ต.ค. 2569) คอลัมน์กลางคงข้อความที่เขียนตอนเป็นข้อเสนอ คอลัมน์สถานะบอกว่าใช้จริงที่ไหน แถวที่ทำจริงต่างจากที่คาดไว้ บอกไว้ในช่องสถานะ รายละเอียดอยู่ในข้อ 9

| Constraint ID | ถ้าอนุมัติ จะใช้ที่ไหนใน plan | สถานะ |
|---|---|---|
| REQ-OP-001 | SLO ค้นหาคือ REQ-QA-003 แถวข้างบน (AC-07-08 รอ CR-02) ส่วนเวลาล่มต่อเดือนต้องมี endpoint /health ใหม่ใน main.py และระบบเฝ้าดูนอกโค้ด | ใช้แล้ว (T-24 /health และ /ready ใน app/ops/router.py ไม่ใช่ main.py) |
| REQ-OP-005 | ตัวนับคำขอ เวลาตอบ และคำขอล้มเหลวต่อ endpoint เป็น middleware ใหม่ใน main.py การแจ้งคนเวรใช้คิวแจ้งเตือนเดิม (notify/queue.py) log ผ่าน privacy.py อยู่แล้ว | ใช้แล้ว (T-24 middleware ใน main.py ตัวนับ app/ops/metrics.py การแจ้งคนเวรใช้ Pager ใน app/ops/alerts.py ไม่ใช้คิวแจ้งเตือนของลูกค้า log เป็น log_event) |
| REQ-OP-006 | เหตุ "gateway ไม่ตอบเกิน 5 นาที" และ "ไม่มีช่างว่าง" เกิดที่ POST /bookings และ GET /technicians ของ feature นี้ คู่มืออยู่ที่ docs/srs/operations.md ไม่มีโค้ด | ใช้แล้ว (T-25 docs/srs/operations.md ฉบับใช้จริง) |
| REQ-OP-007 | ฐานข้อมูลที่สำรองคือฐานข้อมูลของทั้งโครงการ (D-00-02) ไม่มีโค้ดใน feature แต่การซ้อมกู้คืนต้องนับการจองของ feature นี้ที่หายไป | ใช้แล้ว (T-23 app/ops/backup.py และ backend/ops_backup.py) |
| REQ-QA-010 | payments/service.py (timeout และ reference เดิมมีแล้วตาม REQ-IF-005 ต้องเพิ่มพฤติกรรม "รอชำระเงิน" คงล็อก 10 นาทีแทน auto_cancelled ทันที ซึ่งเปลี่ยน AC-07-05 จึงต้องมี CR แก้ AC) notify/queue.py (timeout และส่งซ้ำ) IF-03 ยังไม่เรียกจริงใน R1 | ใช้แล้ว (T-18) ไม่ต้องแก้ AC-07-05 เพราะประชุมตีความ "ไม่ตอบ" = ไม่ตอบทั้ง authorize และ status-inquiry (CR-07 ข้อ ข5) เพิ่ม AC-07-12, AC-07-13 แทน notify/queue.py ทำใน T-08 และ T-10 ของ 003 |
| REQ-SEC-010 | GET /jobs/{id}, GET /jobs/{id}/technician-view และ POST /jobs/{id}/cancel ในข้อ 4 ยังไม่ตรวจว่าผู้ส่งเป็นเจ้าของหรือผู้รับมอบหมาย ต้องเพิ่มการตรวจและบันทึกความพยายามใน booking/router.py และ refund/router.py (รหัสตอบ 403 หรือ 404 รอ Q-47) | ใช้แล้ว (T-20 technician-view ตอบ 403 และบันทึก, T-21 ปิด POST /jobs/{id}/cancel แทนการเพิ่มการตรวจ) GET /jobs/{id} ยังไม่ตรวจ รอ UC-02 (GAP-24) |
| REQ-SEC-011 | POST /slots/{slot_id}/hold ใน booking/service.py ต้องตรวจว่าลูกค้าคนนี้ถือล็อกที่ยังไม่หมดอายุอยู่หรือไม่ก่อนล็อกช่วงใหม่ ค่า 1 ช่วงอยู่ใน config.py (D-00-05, Q-45) | ใช้แล้ว (T-19 HOLD_LIMIT_PER_CUSTOMER = 1) |
| REQ-PRV-010 | ตาราง customers และ service_addresses (ข้อ 3) เป็นที่เก็บเบอร์ ที่อยู่ พิกัด ต้องมี endpoint คำขอลบใหม่ และ job_status_history กับ jobs ต้องอ้างลูกค้าด้วย id อยู่แล้ว (ไม่มีชื่อในตาราง) ส่วนส่งคำขอลบไป IF-02 ใช้คิวเดิม | ใช้แล้ว (T-22 โมดูลใหม่ app/erasure/ endpoint ของ ops ไม่ใช่ของลูกค้า และส่งคำขอลบไป IF-02 ผ่าน Notifier ไม่ใช่คิวข้อความ) |
| REQ-CMP-001 | ไม่มีโค้ด แต่ REQ-PRV-002 (ใช้แล้วใน T-01, T-08) และ REQ-PRV-010 ของ feature นี้ต้องมีบรรทัด "ผลการตรวจโดยฝ่ายกฎหมาย" ตอนนี้คือ "รอการตรวจ" | ใช้แล้ว (SH-05 ตรวจแล้ว EV-045) |
| REQ-SEC-012 (เพิ่มในประชุม EV-045) | ข้อ 4: ปิด /docs /redoc /openapi.json ในโหมด production /notifications/queue และ /metrics ใช้ X-Ops-Token ช่อง now= ใช้ได้เฉพาะโหมด test (clock.py) และบัญชี endpoint ใน operations.md | ใช้แล้ว (T-24, T-25) |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC ID | ชื่อ test | ทดสอบอย่างไร |
|---|---|---|
| AC-07-01 | test_AC_07_01_booking_success | ล็อก slot, POST /bookings กับ FakeGateway approved แล้วตรวจ job confirmed, slot จองแล้ว, payment 1 รายการ |
| AC-07-02 | test_AC_07_02_slot_not_rebookable | ทำให้ slot จองแล้ว แล้ว GET /technicians ด้วยลูกค้าอื่น ตรวจว่าไม่มี slot นั้น |
| AC-07-03 | test_AC_07_03_notify_both_within_60s | หลังจองสำเร็จ อ่านคิว ตรวจว่ามีข้อความถึงลูกค้าและช่าง และ due_at ไม่เกิน created_at + 60 วินาที |
| AC-07-04 | test_AC_07_04_no_charge_when_slot_taken | ลูกค้าอื่นจองก่อน แล้วสมชายยืนยัน ตรวจ 409, ไม่มี payment ของสมชาย, alternatives อย่างน้อย 2 และห่างไม่เกิน 3 ชั่วโมง |
| AC-07-05 | test_AC_07_05_payment_timeout | FakeGateway ไม่ตอบ และ inquiry ตอบ unknown ตรวจ job auto_cancelled, slot ว่าง, ไม่มี payment สำเร็จ |
| AC-07-06 | test_AC_07_06_payment_declined | FakeGateway declined ตรวจ 402, job auto_cancelled, slot ว่าง, มีข้อความแจ้งลูกค้า |
| AC-07-07 | test_AC_07_07_inquiry_approved_no_double_charge | FakeGateway ไม่ตอบ แต่ inquiry ตอบ approved ตรวจ job confirmed, authorize ถูกเรียก 1 ครั้ง, payment สำเร็จ 1 รายการ |
| AC-07-08 | test_AC_07_08_search_under_load_scaled | ยิง GET /technicians 20 คำขอพร้อมกัน (ย่อจาก 500) ตรวจว่า 19 ใน 20 ไม่เกิน 2 วินาที ผลจริงต้องวัดบนเครื่องทดสอบ (รอ CR-02) |
| AC-07-09 | test_AC_07_09_phone_hidden_until_2h | technician-view ที่ now = 11:30 ไม่มี customer_phone, ที่ 12:00 มี และ log ที่จับได้ไม่มีเบอร์ |
| AC-07-10 | test_AC_07_10_refund_R1 ถึง R6 (parametrize) | ตั้งสถานะงานตามแถว แล้ว POST /jobs/{id}/cancel ตรวจสถานะและยอดคืน R3 ข้ามด้วยเหตุผล "รอ Q-14" |
| AC-07-04 (หน้าจอ) | AC-07-04.test.jsx | API จำลองตอบ 409 พร้อม alternatives 2 ช่วง ตรวจว่าหน้าจอแสดง "ช่วงเวลาถูกจองแล้ว" และปุ่ม 2 ปุ่ม |
| AC-07-11 | test_AC_07_11_deposit_shown_equals_charged (3 ประเภทงาน), test_AC_07_11_unknown_category_has_no_guessed_deposit | ขอยอดจาก GET /deposit-quote แล้วจองจริง ตรวจว่า Payment.amount เท่ากับยอดที่แสดง และประเภทงานนอกตารางได้ 422 ไม่มีการเรียก gateway |
| AC-07-11 (หน้าจอ) | AC-07-11.test.jsx | ส่งยอด 370 บาทเข้าไป (ไม่ตรงตารางจริง) ตรวจว่าหน้าจอแสดง 370 ทั้งในรายละเอียดและบนปุ่ม และถ้าไม่มียอด ปุ่มกดไม่ได้ |
| AC-07-06 (หน้าจอ) | AC-07-06.test.jsx | API จำลองตอบ 402 ตรวจว่าหน้าจอแสดง "ชำระมัดจำไม่สำเร็จ" และ "ยังไม่มีการตัดเงิน" |
| UI-07-01, UI-07-02, UI-07-03 | UI-07-01.test.jsx, UI-07-02.test.jsx, UI-07-03.test.jsx | ตรวจรายการ "ต้องตรง" ของแต่ละหน้าตาม spec ส่วน 12 |

หลักแยก: AC ที่ Then บอกว่า "บันทึก" หรือ "สถานะ" ตรวจที่หลังบ้าน AC ที่ Then บอกว่า "แจ้ง" หรือ "เสนอ" ต้องมี test หน้าจอด้วย

## 7. ลำดับงาน

ไม่มีงานของ A2 (จองแทนลูกค้าโดย call center) ในลำดับนี้ ตัดออกตาม D-07-02 เพื่อให้ทัน 8 สัปดาห์ (REQ-CON-001)

หลังบ้าน
1. ตั้งฐานข้อมูลและตาราง (REQ-DAT-002, REQ-PRV-002)
2. ล็อกช่วงเวลาและหมดอายุ (REQ-FN-041, AS-07)
3. ค้นช่างว่าง (REQ-FN-008, BR-02, BR-03, AC-07-02)
4. POST /bookings สร้างงานและตัดมัดจำ (REQ-FN-008, REQ-IF-001, AC-07-01, AC-07-04)
5. timeout และ status-inquiry (REQ-IF-005, AC-07-05, 06, 07)
6. คืนมัดจำตาม BR-01 (REQ-BR-001, AC-07-10)
7. คิวแจ้งเตือน (REQ-FN-012, AC-07-03)
8. มุมมองช่างซ่อนเบอร์ และตัวกรอง log (REQ-SEC-004, REQ-PRV-002, AC-07-09)
9. test ย่อส่วนรับโหลด (REQ-QA-003, AC-07-08)

หน้าจอ (ใช้ API จำลองตามสัญญาข้อ 4 จึงเริ่มพร้อมหลังบ้านได้)
10. หน้าเลือกช่าง หน้ายืนยัน หน้าผล (REQ-FN-008, AC-07-04 หน้าจอ)
11. ต่อหน้าจอกับ API จริง ทำหลังข้อ 3, 4, 5 และ 10

รอบสอง ตาม CR-03 (plan v2)
12. ยอดมัดจำที่เดียว และ GET /deposit-quote (REQ-BR-002, AC-07-11)
13. หน้ายืนยันตาม UI-07-02 (AC-07-11, AC-07-04, AC-07-06 ส่วนหน้าจอ)
14. หน้าเลือกช่างตาม UI-07-01
15. หน้าผลการจองตาม UI-07-03
16. รัน test ทั้งชุด และตรวจหน้าจอจริงเทียบ mockup ด้วยคน

## 8. สิ่งที่ยังไม่ทำ

- Q-14 (BR-01 R3) ยังไม่มีคำตอบ ข้อ 6 ทำได้เฉพาะ R1, R2, R4, R5, R6 ส่วน R3 ใช้พฤติกรรมชั่วคราว "ไม่อนุญาต" ตาม spec ข้อ 9 (D-07-04)
- Q-18 และ Q-19 เป็น config พร้อมค่าชั่วคราว ถ้าคำตอบมาต่างจากนี้ แก้ config ไม่ต้องแก้โค้ด
- AC-07-08 ฉบับวัดได้รอ CR-02 test ที่เขียนเป็นฉบับทดลองย่อส่วน
- A2 จองแทนโดย call center ไม่ทำใน R1 (D-07-02)
- Q-26 ราคาประเมิน: หน้ายืนยันยังไม่แสดงราคาประเมิน แสดงเฉพาะยอดมัดจำ
- Q-27 รูปแบบหมายเลขงาน: แสดง # ตามด้วยเลขงาน
- Q-28 UC-07 A1: แสดงข้อความว่ายังไม่มีช่างว่างอย่างเดียว ไม่มีปุ่มเข้าคิวรอ
- Q-29 เลือกที่อยู่ให้บริการ: หน้าจอยังใช้ที่อยู่หลักของลูกค้า ไม่มีส่วนให้เลือก

## 9. ปรับตาม CR-07 (plan v3, 24 ต.ค. 2569)

ข้อนี้เพิ่มใหม่ ข้อ 1 ถึง 8 ไม่แก้ เพื่อให้เห็นว่าแผนเดิมคืออะไรและ CR-07 เพิ่มอะไร

### 9.1 โมเดลข้อมูลที่เพิ่ม (migration m002_cr07.py)
- customers.erased_at (เวลาที่ลบเบอร์ ชื่อ ที่อยู่ พิกัด) REQ-PRV-010
- ตาราง security_events (kind = denied หรือ phone_revealed, actor_role, actor_id, job_id, endpoint, at) REQ-SEC-010 ไม่มีคอลัมน์เบอร์หรือชื่อ
- ตาราง erasure_requests (customer_id, requested_at, due_at = requested_at + 30 วัน, completed_at, if02_sent_at, if02_result) REQ-PRV-010
- payments.result เพิ่มค่า pending (gateway ไม่ตอบเลย) REQ-QA-010
- ทะเบียนคำขอลบนอกฐานข้อมูล (ไฟล์ ERASURE_LEDGER_PATH) ใช้ลบซ้ำหลังกู้คืน REQ-PRV-010 บรรทัดที่ 4

### 9.2 API ที่เปลี่ยน
| รายการ | เปลี่ยนอย่างไร | รองรับ |
|---|---|---|
| POST /slots/{slot_id}/hold | เพิ่มคำตอบ 409 {reason: hold_limit, message, held[]} เมื่อถือล็อกช่วงอื่นอยู่ | REQ-SEC-011, AC-07-14 |
| POST /bookings | เพิ่มคำตอบ 202 {reason: payment_pending, job_id, hold_expires_at, message} เมื่อ gateway ไม่ตอบเลย กดซ้ำใช้งานเดิมและ reference เดิม | REQ-QA-010, AC-07-12, AC-07-13 |
| GET /jobs/{id}/technician-view | ไม่ใช่งานของช่างหรือไม่มีงาน ตอบ 403 เหมือนกัน (เดิม 404) และบันทึก ส่งเบอร์เมื่อไรบันทึกทุกครั้ง | REQ-SEC-010, AC-07-15 |
| POST /jobs/{id}/cancel | ปิด (ลบ app/refund/router.py) การยกเลิกโดยลูกค้าใช้ customer-cancel ของ 004 | REQ-SEC-010, REQ-SEC-012, AC-07-16 |
| POST /ops/erasure-requests, GET /ops/erasure-requests/{id} | ใหม่ ใช้โดย call center ในนามลูกค้า ต้องมี X-Ops-Token ในโหมด production | REQ-PRV-010, AC-07-17 |
| GET /health, GET /ready, GET /metrics | ใหม่ (/health เดิมย้ายไป app/ops/router.py) | REQ-OP-001, REQ-OP-005, AC-00-01, AC-00-04 |
| GET /notifications/queue | ในโหมด production ต้องมี X-Ops-Token | REQ-SEC-012, AC-00-06 |
| หน้าเลือกช่าง UI-07-01 | ได้ 409 hold_limit แสดงข้อความที่ระบบส่งมา | AC-07-14 (หน้าจอ) |
| หน้ายืนยัน UI-07-02 | ได้ 202 payment_pending แสดงข้อความที่ระบบส่งมา ปุ่มยืนยันยังกดได้ | AC-07-12 (หน้าจอ) |

### 9.3 แผนทดสอบที่เพิ่ม
| AC | test | ตรวจอย่างไร |
|---|---|---|
| AC-07-12 | test_AC_07_12_gateway_unreachable_keeps_hold_as_pending, AC-07-12.test.jsx | FakeGateway(mode=timeout, inquiry_answer=timeout) ตรวจ 202 สถานะงาน ล็อก payment pending แล้วเลื่อนเวลา 10 นาที |
| AC-07-13 | test_AC_07_13_retry_uses_same_reference_no_double_charge, AC-07-12.test.jsx | นับ authorize 1 ครั้ง reference เดียว งาน 1 งาน payment success 1 แถว |
| AC-07-14 | test_AC_07_14_second_hold_rejected, AC-07-14.test.jsx | ล็อกสองช่วงติดกัน ได้ 409 และ time_slots 1 แถว |
| AC-07-15 | test_AC_07_15_technician_view_other_job_forbidden_and_logged | 403 สองกรณีคำตอบเหมือนกัน security_events 2 แถว และ phone_revealed 1 แถว |
| AC-07-16 | test_AC_07_16_legacy_cancel_endpoint_closed | POST /jobs/{id}/cancel ได้ 404 หรือ 405 และ /openapi.json ไม่มี path นี้ |
| AC-07-17 | test_AC_07_17_erasure_removes_phone_keeps_anonymous_history, test_AC_07_17_erasure_waits_for_active_job | ค้นเบอร์ในทุกตารางของ SQLite |
| AC-07-18 | test_AC_07_18_restore_does_not_bring_back_erased_data | สำรอง ลบ กู้คืนบนไฟล์ใหม่ ค้นเบอร์ |
| AC-00-01 ถึง AC-00-08 | backend/tests/test_cross_cutting.py | ดู specs/000-shared/cross-cutting.feature |

### 9.4 ลำดับงาน
T-17 (ตาราง) ก่อน T-18 ถึง T-23 ซึ่งทำคู่กันได้ T-24 (ops) ใช้ audit จาก T-20 T-25 (คู่มือ) หลัง T-21 และ T-24 เพราะต้องมีบัญชี endpoint ล่าสุด T-26 (หน้าจอ) หลัง T-18 และ T-19 T-27 (รันทั้งชุด) สุดท้าย

## 10. ปรับตาม CR-10 และ CR-02 (plan v4, 3 พ.ย. 2569)

ข้อนี้เพิ่มใหม่ ข้อ 1 ถึง 9 ไม่แก้ ร่างด้วย /plan จาก spec 1.6 (prompt-log.md #81)

### 10.1 ค่าใหม่ใน config.py (D-00-05 ค่าทุกตัวอยู่ที่เดียว)
- ESTIMATE_BY_CATEGORY (700, 800, 1000) และ DEPOSIT_PER_100_OF_ESTIMATE = 50 DEPOSIT_BY_CATEGORY คำนวณจากสองค่านี้ ยอดเท่าเดิม (Q-26)
- TRAVEL_FEE_BAHT = 100 (Q-14) REFUND_FOLLOWUP_BUSINESS_DAYS = 1 (Q-34) JOB_ISSUE_REPORT_DAYS = 7 (Q-31)
- PAGER_WEBHOOK_URL (ตัวแปรแวดล้อม) และ PAGER_TIMEOUT_SECONDS = 5 (GAP-28) ใช้ httpx ที่มีอยู่แล้วใน requirements.txt ไม่เพิ่ม library

### 10.2 API ที่เปลี่ยน
| รายการ | เปลี่ยนอย่างไร | รองรับ |
|---|---|---|
| GET /deposit-quote | เพิ่ม estimate_amount และ estimate_note ในคำตอบ ยอดมัดจำมาจากฟังก์ชันเดิม | REQ-FN-057, REQ-BR-002, AC-07-19 |
| หน้ายืนยัน UI-07-02 | แสดงราคาประเมินและข้อความกำกับจากคำตอบ บรรทัดที่ 3 ของเงื่อนไขการยกเลิกตาม BR-01 R3 รุ่น 1.1 | REQ-FN-057, REQ-BR-001 |
| refund/rules.py (BR-01 R3) | R3 เป็น cancelled ยอด = มัดจำ ลบ TRAVEL_FEE_BAHT ไม่ต่ำกว่า 0 (ของ 004 ใช้ตัวเดียวกัน) | REQ-BR-001, AC-07-10 |
| ops/alerts.py Pager | ส่ง HTTPS POST ไป PAGER_WEBHOOK_URL ส่งไม่ถึงให้ส่งใหม่นาทีถัดไป | REQ-OP-005 บรรทัดที่ 2 (GAP-28) |

### 10.3 แผนทดสอบที่เพิ่ม
| AC | test | ตรวจอย่างไร |
|---|---|---|
| AC-07-08 (ฉบับ CR-02) | test_AC_07_08_search_under_load_scaled (เดิม ย่อส่วน 20) และการยิงโหลด 500 คำขอบนเครื่องทดสอบตอนตรวจรับ | test ย่อส่วนไม่เปลี่ยน ผลตรวจรับมาจากการยิงโหลดจริง ไม่ใช่ pytest |
| AC-07-10 แถว R3 | test_AC_07_10_refund_R3 (เอา skip ออก) | ยอดคืน 250 |
| AC-07-19 | test_AC_07_19_estimate_and_deposit_from_same_table, AC-07-19.test.jsx | 3 ประเภทงาน |
| AC-00-02 (ช่องทางจริง) | test_AC_00_02_webhook_pager_reaches_on_call, test_AC_00_02_webhook_pager_retries_next_minute_when_service_fails | เครื่องรับ HTTP ในเครื่อง ใช้ Pager ตัวจริง |

### 10.4 ลำดับงาน
T-28 (config และ deposit-quote) ก่อน T-29 (หน้าจอ) T-30 (BR-01 R3 ใช้ร่วมกับ 004) และ T-31 (Pager) ทำคู่กันได้ รันทั้งชุดหลังทุก task ของ CR-10 (T-14 ของ 004)

## 11. ปรับตาม CR-11, CR-08, CR-12, CR-13 (plan v5, 23 พ.ย. 2569)

ข้อความสั่งในแชต ไม่ได้รัน /plan ใหม่ทั้งไฟล์ (prompt-log.md #91) ข้อ 1 ถึง 10 ไม่แก้
- CR-11: ทุก endpoint ของ feature นี้รับลูกค้าหรือช่างจาก backend/app/auth/deps.py ที่อยู่ของการค้นหาและการจองต้องเป็นของลูกค้าคนนั้น GET /jobs/{id} ใช้ audit.job_for_reader (แผนเต็มอยู่ใน specs/006-identity/plan.md)
- CR-08: ช่างคนเดิมอยู่ใน backend/app/matching/ (ใช้การค้นช่วงเวลาและ slot_visible_to เดิม) GET /me/past-technicians, GET /me/past-technicians/{id}/slots, GET /contact
- CR-12: _finish_payment และ settle_on_hold_expiry เรียก matching.offer เมื่อยืนยันงาน (แผนเต็มอยู่ใน specs/007-accept-rematch/plan.md)
- CR-13: คิวข้อความย้ายไปตาราง notification_messages ผู้เรียก enqueue ส่ง db เข้าไป งานเบื้องหลังผ่าน ops/lease.py ตัวนับรวมผ่าน ops/metrics.py ตัวเริ่มหลังบ้าน ops/serve.py การค้นหารวมคำค้นช่วงเวลาเป็นคำค้นเดียว index ใน m004
- ตารางตรวจ Constraints ข้อ 5 เพิ่ม: REQ-SEC-013 ไม่เกี่ยวกับ feature นี้ เพราะ OTP อยู่ใน 006 | REQ-SEC-014 ใช้แล้ว (ทุก router) | REQ-PRV-011 ใช้แล้ว (พิกัดใช้ใน distance_km เท่านั้น ไม่ส่งกลับ) | REQ-OP-008 ใช้แล้ว (T-37)
