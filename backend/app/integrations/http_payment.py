"""CR-18 ตัวจริงของ IF-01 Payment Gateway (ปิดไว้) เรียกตามสัญญา IF-01 ใน docs/srs/models.md ส่วน 9
reference ของการชำระเดิมส่งทุกครั้งที่ลองใหม่ (REQ-IF-005, REQ-QA-010) และใช้เป็น Idempotency-Key ของคำขอคืนเงิน (REQ-IF-010)
httpx ไม่ตอบภายใน timeout ถือเป็น GatewayTimeout แบบเดียวกับ FakeGateway ส่วน test ใช้ httpx.MockTransport ไม่ออกเครือข่าย"""
import httpx

from app.integrations import AdapterNotConfigured, missing, setting
from app.payments.gateway import Gateway, GatewayResult, GatewayTimeout


class HttpGateway(Gateway):
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport

    def _client(self, timeout: float) -> httpx.Client:
        if missing("payment"):
            raise AdapterNotConfigured("IF-01 ยังไม่ตั้ง " + ", ".join(missing("payment")))
        return httpx.Client(base_url=setting("PAYMENT_API_URL"), timeout=timeout, transport=self.transport,
                            headers={"Authorization": f"Bearer {setting('PAYMENT_API_KEY')}"})

    def _call(self, method: str, path: str, ref: str, timeout: float, json: dict | None = None,
              idem: str | None = None) -> GatewayResult:
        headers = {"Idempotency-Key": idem} if idem else {}
        try:
            with self._client(timeout) as c:
                r = c.request(method, path, json=json, headers=headers)
        except httpx.TimeoutException as e:
            raise GatewayTimeout(ref) from e
        r.raise_for_status()
        return GatewayResult(r.json().get("status", "unknown"), ref)

    def authorize(self, ref, amount, timeout_seconds):
        return self._call("POST", "/payments/authorize", ref, timeout_seconds, {"reference": ref, "amount": amount}, idem=ref)

    def capture(self, ref):
        return self._call("POST", f"/payments/{ref}/capture", ref, 30, idem=f"{ref}-capture")

    def void(self, ref):
        return self._call("POST", f"/payments/{ref}/void", ref, 30, idem=f"{ref}-void")

    def status_inquiry(self, ref):
        return self._call("GET", f"/payments/{ref}", ref, 30)

    def refund(self, ref, amount, timeout_seconds=None):
        return self._call("POST", f"/payments/{ref}/refunds", ref, timeout_seconds or 30, {"amount": amount},
                          idem=f"{ref}-refund")
