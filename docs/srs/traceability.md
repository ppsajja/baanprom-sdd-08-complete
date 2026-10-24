# Traceability Matrix (EV, REQ, UC, AC, MD) | บ้านพร้อม

> หมายเหตุ: ไฟล์นี้เป็นสภาพตอนประกาศ Baseline B1 คงไว้เป็นประวัติ สถานะล่าสุดของคำถาม REQ และ Baseline ดูที่ docs/srs/baseline.md

รุ่น 1.0 (Baseline B1) | เจ้าของ: กลุ่ม X
มาจากบทเรียน: Stories, Scenarios และ Use Cases (EV ถึง AC) เติมคอลัมน์ MD ในบทเรียน Modelling
ตารางนี้ยังไปไม่ถึง test เพราะยังไม่มีโค้ด การตามรอยถึง test task และหน้าจอจะทำในบทเรียน Verification

## 1. ไปข้างหน้า (หลักฐาน ถึง เกณฑ์การยอมรับ)

| EV | REQ | UC และขั้น | AC | MD | BR |
|---|---|---|---|---|---|
| EV-004, EV-009 | REQ-FN-008 | UC-07 ขั้น 1 ถึง 6 | AC-07-01, AC-07-02 | MD-ACT-07, MD-DOM-01 | BR-02, BR-03 |
| derived MD-ACT-07 | REQ-FN-041 | UC-07 ขั้น 3 ถึง 5, E2 | AC-07-04 | MD-ACT-07, MD-DOM-01 (TimeSlot.state) | BR-02 |
| EV-012 | REQ-FN-012 | UC-07 ขั้น 6 (UC-10) | AC-07-03 | MD-SEQ-07-05 | |
| EV-023 | REQ-BR-001 | UC-07 ขั้น 4, E1, E3 | AC-07-10 (Outline R1 ถึง R6) | MD-STM-01 | BR-01 |
| สัญญา gateway | REQ-IF-001 | UC-07 ขั้น 5 (UC-06), E1 | AC-07-05, AC-07-06 | MD-SEQ-07-05, MD-CTX-01 | |
| derived MD-SEQ-07-05 | REQ-IF-005 | UC-07 ขั้น 5 | AC-07-05, AC-07-07 | MD-SEQ-07-05 | |
| EV-007 | REQ-QA-003 | UC-07 ขั้น 2 และ 5 | AC-07-08 | | |
| EV-019 | REQ-SEC-004 | UC-07 (หลังสร้างงาน) | AC-07-09 | MD-DOM-01 | |
| PDPA | REQ-PRV-002 | UC-07 | AC-07-09 | MD-DOM-01, data-dictionary.md | |
| Operations | REQ-DAT-002 | UC-07 ขั้น 5 และ 6 | ไม่มี AC โดยตรง (ตรวจด้วยโมเดล) | MD-STM-01 | |
| Finance | REQ-BR-002 | UC-07 ขั้น 4 | ไม่มี AC โดยตรง | data-dictionary.md (Job.depositAmount) | |

## 2. ตรวจสองทาง

- REQ ใน UC-07 ที่ไม่มี AC: REQ-DAT-002 และ REQ-BR-002 (ตรวจผ่านโมเดลและการคำนวณ) REQ-CON-001 และ REQ-CON-003 เป็นข้อจำกัด ไม่ต้องมี AC
- AC ที่ไม่มี REQ: ไม่มี ทุก scenario ใน booking.feature มีป้าย @REQ
- เส้นทางใน UC-07 ที่ไม่มี AC: A1 (ไม่มีช่างว่าง) A2 (call center จองแทน) และ E3 (ช่างปฏิเสธ) ยังไม่มี scenario แยก E3 ถูกครอบด้วยตัวอย่าง R4 ของ AC-07-10 บางส่วน
- REQ นอก UC-07 (catalogue ส่วน 3) ยังไม่ได้ตามรอยถึง AC เพราะ use case ที่รองรับยังเป็นแบบ brief

ตารางนี้เรียบเรียงจากรหัสที่มีอยู่ใน catalogue.md, UC-07.md, booking.feature และ models.md ไม่มีรหัสใหม่

## 3. หลัง Baseline B7

ตารางนี้เป็นสภาพตอน B1 (UC-07 อย่างเดียว) ตารางตามรอยทั้งระบบ UC-01 ถึง UC-14 อยู่ที่ docs/srs/rtm-all.md สร้างและตรวจด้วย scripts/check_rtm.py
