# โมเดลที่ UC-07 ใช้ (MD-CTX-01, MD-DOM-01, MD-STM-01, MD-SEQ-07-05)

เวอร์ชัน 1.0 เข้า Baseline B1 | เขียนด้วย Mermaid เปิดดูภาพได้บน GitHub
ภาพต้นฉบับขนาดเต็มอยู่ในบทเรียน Integrated Requirements Modelling

## MD-CTX-01 Context Diagram (เฉพาะส่วนที่ UC-07 แตะ)

```mermaid
flowchart LR
  C[ลูกค้า] -->|คำขอจอง / ยืนยัน / ยกเลิก| S((ระบบบ้านพร้อม))
  T[ช่าง] -->|รับงาน / ปฏิเสธ / สถานะงาน| S
  A[เจ้าหน้าที่ call center] -->|จองแทนลูกค้า A2| S
  S -->|IF-01 ตัดมัดจำ / คืนเงิน / สอบถามสถานะ| PG[Payment Gateway]
  S -->|IF-02 ส่งข้อความแจ้งเตือน| SMS[ระบบส่งข้อความ]
  S -->|IF-03 ระยะทางจากพิกัด| MAP[บริการแผนที่]
```

## MD-DOM-01 Domain Model (conceptual)

```mermaid
classDiagram
  class Customer { customerId; name; phone PII REQ-PRV-002 }
  class ServiceAddress { addressId; text; geoPoint PII Q-22 }
  class Technician { technicianId; name; skills; baseGeoPoint }
  class TimeSlot { slotId; start; end; state: ว่าง | ล็อกชั่วคราว | จองแล้ว; holdExpiresAt }
  class Job { jobId; category; status (MD-STM-01); depositAmount; scheduledStart }
  class Payment { paymentId; amount; gatewayRef; result: สำเร็จ | ล้มเหลว | หมดเวลา }
  class Refund { refundId; amount; rule R1..R6 }
  Customer "1" --> "1..*" ServiceAddress : AS-03
  Customer "1" --> "0..*" Job
  Technician "1" --> "0..*" TimeSlot : BR-02 ไม่ซ้อนกัน
  Job "1" --> "1" TimeSlot
  Job "1" --> "1" Technician : ช่างหลัก
  Job "1" --> "0..1" Payment
  Job "1" --> "0..1" Refund : BR-01
```

## MD-STM-01 วงจรชีวิตของงาน (8 สถานะ ตาม REQ-DAT-002 ที่แก้ CC-01 แล้ว)

```mermaid
stateDiagram-v2
  [*] --> รอชำระเงิน : สร้างงาน (UC-07 ขั้น 5)
  รอชำระเงิน --> ยืนยันแล้ว : ชำระมัดจำสำเร็จ
  รอชำระเงิน --> ยกเลิกอัตโนมัติ : ไม่ชำระใน 30 นาที หรือชำระไม่สำเร็จ (E1, BR-01 R5)
  ยืนยันแล้ว --> กำลังหาช่างใหม่ : ช่างปฏิเสธ หรือไม่ตอบใน 30 นาที (E3, UC-12 CR-12)
  กำลังหาช่างใหม่ --> ยืนยันแล้ว : จับคู่ช่างใหม่สำเร็จ (UC-05 BR-07)
  กำลังหาช่างใหม่ --> ยกเลิก : หาไม่ได้ใน 2 ชั่วโมง หรือเหลือน้อยกว่า 1 ชั่วโมงก่อนนัด (BR-01 R4 CR-12)
  ยืนยันแล้ว --> ยกเลิก : ลูกค้ายกเลิก (BR-01 R1 / R2) หรือลูกค้าปฏิเสธช่างแทน (BR-01 R4 CR-12)
  ยืนยันแล้ว --> ช่างกำลังเดินทาง : ช่างกดออกเดินทาง
  ช่างกำลังเดินทาง --> ยกเลิก : ลูกค้ายกเลิก (BR-01 R3)
  ช่างกำลังเดินทาง --> กำลังดำเนินงาน : ช่างกด check-in
  กำลังดำเนินงาน --> เสร็จสิ้น : ช่างปิดงาน
  เสร็จสิ้น --> [*]
  ยกเลิก --> [*]
  ยกเลิกอัตโนมัติ --> [*]
```

CR-12 (B6): ลูกศรของ E3 สร้างจริงแล้ว (specs/007-accept-rematch) "ลูกค้าปฏิเสธช่างแทน" เดิมเขียนเป็นลูกศรออกจาก "กำลังหาช่างใหม่" แต่ลูกค้าเห็นช่างแทนได้หลังงานกลับเป็น "ยืนยันแล้ว" จึงย้ายไปเป็นลูกศรออกจาก "ยืนยันแล้ว" (BR-01 R4 ไม่เปลี่ยน) "รับงาน" ของช่างไม่ใช่สถานะของงาน ดู MD-STM-04 ใน specs/007-accept-rematch/models.md Q-50 ปิด (2 ชั่วโมง)
สถานะ "กำลังดำเนินงาน" และ "เสร็จสิ้น" ยกเลิกไม่ได้ (BR-01 R6) จึงไม่มี transition "ยกเลิก" ออกจากสองสถานะนี้
CR-10 (EV-048): เดิมลูกศรสู่ "เสร็จสิ้น" เขียนว่า "ช่างปิดงาน และลูกค้ายืนยัน" Q-31 พบว่าเป็นสเปกผิด ไม่มีใครต้องการขั้นลูกค้ายืนยันใน R1 และลูกศร R3 ไม่รอ Q-14 แล้ว

## MD-SEQ-07-05 ลำดับการชำระมัดจำ (UC-07 ขั้น 5 รวม E1 และ E2)

```mermaid
sequenceDiagram
  participant C as ลูกค้า
  participant S as ระบบบ้านพร้อม
  participant PG as Payment Gateway (IF-01)
  participant N as ระบบส่งข้อความ (IF-02)
  C->>S: กดยืนยัน (slot ที่ล็อกไว้)
  S->>S: ตรวจว่า slot ยังล็อกโดยลูกค้าคนนี้ (ถ้าไม่ = E2 ตอบ 409 พร้อมช่วงใกล้เคียง ไม่ตัดเงิน)
  S->>S: สร้าง Job สถานะ รอชำระเงิน
  S->>PG: authorize(มัดจำ, ref)
  alt ตอบภายใน gateway-timeout (Q-19 ชั่วคราว 30 วินาที)
    PG-->>S: approved / declined
  else ไม่ตอบใน gateway-timeout
    S->>PG: status-inquiry(ref) (REQ-IF-005)
    PG-->>S: approved / declined / unknown
  end
  alt approved
    S->>PG: capture(ref)
    S->>S: Job = ยืนยันแล้ว, slot = จองแล้ว
    S-)N: แจ้งลูกค้าและช่าง (ไม่รอผล ภายใน 60 วินาที REQ-FN-012)
    S-->>C: หมายเลขงาน
  else declined หรือ unknown
    S->>S: Job = ยกเลิกอัตโนมัติ, slot = ว่าง (E1, BR-01 R5)
    S-->>C: แจ้งว่าชำระไม่สำเร็จ
  end
```
