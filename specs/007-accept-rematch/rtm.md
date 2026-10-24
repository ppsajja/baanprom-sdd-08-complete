# rtm.md ตารางตามรอยของ feature ช่างรับหรือปฏิเสธงาน (UC-12) และจับคู่ช่างใหม่ (UC-05)

รุ่น: 1.0 | วันที่: 2569-11-23 | ผู้ตรวจ: กลุ่ม X (รอบนี้ผู้สอนเดโม) | อ้างอิง: spec.md 1.0, accept-rematch.feature v1.0, plan v1, tasks v1, specs/000-shared/test-run.txt
ร่างครั้งแรกด้วย AI (prompt-log.md #93) ทีมตรวจทุกแถว เลขข้อค้นพบต่อจาก 006 (F-17, F-18) จึงเริ่มที่ F-19

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-061 รับหรือปฏิเสธใน 30 นาที | MD-STM-01, EV-051 (SH-06) | ใช่ | AC-12-01 ถึง 05, AC-05-03 | test_accept_rematch.py 6 ตัว, AC-12-01.test.jsx | T-01, T-02, T-04, T-06 | matching/service.py, matching/router.py, jobstatus/service.py, TechnicianJobs.jsx, UI-09-01 | ครบ | รับ |
| REQ-FN-062 จับคู่ช่างใหม่ BR-07 | UC-07 E3, REQ-003, EV-051 | ใช่ | AC-05-01, 05, 06 | test_AC_05_01, 05, 06 | T-03 | matching/service.py candidate_slots rematch | ครบ (พิสูจน์ชั้น 3 ใน T-03) | รับ |
| REQ-FN-063 R4 คืนเต็ม | BR-01 R4, Q-50, EV-051 | ใช่ | AC-05-02, 04, 06 | test_AC_05_02, 04, 06, UI-02-03.test.jsx | T-04, T-05 | matching/service.py process_due decline_substitute, refund/rules.py, MyJobs.jsx | ครบ | รับ |
| REQ-FN-050 (Q-32) | EV-051 (Ops lead) | ใช่ | AC-09-16 | test_AC_09_16_closed_jobs_shown_30_days_back | T-07 | jobstatus/service.py list_jobs_for_technician | ครบ AS-12 ปิด | รับ |
| REQ-BR-001 (R4) | EV-023 | ใช่ | AC-05-02, AC-05-04 | test_AC_05_02, test_AC_05_04 | T-04, T-05 | refund/rules.py (substitute_declined) | ครบ | รับ |
| REQ-SEC-010 | MU-01 | ใช่ | AC-12-04, AC-05-01 | test_AC_12_04, test_AC_05_01 | T-02 | ops/audit.py (released_from) | ครบ | รับ |

## ตามรอยย้อนกลับ

endpoint ใหม่ 3 ตัวและงานเบื้องหลัง 1 ตัวชี้กลับไปหา REQ ได้ ของเกิน 0 รายการ
ข้อค้นพบ
- F-19 (ตัวเลขซ่อน) BR-07 ข้อ 2 "นับจากงานยืนยัน" งานที่ยืนยันกลางคืนช่างก็มีเวลา 30 นาทีเท่าเดิม ทำให้ช่างที่หลับอยู่ "ไม่ตอบ" และงานถูกส่งต่อ SH-06 รับรู้ใน EV-051 ว่าเป็นพฤติกรรมที่ต้องการ (ลูกค้าได้ช่างเร็ว) ทีมจดไว้ให้ดูตัวเลข no_response ช่วง hypercare ไม่เปิด Q
- F-20 (ข้อความถึงช่าง) ข้อความ "มีงานใหม่" ของ UC-07 เดิมไม่บอกว่าต้องตอบภายใน 30 นาที (ข้อความของช่างแทนบอก) ไม่แก้ในรอบนี้เพราะข้อความเดิมอยู่ใน Baseline และ AC-07-03 ไม่ได้กำหนดถ้อยคำ เสนอแก้พร้อม CR ถัดไปที่แตะข้อความแจ้งเตือน
