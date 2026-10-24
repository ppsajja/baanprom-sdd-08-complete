# rtm.md ตารางตามรอยของ feature ให้คะแนนช่าง (UC-11)

รุ่น: 1.0 | วันที่: 2569-12-10 | ผู้ตรวจ: กลุ่ม X | อ้างอิง: spec.md 1.0, rating.feature v1.0, plan v1, tasks v1, specs/000-shared/test-run.txt
ร่างครั้งแรกด้วย AI (prompt-log.md #99) ทีมตรวจทุกแถว

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-068 ให้คะแนน | Q-20 (EV-051), EV-053 | ใช่ | AC-11-01 ถึง 05, AC-11-08 | test_rating.py 8 ตัว, UI-11-01.test.jsx | T-01, T-04 | rating/service.py rate, MyJobs.jsx, UI-11-01 | ครบ (พิสูจน์ชั้น 3 ใน T-01) | รับ |
| REQ-FN-069 ค่าเฉลี่ย | Q-20 (EV-051) | ใช่ | AC-11-06 | test_AC_11_06, AC-11-06.test.jsx | T-02, T-04 | rating/service.py summaries, technicians/service.py, TechnicianPicker.jsx | ครบ | รับ |
| REQ-PRV-012 ความเห็น | EV-053 (SH-05) | ใช่ | AC-11-07, AC-11-08 | test_AC_11_07, test_AC_11_08 | T-03 | rating/service.py comments_for erase, erasure/service.py | ครบ | รับ |
| REQ-SEC-010 | MU-01 | ใช่ | AC-11-05 | test_AC_11_05 | T-01 | rating/router.py (audit.job_of_customer) | ครบ | รับ |

## ตามรอยย้อนกลับ

endpoint ใหม่ 3 ตัวและช่องใหม่ 3 ช่อง (rating, can_rate, my_rating) ชี้กลับหา REQ ได้ ของเกิน 0 รายการ
ข้อค้นพบ
- F-22 (คุณภาพที่ยังไม่วัด) ผลค้นหาเพิ่มคำค้นคะแนน 1 คำค้นต่อคำขอ AC-07-08 (50 ครั้งต่อวินาที) วัดไว้ก่อนมีคะแนน (EV-052) ทีมไม่วัดซ้ำในรอบนี้ เพราะเครื่องทดสอบไม่ใช่ขนาดจริงอยู่แล้ว ใส่เป็นรายการวัดบนเครื่องจริงพร้อม AC-07-08 ใน docs/handover/hypercare-and-golive.md
