# โมเดลที่ UC-01 และ UC-02 ใช้ (MD-CTX-02, MD-STM-03, MD-SEQ-02-01)

เวอร์ชัน 1.0 เข้า Baseline B6 ตาม CR-11 | เขียนด้วย Mermaid
MD-DOM-01 เพิ่ม Account (1 ต่อ Customer หรือ Technician) AuthSession (0..* ต่อ Account) OtpChallenge (ผูกกับเบอร์ ไม่ผูกกับ Account เพราะลูกค้าใหม่ยังไม่มีบัญชี) ดู docs/srs/models.md ส่วน 6

## MD-CTX-02 Context Diagram (เฉพาะส่วนที่ UC-01 และ UC-02 แตะ)

```mermaid
flowchart LR
  C[ลูกค้า] -->|เบอร์โทร / รหัส OTP / ชื่อ ที่อยู่| S((ระบบบ้านพร้อม))
  T[ช่าง] -->|เบอร์โทร / รหัส OTP| S
  O[Ops] -->|ออกบัญชีช่าง X-Ops-Token| S
  S -->|IF-02 ส่งรหัส OTP ไปที่เบอร์| SMS[ระบบส่งข้อความ]
```

## MD-STM-03 วงจรของคำขอ OTP 1 คำขอ

```mermaid
stateDiagram-v2
  [*] --> รอรหัส : ขอรหัส (ส่งทาง IF-02 หรือไม่ส่งถ้าเป็นเบอร์ช่างที่ไม่มีบัญชี)
  รอรหัส --> รอรหัส : กรอกผิด (ครั้งที่ 1 ถึง 4)
  รอรหัส --> ล็อก : กรอกผิดครั้งที่ 5
  รอรหัส --> หมดอายุ : ครบ 5 นาที หรือมีคำขอใหม่ของเบอร์เดียวกัน
  รอรหัส --> ใช้แล้ว : กรอกถูก และมีบัญชี (ออก session)
  รอรหัส --> ยืนยันแล้ว : กรอกถูก ลูกค้าใหม่
  ยืนยันแล้ว --> ใช้แล้ว : ลงทะเบียนภายใน 10 นาที (ออก session)
  ยืนยันแล้ว --> หมดอายุ : ไม่ลงทะเบียนภายใน 10 นาที
  ล็อก --> [*]
  หมดอายุ --> [*]
  ใช้แล้ว --> [*]
```

## MD-SEQ-02-01 ลำดับการเข้าสู่ระบบ (UC-02 และ UC-01 ใช้ลำดับเดียวกัน)

```mermaid
sequenceDiagram
  participant U as ลูกค้าหรือช่าง
  participant S as ระบบบ้านพร้อม
  participant N as ระบบส่งข้อความ (IF-02)
  U->>S: POST /auth/otp (phone, role)
  S->>S: BR-09 ข้อ 3 (60 วินาที 5 ครั้งต่อชั่วโมง) เก็บแฮชของรหัส
  S->>N: ส่งรหัส (ไม่ผ่านคิว ไม่ลง log) D-02-03
  S-->>U: 202 challenge_id expires_at (เหมือนกันทุกเบอร์)
  U->>S: POST /auth/verify (challenge_id, code)
  alt ผิด หมดอายุ ล็อก
    S-->>U: 401 หรือ 410 พร้อมข้อความ
  else มีบัญชี
    S-->>U: token (30 วัน หรือ 12 ชั่วโมง)
  else ลูกค้าใหม่
    S-->>U: needs_registration
    U->>S: POST /auth/register (challenge_id, ชื่อ, ที่อยู่, พิกัด)
    S-->>U: 201 token
  end
  U->>S: คำขออื่นทุกตัว Authorization: Bearer token
  S->>S: auth/deps.py หา session จากแฮช ตรวจหมดอายุและยกเลิก แล้วส่งตัวตนให้ endpoint
```
