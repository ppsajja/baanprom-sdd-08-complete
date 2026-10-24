"""CR-18 (R2 ส่วน B): ระบบภายนอกทุกตัวอยู่หลัง interface และเลือกตัวที่ใช้ด้วยค่าตั้ง (REQ-IF-012 REQ-OP-009)
| interface | ค่าตั้ง | ตัวจำลอง (ค่าตั้งต้น) | ตัวจริง (ปิดไว้จนกว่าจะตั้ง URL และกุญแจ) |
| IF-01 Payment Gateway | PAYMENT_ADAPTER | fake (FakeGateway) | http (http_payment.HttpGateway) |
| IF-02 SMS | SMS_ADAPTER | mock (notify.channels.MockSms) | http (http_messaging.HttpSmsSender) |
| IF-02 LINE | LINE_ADAPTER | mock (notify.channels.MockLine) | http (http_messaging.LineMessagingSender) |
| IF-03 แผนที่ | MAP_ADAPTER | mock (maps.MockMap ระยะจากพิกัด) | http (http_map.HttpMap) |
| IF-05 LLM | LLM_ADAPTER | mock (assistant.llm.MockLLM) | http (http_llm.HttpLLM) |
ตัวจริงไม่เรียกเครือข่ายตอนสร้าง ถ้าเลือก http แต่ยังไม่ตั้งค่า ทุกการเรียกได้ AdapterNotConfigured และ /ready ตอบ 503
ชื่อผู้ให้บริการไม่อยู่ใน requirement (D-14-02) ตัวจริงเขียนตามสัญญา interface ใน docs/srs/models.md ส่วน 9"""
import os


class AdapterNotConfigured(Exception):
    """เลือกตัวจริงแล้ว แต่ยังไม่ตั้ง URL หรือกุญแจ (ไม่ใช่ระบบภายนอกไม่ตอบ จึงไม่ใช่ timeout)"""


# ค่าตั้งที่ตัวจริงแต่ละตัวต้องมี (ชื่อตัวแปรแวดล้อม) ใช้ทั้งตอนสร้างและตอนรายงานสถานะ
REQUIRED = {
    "payment": ("PAYMENT_API_URL", "PAYMENT_API_KEY"),
    "sms": ("SMS_API_URL", "SMS_API_KEY"),
    "line": ("LINE_CHANNEL_TOKEN", "LINE_CHANNEL_SECRET"),
    "map": ("MAP_API_URL", "MAP_API_KEY"),
    "llm": ("LLM_API_URL", "LLM_API_KEY", "LLM_MODEL"),
}
INTERFACE = {"payment": "IF-01", "sms": "IF-02", "line": "IF-02", "map": "IF-03", "llm": "IF-05"}
ENV = {"payment": "PAYMENT_ADAPTER", "sms": "SMS_ADAPTER", "line": "LINE_ADAPTER", "map": "MAP_ADAPTER", "llm": "LLM_ADAPTER"}
MOCK_NAMES = ("mock", "fake")


def choice(kind: str) -> str:
    """ชื่อตัวที่เลือก อ่านทุกครั้งที่เรียก (ไม่จำไว้ตอน import) ค่าตั้งต้นคือตัวจำลอง"""
    return os.getenv(ENV[kind], "fake" if kind == "payment" else "mock").strip().lower()


def missing(kind: str) -> list[str]:
    return [k for k in REQUIRED[kind] if not os.getenv(k)]


def setting(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def status() -> list[dict]:
    """REQ-OP-009: แต่ละระบบภายนอกใช้ตัวไหน เป็นตัวจำลองไหม ตั้งค่าครบไหม (ไม่แสดงค่าของกุญแจ)"""
    out = []
    for kind in ENV:
        name = choice(kind)
        mock = name in MOCK_NAMES
        out.append({"kind": kind, "interface": INTERFACE[kind], "adapter": name, "mock": mock,
                    "configured": True if mock else not missing(kind),
                    "missing_settings": [] if mock else missing(kind)})
    return out
