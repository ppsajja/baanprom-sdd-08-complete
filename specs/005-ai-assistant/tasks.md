# Tasks: ผู้ช่วยตอบคำถามลูกค้าและเลื่อนนัด (UC-14)

Feature: SPEC-ASSISTANT | อ้างอิง: plan.md (plan v1) | สร้างด้วย /tasks วันที่ 2569-10-31 (tasks v1, prompt-log.md #75)
ทีมสั่งแก้รอบที่ 1 หนึ่งจุด: ร่างแรกของ AI รวม eval set เข้ากับ T-06 ทีมแยกเป็น T-09 เพราะ eval set เป็นงานของนักวิเคราะห์กับเจ้าของ ไม่ใช่ของโปรแกรมเมอร์ (หน้าบทเรียนหัวข้อ 9.3)

สรุป: 13 task (T-13 เพิ่มตาม CR-10 ดูท้ายไฟล์) | 0 task รอ Q-xx ทั้ง task (Q-35 ปิดใน CR-10 ผู้ช่วยยังตอบว่าไม่มีข้อมูลจำนวนวัน)
สถานะปัจจุบัน: เสร็จ 12 (ทุก task ผ่านการตรวจ 5 ข้อ T-10 ตรวจด้วย test ของรายการ "ต้องตรง" การตรวจเทียบ mockup ด้วยคนยังไม่ทำ GAP-33)

### T-01 ตารางใหม่ migration m003 และค่าใน config.py
- รองรับ: REQ-FN-056, REQ-AI-013, REQ-AI-022, D-00-05
- ตรวจด้วย: ไม่มี AC ตรง เป็นงานพื้นฐาน
- ไฟล์ที่แตะ: backend/app/db/models.py (ของ 002 เพิ่มตารางท้ายไฟล์), backend/app/db/migrations/m003_cr09.py, backend/app/config.py, backend/app/main.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: test เดิมทั้งชุดผ่านเท่าเดิม (66 passed 1 skipped)
- สถานะ: เสร็จ

### T-02 API เลื่อนนัดของลูกค้าตาม BR-06
- รองรับ: REQ-FN-056, BR-06, REQ-SEC-010, REQ-FN-012
- ตรวจด้วย: AC-14-16
- ไฟล์ที่แตะ: backend/app/booking/service.py, backend/app/booking/router.py (ของ 002 เพิ่มท้ายไฟล์ ไม่แก้ฟังก์ชันเดิม), backend/tests/test_assistant.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-01
- เสร็จเมื่อ: test_AC_14_16 ผ่าน และ test ของ 002 ผ่านเท่าเดิม
- สถานะ: เสร็จ

### T-03 ข้อความสั่ง คำตัวอย่าง และขั้นจำแนกความตั้งใจ
- รองรับ: REQ-AI-005, REQ-AI-007, REQ-AI-012, D-14-01, D-14-05
- ตรวจด้วย: AC-14-02, AC-14-10 (unclear)
- ไฟล์ที่แตะ: specs/005-ai-assistant/prompts/, backend/app/assistant/prompts.py, intents.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: คำถาม 10 ข้อแรกของ eval set จำแนกถูก 10 ใน 10
- สถานะ: เสร็จ

### T-04 ค้นข้อมูล คลังนโยบาย รั้วสองด้าน และการปิดบังข้อความ
- รองรับ: REQ-DAT-010, REQ-AI-008, REQ-AI-009, REQ-PRV-002, D-14-07
- ตรวจด้วย: AC-14-05, AC-14-06, AC-14-07
- ไฟล์ที่แตะ: backend/app/assistant/retrieval.py, guard.py, policies/, backend/app/privacy.py (ของ 002 เพิ่ม mask_text และช่อง log)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-01
- เสร็จเมื่อ: test_AC_14_05 (7 แบบ) test_AC_14_06 (3 ตัวที่ไม่ใช้ eval) test_AC_14_07 ผ่าน
- สถานะ: เสร็จ

### T-05 interface LLM และ MockLLM
- รองรับ: REQ-AI-006, D-14-02, D-14-04
- ตรวจด้วย: AC-14-01, AC-14-03 (ผ่าน eval)
- ไฟล์ที่แตะ: backend/app/assistant/llm.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: ไม่มี
- เสร็จเมื่อ: MockLLM ตอบคำถามเดิมได้คำตอบเดิมทุกครั้ง และมีทั้งคำตอบที่ถูก ไม่ครบ แต่งเรื่อง และทำตามข้อความหลอก
- สถานะ: เสร็จ

### T-06 ลำดับ 5 ขั้น บันทึกคำตอบ ตั๋วส่งต่อ
- รองรับ: REQ-AI-005, REQ-AI-006, REQ-AI-013, REQ-AI-020, REQ-AI-012
- ตรวจด้วย: AC-14-12, AC-14-15
- ไฟล์ที่แตะ: backend/app/assistant/service.py, records.py, handoff.py, router.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-03, T-04, T-05
- เสร็จเมื่อ: test_AC_14_12 และ test_AC_14_15 ผ่าน
- สถานะ: เสร็จ

### T-07 agent เครื่องมือ 3 รายการ ยืนยัน ปฏิเสธ หยุดปลอดภัย
- รองรับ: REQ-AI-010, REQ-AI-011, REQ-AI-012, REQ-AI-013, D-14-03, D-14-06
- ตรวจด้วย: AC-14-08, AC-14-09, AC-14-10, AC-14-11
- ไฟล์ที่แตะ: backend/app/assistant/tools.py, agent.py, service.py (confirm, decline)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-02, T-06
- เสร็จเมื่อ: test_AC_14_08, test_AC_14_10 (4 ตัว), test_AC_14_11 ผ่าน
- สถานะ: เสร็จ

### T-08 ปุ่มหยุด ร้องเรียน ลบบันทึก 180 วัน และลบข้อความเมื่อขอลบ
- รองรับ: REQ-AI-022, REQ-AI-013, REQ-PRV-010
- ตรวจด้วย: AC-14-11, AC-14-14
- ไฟล์ที่แตะ: backend/app/assistant/service.py, router.py (ops), records.py, backend/app/erasure/service.py และ backend/app/ops/scheduler.py (ของรอบ CR-07 เพิ่มบรรทัดเรียก)
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-06
- เสร็จเมื่อ: test_AC_14_14 (2 ตัว) test_AC_14_11_erasure ผ่าน และ test_erasure.py ของ 002 ผ่านเท่าเดิม
- สถานะ: เสร็จ

### T-09 eval set รุ่น 1.0 และตัวรัน eval
- รองรับ: REQ-AI-005 ถึง REQ-AI-011, REQ-AI-021, REQ-DAT-010
- ตรวจด้วย: AC-14-01 ถึง AC-14-06, AC-14-09, AC-14-13
- ไฟล์ที่แตะ: specs/005-ai-assistant/eval/, backend/app/assistant/evaluation.py, backend/eval_run.py, backend/tests/test_assistant_eval.py
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-07, T-08
- เสร็จเมื่อ: eval_run.py เขียน eval-results.md และคืน 0 test_assistant_eval.py ผ่านทุกตัว
- สถานะ: เสร็จ

### T-10 หน้าแชตผู้ช่วยตามแบบ UI-14-01
- รองรับ: REQ-AI-020, REQ-AI-011, REQ-AI-022
- ตรวจด้วย: AC-14-09 (หน้าจอ), AC-14-12 (หน้าจอ), AC-14-14 (หน้าจอ), UI-14-01
- ไฟล์ที่แตะ: frontend/src/pages/AssistantChat.jsx, api/client.js (assistantApi), App.jsx (เมนู ผู้ช่วย), __tests__/UI-14-01.test.jsx, AC-14-09.test.jsx, AC-14-12.test.jsx, AC-14-14.test.jsx, _assistantFake.js
- แบบหน้าจอ: UI-14-01 mockups/UI-14-01-chat.html
- ต้องทำหลัง: ไม่มี (ใช้ API จำลองตามสัญญาใน plan.md ข้อ 4)
- เสร็จเมื่อ: npm test ผ่านทั้งชุด และไม่มีข้อความของผู้ช่วยที่หน้าจอแต่งเอง
- สถานะ: เสร็จ

### T-11 รัน test ทั้งชุด รัน eval และบันทึกผล
- รองรับ: ทุก REQ ของ feature นี้
- ตรวจด้วย: ทุก AC ของ UC-14 และรันซ้ำทั้งชุดของ 002 003 004 000
- ไฟล์ที่แตะ: specs/000-shared/test-run.txt, specs/005-ai-assistant/eval-results.md, ac-results.md, rtm.md, gaps.md, docs/srs/baseline.md
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-01 ถึง T-10
- เสร็จเมื่อ: Python 3.11 และ 3.12 ผ่านทั้งชุด vitest ผ่านทั้งชุด eval ผ่านทุกเกณฑ์
- สถานะ: เสร็จ

### T-12 คู่มือรับมือเหตุการณ์ที่ 6 และบัญชี endpoint
- รองรับ: REQ-OP-006, REQ-SEC-012, REQ-AI-022
- ตรวจด้วย: ไม่มี AC ตรวจด้วย walkthrough (ยังไม่ได้เดินตาม)
- ไฟล์ที่แตะ: docs/srs/operations.md
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-08
- เสร็จเมื่อ: บัญชี endpoint ตรงกับ /openapi.json ของโหมด development ทุกตัว
- สถานะ: เสร็จ

## ตารางตรวจความครบ

| AC ID | task ที่ตรวจ AC นี้ |
|---|---|
| AC-14-01 | T-05, T-09 |
| AC-14-02 | T-03, T-09 |
| AC-14-03 | T-05, T-09 |
| AC-14-04 | T-04, T-09 |
| AC-14-05 | T-04, T-09 |
| AC-14-06 | T-04, T-09 |
| AC-14-07 | T-04 |
| AC-14-08 | T-07 |
| AC-14-09 | T-07, T-09, T-10 (หน้าจอ) |
| AC-14-10 | T-03, T-07 |
| AC-14-11 | T-07, T-08 |
| AC-14-12 | T-06, T-10 (หน้าจอ) |
| AC-14-13 | T-09 |
| AC-14-14 | T-08, T-10 (หน้าจอ) |
| AC-14-15 | T-06 |
| AC-14-16 | T-02 |
| รายการ "ต้องตรง" ของ UI-14-01 | T-10 |

| Constraint ID | task ที่ทำให้เป็นจริง |
|---|---|
| REQ-DAT-010 | T-04 |
| REQ-AI-008 | T-04 |
| REQ-AI-010, REQ-AI-011 | T-07 |
| REQ-CON-001 | ทุก task ตัด LLM ตัวจริง เครื่องมือเลื่อนกลับ และกุญแจแยกบทบาทออก |
| REQ-CON-003 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ตัดเงินหรือคืนเงิน |
| REQ-PRV-002 | T-04, T-06, T-08 |
| D-00-01 ถึง D-00-04 | T-01, T-06, T-10 |
| D-00-05 | T-01 |
| REQ-OP-001, REQ-OP-005, REQ-OP-007 | T-01, T-06 (ใช้โครงเดิม) |
| REQ-OP-006 | T-12 |
| REQ-QA-010 | T-07 |
| REQ-SEC-010 | T-02, T-04, T-07 |
| REQ-SEC-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ล็อกช่วงเวลา (D-14-06) |
| REQ-SEC-012 | T-08, T-12 |
| REQ-PRV-010 | T-08 |
| REQ-CMP-001 | spec ส่วน 8 (ไม่มีโค้ด) |
| REQ-AI-021 | T-09 |
| REQ-AI-022 | T-08 |

## สิ่งที่ยังไม่ทำ

ตามที่ plan.md ข้อ 8 บอก ไม่มี task ของ LLM ตัวจริง การทดลองกับคน และเครื่องมือเลื่อนกลับของ call center (GAP-31)

### ส่วนที่เพิ่มตาม CR-10 (tasks v2, 3 พ.ย. 2569)

### T-13 คลังนโยบายและ eval set รุ่น 1.1 ตาม BR-01 รุ่น 1.1 (CR-10)
- รองรับ: REQ-DAT-010 บรรทัดที่ 2, REQ-AI-005, REQ-AI-007
- ตรวจด้วย: AC-14-06 (policy_matches_baseline) และ eval ทั้งชุด (AC-14-01 ถึง AC-14-13)
- ไฟล์ที่แตะ: backend/app/assistant/policies/cancel-policy.md, backend/app/assistant/policies/refund-timing.md, specs/005-ai-assistant/eval/qa.jsonl, eval/CHANGELOG.md, eval/README.md, eval-results.md, eval-results.json
- แบบหน้าจอ: ไม่มี
- ต้องทำหลัง: T-30 ของ 002
- เสร็จเมื่อ: eval 20 จาก 20 เกณฑ์ และ eval set มีบันทึกรุ่น 1.1 ใน CHANGELOG
- สถานะ: เสร็จ

### ส่วนที่เพิ่มตาม CR-19 และ CR-18 (tasks v3, 10 ธ.ค. 2569)

### T-14 Q-65 ชั้นที่ 3 ของการรับ ชุดลับของ eval set และ LLM ตัวจริงที่ปิดไว้ (CR-19)
- รองรับ: REQ-AI-023, REQ-AI-006 (Q-65), REQ-AI-012 (F-16), REQ-IF-012 (IF-05)
- ตรวจด้วย: AC-14-17, AC-14-18, AC-14-10 (test เพิ่ม), AC-00-13 และ eval ทั้งชุด
- ไฟล์ที่แตะ: backend/app/assistant/llm.py, service.py, router.py, evaluation.py, policies/refund-timing.md, backend/eval_run.py, backend/app/integrations/http_llm.py, specs/005-ai-assistant/eval/qa.jsonl, heldout.json, CHANGELOG.md, README.md, backend/tests/test_assistant_r2b.py, test_assistant.py (บรรทัดเดียวตาม CR-19)
- แบบหน้าจอ: ไม่มี
- เสร็จเมื่อ: eval 21 จาก 21 เกณฑ์ ชุดลับรายงานแยก
- สถานะ: เสร็จ

### T-15 เครื่องมือ call center ปิดผู้ช่วยด้วยกุญแจของตัวเอง ตั๋ว เลื่อนนัดกลับ (CR-18)
- รองรับ: REQ-FN-075, REQ-SEC-015, REQ-AI-022
- ตรวจด้วย: AC-14-19, AC-00-15, UI-14-02
- ไฟล์ที่แตะ: backend/app/callcenter/router.py, backend/app/auth/deps.py, backend/app/booking/service.py (reschedules_used), frontend/src/pages/CallCenterTools.jsx, App.jsx, api/client.js
- แบบหน้าจอ: UI-14-02
- สถานะ: เสร็จ

