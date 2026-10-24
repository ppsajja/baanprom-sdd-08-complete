"""CR-17 ตัวจริงของ IF-02 (ปิดไว้): SMS ตามสัญญา IF-02 และ LINE Messaging API (push message)
ทั้งสองตัวรอไม่เกิน NOTIFY_TIMEOUT_SECONDS (REQ-QA-010) ไม่ตอบถือเป็น NotifierTimeout คิวส่งซ้ำตามเดิม
ข้อความและเบอร์ไม่ลง log (REQ-PRV-002) test ใช้ httpx.MockTransport ไม่ออกเครือข่าย"""
import base64
import hashlib
import hmac

import httpx

from app.integrations import AdapterNotConfigured, missing, setting
from app.notify.channels import LineSender, SmsSender
from app.notify.queue import NotifierTimeout


def _post(kind: str, base: str, path: str, token: str, body: dict, timeout: float, transport) -> httpx.Response:
    if missing(kind):
        raise AdapterNotConfigured(f"IF-02 {kind} ยังไม่ตั้ง " + ", ".join(missing(kind)))
    try:
        with httpx.Client(base_url=base, timeout=timeout, transport=transport,
                          headers={"Authorization": f"Bearer {token}"}) as c:
            r = c.post(path, json=body)
    except httpx.TimeoutException as e:
        raise NotifierTimeout() from e
    r.raise_for_status()
    return r


class HttpSmsSender(SmsSender):
    name = "http"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport

    def send(self, phone: str, text: str, timeout_seconds: int) -> None:
        _post("sms", setting("SMS_API_URL"), "/messages", setting("SMS_API_KEY"),
              {"to": phone, "text": text, "sender": setting("SMS_SENDER_NAME", "BaanProm")}, timeout_seconds, self.transport)

    def request_erasure(self, customer_id: int, timeout_seconds: int) -> str:
        # REQ-PRV-010 บรรทัดที่ 3: ขอให้ผู้ให้บริการลบข้อมูลของลูกค้ารายนี้ (อ้างด้วยรหัส ไม่ส่งเบอร์ซ้ำ)
        r = _post("sms", setting("SMS_API_URL"), "/data-subjects/erase", setting("SMS_API_KEY"),
                  {"customer_ref": f"BP-C-{customer_id}"}, timeout_seconds, self.transport)
        return r.json().get("result", "accepted")


class LineMessagingSender(LineSender):
    name = "http"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport

    def push(self, line_user_id: str, text: str, timeout_seconds: int) -> None:
        _post("line", setting("LINE_API_URL", "https://api.line.me"), "/v2/bot/message/push",
              setting("LINE_CHANNEL_TOKEN"), {"to": line_user_id, "messages": [{"type": "text", "text": text}]},
              timeout_seconds, self.transport)


def line_signature(body: bytes, secret: str) -> str:
    """ลายเซ็นของ webhook ตามวิธีของ LINE (HMAC-SHA256 ของ body แล้วเข้ารหัส base64) ใช้ตรวจ X-Line-Signature"""
    return base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
