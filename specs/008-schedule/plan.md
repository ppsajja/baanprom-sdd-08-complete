# Plan: ช่างจัดตารางเวลาว่างและวันหยุด (UC-04)

อ้างอิง: spec.md SPEC-SCHEDULE 1.0 | Updated: 2569-12-10 | สร้างด้วย /plan แล้วทีมตรวจ (plan v1, prompt-log.md #97)
อ้างอิง Constraint กลาง: specs/000-shared/constraints.md รุ่น 1.4 (D-00-01 ถึง D-00-05 ใช้ตาม ไม่ถามซ้ำ)

## 1. สรุปแนวทาง

- โมดูลใหม่ backend/app/schedule/ (service.py กฎ BR-10 ทั้งหมด router.py endpoint) ตารางใหม่ technician_days_off (m005)
- ค่าใหม่ของ TimeSlot.state คือ closed ทุกทางที่อ่านช่วงเวลาใช้ฟังก์ชันเดียว technicians/service.unavailable (ค้นหา ช่วงใกล้เคียง ล็อก จอง ช่างคนเดิม) ส่วนการจับคู่และการเลื่อนนัดเลือกเฉพาะ state = free อยู่แล้ว
- หน้าจอใหม่ TechnicianSchedule.jsx (UI-04-01) เมนู "ตารางเวลา" ของช่าง

## 2. เทคโนโลยีที่ใช้

ไม่มีเทคโนโลยีใหม่ ใช้ D-00-01 ถึง D-00-05

### โครงไฟล์ (เฉพาะที่ feature นี้เพิ่มหรือแตะ)

```
backend/app/schedule/__init__.py, service.py, router.py     ใหม่
backend/app/db/models.py, db/migrations/m005_r2b.py         SLOT_CLOSED TechnicianDayOff (แก้ models.py เพิ่มท้ายไฟล์)
backend/app/technicians/service.py, booking/service.py      unavailable() รวมช่วงที่ปิด (แก้)
backend/app/config.py                                       ค่าของ BR-10 (แก้ เพิ่มท้ายไฟล์)
backend/app/main.py                                         include router (แก้)
backend/tests/test_schedule.py                              ใหม่
frontend/src/pages/TechnicianSchedule.jsx, api/client.js, App.jsx   ใหม่และแก้
frontend/src/__tests__/UI-04-01.test.jsx                     ใหม่
```

## 3. โมเดลข้อมูล

technician_days_off(id, technician_id, day, created_at, closed_slot_ids) ใหม่ | time_slots.state ได้ค่า closed (ไม่แก้โครงตาราง)

## 4. API / หน้าจอ

| method path | ผู้เรียก | ตอบ |
|---|---|---|
| GET /me/schedule | ช่าง (token) | 200 days[] rules |
| POST /me/slots {start} | ช่าง | 201 slot (reopened) | 409 overlap day_off | 422 not_on_hour outside_hours too_soon too_far |
| POST /me/slots/{id}/close | ช่าง | 200 | 403 ไม่ใช่ช่วงของตัวเอง (บันทึก) | 409 not_free |
| POST /me/days-off {day} | ช่าง | 201 closed_slots | 409 has_jobs already_day_off | 422 past_day |
| DELETE /me/days-off/{day} | ช่าง | 200 reopened_slots | 404 not_day_off |

## 5. ตารางตรวจ Constraints

| ID | ใช้อย่างไรใน feature นี้ |
|---|---|
| REQ-CON-001 | ไม่เกี่ยวกับ feature นี้ เพราะเป็นข้อจำกัดเวลาของ R1 R2 ใช้งวดของ TOR |
| REQ-CON-003 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีการเงิน |
| REQ-PRV-002 | ใช้แล้ว log มีแค่รหัสช่างและรหัสช่วง มุมมองตารางไม่มีชื่อลูกค้า |
| REQ-OP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี SLO ของตัวเอง |
| REQ-OP-005 | ใช้แล้ว endpoint ใหม่ถูกนับโดย middleware เดิม |
| REQ-OP-006 | ใช้แล้ว คู่มือเหตุการณ์ที่ 3 (ไม่มีช่างว่าง) เพิ่มขั้นให้หัวหน้าช่างโทรถามช่างให้เปิดตาราง |
| REQ-OP-007 | ไม่เกี่ยวกับ feature นี้ เพราะตารางใหม่อยู่ในสำเนาเดิม |
| REQ-OP-008 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีข้อความหรืองานเบื้องหลัง |
| REQ-OP-009 | ไม่เกี่ยวกับ feature นี้ เพราะไม่เรียกระบบภายนอก |
| REQ-QA-010 | ไม่เกี่ยวกับ feature นี้ เพราะไม่เรียกระบบภายนอก |
| REQ-SEC-010 | ใช้แล้ว ช่วงของช่างคนอื่นตอบ 403 และบันทึกผ่าน audit.deny |
| REQ-SEC-011 | ใช้แล้ว ช่วงที่ลูกค้าล็อกอยู่ปิดไม่ได้ (BR-10 ข้อ 5) เพดานการล็อกไม่เปลี่ยน |
| REQ-SEC-012 | ใช้แล้ว endpoint ใหม่อยู่ในบัญชี endpoint |
| REQ-SEC-013 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี OTP |
| REQ-SEC-014 | ใช้แล้ว ช่างมาจาก token (path เป็น /me) |
| REQ-SEC-015 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีบทบาทเจ้าหน้าที่ |
| REQ-PRV-010 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีข้อมูลลูกค้าใหม่ |
| REQ-PRV-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ใช้พิกัดลูกค้า |
| REQ-IF-012 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีระบบภายนอก |
| REQ-CMP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี REQ-PRV ใหม่ |
| REQ-AI-021, REQ-AI-022 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี AI |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC | test |
|---|---|
| AC-04-01 ถึง AC-04-08 | backend/tests/test_schedule.py::test_AC_04_0n | หน้าจอ UI-04-01.test.jsx (AC-04-01 AC-04-06 และรายการต้องตรง) |

## 7. ลำดับงาน

T-01 ตารางและสถานะ closed | T-02 เพิ่มและปิดช่วง | T-03 ทุกทางที่อ่านช่วงเวลาไม่เห็นช่วงที่ปิด | T-04 วันหยุด | T-05 หน้าจอ

## 8. สิ่งที่ยังไม่ทำ

ตารางซ้ำทุกสัปดาห์ | หัวหน้าช่างแก้แทน (Non-goals)
