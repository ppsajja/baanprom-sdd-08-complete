# rtm.md ตารางตามรอยของ feature ผู้ช่วยตอบคำถามและเลื่อนนัด (UC-14)

รุ่น: 1.0 | วันที่: 2569-10-31 | ผู้ตรวจ: กลุ่ม X (รอบนี้ผู้สอนเดโม) | อ้างอิง: spec.md 1.0, ai-assistant.feature v1.0, plan v1, tasks v1, test-run.txt, eval-results.md
ร่างครั้งแรกด้วย AI จากตารางใน plan.md ข้อ 6 และท้าย tasks.md (prompt-log.md #78) ทีมตรวจทุกแถวเทียบไฟล์จริง และเขียนช่อง "ทีมตัดสิน" เอง
เลขข้อค้นพบต่อจาก specs/004-cancel-refund/rtm.md (F-12 ถึง F-14) จึงเริ่มที่ F-15
ของใหม่ของ feature ที่มี AI (หน้าบทเรียนหัวข้อ 9.2): คอลัมน์ test ของ REQ-AI มีทั้ง test และ "eval ข้อ" กับผลวัดรุ่นล่าสุด

## 1. ตามรอยไปข้างหน้า (หลักฐาน ถึง ของที่สร้าง)

| REQ | ที่มา (EV) | อยู่ใน spec ส่วน 4 | AC | test / eval | task | โค้ด / หน้าจอ | สถานะ |
|---|---|---|---|---|---|---|---|
| REQ-DAT-010 ข้อมูลที่ผู้ช่วยใช้ | EV-046, EV-047 | 4.1 | AC-14-06 | test_AC_14_06 (4 ตัว) eval หมวดสิทธิ์ E-006, E-182 ถึง E-200 เวลาถึง 20 ข้อ (topic eta) ข้อมูลที่ส่ง LLM 230 ข้อ | T-04, T-09 | assistant/retrieval.py, policies/, privacy.mask_text | ครบ |
| REQ-AI-005 ขอบเขต 5 เรื่อง | EV-012, EV-046 | 4.2 | AC-14-01, AC-14-02 | test_AC_14_01, test_AC_14_02 eval qa 200 ข้อ (ผล 197 จาก 200 ถูกและครบ) | T-03, T-05, T-09 | assistant/intents.py, service.py (MSG_OUT_OF_SCOPE), handoff.py | ครบ |
| REQ-AI-006 ตอบจากข้อมูลที่ให้ ไม่รู้บอกไม่มีข้อมูล | EV-046 | 4.2 | AC-14-03 | test_AC_14_03 eval หมวดไม่มีข้อมูล 25 ข้อ | T-05, T-09 | assistant/llm.py (ข้อความสั่ง), guard.py, service.fallback | ขาดบางส่วน: คนตรวจ 30 ข้อยังไม่ทำ |
| REQ-AI-007 สิ่งที่ห้าม | EV-046 | 4.2 | AC-14-04 | test_AC_14_04 eval หมวดห้าม 20 ข้อ และทุกคำตอบ 290 ข้อ | T-04, T-09 | intents.py (FORBIDDEN), service.MSG_FORBIDDEN, guard.py | ครบ |
| REQ-AI-008 รั้วสองด้าน | OWASP LLM01, LLM08, LLM10:2026 | 4.2 | AC-14-05 | test_AC_14_05 (7 แบบ) eval injection 30 ข้อ | T-04, T-09 | assistant/guard.py | ครบ |
| REQ-AI-009 เพดานการใช้ | OWASP LLM06:2026 (ทีมเพิ่ม) | 4.2 | AC-14-07 | test_AC_14_07_rate_and_length_limits | T-04 | guard.RateLimiter, config.ASSISTANT_MAX_* | ขาดบางส่วน: ค่าใช้จ่ายต่อคำถามวัดไม่ได้กับ MockLLM |
| REQ-AI-010 เครื่องมือรายการปิด | EV-046, LLM03:2026 | 4.3 | AC-14-08 | test_AC_14_08_closed_tool_list | T-07 | assistant/tools.py | ครบ |
| REQ-AI-011 ยืนยันก่อนเลื่อน | EV-046 | 4.3 | AC-14-09 | test_AC_14_09 eval reschedule 60 ข้อ AC-14-09.test.jsx | T-07, T-09, T-10 | tools.py (ระดับ 2), agent.py, service.confirm, AssistantChat.jsx | ขาดบางส่วน: ลูกค้าจริง 20 คนยังไม่ทดสอบ |
| REQ-AI-012 หยุดปลอดภัย | EV-046, ASI02, ASI08 | 4.3 | AC-14-10, AC-14-15 | test_AC_14_10 (4 ตัว) test_AC_14_15 | T-03, T-06, T-07 | service.py (stop, confirm, decline), handoff.py | ขาดบางส่วน (F-16) |
| REQ-AI-013 บันทึก | EV-046, ASI10, EV-047 | 4.3 | AC-14-11 | test_AC_14_11 (2 ตัว) | T-07, T-08 | assistant/records.py, erasure/service.py, ops/scheduler.py | ครบ |
| REQ-FN-056 API เลื่อนนัดของลูกค้า | EV-046, GAP-29 | 4.3 | AC-14-16 | test_AC_14_16_reschedule_api | T-02 | booking/service.py (check_reschedule, reschedule_job), booking/router.py | ครบ |
| REQ-AI-020 โปร่งใสต่อลูกค้า | EU AI Act มาตรา 50, EV-047 | 4.4 และ 12 | AC-14-12 | test_AC_14_12 AC-14-12.test.jsx UI-14-01.test.jsx | T-06, T-10 | service.GREETING, retrieval (sources), AssistantChat.jsx | ขาดบางส่วน: ผู้ใช้ทดสอบ 20 คนยังไม่ทำ (F-15 ดูคำว่า "ทุกจอ") |
| REQ-AI-021 เป็นธรรม (ไฟล์กลาง) | หน้าบทเรียนหัวข้อ 7.2 | 4.4 | AC-14-13 | test_AC_14_13 รายงานแยกกลุ่มใน eval-results.md | T-09 | evaluation.fairness, ป้าย labels ใน eval set | ขาดบางส่วน: นับซ้ำจากบทสนทนาจริงรายเดือนยังทำไม่ได้ (ยังไม่มีผู้ใช้จริง) |
| REQ-AI-022 กำกับโดยมนุษย์ (ไฟล์กลาง) | หน้าบทเรียนหัวข้อ 7.4 | 4.4 | AC-14-14 | test_AC_14_14 (2 ตัว) AC-14-14.test.jsx | T-08, T-10, T-12 | service.set_enabled, router (ops), operations.md เหตุการณ์ที่ 6 | ขาดบางส่วน: ซ้อมปิดจับเวลาและทบทวนรายสัปดาห์ยังไม่เริ่ม GAP-32 |
| BR-06 กรอบการเลื่อนนัด | EV-046, EV-047 | rules.md | AC-14-09, AC-14-16 | test_AC_14_16 eval หมวดเกินกรอบ 20 ข้อ (5 เหตุ) | T-02 | booking/service.check_reschedule | ครบ |
| REQ-SEC-010, REQ-PRV-002, REQ-PRV-010 (ใช้ร่วม) | MU-01, PDPA | 4.4 | AC-14-06, AC-14-11, AC-14-16 | test_AC_14_16 (403) test_AC_14_11 test_AC_14_06 | T-02, T-04, T-08 | ops/audit.py, privacy.py, erasure/service.py | ครบ |

แหล่งข้อมูลของแต่ละคอลัมน์: ที่มา จาก docs/srs/catalogue.md | AC จาก spec ส่วน 4 และ ai-assistant.feature | test จาก plan.md ข้อ 6 และ test-run.txt | eval จาก eval-results.md | task จากตารางท้าย tasks.md | โค้ด จากคอมเมนต์ "รองรับ REQ-xx" ในไฟล์

## 2. ตามรอยย้อนกลับ (ของที่สร้าง ถึง ความต้องการ)

| ของที่มีอยู่จริง | อ้าง REQ หรือ AC ข้อไหน | ข้อค้นพบ |
|---|---|---|
| endpoint ใหม่ 11 ตัว (บัญชี endpoint ใน operations.md) | REQ-FN-056, REQ-AI-005 ถึง 013, 020, 022 | ไม่มี |
| GET /ops/assistant/jobs/{id}/actions | REQ-AI-013 ข้อตรวจ "ตอบได้ภายใน 1 นาที" | ไม่มี |
| MockLLM และ NotConnectedLLM | D-14-02, D-14-04 (การตัดสินใจ ไม่ใช่ REQ) | ไม่มี (เป็นส่วนของ plan ไม่ใช่พฤติกรรมที่ผู้ใช้เห็น) |
| คลังนโยบาย 4 ไฟล์ (1 ไฟล์เลิกใช้) | REQ-DAT-010 บรรทัดที่ 2, Q-63, D-14-07 | ไม่มี |
| คำตอบสำรองจากโค้ด (service.fallback) | REQ-AI-008 | ไม่มี |
| ข้อความ "ผู้ช่วยยกเลิกให้ไม่ได้ค่ะ" ต่อท้ายเมื่อขอให้ยกเลิก | REQ-AI-010 (ASI01) | ไม่มี |
| เลขโทรของ call center ในคำตอบเมื่อผู้ช่วยปิด (ค่าตั้งต้น 02-000-0000 เลขสมมติ) | REQ-AI-022 | ไม่มี (ระบบจริงตั้งผ่าน CALL_CENTER_TEL) |
| ปุ่ม "คุยกับเจ้าหน้าที่" มีเฉพาะหน้าผู้ช่วย ไม่มีบนหน้าจอของ 002 ถึง 004 | REQ-AI-020 "ทุกจอมีทางเลือกคุยกับเจ้าหน้าที่" | F-15 |
| หมดเวลาหลังเครื่องมือเลื่อนนัดทำงานไปแล้ว (FAULTS after) | REQ-AI-012 | F-16 |
| test หลังบ้าน 31 ตัว หน้าจอ 6 ตัว eval 290 ข้อ | ทุกตัวมีรหัส AC หรือ UI ในชื่อ ทุกข้อของ eval มีหมวดที่ผูกกับ AC (eval/README.md) | ไม่มี |

ข้อค้นพบ
- F-15 REQ-AI-020 เขียนว่า "ทุกจอมีทางเลือกคุยกับเจ้าหน้าที่" ทีมตีความว่าทุกสถานะของหน้าผู้ช่วย (UI-14-01) เพราะหน้าจออื่นไม่มีผู้ช่วย แต่ถ้อยคำอ่านได้ว่าทุกหน้าของแอป ต้องถาม SH-01 ให้ชัดก่อนตรวจรับ (เสนอเป็นคำถามในบท RE in One Line และการตรวจรับ)
- F-16 REQ-AI-012 "เครื่องมือที่ไม่ได้คำตอบต้องไม่ถูกเรียกซ้ำ" มี test กรณีหมดเวลาก่อนทำ ส่วนกรณีทำไปแล้วแต่ไม่ได้คำตอบ (ผลไม่ทราบ) มีแค่ขั้นตอนในคู่มือเหตุการณ์ที่ 6 และ reference P-n กันเลื่อนซ้ำ ยังไม่มี test ที่ตรวจว่าการกดยืนยันซ้ำไม่เลื่อนรอบสอง

## 3. ตรวจความครบของสเปกเอง

| คำถาม | คำตอบ |
|---|---|
| ทุก REQ ในส่วน 4 มี AC | ใช่ 16 AC ครอบคลุม 14 REQ และ BR-06 |
| ทุก AC ของกล่อง AI บอกชุด รุ่น จำนวน และใครเขียนคำตอบที่ถูก | ใช่ (eval/README.md และหัว ai-assistant.feature) |
| ทุกตัวเลขมีที่มา | ใช่ (EV-046, EV-047, หน้าบทเรียน) ค่าในโค้ดอยู่ใน config.py ที่เดียว |
| eval set แยกจากตัวอย่างที่ใส่ในข้อความสั่ง | ใช่ คำตัวอย่างใน intent-examples เป็นคำ ไม่ใช่ประโยคของ eval set (ตรวจด้วยคนตอนเพิ่ม P-1.1) |
| มีเกณฑ์ที่ต้องใช้คนและยังไม่ได้ทำ | มี 4 ข้อ (AC-14-03, 09, 12, 14) บันทึกเป็น "ตรวจด้วยคน (ยังไม่ทำ)" ใน ac-results.md ไม่นับว่าผ่าน |

## 4. ทีมตัดสิน

| เรื่อง | ทีมตัดสิน |
|---|---|
| ประกาศ B4 ได้ไหม | ได้ ทุกส่วนที่วัดอัตโนมัติผ่าน ส่วนที่ต้องใช้คนเป็นเงื่อนไขก่อนทดลองแบบเงาและนำร่อง (CR-09 ส่วนการตัดสิน) ไม่ใช่เงื่อนไขของ Baseline |
| ผล eval กับ MockLLM บอกอะไร | บอกว่ารั้ว กฎ และวิธีวัดทำงาน ไม่ได้บอกว่า LLM ตัวจริงผ่าน ห้ามใช้ตัวเลข 197 จาก 200 เป็นหลักฐานตอนตรวจรับ |
| F-15 | ไม่แก้ในรอบนี้ ถาม SH-01 ในบทถัดไป |
| F-16 | เพิ่ม test ในรอบถัดไป ระหว่างนี้คู่มือเหตุการณ์ที่ 6 ขั้นที่ 4 คือทางกัน |

## แถวที่เปลี่ยนตาม CR-10 (3 พ.ย. 2569)

| REQ | ที่มา | สิ่งที่เปลี่ยน | ตรวจด้วย | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|
| REQ-DAT-010 บรรทัดที่ 2 | BR-01 รุ่น 1.1 (CR-10) | cancel-policy.md ข้อความ R3 และ source_hash refund-timing.md ตาม Q-35 eval set 1.1 (4 ข้อ) | test_AC_14_06_policy_matches_baseline, eval ทั้งชุด | ครบ ผ่าน 20 จาก 20 | รับ หลักฐานว่าบรรทัดที่ 2 ทำงาน: รอบแรกที่ยังไม่แก้ eval set AC-14-13 ไม่ผ่าน |
| REQ-AI-020 | F-15 | ไม่แก้ถ้อยคำ SH-01 ตีความ "ทุกจอ" ว่าทุกจอที่มีผู้ช่วย (EV-048) | UI-14-01.test.jsx เดิม | F-15 ปิด | รับ |

## แถวที่เปลี่ยนตาม CR-19 และ CR-18 (R2 ส่วน B, 10 ธ.ค. 2569)

| REQ | ที่มา | สิ่งที่เปลี่ยน | ตรวจด้วย | สถานะ | ทีมตัดสิน |
|---|---|---|---|---|---|
| REQ-AI-023 ชั้นที่ 3 ของการรับ | TOR R2 ภาคผนวก ค, EV-053 | service.model_accepted (มีผลเฉพาะ production) router status บอกรุ่น config.assistant_accepted_model | test_AC_14_17 | ครบ | รับ |
| REQ-AI-006 (Q-65) | EV-053 หัวหน้า call center | refund-timing.md บรรทัดของลูกค้า MockLLM mock-1.1 คำตอบสำรองมีบรรทัดธนาคาร eval set qa 1.2 เกณฑ์ AC-14-18 | test_AC_14_18, eval 5 จาก 5 | ครบ | รับ |
| REQ-FN-075 เลื่อนกลับ | Q-62, GAP-31, EV-053 | callcenter/router.py revert-reschedule booking.reschedules_used ไม่นับ by_role call_center CallCenterTools.jsx | test_AC_14_19, UI-14-02.test.jsx | ครบ | รับ |
| REQ-SEC-015 กุญแจของ call center | GAP-32, EV-053 | auth/deps.require_call_center /call-center/assistant/switch | test_AC_00_15, UI-14-02.test.jsx | ครบ | รับ |
| REQ-AI-012 (F-16) | F-16 | ไม่แก้โค้ด เพิ่ม test กรณีเครื่องมือทำไปแล้วแต่ไม่ได้คำตอบ | test_AC_14_10_tool_timeout_after_effect_not_called_again | F-16 ปิด | รับ |
| IF-05 LLM ตัวจริง | TOR R2 ข้อ 2, Q-56 | integrations/http_llm.py ปิดไว้ (LLM_ADAPTER=mock) | test_AC_00_13 (ข้อความถึง LLM ไม่มีเบอร์) | ครบ ส่วนที่ทำได้ เปิดจริงเป็นงานของผู้ว่าจ้าง | รับ |

ข้อค้นพบ: ไม่มีข้อใหม่ F-15 ปิดใน CR-10 F-16 ปิดในรอบนี้
