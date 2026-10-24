# docs/srs

ต้นฉบับจากบทเรียนก่อนหน้า (วัตถุดิบของ spec.md) ใช้อ้างอิงเมื่อ spec.md ไม่ชัด

| ไฟล์ | คืออะไร | มาจากบทเรียน |
|---|---|---|
| catalogue.md | ข้อความต้นฉบับของ REQ ทุกข้อที่ UC-07, UC-08, UC-09 แตะ (3 ข้อที่ใช้ทุก feature ย้ายข้อความไปไว้ที่ specs/000-shared/constraints.md ตาม CR-04 REQ ของ UC-08 และ UC-09 เพิ่มตาม CR-05, CR-06 ข้อกำหนดข้ามทุก feature 10 ข้อเพิ่มตาม CR-07 รุ่น 1.4 ข้อของผู้ช่วย UC-14 14 ข้อเพิ่มตาม CR-09 รุ่น 1.5) | Requirements Catalogue |
| UC-07.md | use case fully dressed ของ UC-07 | Use Case และ Acceptance Criteria |
| UC-08.md, UC-09.md | use case fully dressed ของ UC-08 และ UC-09 (AI ร่างตอน /clarify ทีมตรวจ เข้า B2 ตาม CR-06, CR-05) | รอบ R1 release |
| glossary.md | คำที่ใช้ได้ และชื่อในโค้ด | Living Specification |
| baseline.md | Baseline B4 (ด้านบน = B3 + CR-09 กติกาข้อ 10) ถัดลงมาคือบันทึกเดิมของ B3 (= B2 + CR-07) บันทึกเดิมของ B2 (รวมการปรับปรุง 18 ต.ค. 2569 = ขอบเขต R1) และ B1 กติกาเปลี่ยนแปลง (ข้อ 8 และ 9 เพิ่มใน B3) และตาราง CR | Living Specification และ Verification, Traceability และ Change |
| operations.md | คู่มือรับมือเหตุ (runbook) ฉบับใช้จริงรุ่น 1.1 (CR-09 เพิ่มเหตุการณ์ที่ 6 ของผู้ช่วย) เจ้าของ Ops lead: 6 เหตุการณ์ เครื่องมือของคนเวร สำรองและกู้คืน บัญชี endpoint แบบบันทึกเหตุการณ์ และแผนเก็บหลักฐานช่วงใช้งานจริง (CR-07 Approved, EV-045) รุ่นร่างอยู่ในประวัติ git | รอบ Failure Day และประชุมทบทวน CR-07 |
| UC-14.md | use case fully dressed ของ UC-14 ผู้ช่วยตอบคำถามและเลื่อนนัด (เข้า B4 ตาม CR-09) | Data, AI และ Agent |
| UC-01.md, UC-02.md, UC-05.md, UC-12.md | use case fully dressed ของการเข้าสู่ระบบ (UC-01 UC-02) และการรับงานกับจับคู่ช่างใหม่ (UC-12 UC-05) (เข้า B6 ตาม CR-11 CR-12) | บทเสริม การตรวจรับและการส่งมอบ (R2 ส่วน A) |

กฎธุรกิจ (BR-01..03) และโมเดล (MD-xx) ที่ UC-07 ใช้ อยู่ใน specs/002-booking/rules.md และ models.md ส่วน BR-04 อยู่ใน specs/003-job-status/rules.md และ BR-05 ใน specs/004-cancel-refund/rules.md (MD-DOM-01 และ MD-STM-01 ใช้ร่วมทุก feature)
