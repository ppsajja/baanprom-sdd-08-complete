# rtm.md ตารางตามรอยของ feature ตารางเวลาของช่าง (UC-04)

รุ่น: 1.0 | วันที่: 2569-12-10 | ผู้ตรวจ: กลุ่ม X (รอบนี้ผู้สอนเดโม) | อ้างอิง: spec.md 1.0, schedule.feature v1.0, plan v1, tasks v1, specs/000-shared/test-run.txt
ร่างครั้งแรกด้วย AI (prompt-log.md #99) ทีมตรวจทุกแถว เลขข้อค้นพบต่อจาก 007 (F-19, F-20) จึงเริ่มที่ F-21

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-066 ช่วงเวลาว่าง | MD-UCD-01 (UC-04), AS-15, EV-053 (SH-06) | ใช่ | AC-04-01 ถึง 04, AC-04-08 | test_schedule.py 10 ตัว (รวม Outline 6), UI-04-01.test.jsx | T-01, T-02, T-03, T-05 | schedule/service.py, technicians/service.py unavailable, TechnicianSchedule.jsx, UI-04-01 | ครบ (พิสูจน์ชั้น 3 ใน T-03) | รับ |
| REQ-FN-067 วันหยุด | EV-053 (SH-06) | ใช่ | AC-04-05 ถึง 07 | test_AC_04_05, 06, 07, UI-04-01.test.jsx | T-04, T-05 | schedule/service.py add_day_off remove_day_off | ครบ | รับ |
| REQ-SEC-010 | MU-01 | ใช่ | AC-04-08 | test_AC_04_08 | T-02 | schedule/router.py close_slot | ครบ | รับ |

## ตามรอยย้อนกลับ

endpoint ใหม่ 5 ตัว ชี้กลับไปหา REQ-FN-066 หรือ REQ-FN-067 ได้ทุกตัว ของเกิน 0 รายการ
ข้อค้นพบ
- F-21 (สายตามรอยอ้อม) ช่างที่ยังไม่มีบัญชี (REQ-FN-060) ไม่มีตารางให้จัด และไม่ได้รับข้อความ (UC-10 ส่งได้เฉพาะเบอร์ของบัญชี ผล no_contact) ข้อมูลช่างเดิมที่ย้ายเข้าระบบต้องออกบัญชีก่อนเปิดใช้จริง ทีมใส่เป็นรายการก่อนเปิดใช้จริงใน docs/handover/hypercare-and-golive.md (transition requirement)
