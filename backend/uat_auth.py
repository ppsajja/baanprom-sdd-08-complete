"""CR-11 (R2): สคริปต์ตรวจรับ (uat_replay.py, load_test.py) ต้องเข้าสู่ระบบก่อนเรียก API ไม่ใช่ส่วนของระบบ
ระบบจริงไม่ส่งรหัส OTP กลับในคำตอบ (REQ-SEC-012) สคริปต์จึงออก session ให้บัญชีทดสอบตรงในฐานข้อมูลของเครื่องทดสอบ
(บัญชีมาจาก uat_seed.py เบอร์ขึ้นต้นด้วย 000-000 ทุกเบอร์) แล้วแนบ Authorization ให้ทุกคำขอตามผู้ส่งที่สคริปต์ระบุ
การเข้าสู่ระบบด้วย OTP จริงตรวจด้วย test_identity.py และ scenario U-15 ถึง U-17 ของ R2 (เดินบนหน้าจอ)"""
import json
import re
from datetime import datetime, timedelta

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth.service import issue_session, normalize_phone
from app.db.models import Account, Customer


class TestTokens:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.cache: dict[tuple[str, int], str] = {}

    def token(self, role: str, subject_id: int) -> str:
        key = (role, subject_id)
        if key not in self.cache:
            with Session(self.engine, expire_on_commit=False) as s:
                acc = s.scalars(select(Account).where(Account.role == role, Account.subject_id == subject_id)).first()
                if acc is None:
                    phone = s.get(Customer, subject_id).phone if role == "customer" else f"000-000-{1000 + subject_id:04d}"
                    acc = Account(role=role, subject_id=subject_id, phone_norm=normalize_phone(phone), created_at=datetime.now())
                    s.add(acc)
                    s.commit()
                tok, _ = issue_session(s, acc, datetime.now(), lifetime=timedelta(hours=12))
                self.cache[key] = tok
        return self.cache[key]

    def headers(self, role: str, subject_id: int) -> dict:
        return {"Authorization": f"Bearer {self.token(role, subject_id)}"}


def auth_hook(tokens: TestTokens, ops_token: str | None = None):
    """event hook ของ httpx: ผู้ส่งอ่านจาก customer_id หรือ technician_id ที่สคริปต์รุ่น R1 ใส่ไว้ในคำขอ
    (ระบบ R2 ไม่ใช้ค่าเหล่านี้ตัดสินสิทธิ์แล้ว) GET /jobs/{id} และ /history อ่านในนาม call center ด้วยกุญแจของ Ops"""
    def hook(request: httpx.Request) -> None:
        if "authorization" in request.headers:
            return
        body = {}
        if request.content and request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = json.loads(request.content)
            except ValueError:
                body = {}
        params = dict(request.url.params)
        path = request.url.path
        m = re.fullmatch(r"/technicians/(\d+)/jobs", path)
        if m:
            request.headers["Authorization"] = tokens.headers("technician", int(m.group(1)))["Authorization"]
        elif "technician_id" in body:
            request.headers["Authorization"] = tokens.headers("technician", int(body["technician_id"]))["Authorization"]
        elif "customer_id" in body or "customer_id" in params:
            cid = int(body.get("customer_id") or params["customer_id"])
            if not path.startswith("/ops/"):
                request.headers["Authorization"] = tokens.headers("customer", cid)["Authorization"]
        elif re.fullmatch(r"/jobs/\d+(/history)?", path) and ops_token:
            request.headers["X-Ops-Token"] = ops_token
    return hook
