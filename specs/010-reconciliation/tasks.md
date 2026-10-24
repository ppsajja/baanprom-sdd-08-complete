# Tasks: กระทบยอดกับรายงานของ gateway (UC-13)

Feature: SPEC-RECONCILIATION | อ้างอิง: plan.md (plan v1) | /tasks วันที่ 2569-12-10 (tasks v1, prompt-log.md #98)
สรุป: 4 task | 0 task รอ Q-xx | สถานะปัจจุบัน: เสร็จ 4

### T-01 ตรวจไฟล์และจับคู่ (BR-13 ข้อ 1 ถึง 5 และ 7)
- รองรับ: REQ-FN-070 | ตรวจด้วย: AC-13-01 ถึง AC-13-04, AC-13-08
- ไฟล์ที่แตะ: backend/app/reconciliation/service.py, mock_report.py, backend/app/db/models.py
- สถานะ: เสร็จ

### T-02 ผลคืนเงินที่ไม่รู้ (BR-13 ข้อ 6 และ 8)
- รองรับ: REQ-FN-071, REQ-IF-010 | ตรวจด้วย: AC-13-05, AC-13-06
- ไฟล์ที่แตะ: backend/app/reconciliation/service.py (_resolve)
- เสร็จเมื่อ: test ผ่าน และเมื่อตัดการเปลี่ยนผลออก test_AC_13_05 ต้องพัง (พิสูจน์ชั้น 3)
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: ตัดการเรียก _resolve ออก test_AC_13_05 test_AC_13_06 test_AC_13_08 พัง แก้กลับแล้วผ่าน)

### T-03 นำเข้าซ้ำ และกุญแจของ Finance
- รองรับ: REQ-FN-070 (BR-13 ข้อ 9), REQ-SEC-015 | ตรวจด้วย: AC-13-07, AC-13-08
- ไฟล์ที่แตะ: backend/app/reconciliation/router.py, backend/app/auth/deps.py
- สถานะ: เสร็จ

### T-04 หน้าจอ UI-13-01
- ตรวจด้วย: UI-13-01.test.jsx | ไฟล์ที่แตะ: frontend/src/pages/Reconciliation.jsx, App.jsx, api/client.js | แบบหน้าจอ: UI-13-01
- สถานะ: เสร็จ

## ตารางความครบ

| AC | task |
|---|---|
| AC-13-01 ถึง AC-13-04 | T-01, T-04 |
| AC-13-05, AC-13-06 | T-02 |
| AC-13-07 | T-03, T-04 |
| AC-13-08 | T-01, T-03, T-04 |
