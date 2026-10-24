# Tasks: ลูกค้าลงทะเบียนและเข้าสู่ระบบ (UC-02) และช่างเข้าสู่ระบบ (UC-01)

Feature: SPEC-IDENTITY | อ้างอิง: plan.md (plan v1) | สร้างด้วย /tasks วันที่ 2569-11-23 (tasks v1, prompt-log.md #92)
สรุป: 8 task | 0 task รอ Q-xx | สถานะปัจจุบัน: เสร็จ 8 (ผ่านการตรวจ 5 ข้อ task หน้าจอผ่านการตรวจเทียบ mockup)

### T-01 ตาราง accounts otp_challenges auth_sessions และกฎ BR-09
- รองรับ: REQ-SEC-013, REQ-SEC-014, BR-09, D-02-01, D-02-02
- ตรวจด้วย: AC-02-03, AC-02-04, AC-02-05, AC-02-08
- ไฟล์ที่แตะ: backend/app/db/models.py, backend/app/db/migrations/m004_r2.py, backend/app/config.py, backend/app/auth/service.py
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: เปลี่ยน OTP_MAX_WRONG_ATTEMPTS เป็น 6 test_AC_02_04 พัง แก้กลับแล้วผ่าน)

### T-02 endpoint ขอรหัส ยืนยัน ลงทะเบียน ออกจากระบบ ข้อมูลของฉัน
- รองรับ: REQ-FN-058, REQ-FN-059, REQ-PRV-011, D-02-03
- ตรวจด้วย: AC-02-01, AC-02-02, AC-02-11
- ไฟล์ที่แตะ: backend/app/auth/router.py, backend/app/notify/queue.py (send_otp), backend/app/main.py
- สถานะ: เสร็จ

### T-03 ตัวตนจาก token ทุก endpoint
- รองรับ: REQ-SEC-014
- ตรวจด้วย: AC-02-06, AC-01-03 และ AC เดิมทุกข้อ
- ไฟล์ที่แตะ: backend/app/auth/deps.py, booking/router.py, technicians/router.py, jobstatus/router.py, cancel/router.py, assistant/router.py
- สถานะ: เสร็จ

### T-04 ตรวจสิทธิ์ GET /jobs/{id} และ /history (GAP-24)
- รองรับ: REQ-SEC-010
- ตรวจด้วย: AC-02-07
- ไฟล์ที่แตะ: backend/app/ops/audit.py (job_for_reader), booking/router.py, jobstatus/router.py
- สถานะ: เสร็จ

### T-05 ลบข้อมูลแล้วบัญชีและ session หาย
- รองรับ: REQ-PRV-010, REQ-SEC-014
- ตรวจด้วย: AC-02-09
- ไฟล์ที่แตะ: backend/app/erasure/service.py, backend/app/auth/service.py (revoke_customer)
- สถานะ: เสร็จ

### T-06 บัญชีช่างที่ Ops ออกให้
- รองรับ: REQ-FN-060
- ตรวจด้วย: AC-01-01, AC-01-02
- ไฟล์ที่แตะ: backend/app/auth/service.py (create_technician_account), auth/router.py (ops_router)
- สถานะ: เสร็จ

### T-07 หน้าจอเข้าสู่ระบบ ลงทะเบียน งานของฉัน เลือกที่อยู่
- รองรับ: REQ-FN-058, REQ-FN-059, REQ-FN-060, REQ-SEC-014, D-02-04
- ตรวจด้วย: UI-02-01, UI-02-02, UI-02-03, UI-01-01, AC-02-06 (.test.jsx) และ AC-02-10 (AC-07-20.test.jsx)
- ไฟล์ที่แตะ: frontend/src/api/client.js, App.jsx, pages/Login.jsx, Register.jsx, MyJobs.jsx, TechnicianPicker.jsx
- แบบหน้าจอ: UI-02-01, UI-02-02, UI-02-03, UI-01-01
- สถานะ: เสร็จ

### T-08 รัน test ทั้งชุด แก้ test เดิมตามตารางของ CR-11 และสคริปต์ตรวจรับ
- รองรับ: CR-11 (กติกา Baseline ข้อ 8)
- ตรวจด้วย: specs/000-shared/test-run-cr11-round1.txt (ก่อนแก้ test) และ test-run.txt (หลังแก้)
- ไฟล์ที่แตะ: backend/tests/conftest.py และ test เดิมตามตาราง frontend/src/__tests__/AC-07-19, UI-07-02-DEF-01 backend/uat_seed.py, uat_auth.py, uat_replay.py, load_test.py
- สถานะ: เสร็จ

## ตารางความครบ (AC กับ task)

| AC | task |
|---|---|
| AC-02-01, AC-02-02, AC-02-11 | T-02, T-07 |
| AC-02-03, AC-02-04, AC-02-05, AC-02-08 | T-01 |
| AC-02-06 | T-03, T-07 |
| AC-02-07 | T-04 |
| AC-02-09 | T-05 |
| AC-02-10 | T-02, T-07 |
| AC-01-01, AC-01-02 | T-06, T-07 |
| AC-01-03 | T-03, T-07 |
