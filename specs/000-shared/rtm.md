# rtm.md ตารางตามรอยของข้อกำหนดข้ามทุก feature (Constraint กลางรุ่น 1.1 ส่วน 6)

ไฟล์ใหม่ใน CR-07 (24 ต.ค. 2569) AI ร่าง ทีมตรวจทุกแถวและเขียนช่อง "ทีมตัดสิน" เอง แถวที่ผูกกับ feature เดียวอยู่ใน rtm.md ของ feature นั้น ส่วน 3

| REQ | ที่มา (EV) | AC | test | task | โค้ด / เอกสาร | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|
| REQ-OP-001 | เหตุการณ์ A, Q-25, EV-045 | AC-00-04 (และ AC-07-08, AC-09-12, AC-08-09 ใน feature) | test_AC_00_04_health_and_ready | T-24 ของ 002 | ops/router.py | ครบในห้องเรียน เวลาล่มรายเดือนวัดบนระบบจริง | รับ |
| REQ-OP-005 | เหตุการณ์ A, B, C, Q-43 | AC-00-01, AC-00-02, AC-00-03 | test_AC_00_01, test_AC_00_02, test_AC_00_03 | T-24 ของ 002 | main.py (middleware), ops/metrics.py, ops/alerts.py, privacy.py (log_event) | ขาดบางส่วน: ช่องทางถึงคนเวรยังเป็น log (GAP-28) | รับ ตาม GAP-28 ต่อ |
| REQ-OP-006 | เหตุการณ์ B, Q-43 | ไม่มี AC | ไม่มี (walkthrough EV-045) | T-25 ของ 002 | docs/srs/operations.md | ครบสำหรับเหตุการณ์ที่ 1 ถึง 3 | รับ |
| REQ-OP-007 | Q-44 | AC-00-05 (และ AC-07-18) | test_AC_00_05_backup_restore_drill_within_rpo | T-23 ของ 002 | ops/backup.py, ops_backup.py, operations.md ส่วนสำรองและกู้คืน | ครบในห้องเรียน ยังไม่ซ้อมบนระบบจริง | รับ เป็นเงื่อนไขก่อนเปิด R1 |
| REQ-QA-010 | เหตุการณ์ B, Q-40 | ดู rtm.md ของ 002, 003, 004 | | T-18 ของ 002, T-08 และ T-10 ของ 003, T-07 และ T-08 ของ 004 | payments/, notify/queue.py, refund/service.py | ครบ IF-03 ยังไม่เรียกจริง | รับ |
| REQ-SEC-010 | MU-01, เหตุการณ์ C, Q-47 | AC-00-08 (และ AC ใน feature) | test_AC_00_08 | T-24 ของ 002 (บรรทัดที่ 3) | ops/audit.py, ops/alerts.py | ขาดบางส่วน (GAP-24) | รับความเสี่ยงตาม SH-01 |
| REQ-SEC-011 | TH-03, Q-45 | AC-07-14 | ดู 002 | T-19 ของ 002 | booking/service.py | ครบ | รับ |
| REQ-SEC-012 | OWASP API5, API8, API9:2023 EV-045 | AC-00-06, AC-00-07, AC-07-16 | test_AC_00_06, test_AC_00_07 | T-21, T-24, T-25 ของ 002 | main.py, clock.py, ops/guard.py, operations.md บัญชี endpoint | ครบ | รับ |
| REQ-PRV-010 | PDPA, Q-46 | AC-07-17, AC-07-18 | ดู 002 | T-22, T-23 ของ 002 | erasure/ | ครบ | รับ |
| REQ-CMP-001 | PDPA, Q-46 | ไม่มี AC (inspection) | ไม่มี | ไม่มี task | constraints.md บรรทัด "ผลการตรวจโดยฝ่ายกฎหมาย" | ครบ | รับ |

ตามรอยย้อนกลับ: โค้ดใหม่ทุกไฟล์ใน backend/app/ops/ และ backend/app/erasure/ มีรหัส REQ ในบรรทัดแรก ไม่มีของเกิน
ข้อค้นพบ: ไม่มี F ใหม่ ช่องว่างที่พบอยู่ใน gaps.md (GAP-21 ถึง GAP-28)

## รอบตรวจรับ R1 (EV-049 EV-050 ตั้ง Baseline B5)

| REQ | ที่มา (EV) | AC | test | task | โค้ด / เอกสาร | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|
| REQ-OP-005 บรรทัดที่ 3 (log ในระบบจริง) | EV-049 (OAT-6 DEF-02) | AC-00-03 | test_AC_00_03_production_app_writes_structured_log_to_stdout | T-33 ของ 002 | main.py (configure_logging) | ครบ OAT-6 รอบสองผ่าน | รับ (Ops lead) |
| REQ-OP-005 บรรทัดที่ 2 (ช่องทางถึงคนเวร) | EV-048 | AC-00-02 | test_AC_00_02 (webhook) และ OAT-2 | T-31 ของ 002 | ops/alerts.py | ครบบนเครื่องทดสอบ บริการเวรจริงทดสอบวันติดตั้ง | รับ |
| REQ-OP-006 | EV-049 | ไม่มี AC | OAT-3 เดินเหตุการณ์ที่ 4 ถึง 6 | | docs/srs/operations.md รุ่น 1.2 | ครบเหตุการณ์ที่ 1 ถึง 6 | รับ |
| REQ-OP-007 | EV-049 | AC-00-05 | OAT-4 ซ้อมกู้คืนบน PostgreSQL | | INC-01 | ครบบนเครื่องทดสอบ cron บนเครื่องจริงยังไม่ทำ | รับ เป็นเกณฑ์ก่อนเปิดใช้จริง |
| REQ-OP-001 | EV-045 | AC-00-04 | | | | วัดนาทีล่มรายเดือนได้หลังเปิดใช้จริงเท่านั้น | ย้ายไปช่วง hypercare |

ข้อค้นพบ: ไม่มี F ใหม่ ช่องว่างใหม่ GAP-37 (ปิด) GAP-38 (เปิด Q-67) รายการเอกสารส่งมอบอยู่ที่ docs/handover/README.md

## แถวที่เพิ่มตาม R2 ส่วน A (CR-11, CR-13 วันที่ 23 พ.ย. 2569)

| REQ | ที่มา (EV) | AC | test | task | โค้ด | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|---|---|
| REQ-SEC-013 | หน้าบทเรียน A07, EV-051 | AC-02-03, 04, 05, 08, 11, AC-01-02 | test_identity.py | T-01 ของ 006 | auth/service.py | ครบ | รับ |
| REQ-SEC-014 | TH-01, EV-051 | AC-02-06, 09, AC-01-01, 03 และ AC เดิม | test_identity.py และ test เดิมทุกตัว | T-03 ของ 006 | auth/deps.py | ครบ | รับ |
| REQ-PRV-011 | Q-22, EV-051 | AC-02-01 | test_AC_02_01 | T-02 ของ 006 | auth/router.py | ขาดบางส่วน (GAP-40 พิกัดจากหน้าจอ) | รับความเสี่ยง |
| REQ-SEC-010 (มีผลจริง) | EV-045, EV-051 | AC-02-07 | test_AC_02_07 | T-04 ของ 006 | ops/audit.py | ครบ ปิด GAP-24 | รับ |
| REQ-OP-008 | OAT-3, EV-051 | AC-00-09, 10, 11 | test_cross_cutting_cr13.py | T-37 ของ 002 | notify/queue.py, ops/lease.py, ops/metrics.py, ops/serve.py | ครบ ปิด GAP-38 | รับ |

ข้อค้นพบใหม่ใน rtm ของ 006 (F-17, F-18) และ 007 (F-19, F-20) ช่องว่างใหม่ GAP-39 ถึง GAP-42 (gaps.md)
