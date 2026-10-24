# Plan: ลูกค้าให้คะแนนช่าง (UC-11)

อ้างอิง: spec.md SPEC-RATING 1.0 | Updated: 2569-12-10 | /plan แล้วทีมตรวจ (plan v1, prompt-log.md #97)
อ้างอิง Constraint กลาง: specs/000-shared/constraints.md รุ่น 1.4

## 1. สรุปแนวทาง

- โมดูลใหม่ backend/app/rating/ (service.py BR-11 summaries router.py) ตารางใหม่ ratings
- ผลค้นหา (technicians/service.search_available) เพิ่มช่อง rating ต่อช่าง ลำดับเดิม
- งานของฉัน (matching/service.customer_job_view) เพิ่ม can_rate my_rating
- ลบข้อมูลลูกค้า (erasure/service.anonymize) ลบความเห็น
- หน้าจอ: ส่วนให้คะแนนใน MyJobs.jsx ข้อความคะแนนใน TechnicianPicker.jsx

## 2. เทคโนโลยีที่ใช้

ไม่มีเทคโนโลยีใหม่

```
backend/app/rating/__init__.py, service.py, router.py          ใหม่
backend/app/db/models.py (Rating)                              แก้ เพิ่มท้ายไฟล์
backend/app/technicians/service.py, matching/service.py, auth/router.py, erasure/service.py   แก้
backend/tests/test_rating.py                                   ใหม่
frontend/src/pages/MyJobs.jsx, TechnicianPicker.jsx, api/client.js, App.jsx   แก้
frontend/src/__tests__/UI-11-01.test.jsx, AC-11-06.test.jsx     ใหม่
```

## 3. โมเดลข้อมูล

ratings(id, job_id unique, customer_id, technician_id, stars, comment, counted, at)

## 4. API / หน้าจอ

| method path | ผู้เรียก | ตอบ |
|---|---|---|
| POST /jobs/{id}/rating {stars, comment} | ลูกค้า (token) | 201 | 403 ไม่ใช่เจ้าของ (บันทึก) | 409 not_done already_rated window_passed | 422 bad_stars |
| GET /me/rating | ช่าง | {average, count} |
| GET /ops/technicians/{id}/ratings | Ops (หัวหน้าช่าง) | summary ratings (ไม่มีชื่อลูกค้า) |
| GET /technicians (เดิม) GET /me/jobs (เดิม) | ลูกค้า | เพิ่ม rating และ can_rate my_rating |

## 5. ตารางตรวจ Constraints

| ID | ใช้อย่างไรใน feature นี้ |
|---|---|
| REQ-CON-001 | ไม่เกี่ยวกับ feature นี้ เพราะเป็นข้อจำกัดของ R1 |
| REQ-CON-003 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีการเงิน |
| REQ-PRV-002 | ใช้แล้ว log มีแค่เลขงาน รหัสช่าง จำนวนดาว ความเห็นปิดบังก่อนเก็บ |
| REQ-OP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี SLO ของตัวเอง |
| REQ-OP-005 | ใช้แล้ว endpoint ใหม่ถูกนับโดย middleware เดิม |
| REQ-OP-006 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีเหตุการณ์ใหม่ (คำสั่งดูคะแนนต่ำอยู่ในเครื่องมือของคนเวร) |
| REQ-OP-007 | ไม่เกี่ยวกับ feature นี้ เพราะตารางใหม่อยู่ในสำเนาเดิม |
| REQ-OP-008 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีข้อความ |
| REQ-OP-009 | ไม่เกี่ยวกับ feature นี้ เพราะไม่เรียกระบบภายนอก |
| REQ-QA-010 | ไม่เกี่ยวกับ feature นี้ เพราะไม่เรียกระบบภายนอก |
| REQ-QA-003 | ใช้แล้ว ผลค้นหาเพิ่มคำค้นเดียว (group by ต่อคำขอ) ไม่วัดโหลดซ้ำในรอบนี้ (F-22) |
| REQ-SEC-010 | ใช้แล้ว งานของคนอื่นตอบ 403 และบันทึก (audit.job_of_customer) |
| REQ-SEC-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ล็อกช่วงเวลา |
| REQ-SEC-012 | ใช้แล้ว endpoint ใหม่อยู่ในบัญชี endpoint |
| REQ-SEC-013 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี OTP |
| REQ-SEC-014 | ใช้แล้ว ลูกค้าและช่างมาจาก token |
| REQ-SEC-015 | ไม่เกี่ยวกับ feature นี้ เพราะหัวหน้าช่างใช้กุญแจของ Ops ตามเดิม |
| REQ-PRV-010 | ใช้แล้ว ลบความเห็นเมื่อขอลบข้อมูล |
| REQ-PRV-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ใช้พิกัด |
| REQ-IF-012 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีระบบภายนอก |
| REQ-CMP-001 | ใช้แล้ว REQ-PRV-012 ผ่านการตรวจของ SH-05 (spec ส่วน 7) |
| REQ-AI-021, REQ-AI-022 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี AI (กฎกันรีวิวปลอมเป็นโค้ด) |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC | test |
|---|---|
| AC-11-01 ถึง AC-11-08 | backend/tests/test_rating.py | หน้าจอ UI-11-01.test.jsx (AC-11-01 AC-11-03) AC-11-06.test.jsx |

## 7. ลำดับงาน

T-01 ตารางและการให้คะแนน | T-02 ค่าเฉลี่ยในผลค้นหาและของช่าง | T-03 ความเป็นส่วนตัวและการลบ | T-04 หน้าจอ
