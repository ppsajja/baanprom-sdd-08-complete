"""CR-13 (REQ-OP-008): ตัวเริ่มหลังบ้านของระบบจริง หลาย process ได้ (Q-67 ปิด คิวและตัวนับอยู่ในฐานข้อมูลแล้ว)
เหมือน uvicorn app.main:app แต่ตั้ง TCP_NODELAY ทุกการเชื่อมต่อ (app/ops/nodelay.py, GAP-41)
ใช้: python -m app.ops.serve --host 0.0.0.0 --port 8000 --workers 4"""
import argparse

import uvicorn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    uvicorn.run("app.main:app", host=a.host, port=a.port, workers=a.workers,
                http="app.ops.nodelay:NoDelayH11Protocol", proxy_headers=True)


if __name__ == "__main__":
    main()
