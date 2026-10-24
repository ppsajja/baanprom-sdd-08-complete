# รายงานปิดการทดสอบ R2 (test completion report)

แบบเอกสาร: test completion report ตาม ISO/IEC/IEEE 29119-3:2021 | ส่งในงวด 2 ของ TOR R2 | ผู้เขียน: RE lead ของกลุ่ม X | วันที่: 20 ธ.ค. 2569 (สมมติ)
ตัวเลขทุกตัวมาจากการรันจริงบนเครื่องทดสอบ ไฟล์ผลอยู่ตามคอลัมน์ "หลักฐาน"

## 1. สรุป

| ระดับ | สิ่งที่รัน | ผล | หลักฐาน |
|---|---|---|---|
| test หลังบ้าน | pytest -k "AC_" Python 3.11 และ 3.12 จาก export สะอาด | 188 passed ทั้งสองรุ่น ไม่มีข้าม | specs/000-shared/test-run.txt |
| test หน้าจอ | vitest | 78 passed (39 ไฟล์) | specs/000-shared/test-run.txt |
| eval ของผู้ช่วย | eval_run.py P-1.1 mock-1.1 eval set qa 1.2 | 21 จาก 21 เกณฑ์ ชุดลับ 50 จาก 50 | specs/005-ai-assistant/eval-results.md |
| ตามรอย | scripts/check_rtm.py | UC 14 จาก 14 AC 146 ข้อ มี test ทุกข้อ สายขาด 0 | docs/srs/rtm-all.md |
| เดินซ้อม scenario | uat_replay.py uat_replay_r2.py บน PostgreSQL 2 process | 22 จาก 22 ไม่มีคำตอบ 5xx | docs/acceptance/uat-dryrun-r2-full.txt |
| ทดสอบโหลด | load_test.py (รอบ R2 ส่วน A ไม่มีโค้ดค้นหาเปลี่ยนนอกจากอ่านคะแนน) | AC-07-08 ฉบับ Q-68 ผ่านบนเครื่องทดสอบ | docs/acceptance/load-test-r2.md (EV-052) |
| OAT | oat_r2.py ผ่าน tools ของกลุ่ม | ดู oat-results-r2.md | docs/acceptance/oat-raw-r2.txt |

## 2. ความเบี่ยงเบนจากแผน

- test เดิมเปลี่ยน 1 บรรทัดตาม CR-19 (test_AC_14_11 รุ่นโมเดล) ผลรอบแรกก่อนแก้: 1 failed 138 passed (specs/000-shared/test-run-r2b-round1.txt)
- เกณฑ์ eval AC-14-18 รอบแรกกับ mock-1.0 ได้ 0 จาก 5 (eval-results-round1-mock-1.0.md) ผ่านหลังแก้ MockLLM ตาม CR-19
- สคริปต์ OAT ของกลุ่มผิด 2 รอบ (GAP-48 GAP-49) ระบบไม่ผิด ผลที่ใช้คือรอบที่ถูก
- ไม่ได้ทดสอบโหลดซ้ำหลังเพิ่มคะแนนในผลค้นหา (F-22) วัดพร้อม AC-07-08 บนเครื่องจริง

## 3. สิ่งที่ยังไม่ได้ทดสอบ (ความเสี่ยงที่เหลือ)

- ระบบภายนอกตัวจริงทุกตัว (ทดสอบผ่าน transport จำลองเท่านั้น AC-00-13)
- เครื่องขนาดจริง (Q-68) และผู้ใช้จริง (การนำร่อง)
- เกณฑ์ eval ที่ต้องใช้คน (AC-14-03 คนตรวจ 30 ข้อ AC-14-09 AC-14-12 กับผู้ใช้ 20 คน) ยังไม่ได้วัด ทำในการทดลองแบบเงา

## 4. ข้อบกพร่องและช่องว่าง

วิกฤต 0 สูง 0 กลาง 2 (F-21 F-22 มีแผน) ช่องว่างใหม่ GAP-45 ถึง GAP-50 ปิดทั้งหมด (specs/000-shared/gaps.md และ gaps.md ของ 008 011)
