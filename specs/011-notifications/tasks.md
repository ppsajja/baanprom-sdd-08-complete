# Tasks: รับการแจ้งเตือนทาง SMS หรือ LINE (UC-10)

Feature: SPEC-NOTIFICATIONS | อ้างอิง: plan.md (plan v1) | /tasks วันที่ 2569-12-10 (tasks v1, prompt-log.md #98)
สรุป: 5 task | 0 task รอ Q-xx | สถานะปัจจุบัน: เสร็จ 5

### T-01 ChannelRouter และตัวจำลอง SMS LINE
- รองรับ: REQ-FN-072, REQ-IF-012 | ตรวจด้วย: AC-10-01, AC-10-05, AC-10-06
- ไฟล์ที่แตะ: backend/app/notify/channels.py, queue.py, backend/app/booking/service.py, payments/service.py (F-20)
- สถานะ: เสร็จ

### T-02 ตั้งค่าช่องทางและเชื่อม LINE ผ่าน webhook
- รองรับ: REQ-FN-072, BR-12 ข้อ 1 ถึง 3 และ 7 | ตรวจด้วย: AC-10-02, AC-10-03
- ไฟล์ที่แตะ: backend/app/notify/preferences.py, router.py, backend/app/integrations/http_messaging.py (line_signature)
- สถานะ: เสร็จ

### T-03 ส่ง SMS แทน และบันทึกการส่ง
- รองรับ: REQ-FN-073, BR-12 ข้อ 4 และ 6 | ตรวจด้วย: AC-10-04, AC-10-07
- เสร็จเมื่อ: test ผ่าน และเมื่อตัดการส่งแทนออก test_AC_10_04 ต้องพัง (พิสูจน์ชั้น 3)
- สถานะ: เสร็จ (พิสูจน์ชั้น 3: ให้ LINE ล้มแล้วส่งต่อข้อผิดพลาดแทนการส่ง SMS test_AC_10_04 พัง แก้กลับแล้วผ่าน)

### T-04 ตัวจริงที่ปิดไว้ (SMS ตามสัญญา IF-02 LINE push)
- รองรับ: REQ-IF-012 | ตรวจด้วย: AC-00-13 (test_cross_cutting_r2b.py)
- ไฟล์ที่แตะ: backend/app/integrations/http_messaging.py
- สถานะ: เสร็จ

### T-05 หน้าจอ UI-10-01
- ตรวจด้วย: UI-10-01.test.jsx | ไฟล์ที่แตะ: frontend/src/pages/NotificationSettings.jsx, App.jsx, api/client.js
- สถานะ: เสร็จ

## ตารางความครบ

| AC | task |
|---|---|
| AC-10-01, AC-10-05, AC-10-06 | T-01 |
| AC-10-02, AC-10-03 | T-02, T-05 |
| AC-10-04, AC-10-07 | T-03 |
