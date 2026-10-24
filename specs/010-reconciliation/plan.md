# Plan: กระทบยอดกับรายงานของ gateway (UC-13)

อ้างอิง: spec.md SPEC-RECONCILIATION 1.0 | Updated: 2569-12-10 | /plan แล้วทีมตรวจ (plan v1, prompt-log.md #97)
อ้างอิง Constraint กลาง: specs/000-shared/constraints.md รุ่น 1.4

## 1. สรุปแนวทาง

- โมดูลใหม่ backend/app/reconciliation/ (service.py BR-13 router.py mock_report.py ตัวจำลองรายงาน)
- กุญแจของ Finance (auth/deps.require_finance REQ-SEC-015 ของ CR-18)
- ข้อความถึงลูกค้าผ่านคิวเดิม (REQ-OP-008) ข้อความเมื่อปฏิเสธใช้ MSG_REFUND_DECLINED ของ 004 (ข้อความเดียวกัน)
- สคริปต์ backend/gateway_report_mock.py สร้างรายงานจำลองจากฐานข้อมูลของเครื่องทดสอบ (UAT OAT) ไม่ใช่ส่วนของระบบ
- หน้าจอ Reconciliation.jsx (UI-13-01) ในเมนูของเจ้าหน้าที่ Finance

## 2. เทคโนโลยีที่ใช้

ไม่มีเทคโนโลยีใหม่ (csv ของ Python)

```
backend/app/reconciliation/__init__.py, service.py, router.py, mock_report.py   ใหม่
backend/app/db/models.py (ReconciliationRun ReconciliationItem RefundResolution)  แก้ เพิ่มท้ายไฟล์
backend/gateway_report_mock.py                                                   ใหม่ (เครื่องทดสอบ)
backend/tests/test_reconciliation.py                                             ใหม่
frontend/src/pages/Reconciliation.jsx, App.jsx, api/client.js                    ใหม่และแก้
frontend/src/__tests__/UI-13-01.test.jsx                                         ใหม่
```

## 3. โมเดลข้อมูล

reconciliation_runs(id, report_date, report_sha256, rows_in_report, matched, differences, at)
reconciliation_items(id, run_id, kind, entry_type, reference, job_id, system_amount, report_amount, system_status, report_status)
refund_resolutions(id, refund_id, run_id, from_result, to_result, at)

## 4. API / หน้าจอ

| method path | ผู้เรียก | ตอบ |
|---|---|---|
| POST /finance/reconciliations {report_date, csv} | Finance (X-Finance-Token) | 201 ผล | 200 already_imported | 422 bad_report (line) | 403 |
| GET /finance/reconciliations/{id} | Finance | ผลเดิม |
| GET /finance/refunds/follow-up | Finance | รายการเดียวกับ /ops/refunds/follow-up |

## 5. ตารางตรวจ Constraints

| ID | ใช้อย่างไรใน feature นี้ |
|---|---|
| REQ-CON-001 | ไม่เกี่ยวกับ feature นี้ เพราะเป็นข้อจำกัดของ R1 |
| REQ-CON-003 | ใช้แล้ว รายงานเป็นของ gateway รายเดิม (สัญญา IF-01) |
| REQ-PRV-002 | ใช้แล้ว ผลและ log มีแค่เลขงาน reference ยอด ผล |
| REQ-OP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี SLO |
| REQ-OP-005 | ใช้แล้ว endpoint ใหม่ถูกนับ |
| REQ-OP-006 | ใช้แล้ว operations.md เหตุการณ์ที่ 8 (รายการต่างจากการกระทบยอด) |
| REQ-OP-007 | ไม่เกี่ยวกับ feature นี้ เพราะตารางใหม่อยู่ในสำเนาเดิม |
| REQ-OP-008 | ใช้แล้ว ข้อความถึงลูกค้าเข้าคิวในธุรกรรมเดียวกับการเปลี่ยนผล |
| REQ-OP-009 | ไม่เกี่ยวกับ feature นี้ เพราะไม่เรียกระบบภายนอกโดยตรง (รายงานมาทาง Finance) |
| REQ-QA-010 | ไม่เกี่ยวกับ feature นี้ เพราะไม่เรียกระบบภายนอก |
| REQ-SEC-010 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีลูกค้าหรือช่างเป็นผู้เรียก |
| REQ-SEC-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ล็อกช่วงเวลา |
| REQ-SEC-012 | ใช้แล้ว endpoint อยู่ในบัญชี endpoint |
| REQ-SEC-013, REQ-SEC-014 | ไม่เกี่ยวกับ feature นี้ เพราะเจ้าหน้าที่ใช้กุญแจของบทบาท ไม่ใช่ OTP |
| REQ-SEC-015 | ใช้แล้ว router ทั้งชุดต้องมี X-Finance-Token |
| REQ-PRV-010, REQ-PRV-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีข้อมูลส่วนบุคคล |
| REQ-IF-012 | ไม่เกี่ยวกับ feature นี้ เพราะรายงานเป็นไฟล์ ไม่มี adapter (ดึงอัตโนมัติ Won't Q-72) |
| REQ-CMP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี REQ-PRV ใหม่ |
| REQ-AI-021, REQ-AI-022 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี AI |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC | test |
|---|---|
| AC-13-01 ถึง AC-13-08 | backend/tests/test_reconciliation.py | UI-13-01.test.jsx (AC-13-07 AC-13-08 และรายการต้องตรง) |

## 7. ลำดับงาน

T-01 ตรวจไฟล์และจับคู่ | T-02 ผลคืนเงินที่ไม่รู้ | T-03 นำเข้าซ้ำและกุญแจ | T-04 หน้าจอ
