# ดัชนี specs

| โฟลเดอร์ | Use case | ฟีเจอร์ | สถานะ | ผู้รับผิดชอบ |
|---|---|---|---|---|
| 000-shared | ทุก use case | Constraint กลางที่ใช้กับทุก feature (constraints.md รุ่น 1.3 ส่วน 6 เพิ่ม 4 ข้อตาม CR-11 CR-13 ส่วน 7 "AI" เพิ่มตาม CR-09) ไม่ใช่ feature ตั้งแต่ CR-07 มี AC ข้ามทุก feature (cross-cutting.feature AC-00-01 ถึง 08) พร้อม ac-results.md, rtm.md, gaps.md และ test-run.txt ของทั้งโครงการ | รุ่น 1.1 (B3, CR-07) | RE lead กลุ่ม X |
| 002-booking | UC-07 | จองงานบริการซ่อมบำรุง (ทำครบรอบ clarify, plan, tasks, implement, test และรอบเปลี่ยนแปลง CR-03, CR-04 รอบ R1 โค้ดถูกแตะตามตารางผลกระทบของ CR-05, CR-06 spec ไม่เปลี่ยน) | spec 1.5 (B3 = B2 + CR-07) CR-07 อยู่ใน changes/ ของ feature นี้ | กลุ่ม X |
| 003-job-status | UC-09 | ช่างอัปเดตสถานะงานภาคสนาม (ทำครบรอบ clarify, plan, tasks, implement, test วันที่ 18 ต.ค. 2569 ไฟล์ชุดเดียวกับ 002) | spec 1.1 (B3 = B2 + CR-07 เข้า B2 ด้วย CR-05) | กลุ่ม X |
| 004-cancel-refund | UC-08 | ลูกค้ายกเลิกการจองและรับเงินคืน (ทำครบรอบเช่นเดียวกัน ใช้ BR-01 และโค้ดคืนมัดจำของ 002 ร่วม) | spec 1.1 (B3 = B2 + CR-07 เข้า B2 ด้วย CR-06) | กลุ่ม X |
| 005-ai-assistant | UC-14 | ผู้ช่วยตอบคำถามลูกค้าและเลื่อนนัด (ส่วนแรกของระบบที่มี AI อยู่ข้างใน มี eval/ และ prompts/ เพิ่มจากชุดไฟล์ของ 002 ถึง 004) | spec 1.0 (B4 = B3 + CR-09) changes/CR-09.md ผล eval ใน eval-results.md | กลุ่ม X |
| 006-identity | UC-02, UC-01 | ลูกค้าลงทะเบียนและเข้าสู่ระบบ ช่างเข้าสู่ระบบ ด้วยเบอร์โทรและ OTP ตัวตนของทุก endpoint (R2 ส่วน A ตาม CR-11 เข้า B6) | Approved (B6) | กลุ่ม X |
| 007-accept-rematch | UC-12, UC-05 | ช่างรับหรือปฏิเสธงาน และจับคู่ช่างใหม่แบบกฎ (R2 ส่วน A ตาม CR-12 เข้า B6) | Approved (B6) | กลุ่ม X |

001-booking (ตัวอย่างจองคิวตรวจสุขภาพของรายวิชาปริญญาตรี ที่มากับ template) ถูกลบออกหลังใช้ซ้อมใน Studio ช่วงที่ 1

กติกา
- 1 โฟลเดอร์ = 1 ฟีเจอร์ระดับ use case ชื่อโฟลเดอร์ขึ้นต้นด้วยเลข 3 หลัก ตามด้วยชื่อฟีเจอร์ภาษาอังกฤษตัวเล็ก
- เลข 000 สงวนไว้ให้ของที่ใช้ร่วมกันทุก feature
- spec.md ของทุก feature อ้าง Constraint กลางด้วยบรรทัดเดียวในส่วน 8 ไม่คัดลอกข้อความ (ดู docs/shared-constraints-guide.md)
- เลข F-nn (rtm.md) และ GAP-nn (gaps.md) นับต่อกันทั้งโครงการ: 002 ใช้ F-01 ถึง 08 และ GAP-01 ถึง 17, 003 ใช้ F-09 ถึง 11 และ GAP-18, 004 ใช้ F-12 ถึง 14 และ GAP-19, 20 รอบ CR-07 ใช้ GAP-21 ถึง 28 (specs/000-shared/gaps.md) 005 ใช้ F-15, 16 และ GAP-29 ถึง 34 ส่วน T-nn นับใหม่ทุก feature
- ของที่ใช้ร่วมทุก feature (MD-DOM-01, MD-STM-01, BR-01, ตาราง jobs และ job_status_history, set_status, technician_view, cancel_job, คิวแจ้งเตือน) อยู่ที่ 002-booking และโค้ดของมัน feature อื่นอ้างด้วย ID ไม่คัดลอก
- R2 ส่วน A: 006 ใช้ F-17 F-18 และ GAP-43 007 ใช้ F-19 F-20 และ GAP-44 000-shared ใช้ GAP-39 ถึง GAP-42 ส่วน B เริ่มที่ F-21 และ GAP-45 CR ต่อจาก CR-13 Q ต่อจาก Q-70 EV ต่อจาก EV-052
