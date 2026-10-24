# baanprom-sdd-08-complete

repo ตัวอย่างของรายวิชา 517511-266 Requirement Engineering (AI-Native RE)
ภาควิชาคอมพิวเตอร์ คณะวิทยาศาสตร์ มหาวิทยาลัยศิลปากร

เคส: บ้านพร้อม (แพลตฟอร์มจองช่างซ่อมบ้าน) ระบบครบทุก use case UC-01 ถึง UC-14 ส่งมอบตาม TOR ของ R2
ข้อมูลทั้งหมดในเคสนี้เป็นข้อมูลสมมติเพื่อการสอน

## repo นี้คืออะไร

repo นี้คือสภาพสุดท้ายของงานกลุ่มตัวอย่าง (กลุ่ม X) หลังจบวิชา ระบบที่ส่งมอบครบตาม TOR ของ R2 (docs/contract/tor-r2.md) และตรวจรับครบสี่งวด (งวด 4 รับแบบมีเงื่อนไข)
ต่อจาก baanprom-sdd-07-r1-done (ประวัติ commit ของ repo 07 อยู่ครบใน repo นี้) และเพิ่มงานสองส่วน

- ส่วน A (แท็ก r2-part-a) ตัวตนด้วย OTP (UC-01 UC-02) ช่างรับหรือปฏิเสธงานและจับคู่ช่างใหม่ (UC-12 UC-05) จองช่างคนเดิม คิวข้อความในฐานข้อมูลและการรันหลาย process ตั้ง Baseline B6
- ส่วน B (แท็ก b7) ตารางเวลาของช่าง (UC-04) การแจ้งเตือนทาง SMS หรือ LINE (UC-10) การให้คะแนน (UC-11) การกระทบยอด (UC-13) ตัวเชื่อมระบบภายนอกที่สลับเป็นของจริงได้ด้วยค่าตั้ง TOR การตรวจรับรายงวด เอกสารส่งมอบ ตั้ง Baseline B7

การเดินของคน คำตอบของเจ้าของเรื่อง การประชุม และการลงนาม เป็นข้อมูลสมมติ ผลที่วัดด้วยเครื่อง (test eval เดินซ้อม UAT OAT ทดสอบโหลด) มาจากการรันจริงทุกตัว รวมทั้งรอบที่ไม่ผ่าน

## ใช้เริ่มบทเรียนไหน และเป็นเฉลยของบทไหน

- ไม่ใช่จุดเริ่มของบทใด เป็นสภาพสุดท้ายหลังจบวิชา ใช้เทียบงานของกลุ่มทั้งเทอม
- เป็นเฉลยของ **บทเสริม การตรวจรับและการส่งมอบในงานจ้าง** (TOR ของ R2 หัวข้อ 4 และ 8 เกณฑ์ตรวจรับรายงวด ตารางความรุนแรง ระยะรับประกัน การรับส่วน AI สามชั้น)

## ชุด repo ทั้ง 8

แต่ละ repo คือจุดเริ่มของบทหนึ่ง และเป็นเฉลยของบทก่อนหน้า repo ถัดไปจึงเป็นเฉลยของงานในบทนี้

| repo | ใช้เริ่มบท | ข้างในคือเฉลยของ |
|---|---|---|
| [baanprom-sdd-01-spec](https://github.com/ppsajja/baanprom-sdd-01-spec) | Modern Specification และ SDD | ชิ้นงานบท 1 ถึง 7 (Problem Framing ถึง Integrated Modelling) |
| [baanprom-sdd-02-build](https://github.com/ppsajja/baanprom-sdd-02-build) | AI Build from Spec | Modern Specification และ SDD: spec plan tasks ที่กลุ่มเขียนเอง และ Baseline B1 |
| [baanprom-sdd-03-vv](https://github.com/ppsajja/baanprom-sdd-03-vv) | Verification, Validation และ Change | AI Build from Spec: โค้ดและ test ที่ AI สร้าง ac-results gaps CR-01 CR-02 |
| [baanprom-sdd-04-ops](https://github.com/ppsajja/baanprom-sdd-04-ops) | Operational, Security และ Privacy | V&V และ Change: RTM mockup CR-03 ถึง CR-06 Baseline B2 และ R1 ครบ (003 004) |
| [baanprom-sdd-05-ai](https://github.com/ppsajja/baanprom-sdd-05-ai) | Data, AI และ Agent | Operational, Security และ Privacy: CR-07 อนุมัติ และ Baseline B3 |
| [baanprom-sdd-06-accept](https://github.com/ppsajja/baanprom-sdd-06-accept) | RE in One Line และการตรวจรับ | Data, AI และ Agent: ผู้ช่วย AI UC-14 (CR-09) และ Baseline B4 |
| [baanprom-sdd-07-r1-done](https://github.com/ppsajja/baanprom-sdd-07-r1-done) | บทเสริม การตรวจรับและการส่งมอบ | RE in One Line และการตรวจรับ: ตรวจรับ R1 (CR-10) และ Baseline B5 |
| **baanprom-sdd-08-complete** (repo นี้) | (ระบบสมบูรณ์ของวิชา) | บทเสริม การตรวจรับและการส่งมอบ: R2 ครบทุก UC ส่งมอบตาม TOR และ Baseline B7 |

## อะไรใหม่เมื่อเทียบกับ repo ก่อนหน้า (baanprom-sdd-07-r1-done)

ส่วน A: commit "R2 ส่วน A" (แท็ก r2-part-a)

| เรื่อง | ไฟล์ | มาจาก |
|---|---|---|
| ลูกค้าลงทะเบียนและเข้าสู่ระบบ ช่างเข้าสู่ระบบ ด้วยเบอร์และ OTP ตัวตนจาก token ทุก endpoint | specs/006-identity, backend/app/auth | CR-11 |
| ช่างรับหรือปฏิเสธงาน จับคู่ช่างใหม่แบบกฎ ลูกค้าปฏิเสธช่างแทนได้ | specs/007-accept-rematch, backend/app/matching | CR-12 |
| ลูกค้าจองช่างคนเดิม เลขโทร call center เมื่อไม่มีช่างว่าง | specs/002-booking (BR-08) | CR-08 |
| คิวข้อความและตัวนับในฐานข้อมูล หลาย process งานเบื้องหลังที่เดียว | backend/app/notify/queue.py, backend/app/ops/ | CR-13 |
| ทดสอบโหลดบน PostgreSQL หลาย process | docs/acceptance/load-test-r2.md | EV-052 |
| Baseline B6 | docs/srs/baseline.md | EV-051 |

ส่วน B: commit "R2 ส่วน B" และ commit ของการตรวจรับและส่งมอบ (แท็ก b7)

| เรื่อง | ไฟล์ | มาจาก |
|---|---|---|
| UC-04 ช่างเพิ่ม ปิดช่วงเวลาว่าง ประกาศวันหยุด ช่วงที่ปิดไม่ถูกค้นหา จอง หรือจับคู่ | specs/008-schedule, backend/app/schedule | CR-14 |
| UC-11 ลูกค้าให้คะแนนงานที่เสร็จ งานละครั้งใน 14 วัน กันรีวิวตัวเอง ปิดบังข้อมูลในความเห็น ค่าเฉลี่ยในผลค้นหาไม่เปลี่ยนลำดับ | specs/009-rating, backend/app/rating | CR-15 |
| UC-13 Finance นำเข้ารายงานประจำวันของ gateway จับคู่ แสดงรายการต่าง ปิดเงินคืนที่ไม่รู้ผลโดยไม่ส่งซ้ำ (Q-41) | specs/010-reconciliation, backend/app/reconciliation | CR-16 |
| UC-10 เลือกรับข้อความทาง SMS หรือ LINE เชื่อม LINE ผ่าน webhook ที่ตรวจลายเซ็น LINE ล้มส่ง SMS แทน | specs/011-notifications, backend/app/notify | CR-17 |
| ตัวเชื่อม IF-01 IF-02 IF-03 IF-05 สลับตัวจำลองกับตัวจริงด้วยค่าตั้ง สถานะใน /ops/integrations หน้าที่อยู่ของลูกค้า พิกัดจาก IF-03 กุญแจแยกของ call center และ Finance เครื่องมือเลื่อนนัดกลับ | backend/app/integrations, backend/app/maps, backend/app/callcenter, specs/000-shared/constraints.md รุ่น 1.4 | CR-18 |
| ผู้ช่วย: บอกว่าระยะเวลาเงินคืนขึ้นกับธนาคาร (Q-65) ปิดเองเมื่อรุ่นโมเดลไม่ผ่าน eval ชุดลับ 50 ข้อ LLM ตัวจริงที่ปิดไว้ LLM ไม่ตอบใช้คำตอบสำรอง | specs/005-ai-assistant, backend/app/assistant | CR-19, GAP-50 |
| ปิดทุกคำถามในทะเบียน (ตอบหรือ Won't พร้อมเหตุผลและเจ้าของ) | specs/000-shared/changes/CR-18.md (บันทึก EV-053), docs/srs/question-register.md | EV-053 |
| ตามรอยทั้งระบบ EV ถึง test สคริปต์ตรวจสายขาด | docs/srs/rtm-all.md, scripts/check_rtm.py | |
| สเปกทั้งระบบ: catalogue 1.8 MD-UCD-01 MD-CTX-01 MD-DOM-01 รุ่น B7 สัญญา interface ของตัวจริง SRS index ตาม 29148 | docs/srs/ | |
| TOR ของ R2 ผลตรวจรับรายงวด UAT R2 OAT R2 รายงานปิดการทดสอบ บันทึกการตรวจรับ | docs/contract/tor-r2.md, docs/acceptance/ | EV-054 ถึง EV-056 |
| เอกสารส่งมอบ: คู่มือผู้ใช้ห้าบทบาท คู่มือติดตั้ง รายการของจำลอง แผน hypercare และระยะรับประกัน | docs/handover/ | TOR งวด 4 |
| Baseline B7 | docs/srs/baseline.md | |

ดู diff ของแต่ละส่วน: `git diff b5 r2-part-a --stat` (ส่วน A) และ `git diff r2-part-a b7 --stat` (ส่วน B)

> แท็ก (เช่น b5, r2-part-a, b7) ใช้ได้เมื่อ clone repo นี้ ถ้าสร้างด้วยปุ่ม Use this template บน GitHub จะไม่ได้ประวัติ commit และแท็กมาด้วย

## ระบบที่ส่งมอบ แยกตาม use case

| UC | ทำอะไรได้ | สเปก |
|---|---|---|
| UC-01 | ช่างเข้าสู่ระบบด้วยเบอร์ที่บ้านพร้อมลงทะเบียนและ OTP | 006-identity |
| UC-02 | ลูกค้าลงทะเบียน เข้าสู่ระบบ ดู เพิ่ม ลบที่อยู่ (พิกัดหาจากข้อความ) | 006-identity |
| UC-03 | ค้นหาช่างที่ว่างใน 7 วันในระยะ 15 กม. (ขั้น 2 ของ UC-07) | 002-booking |
| UC-04 | ช่างจัดตารางเวลาว่างและวันหยุด | 008-schedule |
| UC-05 | จับคู่ช่างใหม่เมื่อช่างปฏิเสธ หาไม่ได้ใน 2 ชั่วโมงคืนเงินเต็ม | 007-accept-rematch |
| UC-06 | ชำระมัดจำ 50 ใน 100 ของราคาประเมิน (ขั้น 5 ของ UC-07) | 002-booking |
| UC-07 | จองงาน ล็อกช่วงเวลา 10 นาที จองช่างคนเดิม | 002-booking |
| UC-08 | ลูกค้ายกเลิกและรับเงินคืนตาม BR-01 | 004-cancel-refund |
| UC-09 | ช่างอัปเดตสถานะงาน ลูกค้าและ call center เห็นประวัติ | 003-job-status |
| UC-10 | รับข้อความของงานทาง SMS หรือ LINE | 011-notifications |
| UC-11 | ให้คะแนนช่างหลังงานเสร็จ | 009-rating |
| UC-12 | ช่างรับหรือปฏิเสธงานภายใน 30 นาที | 007-accept-rematch |
| UC-13 | Finance กระทบยอดกับรายงานของ gateway | 010-reconciliation |
| UC-14 | ผู้ช่วยตอบคำถาม 5 เรื่องและเลื่อนนัดตาม BR-06 หัวหน้า call center ปิดได้ทันที | 005-ai-assistant |

ไม่อยู่ในระบบ (ตัดสินแล้ว): จองหรือยกเลิกแทนโดย call center (UC-07 A2) ยืนยันตัวตนช่างกับ Thai-ID (Q-69) โหมดออฟไลน์ของแอปช่าง คิวรอ ดูเหตุผลใน docs/srs/baseline.md ส่วน B7

## อ่านตามลำดับนี้เพื่อเห็นการส่งมอบ

1. docs/contract/tor-r2.md (สัญญา: ขอบเขต งวด เกณฑ์ รับประกัน และตาราง "ต่างจากหน้าบทเรียน")
2. specs/000-shared/changes/CR-18.md ส่วนบันทึกประชุม EV-053 แล้ว docs/srs/question-register.md
3. specs/008-schedule ถึง specs/011-notifications (spec, .feature, rules, mockups, changes)
4. docs/srs/rtm-all.md (ตามรอยทั้งระบบ) และ docs/srs/srs-index-r2.md
5. docs/acceptance/r2-milestone-1.md ถึง r2-milestone-4.md แล้ว acceptance-record-r2.md (หลักฐานที่ใช้อยู่ใน uat-r2.md oat-results-r2.md test-completion-r2.md)
6. docs/handover/README.md แล้ว docs/srs/baseline.md ส่วน B7

## ทีม

- ชื่อทีม: กลุ่ม X (ตัวอย่างของรายวิชา)
- สมาชิก: สมาชิก A, สมาชิก B, สมาชิก C, สมาชิก D
- เครื่องมือ AI ที่ใช้: Copilot Chat โหมด Agent ใน GitHub Codespaces (รอบนี้ผู้สอนเดโมด้วย Claude Code)

## โครงของ repo

```
README.md                      ไฟล์นี้
AGENTS.md                      กติกาที่ AI ต้องทำตาม 10 ข้อ (agent-pack รุ่น 2)
CLAUDE.md                      ชี้ไป AGENTS.md (สำหรับ Claude Code)
prompt-log.md                  บันทึกทุกคำสั่ง (เพิ่มต่อท้ายเท่านั้น ล่าสุด #101)
scripts/check_rtm.py           ตรวจสายตามรอยทั้งระบบ และเขียน docs/srs/rtm-all.md
docs/contract/                 TOR ของ R2
docs/acceptance/               แผนและผลตรวจรับ R1 และ R2 UAT OAT ทดสอบโหลด ผลรายงวด
docs/handover/                 เอกสารส่งมอบ (เริ่มอ่านที่ docs/handover/README.md)
docs/srs/                      catalogue 1.8, UC-xx.md 12 ไฟล์, baseline (B7 ด้านบน), operations.md รุ่น 1.4, rtm-all, question-register, srs-index-r2
specs/000-shared/              Constraint กลางรุ่น 1.4 AC ข้ามทุก feature CR-10 CR-11 CR-13 CR-18 test-run ของทั้งโครงการ
specs/002-booking/ ถึง 011-notifications/   หนึ่งโฟลเดอร์ต่อหนึ่ง feature (ดู specs/README.md)
backend/                       Python FastAPI + SQLAlchemy (app/integrations คือตัวเชื่อมระบบภายนอก) uat_*.py oat_r2.py load_test.py ใช้ตอนตรวจรับ ไม่ใช่ส่วนของระบบ
frontend/                      React (Vite) + Tailwind CSS + Vitest
```

## วิธีรันทั้งระบบ

หลังบ้าน (test และ eval)

```
cd backend
pip install -r requirements.txt
python -m pytest -v -k "AC_"
python eval_run.py
```

เปิดระบบทั้งระบบบนเครื่องนักพัฒนา พร้อมข้อมูลสมมติ

```
cd backend
python seed_demo.py
APP_ENV=development OPS_TOKEN=ops-dev CALL_CENTER_TOKEN=cc-dev FINANCE_TOKEN=fin-dev uvicorn app.main:app --reload --port 8000
```

อีกหน้าต่างหนึ่ง

```
cd frontend
npm install
npm test
npm run dev
```

เปิด http://localhost:5173 แล้วเข้าสู่ระบบ
- ลูกค้า: 081-234-5678 (สมชาย) หรือ 089-111-2222 (สมศรี) ช่าง: 086-555-0101 ถึง 086-555-0103 โหมด development หน้าจอแสดงรหัส OTP ให้เอง
- เจ้าหน้าที่: แตะ "เจ้าหน้าที่" เลือกบทบาท ใส่กุญแจที่ตั้งไว้ข้างบน (call center = cc-dev, Finance = fin-dev) กุญแจของบทบาทที่ไม่ได้ตั้งใช้ไม่ได้ทุกโหมด
- ระบบภายนอกทุกตัวเป็นตัวจำลอง ข้อความที่ส่งดูได้ที่ `curl -H "X-Ops-Token: ops-dev" localhost:8000/ops/notifications/outbox` รายงานของ gateway สำหรับลองหน้ากระทบยอด สร้างด้วย `python gateway_report_mock.py --date <วันที่ YYYY-MM-DD> > report.csv`
- ระบบตั้งค่าตั้งต้นเป็นโหมด production (REQ-SEC-012) ถ้าไม่ตั้ง APP_ENV หน้า /docs จะปิด และไม่แสดงรหัส OTP

ติดตั้งแบบระบบจริงบน PostgreSQL หลาย process และเปลี่ยนตัวจำลองเป็นตัวจริง: docs/handover/install-guide.md (ส่วน R2)
ทำซ้ำการตรวจรับบนเครื่องทดสอบ: docs/acceptance/uat-r2.md ข้อ 3 และ oat-plan-r2.md (backend/uat_seed.py uat_replay.py uat_replay_r2.py oat_r2.py)
ตรวจสายตามรอย: `python3 scripts/check_rtm.py` ต้องจบด้วย "สายขาด: 0"

ผลที่ควรเห็น (รันจริงจาก repo นี้ ตรงกับ specs/000-shared/test-run.txt และ specs/005-ai-assistant/eval-results.md)

- Python 3.11 และ 3.12: บรรทัดสุดท้าย `188 passed, 1 warning` ไม่มี test ข้าม
- หน้าจอ: `Test Files 39 passed (39)` และ `Tests 78 passed (78)`
- eval: 21 จาก 21 เกณฑ์ ชุดลับ 50 จาก 50
- เดินซ้อม scenario R1 และ R2 ผ่าน API: 22 จาก 22 (docs/acceptance/uat-dryrun-r2-full.txt)
- OAT R2: docs/acceptance/oat-results-r2.md
- ถ้าเปิดแท็ก r2-part-a จะได้ 139 passed และ 63 passed

## สิ่งที่ยังเป็นของจำลอง

รายการเต็มพร้อมผู้รับผิดชอบและรายการตรวจก่อนเปิดใช้จริงอยู่ที่ docs/handover/mocks-and-limits.md ส่วน R2

- Payment Gateway (IF-01) SMS และ LINE (IF-02) บริการแผนที่ (IF-03 รู้จัก 15 เขต) LLM ของผู้ช่วย (IF-05 MockLLM) ใช้ตัวจำลองอยู่ ตัวจริงเขียนตามสัญญา interface และทดสอบผ่าน transport จำลองเท่านั้น ยังไม่เคยเรียกผู้ให้บริการจริง เพราะยังไม่มีสัญญา
- ผล eval วัดกับ MockLLM จึงไม่ได้บอกว่า LLM ตัวจริงจะผ่าน ผู้ช่วยปิดเองเมื่อใช้รุ่นที่ยังไม่ผ่าน eval (REQ-AI-023)
- ชั้นที่ 2 ของการรับผู้ช่วย (ทดลองแบบเงา 2 สัปดาห์ นำร่อง 4 สัปดาห์) ยังไม่ได้ทำ งวด 4 จึงรับแบบมีเงื่อนไข
- เครื่องทดสอบคือเครื่องเดียว CPU 2 ตัว AC-07-08 ยังไม่ได้วัดบนเครื่องขนาดจริง (Q-68)
- การเดินของผู้ใช้และคณะกรรมการ การประชุม และการลงนาม เป็นข้อมูลสมมติ ชุดลับของ eval set อยู่ใน repo เพื่อการสอน ในงานจริงอยู่กับผู้ว่าจ้าง
- เลขโทรของ call center เป็นเลขสมมติ 02-000-0000 เบอร์ทุกเบอร์เป็นเบอร์สมมติ

## คำถามที่ยังเปิด

ไม่มี ทุกคำถามมีคำตอบ หรือเป็น Won't พร้อมเหตุผลและเจ้าของ (docs/srs/question-register.md)
สิ่งที่เหลือเป็นเงื่อนไขก่อนเปิดใช้จริง ไม่ใช่คำถาม: สัญญากับผู้ให้บริการ ทดลองแบบเงาและนำร่อง AC-07-08 บนเครื่องจริง ออกบัญชีช่างทุกคน (F-21) (docs/handover/hypercare-and-golive.md ส่วน 3)

## Reflection ของกลุ่ม X รอบ R2 (5 บรรทัด)

1. TOR ที่ตรวจด้วยหลักฐานได้ ทำให้การตรวจรับแต่ละงวดเป็นการเปิดไฟล์ผล ไม่ใช่การต่อรอง แต่งวดที่ขึ้นกับผู้ใช้จริง (นำร่อง) ต้องมีข้อในสัญญาที่บอกว่าทำอย่างไรเมื่อทำไม่ได้
2. สคริปต์ตรวจรับของเราผิดสามครั้ง (GAP-46 GAP-48 GAP-49) ระบบไม่ผิดเลย ถ้าไม่อ่านผลดิบทุกบรรทัด เราจะเขียนผลผิดทั้งสองทาง
3. test เขียวทั้งชุดไม่เห็นว่า LLM ไม่ตอบแล้วลูกค้าได้ 500 (GAP-50) เพราะตัวจำลองไม่เคยล้ม ช่องว่างนี้โผล่ตอนเขียนสัญญา interface ของตัวจริง
4. การทำตารางตามรอยทั้งระบบด้วยสคริปต์ เจอว่าแผนภาพ use case รุ่นแรกไม่มี UC-14 เลย ทั้งที่มีสเปกและโค้ดมาตั้งแต่ B4
5. "ส่งมอบครบ" ไม่เท่ากับ "เปิดใช้ได้" รายการก่อนเปิดใช้จริงส่วนใหญ่เป็นงานของผู้ว่าจ้าง (สัญญา เครื่อง การอบรม) ไม่ใช่โค้ด
