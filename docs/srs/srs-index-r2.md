# SRS บ้านพร้อม | รุ่น 2.0 | Baseline B7 | 2569-12-10

SRS ฉบับนี้คือสารบัญของระบบที่ส่งมอบครบตาม TOR ของ R2 จัดตามโครงเนื้อหา SRS ใน ISO/IEC/IEEE 29148:2018 ข้อ 9.6 แบบเดียวกับ srs-index.md รุ่น 1.0 (Baseline B1 repo 02)
ทุกช่องชี้ไปไฟล์และรหัสจริง ไม่คัดลอกข้อความ ถ้าเนื้อหาในตารางนี้ขัดกับไฟล์ต้นทาง ให้เชื่อไฟล์ต้นทาง แล้วแก้ตารางนี้
ภาคผนวก ก ของ TOR R2 คือ Baseline ที่สารบัญนี้ชี้ (B5 ตอนลงนาม เปลี่ยนด้วย CR-11 ถึง CR-19 เป็น B7) docs/contract/tor-r2.md

| หัวข้อ SRS (ข้อใน 29148:2018) | บ้านพร้อมอยู่ที่ไหน (B7) | เปลี่ยนจากรุ่น 1.0 |
|---|---|---|
| 1.1 Purpose (9.6.2) | problem-statement.md (PB-01 PB-02) TOR R2 ข้อ 1 (วัตถุประสงค์) | เพิ่ม TOR |
| 1.2 Scope (9.6.3) | baseline.md B7 "ขอบเขตที่ส่งมอบ" spec.md ส่วน 2 ของ 002 ถึง 011 TOR R2 ข้อ 2 (UC-07 A2 ไม่อยู่ในขอบเขต) | จาก UC-07 อย่างเดียว เป็น 14 use case |
| 1.3 Product perspective (9.6.4) | MD-CTX-01 และ MD-SYS-01 รุ่น B7 ใน models.md ระบบภายนอก IF-01 IF-02 IF-03 IF-05 (IF-04 Won't ใน R2) | เพิ่ม IF-05 ตัวจริงที่สลับได้ |
| 1.4 Product functions (9.6.5) | use-cases.md ส่วน 1 และ 7 MD-UCD-01 รุ่น B7 พร้อมตารางสถานะ 14 use case UC-xx.md 12 ไฟล์ | ทุก use case มีสเปก |
| 1.5 User characteristics (9.6.6) | stakeholders.md (SH-01 ถึง SH-06) บทบาทเจ้าหน้าที่ call center Finance Ops ใน docs/handover/user-guide.md | เพิ่มคู่มือรายบทบาท |
| 1.6 Limitations (9.6.7) | specs/000-shared/constraints.md รุ่น 1.4 (REQ-CON-001, REQ-CON-003, D-00-01 ถึง D-00-05) docs/handover/mocks-and-limits.md | เพิ่มรายการของจำลอง |
| 1.7 Assumptions and dependencies (9.6.8) | question-register.md (ทุก Q ปิดแล้ว) spec.md ส่วน 9 (AS-15 AS-17 AS-18 AS-19) | B7 ไม่มีคำถามค้าง |
| 1.8 Apportioning of requirements (9.6.9) | baseline.md (B5 R1 รับแล้ว B6 R2 ส่วน A B7 R2 ส่วน B) TOR R2 ข้อ 4 งวดงาน | จากแผนร่างเป็นงวดตามสัญญา |
| 2 References | PDPA, สัญญา Payment Gateway (REQ-CON-003), OWASP Top 10:2025 และ API Security Top 10:2023, ISO/IEC/IEEE 29148:2018 และ 29119-3:2021, evidence.md และตาราง EV ใน catalogue.md (ถึง EV-056) | เพิ่ม OWASP และ 29119 |
| 3.1 External interfaces (9.6.11) | REQ-IF-001, 005, 010, 012 ใน catalogue.md และไฟล์กลาง สัญญา interface ส่วน 9.1 ของ models.md หน้าจอ 18 หน้าใน specs/*/mockups (UI-xx-nn) | ครบทุกหน้าจอและตัวจริง |
| 3.2 Functions (9.6.12) | REQ-FN ใน catalogue.md (ถึง REQ-FN-075) กฎ BR-01 ถึง BR-13 (business-rules.md ชี้ rules.md ของ feature) | จาก 5 ข้อเป็นทุกข้อของ 14 use case |
| 3.3 Usability (9.6.13) | รายการ "ต้องตรง" ในส่วน 12 ของทุก spec และ test UI-xx-nn ข้อเสนอ REQ-UX-002 Won't ใน R2 (วัดในการนำร่อง) | ยังบาง บอกตรง ๆ |
| 3.4 Performance (9.6.14) | REQ-QA-003 (ฉบับ Q-68) AC-07-08 AC-09-12 AC-08-09 QAS-1 ของผู้ช่วย docs/acceptance/load-test-r2.md | วัดจริงบนเครื่องทดสอบ ยังไม่วัดบนเครื่องจริง |
| 3.5 Logical database (9.6.15) | MD-DOM-01 รุ่น B7 data-dictionary.md (แถว B7) glossary.md backend/app/db/models.py | เพิ่ม entity ของ R2 |
| 3.6 Design constraints (9.6.16) | constraints.md ส่วน 1 2 (D-00-01 ถึง D-00-05) plan.md ข้อ 2 ของทุก feature | เพิ่มการตัดสินใจทางเทคนิค |
| 3.7 Standards compliance (9.6.17) | REQ-PRV-002, 010, 011, 012, REQ-CMP-001 (SH-05 ตรวจ PDPA) REQ-AI-020 ถึง 023 (หลักกลางส่วน 7) | ครบตามที่ SH-05 ตรวจ |
| 3.8 Software system attributes (9.6.18) | ไฟล์กลางส่วน 6 (REQ-OP-001, 005 ถึง 009, REQ-QA-010, REQ-SEC-010 ถึง 015) operations.md รุ่น 1.4 | จาก 2 ข้อเป็น 17 ข้อ |
| 4 Verification (9.6.19) | AC 146 ข้อใน specs/*/*.feature rtm-all.md (สร้างโดย scripts/check_rtm.py สายขาด 0) specs/000-shared/test-run.txt eval-results.md docs/acceptance/ (UAT OAT ทดสอบโหลด ผลตรวจรับรายงวด) | ตามรอยครบทั้งระบบ |
| 5 Supporting information (9.6.20) | UC-xx.md, business-rules.md, models.md, decisions.md, CR-01 ถึง CR-19 ในโฟลเดอร์ changes ของ feature, prompt-log.md, docs/handover/ | เพิ่ม CR และเอกสารส่งมอบ |

หัวข้อที่ยังบาง เขียนไว้ตรง ๆ ไม่แต่งให้เต็ม: 3.3 (ไม่มีการวัดกับผู้ใช้จริง) 3.4 (ยังไม่วัดบนเครื่องขนาดจริง Q-68)
