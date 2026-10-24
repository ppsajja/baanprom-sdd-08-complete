# Tasks: ลูกค้าให้คะแนนช่าง (UC-11)

Feature: SPEC-RATING | อ้างอิง: plan.md (plan v1) | /tasks วันที่ 2569-12-10 (tasks v1, prompt-log.md #98)
สรุป: 4 task | 0 task รอ Q-xx | สถานะปัจจุบัน: เสร็จ 4

### T-01 ตาราง ratings และ POST /jobs/{id}/rating
- รองรับ: REQ-FN-068, BR-11 ข้อ 1 ถึง 5 และ 8, REQ-SEC-010
- ตรวจด้วย: AC-11-01 ถึง AC-11-05, AC-11-08
- ไฟล์ที่แตะ: backend/app/rating/service.py, router.py, backend/app/db/models.py, backend/app/matching/service.py, backend/app/auth/router.py
- เสร็จเมื่อ: test ผ่าน และเมื่อตัดเงื่อนไข "งานต้องเสร็จสิ้น" ออก test_AC_11_02 ต้องพัง (พิสูจน์ชั้น 3)
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: ตัดเงื่อนไขแล้ว test_AC_11_02_not_done_cannot_rate พัง แก้กลับแล้วผ่าน)

### T-02 ค่าเฉลี่ยในผลค้นหาและของช่าง
- รองรับ: REQ-FN-069, BR-11 ข้อ 6 และ 7
- ตรวจด้วย: AC-11-06
- ไฟล์ที่แตะ: backend/app/rating/service.py (summaries), backend/app/technicians/service.py
- สถานะ: เสร็จ

### T-03 ความเห็นเป็นส่วนตัว และลบเมื่อขอลบข้อมูล
- รองรับ: REQ-PRV-012, REQ-PRV-010
- ตรวจด้วย: AC-11-07, AC-11-08
- ไฟล์ที่แตะ: backend/app/rating/service.py (comments_for erase), backend/app/erasure/service.py
- สถานะ: เสร็จ

### T-04 หน้าจอ UI-11-01 และคะแนนใน UI-07-01
- ตรวจด้วย: UI-11-01.test.jsx, AC-11-06.test.jsx
- ไฟล์ที่แตะ: frontend/src/pages/MyJobs.jsx, TechnicianPicker.jsx, api/client.js, App.jsx
- แบบหน้าจอ: UI-11-01, UI-07-01 (แก้)
- สถานะ: เสร็จ

## ตารางความครบ

| AC | task |
|---|---|
| AC-11-01 ถึง AC-11-05 | T-01, T-04 |
| AC-11-06 | T-02, T-04 |
| AC-11-07 | T-03 |
| AC-11-08 | T-01, T-03 |
