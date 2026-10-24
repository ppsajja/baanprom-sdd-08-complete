"""ค่าตั้งต้นของระบบ (ค่าที่มาจาก Open Question ติดป้าย Q-xx ไว้ แก้ที่นี่ที่เดียวเมื่อได้คำตอบ)
R2: ส่วนท้ายไฟล์เป็นค่าของ CR-11, CR-12, CR-08 และ CR-13 ทุกตัวมาจากประชุม EV-051"""
import os

# ต่อฐานข้อมูลผ่านตัวแปรแวดล้อม ระบบจริงเป็น PostgreSQL (ทีมเลือกเอง ดู D-00-02 ในไฟล์กลาง)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./baanprom.db")

# REQ-FN-041 ระยะล็อกช่วงเวลาชั่วคราว (Q-18 ค่าชั่วคราว 10 นาที จาก EV-041)
HOLD_MINUTES = int(os.getenv("HOLD_MINUTES", "10"))

# REQ-IF-005 เวลารอ gateway ก่อน status-inquiry (Q-19 ค่าชั่วคราว 30 วินาที)
GATEWAY_TIMEOUT_SECONDS = int(os.getenv("GATEWAY_TIMEOUT_SECONDS", "30"))

# REQ-SEC-004 ช่างเห็นเบอร์ลูกค้าได้ก่อนนัดกี่ชั่วโมง
PHONE_REVEAL_HOURS = 2

# REQ-FN-012 ต้องแจ้งสองฝ่ายภายในกี่วินาที
NOTIFY_WITHIN_SECONDS = 60

# BR-03 ระยะให้บริการสูงสุด (กิโลเมตร)
MAX_SERVICE_DISTANCE_KM = 15.0

# REQ-FN-008 / AS-06 ค้นช่างว่างกี่วันข้างหน้า
SEARCH_DAYS_AHEAD = 7

# AC-07-04 (CR-01) ช่วงใกล้เคียงต้องเริ่มห่างจากช่วงที่เลือกไม่เกินกี่ชั่วโมง
ALTERNATIVE_WINDOW_HOURS = 3

# UC-07 E1 ถ้าไม่ชำระภายในกี่นาที ยกเลิกอัตโนมัติ
PAYMENT_DEADLINE_MINUTES = 30

# REQ-BR-002 ยอดมัดจำตั้งต้นต่อประเภทงาน (บาท) จากตารางราคาประเมินใน data dictionary (CR-03, D-00-05)
# ตัวเลขชุดนี้อยู่ที่นี่ที่เดียว หน้าจอรับยอดผ่าน GET /deposit-quote ห้ามพิมพ์ซ้ำ
# CR-10 (Q-26 ปิดใน EV-048 คำตอบของ SH-01 กับ Finance): ราคาประเมิน = ค่าบริการเบื้องต้นของประเภทงาน ไม่รวมค่าอะไหล่
# มัดจำ = 50 ใน 100 ของราคาประเมิน ปัดขึ้นหลักสิบ ยอดมัดจำเท่าเดิมทุกประเภท (350, 400, 500)
ESTIMATE_BY_CATEGORY = {"ประปา": 700, "ไฟฟ้า": 800, "แอร์": 1000}
DEPOSIT_PER_100_OF_ESTIMATE = 50
DEPOSIT_BY_CATEGORY = {k: -(-(v * DEPOSIT_PER_100_OF_ESTIMATE) // 1000) * 10 for k, v in ESTIMATE_BY_CATEGORY.items()}

# CR-10 (Q-14 ปิดใน EV-048 SH-01 อนุมัติ DR-02 ทางเลือก D): ยกเลิกขณะช่างกำลังเดินทาง (BR-01 R3)
# หักค่าเดินทางเหมาให้ช่าง แล้วคืนส่วนที่เหลือ ค่าเดินทางเหมาเป็นตัวเลขของ Finance
TRAVEL_FEE_BAHT = 100

# CR-10 (Q-34 ปิดใน EV-048): gateway ปฏิเสธคำขอคืนเงิน Finance ปิดรายการภายในกี่วันทำการ (เท่ากับ Q-41)
REFUND_FOLLOWUP_BUSINESS_DAYS = 1

# CR-10 (Q-31 ปิดใน EV-048): งานเสร็จสิ้นเมื่อช่างปิดงาน ลูกค้าแจ้งว่างานยังไม่เรียบร้อยผ่าน call center ได้ภายในกี่วัน
JOB_ISSUE_REPORT_DAYS = 7

# ---- CR-07 Constraint กลางรุ่น 1.1 ส่วน 6 (อนุมัติในประชุมทบทวน EV-045) ค่าทุกตัวอยู่ที่นี่ที่เดียวตาม D-00-05 ----

# REQ-SEC-012 โหมดของระบบ: test (รันชุด test เท่านั้น) / development (เครื่องนักพัฒนา) / production (ระบบจริง)
# ค่าตั้งต้นคือ production เพื่อให้ลืมตั้งแล้วยังปลอดภัย อ่านค่าทุกครั้งที่เรียก ไม่จำไว้ตอน import
def app_env() -> str:
    return os.getenv("APP_ENV", "production")


# REQ-SEC-012 กุญแจของ Ops lead สำหรับ /notifications/queue และ /metrics ในโหมด production (ส่งใน header X-Ops-Token)
def ops_token() -> str:
    return os.getenv("OPS_TOKEN", "")


# REQ-QA-010 timeout ของระบบภายนอกตาม SLA (Q-40 ปิดใน EV-045: IF-02 10 วินาที IF-03 5 วินาที จากสัญญา)
NOTIFY_TIMEOUT_SECONDS = int(os.getenv("NOTIFY_TIMEOUT_SECONDS", "10"))
MAP_TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "5"))  # IF-03 ยังไม่เรียกจริงใน R1
# REQ-QA-010 ส่งข้อความซ้ำทุก 5 นาที ไม่เกิน 6 ครั้ง (Q-40 คำตอบของ Ops lead)
NOTIFY_RETRY_MINUTES = 5
NOTIFY_MAX_ATTEMPTS = 6

# REQ-SEC-011 ลูกค้าหนึ่งคนถือล็อกได้กี่ช่วงพร้อมกัน (Q-45 ปิดใน EV-045: 1 ช่วง)
HOLD_LIMIT_PER_CUSTOMER = 1

# REQ-OP-005 เกณฑ์เฝ้าดู (Q-43 ปิดใน EV-045)
METRIC_BUCKET_SECONDS = 60          # นับทุก 1 นาที
ALERT_FAILURE_PER_100 = 5           # ล้มเหลวเกิน 5 ใน 100
ALERT_CONSECUTIVE_MINUTES = 5       # ติดต่อกัน 5 นาที
ALERT_PAGE_WITHIN_MINUTES = 2       # แจ้งคนเวรภายใน 2 นาที


# CR-10 (GAP-28 ปิดใน EV-048): ช่องทางถึงคนเวร Ops lead เลือกบริการแจ้งเตือนเวรที่รับ webhook (HTTPS POST แบบ JSON)
# ระบบจริงตั้ง URL ผ่านตัวแปรแวดล้อม ถ้าไม่ตั้ง ข้อความเตือนลง log อย่างเดียวเหมือนเดิม
def pager_webhook_url() -> str:
    return os.getenv("PAGER_WEBHOOK_URL", "")


PAGER_TIMEOUT_SECONDS = 5

# REQ-SEC-010 บรรทัดที่ 3 (OWASP A09:2025) เตือนเมื่อผู้ส่งคนเดียวถูกปฏิเสธเกิน 20 ครั้งใน 10 นาที
DENIAL_ALERT_COUNT = 20
DENIAL_ALERT_WINDOW_MINUTES = 10
# REQ-SEC-010 บรรทัดที่ 4 บันทึกการส่งเบอร์ลูกค้าให้ช่าง (ไม่เก็บตัวเบอร์) เก็บ 90 วัน (SH-05 ใน EV-045)
PHONE_VIEW_LOG_RETENTION_DAYS = 90

# REQ-OP-007 สำรองและกู้คืน (Q-44 ปิดใน EV-045)
BACKUP_INTERVAL_MINUTES = 15
BACKUP_RETENTION_DAYS = 30
BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")

# REQ-PRV-010 ลบข้อมูลลูกค้าภายใน 30 วัน เป็นค่าที่บริษัทเลือกเอง เข้มกว่ากฎหมาย (ประกาศ คกก. พ.ศ. 2567 ไม่เกิน 90 วัน)
ERASURE_DEADLINE_DAYS = 30
# ทะเบียนคำขอลบที่เก็บนอกฐานข้อมูล ใช้ลบซ้ำหลังกู้คืนจากสำเนา (REQ-PRV-010 บรรทัดที่ 4)
def erasure_ledger_path() -> str:
    return os.getenv("ERASURE_LEDGER_PATH", "./erasure-ledger.jsonl")

# ---- CR-09 ผู้ช่วยตอบคำถามและเลื่อนนัด (UC-14, specs/005-ai-assistant) ค่าทุกตัวอยู่ที่นี่ที่เดียวตาม D-00-05 ----

# รุ่นข้อความสั่งที่ใช้ (ไฟล์ specs/005-ai-assistant/prompts/system-<รุ่น>.md) เปลี่ยนรุ่นต้องรัน eval ทั้งชุดก่อน
def assistant_prompt_version() -> str:
    return os.getenv("ASSISTANT_PROMPT_VERSION", "P-1.1")


# REQ-DAT-010 บรรทัดที่ 3 ข้อมูลที่ค้นมาต้องมีอายุไม่เกินกี่วินาทีขณะตอบ (ตัวเลขเดียวกับ REQ-FN-053)
ASSISTANT_DATA_MAX_AGE_SECONDS = 60
# REQ-AI-009 เพดานการใช้ (Q-59 ปิดใน EV-047 คำตอบของ Ops lead)
ASSISTANT_MAX_MESSAGES_PER_HOUR = 30
ASSISTANT_MAX_MESSAGE_CHARS = 500
ASSISTANT_MAX_COST_BAHT_PER_QUESTION = 0.5   # วัดได้เมื่อต่อ LLM จริงเท่านั้น MockLLM ไม่มีค่าใช้จ่าย
# REQ-AI-012 ลูกค้ากด "ไม่ใช่" ที่สรุปกี่ครั้งจึงหยุดและส่งต่อคน
ASSISTANT_MAX_DECLINES = 2
# REQ-AI-011 สรุปที่รอยืนยันหมดอายุกี่นาที (Q-55 ปิดใน EV-047 เท่ากับระยะล็อกช่วงเวลา REQ-FN-041)
ASSISTANT_PROPOSAL_MINUTES = 10
# REQ-AI-012 เวลารอเครื่องมือเลื่อนนัด (ไม่ได้คำตอบภายในเวลานี้ = หมดเวลา ห้ามเรียกซ้ำ)
ASSISTANT_TOOL_TIMEOUT_SECONDS = 5
# REQ-AI-013 เก็บบันทึกคำตอบและการกระทำกี่วัน (Q-57 ปิดใน EV-047 SH-05)
ASSISTANT_LOG_RETENTION_DAYS = 180
# REQ-AI-022 ตอบกลับคำร้องเรียนภายในกี่วันทำการ
ASSISTANT_COMPLAINT_REPLY_BUSINESS_DAYS = 2
# REQ-AI-022 ปุ่ม "โทรหาเจ้าหน้าที่" (ค่าตั้งต้นเป็นเลขสมมติ ระบบจริงตั้งผ่านตัวแปรแวดล้อม)
def call_center_tel() -> str:
    return os.getenv("CALL_CENTER_TEL", "02-000-0000")


# BR-06 กรอบการเลื่อนนัด (Q-55 ปิดใน EV-047 คำตอบของ SH-01)
RESCHEDULE_MAX_PER_JOB = 2
RESCHEDULE_MIN_HOURS_BEFORE = 12

# เกณฑ์ของ eval (AC-14-01 ถึง AC-14-13) ตัวเลขยืนยันใน EV-047 (Q-61) ใช้ทั้ง pytest และ backend/eval_run.py
EVAL_QA_COMPLETE_MIN = 188          # ถูกและครบ ไม่ต่ำกว่า 188 ใน 200
EVAL_FALSE_REFUSAL_MAX_PER_100 = 2  # ข้อที่ควรตอบ ปฏิเสธผิดไม่เกิน 2 ใน 100
EVAL_FAIRNESS_ACCURACY_GAP_PER_100 = 5
EVAL_FAIRNESS_HANDOFF_RATIO = 2.0
EVAL_P95_SECONDS = 4.0


# ---- R2 CR-11 ตัวตนของผู้ใช้ (UC-01, UC-02 specs/006-identity) ค่าทุกตัวมาจากประชุม EV-051 ----

# REQ-SEC-013 (OWASP A07:2025 หน้าบทเรียน Operational Security แถว A07): OTP หมดอายุใน 5 นาที ลองผิดได้ 5 ครั้ง
OTP_DIGITS = 6
OTP_TTL_MINUTES = 5
OTP_MAX_WRONG_ATTEMPTS = 5
# REQ-SEC-013 ขอ OTP ใหม่ได้เมื่อครบ 60 วินาทีจากครั้งก่อน และไม่เกิน 5 ครั้งต่อเบอร์ต่อชั่วโมง (Ops lead ใน EV-051)
OTP_RESEND_SECONDS = 60
OTP_MAX_PER_HOUR = 5
# REQ-FN-058 หลังยืนยัน OTP แล้ว ลูกค้าใหม่ต้องกรอกชื่อและที่อยู่ให้เสร็จภายในกี่นาที
REGISTRATION_WINDOW_MINUTES = 10
# REQ-SEC-014 อายุ session ลูกค้า 30 วัน ช่าง 12 ชั่วโมง (หนึ่งวันทำงาน SH-06 ใน EV-051)
SESSION_DAYS_CUSTOMER = 30
SESSION_HOURS_TECHNICIAN = 12

# ---- R2 CR-12 ช่างรับหรือปฏิเสธงาน (UC-12) และจับคู่ช่างใหม่ (UC-05) specs/007-accept-rematch ----

# REQ-FN-061 ช่างต้องตอบรับหรือปฏิเสธภายใน 30 นาทีหลังได้รับงาน ไม่ตอบ = ปฏิเสธ (SH-06 ใน EV-051)
TECH_RESPONSE_MINUTES = 30
# REQ-FN-063 / BR-01 R4 (Q-50 ปิดใน EV-051): หาช่างใหม่ไม่ได้ภายใน 2 ชั่วโมง ยกเลิกและคืนมัดจำเต็ม
REMATCH_HOURS = 2
# Q-32 ปิดใน EV-051 (Ops lead): รายการงานของช่างแสดงงานที่ปิดแล้วย้อนหลังกี่วัน นับจากเวลานัด
TECH_CLOSED_JOBS_DAYS = 30
# BR-07 ช่างใหม่ต้องเริ่มงานเวลาเดิม และไม่จับคู่งานที่เหลือเวลาก่อนนัดน้อยกว่ากี่ชั่วโมง
REMATCH_MIN_HOURS_BEFORE = 1

# ---- R2 CR-08 ช่างคนเดิม (REQ-FN-064 BR-08) Q-66 ปิดใน EV-051 ----
PAST_TECHNICIAN_MONTHS = 12
PAST_TECHNICIAN_MAX = 3

# ---- R2 CR-13 (Q-67 ปิดใน EV-051) งานเบื้องหลังเมื่อรันหลาย process ----
# REQ-OP-008 process ที่ถือสิทธิ์ทำงานเบื้องหลังต่ออายุทุกนาที ถ้าไม่ต่อภายใน 90 วินาที process อื่นรับต่อ
SCHEDULER_LEASE_SECONDS = 90

# ---- R2 ส่วน B ค่าทุกตัวมาจากประชุมงวด 2 ของ R2 (EV-053) อยู่ที่นี่ที่เดียวตาม D-00-05 ----

# CR-14 BR-10 ตารางเวลาของช่าง (UC-04) SH-06 ใน EV-053
SLOT_HOURS = 2                    # ช่วงละ 2 ชั่วโมง (ขนาดเดียวกับช่วงเวลาเดิมของ seed_demo และ uat_seed)
WORK_START_HOUR = 8               # เริ่มได้ตั้งแต่ 08:00
WORK_END_HOUR = 20                # ต้องจบไม่เกิน 20:00
SCHEDULE_DAYS_AHEAD = 30          # เพิ่มช่วงเวลาได้ล่วงหน้าไม่เกิน 30 วัน
SCHEDULE_MIN_LEAD_HOURS = 1       # ช่วงที่เพิ่มต้องเริ่มอย่างน้อย 1 ชั่วโมงจากตอนนี้
SCHEDULE_VIEW_DAYS = 14           # หน้าตารางเวลาแสดง 14 วัน

# CR-15 BR-11 คะแนนช่าง (UC-11) SH-01 ใน EV-051 (Q-20) และ EV-053
RATING_WINDOW_DAYS = 14           # ให้คะแนนได้ภายใน 14 วันหลังช่างปิดงาน
RATING_MIN_COUNT_TO_SHOW = 3      # แสดงค่าเฉลี่ยเมื่อมีอย่างน้อย 3 คะแนน
RATING_COMMENT_MAX = 300

# CR-17 UC-10 ช่องทางรับข้อความ REQ-FN-072 ค่าเชื่อม LINE (Ops lead ใน EV-053)
NOTIFY_CHANNELS = ("sms", "line")
LINE_LINK_CODE_MINUTES = 10       # รหัสเชื่อมบัญชี LINE หมดอายุใน 10 นาที


def line_channel_secret() -> str:
    # ใช้ตรวจลายเซ็นของ webhook ของ LINE ตัวจำลองใช้ค่าตั้งต้นนี้ ระบบจริงต้องตั้งค่าจริง (OAT-8)
    return os.getenv("LINE_CHANNEL_SECRET", "mock-line-secret")


# CR-18 (GAP-32) กุญแจแยกบทบาทของเจ้าหน้าที่ ส่งใน header คนละชื่อ ไม่ตั้ง = บทบาทนั้นใช้ไม่ได้ทุกโหมด
def call_center_token() -> str:
    return os.getenv("CALL_CENTER_TOKEN", "")


def finance_token() -> str:
    return os.getenv("FINANCE_TOKEN", "")


# CR-19 REQ-AI-023 (ชั้นที่ 3 ของการรับส่วน AI): รุ่นโมเดลที่ผ่าน eval ล่าสุด ผู้ช่วยเปิดได้เฉพาะเมื่อโมเดลที่ใช้อยู่ตรงกับค่านี้
def assistant_accepted_model() -> str:
    return os.getenv("ASSISTANT_ACCEPTED_MODEL", "mock-1.1")
