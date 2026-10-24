# rtm.md ตารางตามรอยของ feature กระทบยอด (UC-13)

รุ่น: 1.0 | วันที่: 2569-12-10 | ผู้ตรวจ: กลุ่ม X | อ้างอิง: spec.md 1.0, reconciliation.feature v1.0, plan v1, tasks v1, specs/000-shared/test-run.txt

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test | task | โค้ด / หน้าจอ | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|---|
| REQ-FN-070 กระทบยอด | MD-UCD-01 (UC-13), สัญญา IF-01, EV-053 (Finance) | ใช่ | AC-13-01 ถึง 04, AC-13-08 | test_reconciliation.py 3 ตัว, UI-13-01.test.jsx | T-01, T-03, T-04 | reconciliation/service.py, router.py, Reconciliation.jsx, UI-13-01 | ครบ | รับ |
| REQ-FN-071 คืนเงินที่ไม่รู้ผล | Q-41, EV-053 | ใช่ | AC-13-05, AC-13-06 | test_AC_13_05, test_AC_13_06 | T-02 | reconciliation/service.py _resolve | ครบ (พิสูจน์ชั้น 3 ใน T-02) | รับ |
| REQ-SEC-015 กุญแจของ Finance | GAP-32, EV-053 | ใช่ | AC-13-07 | test_AC_13_07, UI-13-01.test.jsx | T-03 | auth/deps.py require_finance | ครบ | รับ |

## ตามรอยย้อนกลับ

endpoint ใหม่ 3 ตัวชี้กลับหา REQ ได้ backend/gateway_report_mock.py และ mock_report.py เป็นเครื่องมือของเครื่องทดสอบ (AS-18) ไม่ใช่ของเกิน
ข้อค้นพบ
- F-23 (ข้อมูลที่ไม่มี) ตาราง refunds ไม่มีเวลา (ออกแบบใน R1) วันของการคืนเงินจึงอ่านจากประวัติสถานะงาน (D-13-01) ถ้าวันหนึ่งงานถูกยกเลิกแล้วคืนเงินแยกวัน (ไม่มีทางเกิดใน R2 เพราะคืนในธุรกรรมเดียวกับการยกเลิก) วันจะผิด ทีมจดไว้ให้ CR ถัดไปที่แตะการคืนเงินเพิ่มเวลา
