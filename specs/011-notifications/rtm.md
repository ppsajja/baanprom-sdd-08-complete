# rtm.md ตารางตามรอยของ feature การแจ้งเตือน (UC-10)

รุ่น: 1.0 | วันที่: 2569-12-10 | ผู้ตรวจ: กลุ่ม X | อ้างอิง: spec.md 1.0, notifications.feature v1.0, plan v1, tasks v1, specs/000-shared/test-run.txt

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-072 ช่องทาง | EV-004 (ลูกค้าใช้ LINE), EV-053 | ใช่ | AC-10-01 ถึง 03, 05, 06 | test_notifications.py 5 ตัว, UI-10-01.test.jsx | T-01, T-02, T-05 | notify/channels.py preferences.py router.py, NotificationSettings.jsx, UI-10-01 | ครบ | รับ |
| REQ-FN-073 ส่งแทนและบันทึก | EV-053 (Ops lead) | ใช่ | AC-10-04, AC-10-07 | test_AC_10_04, test_AC_10_07 | T-03 | notify/channels.py ChannelRouter | ครบ (พิสูจน์ชั้น 3 ใน T-03) | รับ |
| REQ-IF-012 (IF-02) | EV-053 | ใช่ | AC-00-12, AC-00-13 | test_cross_cutting_r2b.py | T-04 | integrations/http_messaging.py | ครบ | รับ |

## ตามรอยย้อนกลับ

endpoint ใหม่ 6 ตัวชี้กลับหา REQ ได้ GET /ops/notifications/outbox ใช้กับตัวจำลองบนเครื่องทดสอบเท่านั้น (UAT OAT) อยู่ในบัญชี endpoint
ข้อค้นพบ: F-21 (ช่างที่ยังไม่มีบัญชีไม่ได้รับข้อความ) บันทึกไว้ที่ 008 rtm.md เพราะพบตอนทำตารางเวลา และพิสูจน์ใน test_AC_10_01 รอบแรก (GAP-47)
