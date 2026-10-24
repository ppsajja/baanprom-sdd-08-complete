# SRS บ้านพร้อม | รุ่น 1.0 | Baseline B1 | 2569-09-06

> หมายเหตุ: ไฟล์นี้เป็นสภาพตอนประกาศ Baseline B1 คงไว้เป็นประวัติ สถานะล่าสุดของคำถาม REQ และ Baseline ดูที่ docs/srs/baseline.md
> สารบัญ SRS ของระบบที่ส่งมอบครบ (Baseline B7) อยู่ที่ docs/srs/srs-index-r2.md

SRS ฉบับนี้เป็นสารบัญตามโครงเนื้อหา SRS ใน ISO/IEC/IEEE 29148:2018 ข้อ 9.6 ทุกช่องชี้ไปไฟล์และรหัสจริง ไม่คัดลอกข้อความ
มาจากบทเรียน: Modern Specification และ SDD
ถ้าเนื้อหาในตารางนี้ขัดกับไฟล์ต้นทาง ให้เชื่อไฟล์ต้นทาง แล้วแก้ตารางนี้

| หัวข้อ SRS (ข้อใน 29148:2018) | บ้านพร้อมอยู่ที่ไหน |
|---|---|
| 1.1 Purpose (9.6.2), 1.2 Scope (9.6.3) | specs/002-booking/spec.md ส่วน 1 และ 2 (PB-02, EV-004, EV-009, EV-012) และ problem-statement.md (SC-01 ถึง SC-04) |
| 1.3 Product perspective (9.6.4) | MD-CTX-01 และ MD-SYS-01 ใน models.md ระบบภายนอก IF-01 ถึง IF-04 |
| 1.4 Product functions (9.6.5) | use-cases.md (UC-01 ถึง UC-13) feature ที่มีสเปกแล้วคือ UC-07 |
| 1.5 User characteristics (9.6.6) | stakeholders.md (SH-01 ถึง SH-06) |
| 1.6 Limitations (9.6.7) | REQ-CON-001, REQ-CON-003 ใน catalogue.md |
| 1.7 Assumptions and dependencies (9.6.8) | questions.md (AS-01 ถึง AS-05, Q-xx) และ spec.md ส่วน 9 |
| 1.8 Apportioning of requirements (9.6.9) | decisions.md ส่วน 5 แผนรุ่น R1 และ R2 |
| 2 References | PDPA, สัญญา Payment Gateway (REQ-CON-003), evidence.md |
| 3.1 External interfaces (9.6.11) | REQ-IF-001, REQ-IF-005 (Draft), REQ-IF-002, REQ-IF-006 (Draft) และ Interface Contract IF-01, IF-02 ใน models.md ยังไม่มีหน้าจอ |
| 3.2 Functions (9.6.12) | REQ-FN-008, REQ-FN-012, REQ-FN-041 (Draft), REQ-BR-001, REQ-BR-002 ใน catalogue.md และ REQ-FN-014, REQ-FN-030 ใน catalogue-other.md |
| 3.3 Usability (9.6.13) | REQ-UX-005 ใน catalogue-other.md หมวดนี้ยังบาง |
| 3.4 Performance (9.6.14) | REQ-QA-003 ข้อเดียว หมวดนี้จะเติมในบทเรียนข้อกำหนดคุณภาพ |
| 3.5 Logical database (9.6.15) | REQ-DAT-002, MD-DOM-01, data-dictionary.md, glossary.md |
| 3.6 Design constraints (9.6.16) | REQ-CON-001, REQ-CON-003 ยังไม่มีข้อตัดสินใจทางเทคนิค (เป็นงานของ plan.md) |
| 3.7 Standards compliance (9.6.17) | REQ-PRV-002 (PDPA) REQ-PRV-00x และ REQ-CMP-00x ยังเป็น Draft |
| 3.8 Software system attributes (9.6.18) | REQ-SEC-004, REQ-OP-002 หมวดนี้ยังบาง |
| 4 Verification (9.6.19) | AC-07-01 ถึง AC-07-10 ใน specs/002-booking/booking.feature และ traceability.md |
| 5 Supporting information (9.6.20) | UC-07.md, business-rules.md (BR-01 ถึง BR-05), models.md, cc-log.md, decisions.md (DR-01, DR-02), Decision Log D-07-01, D-07-02 ใน spec.md |

รหัส SC และ AS บางตัวกำหนดขึ้นเพื่อให้ชุด repo ต่อเนื่อง ดูหมายเหตุใน problem-statement.md และ questions.md

หัวข้อที่ยังว่างหรือบาง เขียนไว้ตรง ๆ ไม่แต่งให้เต็ม: 3.3, 3.4, 3.7, 3.8
