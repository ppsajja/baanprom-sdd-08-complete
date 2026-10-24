# Tasks: ช่างรับหรือปฏิเสธงาน (UC-12) และจับคู่ช่างใหม่ (UC-05)

Feature: SPEC-ACCEPT-REMATCH | อ้างอิง: plan.md (plan v1) | สร้างด้วย /tasks วันที่ 2569-11-23 (tasks v1, prompt-log.md #92)
สรุป: 7 task | 0 task รอ Q-xx | สถานะปัจจุบัน: เสร็จ 7 (ผ่านการตรวจ 5 ข้อ task หน้าจอผ่านการตรวจเทียบ mockup)

### T-01 ตาราง job_assignments และการมอบงานตอนงานยืนยัน
- รองรับ: REQ-FN-061, MD-STM-04
- ตรวจด้วย: AC-12-01
- ไฟล์ที่แตะ: backend/app/db/models.py, backend/app/matching/service.py (offer), backend/app/booking/service.py, backend/app/payments/service.py
- เสร็จเมื่อ: จองสำเร็จแล้วมีแถวการมอบงาน respond_by = เวลายืนยัน + 30 นาที
- สถานะ: เสร็จ

### T-02 รับงาน ปฏิเสธงาน และออกเดินทางถือว่ารับ
- รองรับ: REQ-FN-061, BR-07 ข้อ 1 และ 2, REQ-SEC-010, D-12-01
- ตรวจด้วย: AC-12-02 ถึง AC-12-05
- ไฟล์ที่แตะ: backend/app/matching/service.py, router.py, backend/app/jobstatus/service.py, backend/app/ops/audit.py, backend/app/main.py
- เสร็จเมื่อ: test_AC_12_02 ถึง 05 ผ่าน
- สถานะ: เสร็จ

### T-03 จับคู่ช่างใหม่ตาม BR-07 ข้อ 3 และ 4
- รองรับ: REQ-FN-062, BR-07, BR-03
- ตรวจด้วย: AC-05-01, AC-05-05, AC-05-06
- ไฟล์ที่แตะ: backend/app/matching/service.py (candidate_slots, rematch)
- เสร็จเมื่อ: test_AC_05_01, 05, 06 ผ่าน และเมื่อลบเงื่อนไขทักษะออก test_AC_05_05 ต้องพัง (พิสูจน์ชั้น 3)
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: ตัดเงื่อนไขทักษะออก test พัง 4 ตัว รวม test_AC_05_01 และ test_AC_05_05 ที่ได้ช่าง "ไฟฟ้าล้วน" แก้กลับแล้วผ่าน)

### T-04 งานเบื้องหลัง ไม่ตอบ 30 นาที และยกเลิกเมื่อครบ 2 ชั่วโมง (R4)
- รองรับ: REQ-FN-061, REQ-FN-063, BR-07 ข้อ 5, REQ-OP-008
- ตรวจด้วย: AC-05-02, AC-05-03, AC-05-06
- ไฟล์ที่แตะ: backend/app/matching/service.py (process_due), backend/app/ops/scheduler.py, backend/app/refund/service.py (ไม่แจ้งช่างเดิมซ้ำ)
- สถานะ: เสร็จ

### T-05 ลูกค้าปฏิเสธช่างแทน (R4)
- รองรับ: REQ-FN-063, BR-07 ข้อ 6, D-12-04
- ตรวจด้วย: AC-05-04
- ไฟล์ที่แตะ: backend/app/refund/rules.py, refund/service.py, backend/app/matching/router.py
- สถานะ: เสร็จ

### T-06 หน้าจอ ปุ่มรับและปฏิเสธ (UI-09-01) และช่างแทน (UI-02-03)
- รองรับ: REQ-FN-061, REQ-FN-063
- ตรวจด้วย: AC-12-01.test.jsx, UI-02-03.test.jsx
- ไฟล์ที่แตะ: frontend/src/pages/TechnicianJobs.jsx, frontend/src/api/client.js, specs/003-job-status/mockups/UI-09-01-technician-jobs.html
- แบบหน้าจอ: UI-09-01 (แก้), UI-02-03
- สถานะ: เสร็จ

### T-07 ขอบเขตรายการงานของช่าง (Q-32)
- รองรับ: REQ-FN-050 (Q-32)
- ตรวจด้วย: AC-09-16
- ไฟล์ที่แตะ: backend/app/jobstatus/service.py (list_jobs_for_technician), backend/app/config.py (TECH_CLOSED_JOBS_DAYS), backend/tests/test_job_status_cr12.py
- สถานะ: เสร็จ

## ตารางความครบ (AC กับ task)

| AC | task |
|---|---|
| AC-12-01 | T-01, T-06 |
| AC-12-02 ถึง AC-12-05 | T-02, T-06 |
| AC-05-01, AC-05-05, AC-05-06 | T-03, T-06 |
| AC-05-02, AC-05-03 | T-04 |
| AC-05-04 | T-05, T-06 |
| AC-09-16 | T-07 |
