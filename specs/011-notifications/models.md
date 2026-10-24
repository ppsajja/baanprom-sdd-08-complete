# โมเดลที่ UC-10 ใช้ (MD-CTX-10, MD-SEQ-10-01)

เวอร์ชัน 1.0 เข้า Baseline B7 ตาม CR-17 | สัญญา IF-02 (SMS และ LINE) อยู่ที่ docs/srs/models.md ส่วน 9

## MD-CTX-10 Context Diagram

```mermaid
flowchart LR
  F[ทุก feature] -->|วางข้อความลงคิว REQ-OP-008| Q[(notification_messages)]
  Q -->|งานเบื้องหลังทุก 1 นาที| R((ChannelRouter))
  R -->|IF-02 SMS| SMS[[ผู้ให้บริการ SMS]]
  R -->|IF-02 LINE push| LINE[[LINE Messaging API]]
  LINE -->|webhook รหัสเชื่อม ลายเซ็น| S((ระบบบ้านพร้อม))
  U[ลูกค้า ช่าง] -->|เลือกช่องทาง| S
```

## MD-SEQ-10-01 ส่งข้อความ 1 ข้อความ

```mermaid
sequenceDiagram
  participant Q as คิว (deliver_due)
  participant R as ChannelRouter
  participant L as IF-02 LINE
  participant M as IF-02 SMS
  Q->>R: send(ข้อความ, timeout 10 วินาที)
  R->>R: อ่านช่องทางของผู้รับ
  alt LINE และเชื่อมแล้ว
    R->>L: push
    alt สำเร็จ
      R->>R: บันทึก line sent
    else ไม่ตอบหรือปฏิเสธ
      R->>R: บันทึก line failed
      R->>M: send (ส่งแทน BR-12 ข้อ 4)
    end
  else SMS
    R->>M: send
  end
  alt SMS ไม่ตอบ
    R-->>Q: NotifierTimeout ส่งซ้ำรอบหน้า (REQ-QA-010)
  else ไม่มีเบอร์
    R->>R: บันทึก no_contact (BR-12 ข้อ 6)
  end
```
