# Plan: รับการแจ้งเตือนทาง SMS หรือ LINE (UC-10)

อ้างอิง: spec.md SPEC-NOTIFICATIONS 1.0 | Updated: 2569-12-10 | /plan แล้วทีมตรวจ (plan v1, prompt-log.md #97)
อ้างอิง Constraint กลาง: specs/000-shared/constraints.md รุ่น 1.4

## 1. สรุปแนวทาง

- notify/channels.py: interface SmsSender LineSender ตัวจำลอง MockSms MockLine และ ChannelRouter (Notifier ตัวที่ระบบใช้) สร้างจากค่าตั้ง SMS_ADAPTER LINE_ADAPTER
- notify/preferences.py notify/router.py: ตั้งค่าช่องทาง เชื่อม LINE webhook ตรวจลายเซ็น กล่องข้อความของตัวจำลอง (เครื่องทดสอบ)
- integrations/http_messaging.py: ตัวจริงที่ปิดไว้ (SMS ตามสัญญา IF-02 LINE push message)
- คิวเดิม (queue.deliver_due) ส่ง session ให้ตัวส่งที่ต้องการบันทึกผล (wants_db) FakeNotifier เดิมใช้ได้เหมือนเดิม (test เดิมไม่ต้องแก้)
- ข้อความ "มีงานใหม่" ของ booking และ payments เพิ่มเวลาที่ต้องตอบ (F-20)
- หน้าจอ NotificationSettings.jsx (UI-10-01) เมนู "การแจ้งเตือน" ของลูกค้าและช่าง

## 2. เทคโนโลยีที่ใช้

httpx (มีอยู่แล้วใน requirements) สำหรับตัวจริง ไม่มีของใหม่

```
backend/app/notify/channels.py, preferences.py, router.py          ใหม่
backend/app/notify/queue.py                                        แก้ (deliver_due ส่ง db ตัวส่งตั้งต้น ChannelRouter)
backend/app/integrations/http_messaging.py                         ใหม่
backend/app/booking/service.py, payments/service.py                แก้ ข้อความงานใหม่ (F-20)
backend/app/erasure/service.py                                     แก้ ลบรหัส LINE
backend/tests/test_notifications.py                                ใหม่
frontend/src/pages/NotificationSettings.jsx, App.jsx, api/client.js   ใหม่และแก้
frontend/src/__tests__/UI-10-01.test.jsx                           ใหม่
```

## 3. โมเดลข้อมูล

notification_preferences, notification_deliveries (spec ส่วน 7)

## 4. API / หน้าจอ

| method path | ผู้เรียก | ตอบ |
|---|---|---|
| GET /me/notifications | ลูกค้าหรือช่าง | {channel, line_linked, channels} |
| PUT /me/notifications {channel} | ลูกค้าหรือช่าง | 200 | 409 line_not_linked | 422 unknown_channel |
| POST /me/notifications/line-link | ลูกค้าหรือช่าง | {link_code, instruction, expires_at} |
| POST /me/notifications/line-unlink | ลูกค้าหรือช่าง | 200 |
| POST /integrations/line/webhook | LINE (X-Line-Signature) | {linked} | 403 ลายเซ็นผิด |
| GET /ops/notifications/outbox | Ops (เครื่องทดสอบ) | ข้อความล่าสุดของตัวจำลอง เบอร์เหลือ 4 ตัวท้าย |

## 5. ตารางตรวจ Constraints

| ID | ใช้อย่างไรใน feature นี้ |
|---|---|
| REQ-CON-001 | ไม่เกี่ยวกับ feature นี้ เพราะเป็นข้อจำกัดของ R1 |
| REQ-CON-003 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีการเงิน |
| REQ-PRV-002 | ใช้แล้ว บันทึกการส่งและ log ไม่มีข้อความ เบอร์ หรือรหัส LINE (AC-10-07) |
| REQ-OP-001 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี SLO ของตัวเอง |
| REQ-OP-005 | ใช้แล้ว endpoint ใหม่ถูกนับ |
| REQ-OP-006 | ใช้แล้ว operations.md เหตุการณ์ที่ 4 เพิ่มคำสั่งดูบันทึกการส่งตามช่องทาง |
| REQ-OP-007 | ไม่เกี่ยวกับ feature นี้ เพราะตารางใหม่อยู่ในสำเนาเดิม |
| REQ-OP-008 | ใช้แล้ว ตัวส่งบันทึกผลในธุรกรรมเดียวกับคิว หลาย process ใช้กล่องข้อความของตัวจำลองร่วมกันผ่าน MOCK_OUTBOX_PATH |
| REQ-OP-009 | ใช้แล้ว SMS และ LINE รายงานใน /ops/integrations |
| REQ-QA-010 | ใช้แล้ว timeout 10 วินาทีทั้งสองช่องทาง SMS ไม่ตอบใช้การส่งซ้ำเดิม |
| REQ-SEC-010 | ไม่เกี่ยวกับ feature นี้ เพราะไม่รับเลขงาน (การตั้งค่าเป็นของผู้เรียกเองจาก token) |
| REQ-SEC-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ล็อกช่วงเวลา |
| REQ-SEC-012 | ใช้แล้ว endpoint ใหม่อยู่ในบัญชี endpoint กล่องข้อความของตัวจำลองต้องมีกุญแจของ Ops |
| REQ-SEC-013 | ใช้แล้ว OTP ส่ง SMS เสมอ (AC-10-05) |
| REQ-SEC-014 | ใช้แล้ว ผู้ตั้งค่ามาจาก token |
| REQ-SEC-015 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มีบทบาทเจ้าหน้าที่ |
| REQ-PRV-010 | ใช้แล้ว ลบรหัส LINE และส่งคำขอลบไปผู้ให้บริการ SMS |
| REQ-PRV-011 | ไม่เกี่ยวกับ feature นี้ เพราะไม่ใช้พิกัด |
| REQ-IF-012 | ใช้แล้ว SMS_ADAPTER LINE_ADAPTER ตัวจริงตามสัญญา IF-02 (AC-00-13) |
| REQ-CMP-001 | ใช้แล้ว SH-05 ตรวจข้อ 5 ของรายการ PDPA (spec ส่วน 7) |
| REQ-AI-021, REQ-AI-022 | ไม่เกี่ยวกับ feature นี้ เพราะไม่มี AI |

## 6. แผนทดสอบจาก Acceptance Criteria

| AC | test |
|---|---|
| AC-10-01 ถึง AC-10-07 | backend/tests/test_notifications.py | UI-10-01.test.jsx (AC-10-02 และรายการต้องตรง) |

## 7. ลำดับงาน

T-01 ChannelRouter และตัวจำลอง | T-02 ตั้งค่าและเชื่อม LINE | T-03 ส่งแทนและบันทึก | T-04 ตัวจริงที่ปิดไว้ | T-05 หน้าจอ
