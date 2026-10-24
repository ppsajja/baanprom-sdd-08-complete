"""CR-13 (Q-68 ทดสอบโหลดบน PostgreSQL หลาย process): เมื่อรัน uvicorn แบบ --workers มากกว่า 1 พบว่าการเชื่อมต่อที่ใช้ซ้ำ
(keep-alive ซึ่งเบราว์เซอร์ใช้เสมอ) ช้าเพิ่มราว 40 มิลลิวินาทีทุกคำขอ แม้ GET /health (GAP-41) เพราะ socket ไม่ได้ตั้ง TCP_NODELAY
ข้อความตอบส่งเป็นสองชิ้น ชิ้นที่สองรอ ACK ที่ฝั่งรับหน่วงไว้ ตัวนี้ตั้ง TCP_NODELAY ทุกการเชื่อมต่อ
ใช้ผ่าน app/ops/serve.py (คู่มือติดตั้ง ขั้นที่ 3)"""
import socket

from uvicorn.protocols.http.h11_impl import H11Protocol


class NoDelayH11Protocol(H11Protocol):
    def connection_made(self, transport) -> None:  # type: ignore[override]
        sock = transport.get_extra_info("socket")
        if sock is not None:
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass
        super().connection_made(transport)
