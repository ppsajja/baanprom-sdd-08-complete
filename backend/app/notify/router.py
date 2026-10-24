"""CR-17 endpoint ของ UC-10 (specs/011-notifications/plan.md ข้อ 4) ทุกตัวอยู่ในบัญชี endpoint ของ operations.md
GET /me/notifications, PUT /me/notifications, POST /me/notifications/line-link, POST /me/notifications/line-unlink
POST /integrations/line/webhook (LINE เรียก ตรวจลายเซ็น) GET /ops/notifications/outbox (ตัวจำลองเท่านั้น X-Ops-Token)"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import config
from app.auth.deps import current_actor
from app.auth.service import Actor
from app.clock import get_now
from app.db.session import get_db
from app.notify import preferences
from app.notify.queue import get_notifier
from app.ops.guard import require_ops
from app.privacy import get_logger, log_event

router = APIRouter()
log = get_logger(__name__)


class ChannelIn(BaseModel):
    channel: str


@router.get("/me/notifications")
def my_settings(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    return preferences.view(db, actor.role, actor.subject_id)


@router.put("/me/notifications")
def set_channel(body: ChannelIn, actor: Actor = Depends(current_actor), db: Session = Depends(get_db),
                now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-072: เลือก SMS หรือ LINE (LINE ต้องเชื่อมก่อน)
    try:
        return preferences.set_channel(db, actor.role, actor.subject_id, body.channel, now)
    except preferences.PreferenceError as e:
        return JSONResponse({"reason": e.reason, "message": e.message}, status_code=409 if e.reason == "line_not_linked" else 422)


@router.post("/me/notifications/line-link")
def line_link(actor: Actor = Depends(current_actor), db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    code, until = preferences.start_line_link(db, actor.role, actor.subject_id, now)
    out = {"expires_at": until.isoformat(),
           "instruction": f"เพิ่มเพื่อนบัญชี LINE ของบ้านพร้อม แล้วพิมพ์รหัส {code} ภายใน {config.LINE_LINK_CODE_MINUTES} นาที",
           "link_code": code}
    return out


@router.post("/me/notifications/line-unlink")
def line_unlink(actor: Actor = Depends(current_actor), db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    return preferences.unlink_line(db, actor.role, actor.subject_id, now)


@router.post("/integrations/line/webhook")
async def line_webhook(request: Request, x_line_signature: str | None = Header(default=None),
                       db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    """BR-12 ข้อ 2: LINE ส่งข้อความที่ผู้ใช้พิมพ์มา ระบบตรวจลายเซ็นด้วย LINE_CHANNEL_SECRET ไม่ตรงตอบ 403 และไม่ทำอะไร"""
    from app.integrations.http_messaging import line_signature
    import hmac
    body = await request.body()
    if not x_line_signature or not hmac.compare_digest(x_line_signature, line_signature(body, config.line_channel_secret())):
        raise HTTPException(403, "ลายเซ็นไม่ถูกต้อง")
    linked = 0
    for ev in json.loads(body or b"{}").get("events", []):
        text = (ev.get("message") or {}).get("text", "")
        user = (ev.get("source") or {}).get("userId", "")
        if ev.get("type") == "message" and user and text.strip().isdigit():
            if preferences.complete_line_link(db, text, user, now) is not None:
                linked += 1
    log_event(log, "line_webhook", count=linked)
    return {"linked": linked}


@router.get("/ops/notifications/outbox", dependencies=[Depends(require_ops)])
def outbox(limit: int = 50):
    """ตัวจำลองเท่านั้น (เครื่องทดสอบ UAT และ OAT): ข้อความล่าสุดที่ "ส่ง" เบอร์และรหัส LINE เหลือ 4 ตัวท้าย"""
    from app.notify.channels import read_outbox_file
    rows = read_outbox_file()
    if rows is None:
        n = get_notifier()
        rows = [m for sender in (getattr(n, "sms", None), getattr(n, "line", None)) for m in list(getattr(sender, "outbox", []))]
    out = [{**m, "to": "***" + str(m["to"])[-4:]} for m in rows]
    return sorted(out, key=lambda m: m["at"])[-limit:]
