# โมเดลที่ UC-11 ใช้ (MD-CTX-11, MD-SEQ-11-01)

เวอร์ชัน 1.0 เข้า Baseline B7 ตาม CR-15 | Rating อยู่ใน MD-DOM-01 (docs/srs/models.md ส่วน 6)

## MD-CTX-11 Context Diagram

```mermaid
flowchart LR
  C[ลูกค้า] -->|ดาว ความเห็น| S((ระบบบ้านพร้อม))
  S -->|ค่าเฉลี่ยและจำนวน| C2[ลูกค้าที่ค้นหาช่าง]
  S -->|ค่าเฉลี่ยของตัวเอง| T[ช่าง]
  S -->|ความเห็นไม่มีชื่อลูกค้า| H[หัวหน้าช่าง SH-06]
```

## MD-SEQ-11-01 ให้คะแนน

```mermaid
sequenceDiagram
  participant C as ลูกค้า
  participant S as ระบบบ้านพร้อม
  C->>S: GET /me/jobs (can_rate จากระบบ)
  C->>S: POST /jobs/{id}/rating {stars, comment}
  S->>S: ตรวจเจ้าของงาน (REQ-SEC-010) BR-11 ข้อ 2 ถึง 4 และ 8
  S->>S: ปิดบังความเห็น ตรวจข้อ 5 (counted) บันทึก
  S-->>C: 201 ขอบคุณสำหรับคะแนน
```
