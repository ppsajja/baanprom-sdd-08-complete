# Plan: ช่างรับหรือปฏิเสธงาน (UC-12) และจับคู่ช่างใหม่ (UC-05)

อ้างอิง: spec.md SPEC-ACCEPT-REMATCH 1.0 | Updated: 2569-11-23 | สร้างด้วย /plan แล้วทีมตรวจ (plan v1, prompt-log.md #91)
อ้างอิง Constraint กลาง: specs/000-shared/constraints.md รุ่น 1.3 (D-00-01 ถึง D-00-05 ใช้ตาม ไม่ถามซ้ำ)

## 1. สรุปแนวทาง

- โมดูลใหม่ backend/app/matching/ (service.py กฎ BR-07 ทั้งหมด router.py endpoint) ตารางใหม่ job_assignments
- จุดที่งานเป็น "ยืนยันแล้ว" (booking/service.py และ payments/service.py ตอนปิดเรื่องเงินที่ค้าง) เรียก matching.offer สร้างการมอบงาน
- ปฏิเสธใช้ set_status เดิม (ประวัติ REQ-DAT-002) และ cancel_job เดิมของ 004 สำหรับ R4 (D-12-04)
- งานเบื้องหลังทุก 1 นาที (ops/scheduler.py) เรียก matching.process_due: ไม่ตอบ 30 นาที จับคู่ซ้ำ ยกเลิกเมื่อครบ 2 ชั่วโมง
- หน้าจอ: ปุ่มใน TechnicianJobs.jsx (UI-09-01) และ MyJobs.jsx (UI-02-03 ของ 006)

## 2. เทคโนโลยีที่ใช้

ไม่มีเทคโนโลยีใหม่ ใช้ D-00-01 ถึง D-00-05 (FastAPI SQLAlchemy PostgreSQL React Vitest) รัน test ด้วยคำสั่งเดิมของโครงการ

### โครงไฟล์ (เฉพาะที่ feature นี้เพิ่มหรือแตะ)

```
backend/app/matching/__init__.py, service.py, router.py   ใหม่
backend/app/db/models.py                                  เพิ่ม JobAssignment (m004)
backend/app/booking/service.py, payments/service.py       เรียก offer ตอนยืนยัน
backend/app/jobstatus/service.py                          ออกเดินทาง = รับ รายการงาน (Q-32) responses ในมุมมองช่าง
backend/app/refund/rules.py, refund/service.py            R4 ปฏิเสธช่างแทน ไม่แจ้งช่างเดิมซ้ำ
backend/app/ops/audit.py, ops/scheduler.py                กันช่างที่ปฏิเสธแล้ว งานเบื้องหลัง
backend/tests/test_accept_rematch.py, test_job_status_cr12.py
frontend/src/pages/TechnicianJobs.jsx, api/client.js      ปุ่มรับและปฏิเสธ
frontend/src/__tests__/AC-12-01.test.jsx
```

## 3. โมเดลข้อมูล

job_assignments(id, job_id, technician_id, slot_id, via_rematch, offered_at, respond_by, response, responded_at, reason) ไม่แก้ตารางเดิม (D-12-02)

## 4. API / หน้าจอ

| method path | ผู้เรียก | ตอบ |
|---|---|---|
| POST /jobs/{id}/accept | ช่าง (token) | 200 มุมมองช่าง | 403 ไม่ใช่งานของช่าง | 409 not_pending / not_confirmed |
| POST /jobs/{id}/reject {reason?} | ช่าง (token) | 200 released | 403 | 409 |
| POST /jobs/{id}/decline-substitute | ลูกค้า (token) | 200 rule R4 refund_amount | 403 | 409 not_substitute / not_confirmed |
| GET /technicians/{id}/jobs (เดิม) | ช่าง | เพิ่ม responses และ assignment ในแต่ละงาน |
| GET /me/jobs (ของ 006) | ลูกค้า | substitute can_decline_substitute |

## 5. ตารางตรวจ Constraints

| ID | ใช้อย่างไรใน feature นี้ |
|---|---|
| REQ-CON-001 | ไม่เกี่ยวกับ feature นี้ เพราะเป็นข้อจำกัดเวลาของ R1 (8 สัปดาห์) R2 ใช้งวดของ TOR |
| REQ-CON-003 | ใช้แล้ว คืนเงิน R4 ผ่าน gateway รายเดิมด้วย cancel_job เดิม |
| REQ-PRV-002 | ใช้แล้ว log มีแค่รหัสงานและรหัสช่าง (log_event) |
| REQ-OP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี endpoint ที่มี SLO ของตัวเอง |
| REQ-OP-005 | ใช้แล้ว endpoint ใหม่ถูกนับโดย middleware เดิม |
| REQ-OP-006 | ใช้แล้ว operations.md เพิ่มคำสั่งดูงานที่ค้าง กำลังหาช่างใหม่ |
| REQ-OP-007 | ไม่เกี่ยวกับ feature นี้ เพราะตารางใหม่อยู่ในสำเนาสำรองเดิมอยู่แล้ว |
| REQ-OP-008 | ใช้แล้ว process_due อยู่ใน tick ที่ทำ process เดียว (CR-13) |
| REQ-QA-010 | ใช้แล้ว ข้อความทุกตัวผ่านคิวเดิม |
| REQ-SEC-010 | ใช้แล้ว audit.job_of_technician job_of_customer และกันช่างที่ปฏิเสธแล้ว |
| REQ-SEC-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ล็อกช่วงเวลา (จองช่วงใหม่ตรงในธุรกรรม) |
| REQ-SEC-012 | ใช้แล้ว endpoint ใหม่อยู่ในบัญชี endpoint |
| REQ-SEC-013 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี OTP |
| REQ-SEC-014 | ใช้แล้ว ช่างและลูกค้ามาจาก token |
| REQ-PRV-010 | ใช้แล้ว ไม่มีข้อมูลลูกค้าใหม่ reason เป็นข้อความของช่าง |
| REQ-PRV-011 | ไม่เกี่ยวกับ feature นี้ เพราะใช้พิกัดคำนวณระยะภายในเท่านั้น ไม่ส่งออก |
| REQ-CMP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี REQ-PRV หรือ CMP ใหม่ |
| REQ-AI-021, REQ-AI-022 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี AI (BR-07 เป็นกฎ) |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC | test |
|---|---|
| AC-12-01 ถึง AC-12-05 | backend/tests/test_accept_rematch.py::test_AC_12_0n | หน้าจอ AC-12-01.test.jsx |
| AC-05-01 ถึง AC-05-06 | test_accept_rematch.py::test_AC_05_0n | หน้าจอ AC-12-01.test.jsx (AC-05-01) UI-02-03.test.jsx (AC-05-04) |
| AC-09-16 | test_job_status_cr12.py |

## 7. ลำดับงาน

T-01 ตารางและ offer | T-02 รับ ปฏิเสธ (UC-12) | T-03 จับคู่ (UC-05) | T-04 งานเบื้องหลังและ R4 | T-05 ปฏิเสธช่างแทน | T-06 หน้าจอ | T-07 รายการงาน Q-32 (AC-09-16)

## 8. สิ่งที่ยังไม่ทำ

ระงับช่าง (Q-70) | เสนอเวลาใหม่เมื่อไม่มีช่างเวลาเดิม | ช่างทิ้งงานหลังออกเดินทาง (Q-51)
