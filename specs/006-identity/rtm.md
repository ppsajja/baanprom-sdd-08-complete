# rtm.md ตารางตามรอยของ feature ลูกค้าลงทะเบียนและเข้าสู่ระบบ (UC-02) และช่างเข้าสู่ระบบ (UC-01)

รุ่น: 1.0 | วันที่: 2569-11-23 | ผู้ตรวจ: กลุ่ม X (รอบนี้ผู้สอนเดโม) | อ้างอิง: spec.md 1.0, identity.feature v1.0, plan v1, tasks v1, specs/000-shared/test-run.txt
ร่างครั้งแรกด้วย AI จาก plan.md ข้อ 6 และ tasks.md (prompt-log.md #93) ทีมตรวจทุกแถวเทียบไฟล์จริง และเขียนช่อง "ทีมตัดสิน" เอง
เลขข้อค้นพบต่อจาก F-16 จึงเริ่มที่ F-17

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-058 ลงทะเบียน หลายที่อยู่ | TH-01, EV-051 | ใช่ | AC-02-01, AC-02-10 | test_AC_02_01, test_AC_02_10, UI-02-02.test.jsx, AC-07-20.test.jsx | T-02, T-07 | auth/service.py register_customer, auth/router.py, Register.jsx, TechnicianPicker.jsx | ขาดบางส่วน: หน้าจอเพิ่มที่อยู่ยังไม่มี (F-17) | รับ ส่วน B ตัดสินว่าจะทำหรือ Won't |
| REQ-FN-059 ลูกค้าเข้าสู่ระบบ | EV-051 | ใช่ | AC-02-02 | test_AC_02_02, UI-02-01.test.jsx, AC-02-06.test.jsx | T-02, T-07 | auth/router.py, Login.jsx, App.jsx | ครบ | รับ |
| REQ-FN-060 ช่างเข้าสู่ระบบ | EV-051 (SH-06) | ใช่ | AC-01-01, AC-01-02 | test_AC_01_01, test_AC_01_02, UI-01-01.test.jsx | T-06, T-07 | auth/service.py create_technician_account, Login.jsx | ครบ | รับ |
| REQ-SEC-013 OTP | หน้าบทเรียน A07, EV-051 | ใช่ | AC-02-03, 04, 05, 08, 11, AC-01-02 | test_identity.py 6 ตัว | T-01 | auth/service.py, config.py | ครบ (พิสูจน์ชั้น 3 ใน T-01) | รับ |
| REQ-SEC-014 ตัวตนจาก token | TH-01, EV-051 | ใช่ | AC-02-02, 06, 09, AC-01-01, 03 | test_identity.py 5 ตัว และ test เดิมทุกตัวที่ผ่าน auth_headers | T-03 | auth/deps.py, ทุก router | ครบ | รับ |
| REQ-SEC-010 (มีผลจริง) | MU-01, EV-045, EV-051 | ใช่ | AC-02-07, AC-01-03 | test_AC_02_07, test_AC_01_03 | T-04 | ops/audit.py job_for_reader | ครบ ปิด GAP-24 call center ยังใช้กุญแจของ Ops (GAP-32) | รับ |
| REQ-PRV-011 พิกัด | Q-22, EV-051 | ใช่ | AC-02-01 | test_AC_02_01 (ไม่มี lat ใน /me) | T-02 | auth/router.py addresses_of | ขาดบางส่วน: พิกัดจากหน้าจอเป็นค่าคงที่ (GAP-40) | รับความเสี่ยงจนต่อ IF-03 |
| REQ-PRV-010 (บัญชี) | PDPA | ใช่ | AC-02-09 | test_AC_02_09 | T-05 | erasure/service.py, auth/service.py revoke_customer | ครบ | รับ |
| REQ-PRV-002 | PDPA | ใช่ | AC-02-08 | test_AC_02_08 | T-01 | privacy.log_event | ครบ | รับ |

## ตามรอยย้อนกลับ

endpoint ใหม่ทั้ง 8 ตัวชี้กลับไปหา REQ ได้ (คอมเมนต์ "รองรับ REQ-xx" ใน auth/router.py) ของเกิน 0 รายการ
ข้อค้นพบ
- F-17 (REQ ทำไม่ครบบนหน้าจอ) REQ-FN-058 บอกว่า "เพิ่มที่อยู่ได้หลายแห่ง" API มี (POST /me/addresses AC-02-10) แต่ไม่มีหน้าจอให้ลูกค้าเพิ่มเอง test ทุกตัวผ่านเพราะ AC-02-10 ตรวจผ่าน API แบบเดียวกับ F-06 ของ 002 ส่งต่อส่วน B ของ R2
- F-18 (สายตามรอยอ้อม) "งานของฉัน" (UI-02-03, GET /me/jobs) รองรับ REQ-FN-052 ของ 003 ไม่มี AC ของตัวเองใน identity.feature ตรวจด้วย UI-02-03.test.jsx และ test_AC_05_04 ของ 007 ทีมรับไว้ ไม่เพิ่ม AC เพราะ REQ-FN-052 มี AC-09-07 อยู่แล้ว
