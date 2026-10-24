"""IF-01 Payment Gateway รายเดิม (REQ-CON-003) อยู่หลัง interface นี้
ระบบจริงเขียน class ที่เรียก HTTP ของ gateway; ตอน test ใช้ FakeGateway"""
from dataclasses import dataclass, field


class GatewayTimeout(Exception):
    """gateway ไม่ตอบภายใน GATEWAY_TIMEOUT_SECONDS (UC-07 E1, REQ-IF-005)"""


@dataclass
class GatewayResult:
    status: str   # approved / declined / unknown
    ref: str


class Gateway:
    def authorize(self, ref: str, amount: int, timeout_seconds: int) -> GatewayResult:  # กันวงเงิน รอไม่เกิน timeout
        raise NotImplementedError

    def capture(self, ref: str) -> GatewayResult:  # ตัดเงินจริง
        raise NotImplementedError

    def void(self, ref: str) -> GatewayResult:  # ยกเลิกการกันวงเงิน (BR-01 R5)
        raise NotImplementedError

    def status_inquiry(self, ref: str) -> GatewayResult:  # REQ-IF-005
        raise NotImplementedError

    def refund(self, ref: str, amount: int, timeout_seconds: int | None = None) -> GatewayResult:
        # REQ-IF-010 คืนเงินด้วย reference ของการชำระเดิม (CR-06) | CR-07 REQ-QA-010 รอไม่เกิน timeout_seconds
        raise NotImplementedError


@dataclass
class FakeGateway(Gateway):
    """สั่งพฤติกรรมได้: mode = approved | declined | timeout
    inquiry_answer = คำตอบของ status-inquiry เมื่อ timeout (approved / declined / unknown)
                     CR-07: "timeout" = gateway ไม่ตอบ status-inquiry ด้วย (ไม่ตอบเลย เหตุการณ์ B)
    refund_mode = คำตอบของคำขอคืนเงิน (approved / declined) CR-06 | CR-07: "timeout" = ไม่ตอบคำขอคืนเงิน"""
    mode: str = "approved"
    inquiry_answer: str = "unknown"
    refund_mode: str = "approved"
    calls: list[str] = field(default_factory=list)
    last_timeout_seconds: int | None = None
    last_refund_timeout_seconds: int | None = None

    def authorize(self, ref, amount, timeout_seconds):
        self.calls.append(f"authorize:{ref}")
        self.last_timeout_seconds = timeout_seconds
        if self.mode == "timeout":
            raise GatewayTimeout(ref)
        return GatewayResult(self.mode, ref)

    def capture(self, ref):
        self.calls.append(f"capture:{ref}")
        return GatewayResult("approved", ref)

    def void(self, ref):
        self.calls.append(f"void:{ref}")
        return GatewayResult("voided", ref)

    def status_inquiry(self, ref):
        self.calls.append(f"inquiry:{ref}")
        if self.inquiry_answer == "timeout":
            raise GatewayTimeout(ref)
        return GatewayResult(self.inquiry_answer, ref)

    def refund(self, ref, amount, timeout_seconds=None):
        self.calls.append(f"refund:{ref}:{amount}")
        self.last_refund_timeout_seconds = timeout_seconds
        if self.refund_mode == "timeout":
            raise GatewayTimeout(ref)
        return GatewayResult(self.refund_mode, ref)


# gateway ที่ระบบใช้จริง ตั้งค่าใน main.py; test สลับเป็น FakeGateway ผ่าน dependency
# CR-10 (เตรียมเครื่องทดสอบสำหรับการตรวจรับ R1): ตอนยังไม่ต่อ IF-01 จริง เครื่องทดสอบตั้งพฤติกรรมของ FakeGateway
# ผ่านตัวแปรแวดล้อมได้ เพื่อซ้อม OAT-2 และ OAT-5 และ scenario ของ AC-08-11 บนระบบที่รันจริง ระบบจริงต้องไม่ใช้ FakeGateway เลย
def _fake_from_env() -> FakeGateway:
    import os
    return FakeGateway(mode=os.getenv("FAKE_GATEWAY_MODE", "approved"),
                       inquiry_answer=os.getenv("FAKE_GATEWAY_INQUIRY", "unknown"),
                       refund_mode=os.getenv("FAKE_GATEWAY_REFUND_MODE", "approved"))


def build_from_config() -> Gateway:
    """CR-18 REQ-IF-012: PAYMENT_ADAPTER = fake (ค่าตั้งต้น FakeGateway) หรือ http (ตัวจริงตามสัญญา IF-01 ปิดไว้จนกว่าจะตั้งค่า)"""
    from app.integrations import choice
    if choice("payment") == "http":
        from app.integrations.http_payment import HttpGateway
        return HttpGateway()
    return _fake_from_env()


_current: Gateway = build_from_config()


def get_gateway() -> Gateway:
    return _current


def set_gateway(g: Gateway) -> None:
    global _current
    _current = g
