# Plan: ลูกค้าลงทะเบียนและเข้าสู่ระบบ (UC-02) และช่างเข้าสู่ระบบ (UC-01)

อ้างอิง: spec.md SPEC-IDENTITY 1.0 | Updated: 2569-11-23 | สร้างด้วย /plan แล้วทีมตรวจ (plan v1, prompt-log.md #91)
อ้างอิง Constraint กลาง: specs/000-shared/constraints.md รุ่น 1.3 (D-00-01 ถึง D-00-05 ใช้ตาม ไม่ถามซ้ำ)

## 1. สรุปแนวทาง

- โมดูลใหม่ backend/app/auth/ (service.py กฎ BR-09 deps.py ตัวตนของผู้เรียก router.py endpoint) ตารางใหม่ 3 ตาราง (m004)
- deps.py เป็นที่เดียวที่อ่าน header Authorization ทุก router ของ 002 ถึง 005 รับ current_customer current_technician หรือ current_reader แทนรหัสในคำขอ
- ตรวจสิทธิ์ต่องานยังผ่าน ops/audit.py ตัวเดิม (REQ-SEC-010) เพิ่ม job_for_reader สำหรับ GET /jobs/{id} และ /history
- OTP ส่งผ่าน Notifier ของ IF-02 ตัวเดิม (เพิ่มเมธอด send_otp) FakeNotifier เก็บข้อความไว้ให้ test อ่าน
- หน้าจอ: Login.jsx Register.jsx MyJobs.jsx ใหม่ App.jsx มีด่านเข้าสู่ระบบ api/client.js แนบ token ทุกคำขอ

## 2. เทคโนโลยีที่ใช้

ไม่มี library ใหม่ token สุ่มด้วย secrets และแฮช sha256 ของ Python มาตรฐาน (D-02-01) ใช้ D-00-01 ถึง D-00-05

### โครงไฟล์ (เฉพาะที่ feature นี้เพิ่มหรือแตะ)

```
backend/app/auth/__init__.py, service.py, deps.py, router.py   ใหม่
backend/app/db/models.py, db/migrations/m004_r2.py             Account OtpChallenge AuthSession
backend/app/config.py                                           ตัวเลข BR-09
backend/app/notify/queue.py                                     Notifier.send_otp
backend/app/booking/router.py, technicians/router.py, jobstatus/router.py, cancel/router.py, assistant/router.py
backend/app/ops/audit.py, erasure/service.py, main.py
backend/tests/conftest.py (auth_headers), tests/test_identity.py
backend/uat_seed.py, uat_auth.py, uat_replay.py, load_test.py  สคริปต์ตรวจรับ (ไม่ใช่ส่วนของระบบ)
frontend/src/api/client.js, App.jsx, pages/Login.jsx, Register.jsx, MyJobs.jsx, TechnicianPicker.jsx (เลือกที่อยู่)
frontend/src/__tests__/UI-02-01, UI-02-02, UI-02-03, UI-01-01, AC-02-06 .test.jsx
```

## 3. โมเดลข้อมูล

accounts(role, subject_id, phone_norm UNIQUE(role, phone_norm)) | otp_challenges(role, phone_norm, code_hash, sent, created_at, expires_at, wrong_attempts, verified_at, used_at, replaced_at) | auth_sessions(token_hash UNIQUE, account_id, role, subject_id, created_at, expires_at, revoked_at)

## 4. API / หน้าจอ

| method path | ผู้เรียก | ตอบ |
|---|---|---|
| POST /auth/otp {phone, role} | ทุกคน | 202 challenge_id expires_at (dev_code เฉพาะ test และ development) | 422 invalid_phone | 429 too_soon too_many | 503 notify_down |
| POST /auth/verify {challenge_id, code} | ทุกคน | 200 token role subject_id name expires_at หรือ needs_registration | 401 wrong_code attempts_left | 410 expired locked used |
| POST /auth/register {challenge_id, name, address_text, lat, lng} | ลูกค้าใหม่ | 201 token | 409 not_verified already_registered | 410 |
| POST /auth/logout | ผู้เข้าสู่ระบบ | 200 |
| GET /me | ผู้เข้าสู่ระบบ | role subject_id name addresses (ลูกค้า ไม่มีพิกัด) |
| POST /me/addresses | ลูกค้า | 201 |
| GET /me/jobs | ลูกค้า | งานของตัวเอง (substitute can_decline_substitute ของ CR-12) |
| POST /ops/technicians/{id}/account {phone} | Ops (X-Ops-Token) | 201 |
| ทุก endpoint เดิมของ 002 ถึง 005 | ตาม REQ-SEC-014 | ไม่มี token 401 บทบาทผิด 403 |

## 5. ตารางตรวจ Constraints

| ID | ใช้อย่างไรใน feature นี้ |
|---|---|
| REQ-CON-001 | ไม่เกี่ยวกับ feature นี้ เพราะเป็นข้อจำกัดเวลาของ R1 |
| REQ-CON-003 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ตัดเงินหรือคืนเงิน |
| REQ-PRV-002 | ใช้แล้ว log_event ไม่มีเบอร์ รหัส token (AC-02-08) |
| REQ-OP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี SLO ของการเข้าสู่ระบบในรอบนี้ |
| REQ-OP-005 | ใช้แล้ว endpoint ใหม่นับโดย middleware เดิม การปฏิเสธสิทธิ์ใหม่บันทึกใน security_events |
| REQ-OP-006 | ใช้แล้ว operations.md เพิ่มเหตุการณ์ "ลูกค้าเข้าสู่ระบบไม่ได้เพราะ IF-02 ไม่ตอบ" |
| REQ-OP-007 | ไม่เกี่ยวกับ feature นี้ เพราะตารางใหม่อยู่ในสำเนาสำรองเดิม |
| REQ-OP-008 | ไม่เกี่ยวกับ feature นี้ เพราะ OTP ไม่ผ่านคิว (D-02-03) |
| REQ-QA-010 | ใช้แล้ว ส่ง OTP ใช้ timeout 10 วินาทีของ IF-02 ไม่ตอบได้ 503 ไม่ส่งซ้ำเอง |
| REQ-SEC-010 | ใช้แล้ว job_for_reader ปิด GAP-24 ทุก router ส่งรหัสจาก token ให้ audit |
| REQ-SEC-011 | ใช้แล้ว เพดานล็อกนับต่อลูกค้าที่เข้าสู่ระบบจริง |
| REQ-SEC-012 | ใช้แล้ว dev_code ไม่มีในโหมด production endpoint ใหม่อยู่ในบัญชี |
| REQ-SEC-013 | ใช้แล้ว auth/service.py |
| REQ-SEC-014 | ใช้แล้ว auth/deps.py |
| REQ-PRV-010 | ใช้แล้ว erasure/service.py เรียก revoke_customer |
| REQ-PRV-011 | ใช้แล้ว GET /me ไม่ส่งพิกัด |
| REQ-CMP-001 | ใช้แล้ว SH-05 ตรวจ REQ-PRV-011 และส่วนการเก็บเบอร์ของ REQ-SEC-013 แล้ว (EV-051) |
| REQ-AI-021, REQ-AI-022 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี AI |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC | test |
|---|---|
| AC-02-01 ถึง AC-02-11, AC-01-01 ถึง AC-01-03 | backend/tests/test_identity.py::test_AC_02_nn และ test_AC_01_nn |
| หน้าจอ | UI-02-01, UI-02-02, UI-02-03, UI-01-01, AC-02-06 .test.jsx และ AC-07-20.test.jsx (AC-02-10 ฝั่งหน้าจอ) |
| AC เดิมทุกข้อที่บอกผู้ส่ง | test เดิมผ่าน conftest.auth_headers (ตาราง test เดิมที่เปลี่ยนของ CR-11) |

## 7. ลำดับงาน

T-01 ตารางและ BR-09 | T-02 endpoint /auth | T-03 deps และย้ายทุก router | T-04 job_for_reader (GAP-24) | T-05 ลบข้อมูล | T-06 บัญชีช่าง | T-07 หน้าจอ | T-08 รัน test ทั้งชุด แก้ test เดิมตาม CR-11 สคริปต์ตรวจรับ

## 8. สิ่งที่ยังไม่ทำ

หน้าจอเพิ่มที่อยู่ (API มีแล้ว) | แผนที่จริง IF-03 (GAP-40) | กุญแจแยกบทบาท call center (GAP-32) | Thai-ID (Q-69)
