# Tasks: ช่างจัดตารางเวลาว่างและวันหยุด (UC-04)

Feature: SPEC-SCHEDULE | อ้างอิง: plan.md (plan v1) | สร้างด้วย /tasks วันที่ 2569-12-10 (tasks v1, prompt-log.md #98)
สรุป: 5 task | 0 task รอ Q-xx | สถานะปัจจุบัน: เสร็จ 5 (ผ่านการตรวจ 5 ข้อ task หน้าจอผ่านการตรวจเทียบ mockup)

### T-01 สถานะ closed และตาราง technician_days_off
- รองรับ: REQ-FN-066, REQ-FN-067, MD-STM-05
- ตรวจด้วย: AC-04-03, AC-04-05
- ไฟล์ที่แตะ: backend/app/db/models.py, backend/app/db/migrations/m005_r2b.py
- สถานะ: เสร็จ

### T-02 เพิ่มช่วง ปิดช่วง และดูตาราง
- รองรับ: REQ-FN-066, BR-10 ข้อ 1 ถึง 5, REQ-SEC-010
- ตรวจด้วย: AC-04-01, AC-04-02, AC-04-04, AC-04-08
- ไฟล์ที่แตะ: backend/app/schedule/service.py, router.py, backend/app/config.py, backend/app/main.py
- สถานะ: เสร็จ

### T-03 ทุกทางที่อ่านช่วงเวลาไม่เห็นช่วงที่ปิด
- รองรับ: REQ-FN-066, BR-02, BR-07 ข้อ 3
- ตรวจด้วย: AC-04-03, AC-04-05
- ไฟล์ที่แตะ: backend/app/technicians/service.py (unavailable), backend/app/booking/service.py
- เสร็จเมื่อ: test_AC_04_03 ผ่าน และเมื่อตัด SLOT_CLOSED ออกจาก unavailable() test ต้องพัง (พิสูจน์ชั้น 3)
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: ตัด SLOT_CLOSED ออก test_AC_04_03 และ test_AC_04_05 พัง แก้กลับแล้วผ่าน)

### T-04 วันหยุด
- รองรับ: REQ-FN-067, BR-10 ข้อ 6 ถึง 8, D-04-02
- ตรวจด้วย: AC-04-05, AC-04-06, AC-04-07
- ไฟล์ที่แตะ: backend/app/schedule/service.py
- สถานะ: เสร็จ

### T-05 หน้าจอ UI-04-01
- รองรับ: REQ-FN-066, REQ-FN-067
- ตรวจด้วย: UI-04-01.test.jsx
- ไฟล์ที่แตะ: frontend/src/pages/TechnicianSchedule.jsx, frontend/src/api/client.js, frontend/src/App.jsx
- แบบหน้าจอ: UI-04-01
- สถานะ: เสร็จ

## ตารางความครบ (AC กับ task)

| AC | task |
|---|---|
| AC-04-01 | T-02, T-05 |
| AC-04-02 | T-02 |
| AC-04-03 | T-01, T-02, T-03 |
| AC-04-04 | T-02 |
| AC-04-05 | T-01, T-03, T-04 |
| AC-04-06, AC-04-07 | T-04, T-05 |
| AC-04-08 | T-02 |
