# ตารางผล AC ของข้อกำหนดข้ามทุก feature (specs/000-shared/cross-cutting.feature)

ไฟล์ใหม่ใน CR-07 (24 ต.ค. 2569) ผลรันจริงอยู่ที่ specs/000-shared/test-run.txt ไฟล์เดียวทั้งโครงการ
คำสั่ง: cd backend && pytest -v -k "AC_" | cd frontend && npx vitest run
สถานะที่ใช้: ผ่าน | ไม่ผ่าน | ยังไม่มี test | ตรวจด้วยคน

## รอบ CR-07 (24 ต.ค. 2569)

| AC ID | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-00-01 | REQ-OP-005 | test_AC_00_01_metrics_per_endpoint_per_minute | T-24 ของ 002 | ผ่าน | |
| AC-00-02 | REQ-OP-005 | test_AC_00_02_page_on_call_after_5_failing_minutes | T-24 ของ 002 | ผ่าน (นาฬิกาจำลอง) | การส่งถึงคนเวรจริงตรวจบนระบบจริง ช่องทางยังไม่เลือก (GAP-28) |
| AC-00-03 | REQ-OP-005, REQ-PRV-002 | test_AC_00_03_structured_log_without_pii | T-24 ของ 002 | ผ่าน | ค้นเบอร์ ชื่อ ที่อยู่ และพิกัดใน log ของทุกโมดูล app. |
| AC-00-04 | REQ-OP-001 | test_AC_00_04_health_and_ready | T-24 ของ 002 | ผ่าน | ส่วน "ล่มไม่เกิน 4 ชั่วโมงต่อเดือน" วัดบนระบบจริงรายเดือน |
| AC-00-05 | REQ-OP-007 | test_AC_00_05_backup_restore_drill_within_rpo | T-23 ของ 002 | ผ่าน (ย่อส่วนบน SQLite) | ไม่ใช่การซ้อมจริง ซ้อมบน PostgreSQL ก่อนเปิด R1 (เงื่อนไขของ CR-07) |
| AC-00-06 | REQ-SEC-012 | test_AC_00_06_production_hides_docs_and_guards_ops_endpoints | T-24 ของ 002 | ผ่าน | สร้างแอปในโหมด production ภายใน test |
| AC-00-07 | REQ-SEC-012 | test_AC_00_07_now_parameter_ignored_outside_test_mode | T-24 ของ 002 | ผ่าน | |
| AC-00-08 | REQ-SEC-010 บรรทัดที่ 3 | test_AC_00_08_page_when_one_actor_denied_over_20_in_10_minutes | T-24 ของ 002 | ผ่าน | |
| REQ-OP-006 | REQ-OP-006 | ไม่มี test | T-25 ของ 002 | ตรวจด้วยคน: ผ่าน (เหตุการณ์ที่ 1 ถึง 3) | walkthrough ใน EV-045 เหตุการณ์ที่ 4 และ 5 ยังไม่ได้ตรวจ |
| REQ-CMP-001 | REQ-CMP-001 | ไม่มี test | | ตรวจด้วยคน: ผ่าน | SH-05 ตรวจตามรายการ PDPA 5 ข้อ (EV-045) |

## รวมทั้งโครงการรอบนี้

| | B2 ปรับปรุง (18 ต.ค.) | B3 (24 ต.ค. หลัง CR-07) |
|---|---|---|
| AC ในสเปก | 27 (11 + 10 + 6) | 50 (18 + 14 + 10 + 8 ข้ามทุก feature) |
| test หลังบ้าน | 41 ผ่าน 1 ข้าม | 66 ผ่าน 1 ข้าม |
| test หน้าจอ | 27 ผ่าน (14 ไฟล์) | 31 ผ่าน (17 ไฟล์) |
| test เดิมที่ต้องเปลี่ยนเพราะ CR | | 8 ตัว ตามตารางใน CR-07 (ไม่มีตัวอื่น) |
| ข้อค้นพบและช่องว่างที่เปิด | F-05, F-06, F-07, F-09, F-10, F-11, F-13, F-14 | เดิมทั้งหมด และ GAP-24, GAP-26, GAP-28 |

## รอบ CR-09 (บทเรียน Data, AI และ Agent และประชุมทบทวน EV-047)

AC-00-01 ถึง AC-00-08 ไม่เปลี่ยน รันซ้ำทั้งชุดแล้วผ่านเท่าเดิม (specs/000-shared/test-run.txt) feature ใหม่ 005-ai-assistant มีตารางผลของตัวเองที่ specs/005-ai-assistant/ac-results.md

| | B3 (24 ต.ค. หลัง CR-07) | B4 (หลัง CR-09) |
|---|---|---|
| AC ในสเปก | 50 | 66 (เพิ่ม AC-14-01 ถึง AC-14-16) |
| test หลังบ้าน | 66 ผ่าน 1 ข้าม | 97 ผ่าน 1 ข้าม (Python 3.11 และ 3.12) |
| test หน้าจอ | 31 ผ่าน (17 ไฟล์) | 37 ผ่าน (21 ไฟล์) |
| eval (ใหม่) | ไม่มี | 20 จาก 20 เกณฑ์ผ่าน บน eval set 290 ข้อ ด้วย MockLLM และข้อความสั่ง P-1.1 (รอบที่ 1 ด้วย P-1.0 ผ่าน 11 จาก 20) |
| test เดิมที่ต้องเปลี่ยนเพราะ CR | 8 ตัว (CR-07) | 0 ตัว |
| ข้อค้นพบและช่องว่างที่เปิด | F-05, F-06, F-07, F-09, F-10, F-11, F-13, F-14, GAP-24, GAP-26, GAP-28 | เดิมทั้งหมด และ GAP-31, GAP-32, GAP-33, F-15, F-16 |

## รอบ CR-10 และ CR-02 (ประชุม EV-048 3 พ.ย. 2569 ก่อนตรวจรับ R1)

ตารางนี้รวม AC ที่ CR-10 และ CR-02 เพิ่มหรือแก้ของทุก feature ไว้ที่เดียว ไฟล์ ac-results.md ของแต่ละ feature ชี้มาที่นี่ AC อื่นผลเท่ารอบก่อนและ test ไม่ถูกแตะ
ผลรันจริง: specs/000-shared/test-run-cr10.txt (รอบนั้น เก็บไว้ไม่ทับ ผลล่าสุดอยู่ที่ test-run.txt) (Python 3.11 และ 3.12 104 passed หน้าจอ 40 passed 24 ไฟล์) รอบแรกก่อนแก้ test เดิม: test-run-cr10-round1.txt

| AC ID | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-07-08 (ฉบับ CR-02) | REQ-QA-003 | test_AC_07_08_search_under_load_scaled | T-09 ของ 002 | ผ่าน (ย่อส่วน 20 จาก 500) | test ไม่แตะ ผลตรวจรับต้องมาจากการยิงโหลด 500 คำขอบนเครื่องทดสอบ (uat-plan-r1.md เกณฑ์จบข้อ 4) |
| AC-07-10 แถว R3 | REQ-BR-001 | test_AC_07_10_refund_R3 | T-30 ของ 002 | ผ่าน | เดิมข้าม (Q-14) ไม่มี test ข้ามในโครงการแล้ว |
| AC-07-19 | REQ-FN-057, REQ-BR-002 | test_AC_07_19_estimate_and_deposit_from_same_table x3, AC-07-19.test.jsx, UI-07-02.test.jsx (ราคาประเมิน) | T-28, T-29 ของ 002 | ผ่าน | ยอดมัดจำเท่าเดิมทุกประเภท test ของ AC-07-11 ไม่แตะ |
| AC-08-06 | REQ-BR-001, REQ-FN-054 | test_AC_08_06_not_cancellable_returns_message (แถว R6), AC-08-06.test.jsx (R6) | T-13 ของ 004 | ผ่าน | แถว R3 ออกตามตาราง "test เดิมที่เปลี่ยน" ของ CR-10 |
| AC-08-11 | REQ-IF-010 | test_AC_08_11_gateway_declines_refund_no_retry_finance_follow_up, AC-08-11.test.jsx | T-12 ของ 004 | ผ่าน | ปิด F-13 |
| AC-08-12 | REQ-BR-001, REQ-FN-054, REQ-FN-055 | test_AC_08_12_cancel_while_en_route_deducts_travel_fee, AC-08-12.test.jsx | T-13 ของ 004 | ผ่าน | |
| AC-09-15 | REQ-FN-051, REQ-FN-053 | test_AC_09_15_done_without_customer_confirm_and_message_tells_how_to_report | T-13 ของ 003 | ผ่าน | |
| AC-00-02 (ช่องทางจริง) | REQ-OP-005 | test_AC_00_02_webhook_pager_reaches_on_call, test_AC_00_02_webhook_pager_retries_next_minute_when_service_fails | T-31 ของ 002 | ผ่าน | เครื่องรับ webhook ในเครื่อง OAT-2 ตรวจบนระบบที่รันจริง |
| UI-08-02 (รายการใหม่) | REQ-FN-054 (Q-35) | UI-08-02.test.jsx test ที่ 2 | T-13 ของ 004 | ผ่าน | |
| eval ของ UC-14 | REQ-AI-005 ถึง 013, REQ-AI-021 | eval_run.py กับ eval set 1.1 | T-13 ของ 005 | 20 จาก 20 เกณฑ์ | รอบแรก (eval set 1.0 กับ BR ใหม่) AC-14-13 ไม่ผ่าน 6.9 ใน 100 เกินเกณฑ์ 5 |

| | B4 (31 ต.ค.) | หลัง CR-10 (3 พ.ย. ก่อนตรวจรับ) |
|---|---|---|
| AC ในสเปก | 66 | 70 (เพิ่ม AC-07-19, AC-08-11, AC-08-12, AC-09-15) |
| test หลังบ้าน | 97 ผ่าน 1 ข้าม | 104 ผ่าน 0 ข้าม |
| test หน้าจอ | 37 ผ่าน (21 ไฟล์) | 40 ผ่าน (24 ไฟล์) |
| eval | 20 จาก 20 (eval set 1.0) | 20 จาก 20 (eval set 1.1) |
| test เดิมที่ต้องเปลี่ยนเพราะ CR | 0 | 5 จุด และ eval 4 ข้อ ตามตารางใน CR-10 |
| ข้อค้นพบและช่องว่างที่ปิด | | F-13 (AC-08-11), F-15 (การตีความของ SH-01), GAP-07 (Q-19) |

## รอบตรวจรับ R1 รอบสอง (16 พ.ย. 2569 EV-050 ตั้ง Baseline B5)

ผลรันจริง: specs/000-shared/test-run.txt (Python 3.11 และ 3.12 105 passed หน้าจอ 42 passed 25 ไฟล์ eval 20 จาก 20) test ใหม่ไม่ผ่านก่อนแก้: docs/acceptance/def-fix-red-r1.txt
ผลทดสอบโหลดเต็มรูปไม่ใช่ test ของ pytest บันทึกแยกที่ docs/acceptance/load-test-r1.md ตัวเลขทุกตัวมาจากการรันจริงบนเครื่องทดสอบ

| AC หรือ UI | REQ ที่พิสูจน์ | test หรือการวัด | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| UI-07-02 (บรรทัดเวลาหมดล็อก ทางเข้าจากช่วงใกล้เคียง) | REQ-FN-041 | UI-07-02-DEF-01.test.jsx 2 ตัว | T-32 ของ 002 | ผ่าน | DEF-01 (GAP-36) test เดิมของ UI-07-02 และ AC-07-04 ไม่แตะ |
| AC-00-03 (log ในระบบจริง) | REQ-OP-005 บรรทัดที่ 3 | test_AC_00_03_production_app_writes_structured_log_to_stdout และ OAT-6 รอบสอง | T-33 ของ 002 | ผ่าน | DEF-02 (GAP-37) test เดิมของ AC-00-03 ไม่แตะ |
| AC-07-08 (เต็มรูป 500 คนพร้อมกัน) | REQ-QA-003 | backend/load_test.py 3 รอบ | ตรวจรับ ค3 | ไม่ผ่าน บนเครื่องทดสอบ | p95 8.04, 7.66, 7.48 วินาที ผ่านได้ถึงราว 200 คน ผลย่อส่วนใน pytest ยังผ่าน แต่ไม่ใช่ผลของเกณฑ์นี้ ต้องวัดซ้ำบนเครื่องจริง (Q-68) |
| AC-09-12 (เต็มรูป 50 คน) | REQ-QA-003 ฝั่งช่าง | load_test.py | ตรวจรับ ค3 | ผ่าน | p95 0.30 วินาที |
| AC-08-09 (เต็มรูป 50 คน) | REQ-QA-003 ฝั่งยกเลิก | load_test.py | ตรวจรับ ค3 | ผ่าน | p95 0.39 วินาที gateway จำลองตอบทันที |

| | หลัง CR-10 (3 พ.ย.) | B5 (16 พ.ย.) |
|---|---|---|
| AC ในสเปก | 70 | 70 (ไม่เปลี่ยน แก้โค้ดให้ตรงสเปกเดิม) |
| test หลังบ้าน | 104 ผ่าน | 105 ผ่าน |
| test หน้าจอ | 40 ผ่าน (24 ไฟล์) | 42 ผ่าน (25 ไฟล์) |
| eval | 20 จาก 20 | 20 จาก 20 (รันซ้ำ ผลเท่าเดิม) |
| test เดิมที่เปลี่ยน | 5 จุดตาม CR-10 | 0 |
| ข้อบกพร่องค้าง | | 0 (DEF-01 DEF-02 ปิด) |

## รอบ R2 ส่วน A (23 พ.ย. 2569 รันจริงจาก export สะอาด test-run.txt)

| AC | REQ | test | ผล | หมายเหตุ |
|---|---|---|---|---|
| AC-00-01 ถึง AC-00-08 | | test เดิม | ผ่าน | AC-00-03 AC-00-07 แก้เฉพาะการบอกผู้ส่ง (CR-11) AC-00-01 ไม่แก้ (GAP-39) |
| AC-00-09 | REQ-OP-008 | test_AC_00_09_queued_messages_survive_restart | ผ่าน | |
| AC-00-10 | REQ-OP-008 | test_AC_00_10_one_process_holds_the_scheduler_lease | ผ่าน | |
| AC-00-11 | REQ-OP-008, REQ-OP-005 | test_AC_00_11_metrics_from_two_processes_add_up | ผ่าน | |
| ทดสอบโหลด R2 | REQ-QA-003, REQ-OP-001 | backend/load_test.py บน PostgreSQL 2 process | AC-07-08 ฉบับ Q-68 ผ่าน AC-09-12 AC-08-09 ผ่าน แบบ 500 คำขอในวินาทีเดียวไม่ผ่าน (ไม่ใช่เกณฑ์แล้ว) | docs/acceptance/load-test-r2.md EV-052 |
| เดินซ้อม scenario R1 ผ่าน API พร้อม token | ทุก REQ ของ R1 | backend/uat_replay.py บน PostgreSQL 2 process | 13 จาก 13 | docs/acceptance/uat-dryrun-r2-auth.txt |

สรุปจำนวน: หลังบ้าน 139 passed (Python 3.11 และ 3.12) หน้าจอ 63 passed (32 ไฟล์) eval 20 จาก 20
