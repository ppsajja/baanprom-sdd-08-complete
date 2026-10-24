# คู่มือติดตั้งและตั้งค่าระบบจริง บ้านพร้อม R1

ผู้ใช้คู่มือ: Ops lead และผู้ดูแลเครื่อง | เจ้าของคู่มือ: Dev lead | รุ่นของระบบ: Baseline B5 (commit ที่ติดป้ายตอนลงนามรับ R1)
ทุกขั้นในคู่มือนี้ผ่านการทำจริงแล้วบนเครื่องทดสอบใน OAT-1 และ OAT-4 (docs/acceptance/oat-results-r1.md) ส่วนที่ยังไม่เคยทำบนเครื่องจริงเขียนกำกับไว้

## 1. สิ่งที่ต้องมีก่อน

- เครื่องหลังบ้าน Linux ที่มี Python 3.11 หรือ 3.12 (test ผ่านทั้งสองรุ่น D-00-01)
- PostgreSQL 16 หรือใหม่กว่า (D-00-02) แยกเครื่องหรือแยกบริการได้
- Node.js 22 สำหรับ build หน้าจอ (ใช้เฉพาะตอน build ไม่ต้องอยู่บนเครื่องจริง)
- ที่เก็บสำเนาที่อยู่คนละเครื่องกับฐานข้อมูล (REQ-OP-007) เช่น /mnt/offsite
- URL ของบริการแจ้งเตือนเวรที่ Ops lead เลือก (GAP-28)

## 2. ติดตั้งหลังบ้าน

ติดตั้งจากของที่ส่งมอบเท่านั้น (git archive ของ commit ที่ติดป้าย) ไม่ใช้โฟลเดอร์ของนักพัฒนา

```
mkdir /opt/baanprom && cd /opt/baanprom
git archive --remote=<repo ที่ส่งมอบ> <ป้ายรุ่น B5> | tar -x     # หรือแตกไฟล์ zip ที่ส่งมอบ
python3.12 -m venv venv
venv/bin/pip install -r backend/requirements.txt
cd backend && ../venv/bin/python -m pytest -q -k "AC_"           # ต้องได้ passed ทั้งหมด ไม่มี failed
```

requirements.txt กำหนดแค่รุ่นต่ำสุด ตอน OAT-1 venv ใหม่ได้ fastapi 0.162.0 และ SQLAlchemy 2.1.6 ซึ่งใหม่กว่าเครื่องนักพัฒนา test ยังผ่าน แต่ถ้าวันติดตั้งจริง test ไม่ผ่าน ให้หยุดและแจ้ง Dev lead ห้ามเปิดระบบ (ความเสี่ยงชนิด env เสนอให้ล็อกรุ่นใน R2)

## 3. ตั้งค่า (ตัวแปรแวดล้อม)

| ตัวแปร | ค่าในระบบจริง | ถ้าไม่ตั้ง | อ้าง |
|---|---|---|---|
| APP_ENV | production (หรือไม่ตั้ง) | เป็น production เอง ห้ามตั้ง test หรือ development บนเครื่องจริง | REQ-SEC-012 |
| DATABASE_URL | postgresql+psycopg://<ผู้ใช้>:<รหัส>@<เครื่อง>/<ฐาน> | ใช้ SQLite ในโฟลเดอร์ ห้ามใช้ในระบบจริง | D-00-02 |
| OPS_TOKEN | กุญแจยาวที่ Ops lead สร้าง เก็บนอกเอกสารและแชต | endpoint ของ ops ใช้ไม่ได้ | REQ-SEC-012 |
| PAGER_WEBHOOK_URL | URL ของบริการแจ้งเตือนเวร | ข้อความเตือนลง log อย่างเดียว คนเวรไม่รู้ ห้ามเปิดระบบ | REQ-OP-005, GAP-28 |
| ERASURE_LEDGER_PATH | ไฟล์บนที่เก็บนอกฐานข้อมูล เช่น /mnt/offsite/erasure-ledger.jsonl | ไฟล์ในโฟลเดอร์โปรแกรม หายพร้อมเครื่อง | REQ-PRV-010 บรรทัดที่ 4 |
| BACKUP_DIR | /mnt/offsite | ./backups | REQ-OP-007 |
| CALL_CENTER_TEL | เลขจริงของ call center | 02-000-0000 (เลขสมมติ) | Q-31, REQ-AI-022 |
| HOLD_MINUTES, GATEWAY_TIMEOUT_SECONDS, NOTIFY_TIMEOUT_SECONDS | ไม่ต้องตั้ง (ค่าใน config.py มีผู้ยืนยันแล้ว Q-18, Q-19, Q-40) | ใช้ค่าใน config.py | D-00-05 |
| FAKE_GATEWAY_MODE, FAKE_GATEWAY_INQUIRY, FAKE_GATEWAY_REFUND_MODE | ห้ามตั้ง มีไว้สำหรับเครื่องทดสอบเท่านั้น | | CR-10 |

สิ่งที่ปิดเองในโหมด production ไม่ต้องตั้งเพิ่ม แต่ต้องตรวจหลังเปิดทุกครั้ง (ขั้นที่ 5)
- หน้าเอกสารที่ framework เปิดให้ (/docs /redoc /openapi.json) ปิด
- ช่อง now= ที่ test ใช้กำหนดเวลา ถูกเพิกเฉย ระบบใช้นาฬิกาของเครื่องเสมอ

## 4. ฐานข้อมูลและข้อมูลตั้งต้น

- สร้างฐานข้อมูลว่างและผู้ใช้ของระบบ ตารางสร้างเองตอนหลังบ้านเริ่ม (migration m001 ถึง m003 และ m004 ของ R2 ซึ่งเพิ่ม index ของตารางเดิมด้วย)
- ข้อมูลช่างและตารางเวลาของช่าง: R1 ยังไม่มีหน้าจอหรือ REQ สำหรับเติม (operations.md เหตุการณ์ที่ 3) วันติดตั้งจริงให้ Dev lead ใส่จากรายชื่อที่ SH-06 ส่ง ด้วยสคริปต์แบบเดียวกับ backend/uat_seed.py และบันทึกเป็นบันทึกเหตุการณ์ (transition requirement ที่ยังไม่มีเจ้าของในสเปก เสนอใน TOR ของ R2)
- ห้ามใช้ uat_seed.py หรือ seed_demo.py กับฐานข้อมูลจริง (สร้างลูกค้าทดสอบ)

## 5. เปิดหลังบ้านและตรวจหลังเปิด

```
cd /opt/baanprom/backend
../venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

R2 (CR-13, Q-67 ปิด): ใช้คำสั่งนี้แทน รันได้หลาย process จำนวน process เท่าจำนวน CPU ของเครื่อง (เครื่องจริง 4 CPU ตาม Q-68)

```
cd /opt/baanprom/backend
DB_POOL_SIZE=40 ../venv/bin/python -m app.ops.serve --host 0.0.0.0 --port 8000 --workers 4
```

app.ops.serve ตั้ง TCP_NODELAY ให้ทุกการเชื่อมต่อ (GAP-41 uvicorn ตรงแบบหลาย process ช้าเพิ่มราว 40 มิลลิวินาทีต่อคำขอ) จำนวน process คูณ DB_POOL_SIZE ต้องไม่เกิน max_connections ของ PostgreSQL บัญชีช่างออกด้วย POST /ops/technicians/{id}/account หลัง SH-06 ตรวจตัวตน
ข้อความเดิมของ R1 คงไว้อ่านย้อนหลัง: ใช้ process เดียว (--workers 1) เท่านั้นใน R1 เพราะคิวข้อความ ตัวนับ /metrics และสถานะการเตือนอยู่ในหน่วยความจำของ process ถ้ามีหลาย process แต่ละตัวนับเฉพาะคำขอของตัวเอง /metrics จะแสดงไม่ครบ และเกณฑ์เตือนของ REQ-OP-005 อาจไม่ถึง (Q-67) การทดสอบโหลดใช้ 2 process แล้วเร็วขึ้นไม่มาก (docs/acceptance/load-test-r1.md)

ให้บริการระบบ (systemd หรือเทียบเท่า) เริ่มคำสั่งนี้เองเมื่อเครื่องเปิด และเก็บ stdout ไว้ log ของแอปออก stdout เป็น JSON บรรทัดละเหตุการณ์ (DEF-02 แก้แล้ว)
ตรวจทุกครั้งหลังเปิด (ใช้เวลาไม่ถึง 1 นาที)

```
curl -s $BASE/health                                   # {"ok":true}
curl -s $BASE/ready                                    # {"ok":true,"database":"ok"}
curl -s -o /dev/null -w "%{http_code}\n" $BASE/docs    # 404
curl -s -o /dev/null -w "%{http_code}\n" $BASE/metrics # 403 (ไม่มีกุญแจ)
curl -s -H "X-Ops-Token: $TOKEN" $BASE/metrics          # รายการตัวนับ
curl -s $BASE/assistant/status                         # "enabled": false (ผู้ช่วยต้องปิดใน R1 ดูขั้นที่ 7)
```

## 6. หน้าจอ

```
cd frontend && npm ci && npm run build      # ได้โฟลเดอร์ dist/
```

ให้เว็บเซิร์ฟเวอร์ส่งไฟล์ใน dist/ และส่งต่อ /api/ ไปที่หลังบ้าน (ตอนพัฒนา Vite ทำหน้าที่นี้ ระบบจริงต้องตั้งที่เว็บเซิร์ฟเวอร์) หรือ build ด้วย VITE_API_BASE=<URL ของหลังบ้าน>

## 7. ปิดผู้ช่วย UC-14 ก่อนเปิดระบบ

ผู้ช่วยไม่อยู่ในสิ่งที่รับใน R1 (บันทึกการตรวจรับ) แต่ค่าตั้งต้นของระบบคือเปิด ต้องปิดหลังติดตั้งครั้งแรก

```
curl -s -X POST -H "X-Ops-Token: $TOKEN" -H "Content-Type: application/json" -d '{"enabled": false}' $BASE/ops/assistant/switch
```

ค่าปิดเก็บในฐานข้อมูล เริ่มหลังบ้านใหม่แล้วยังปิดอยู่ ถ้ากู้คืนจากสำเนาที่ทำก่อนปิด ต้องสั่งปิดซ้ำ

## 8. สำรองข้อมูล

ตั้ง cron บนเครื่องที่ Ops lead ดูแล ตามส่วน "สำรองและกู้คืน" ของ docs/srs/operations.md (สำรองทุก 15 นาที ลบสำเนาเกิน 30 วัน) แล้วซ้อมกู้คืน 1 ครั้งในวันติดตั้ง บันทึกเป็น INC-nn เหมือน docs/srs/incidents/INC-01.md เครื่องทดสอบไม่มี cron ขั้นนี้จึงยังไม่เคยทำจริง

## 9. ย้อนกลับรุ่น

ถ้ารุ่นใหม่มีปัญหาหลังติดตั้ง: หยุดหลังบ้าน แตกไฟล์รุ่นก่อนลงโฟลเดอร์ใหม่ ชี้บริการไปโฟลเดอร์นั้น แล้วเปิด ตารางของรุ่นใหม่ที่เพิ่มขึ้นไม่ทำให้รุ่นเก่าพัง (migration เพิ่มตารางและคอลัมน์ ไม่ลบ) ถ้าข้อมูลเสีย ใช้ขั้นตอนกู้คืนใน operations.md ผู้สั่งย้อนกลับคือ Ops lead
