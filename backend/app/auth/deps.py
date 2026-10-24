"""CR-11 REQ-SEC-014: ตัวตนของผู้เรียก มาจาก header Authorization: Bearer <token> เท่านั้น
customer_id หรือ technician_id ที่ส่งมาใน body หรือ query ไม่ถูกใช้ตัดสินสิทธิ์อีกต่อไป (ปิด TH-01 และ GAP-24)
call center อ่านงานได้ด้วยกุญแจของ Ops (X-Ops-Token) จนกว่าจะมีกุญแจแยกบทบาท (GAP-32)"""
import hmac
from datetime import datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import config
from app.auth.service import Actor, actor_from_token
from app.clock import get_now
from app.db.session import get_db

MSG_LOGIN_REQUIRED = "กรุณาเข้าสู่ระบบ"
MSG_WRONG_ROLE = "บัญชีนี้ใช้กับเมนูนี้ไม่ได้"


def bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def optional_actor(authorization: str | None = Header(default=None), db: Session = Depends(get_db),
                   now: datetime = Depends(get_now)) -> Actor | None:
    actor = actor_from_token(db, bearer(authorization), now)
    # CR-13 (GAP-42): บน PostgreSQL คืน connection ให้ pool ทันทีหลังตรวจ token ไม่ถือไว้ระหว่างรอเธรดของ endpoint
    # (ทดสอบโหลด 500 คำขอพร้อมกันพบ pool หมดแล้วค้าง 30 วินาที) SQLite ใน test ใช้ connection เดียวร่วมกัน จึงไม่ทำ
    if db.get_bind().dialect.name != "sqlite":
        db.rollback()
    return actor


def current_actor(actor: Actor | None = Depends(optional_actor)) -> Actor:
    if actor is None:
        raise HTTPException(401, MSG_LOGIN_REQUIRED, headers={"WWW-Authenticate": "Bearer"})
    return actor


def current_customer(actor: Actor = Depends(current_actor)) -> Actor:
    if actor.role != "customer":
        raise HTTPException(403, MSG_WRONG_ROLE)
    return actor


def current_technician(actor: Actor = Depends(current_actor)) -> Actor:
    if actor.role != "technician":
        raise HTTPException(403, MSG_WRONG_ROLE)
    return actor


def is_ops(x_ops_token: str | None = Header(default=None)) -> bool:
    """call center และ Ops: ต้องตั้ง OPS_TOKEN และส่งค่าที่ตรงกันทุกโหมด (ต่างจาก require_ops ที่เปิดในโหมด test)"""
    expected = config.ops_token()
    return bool(expected and x_ops_token and hmac.compare_digest(x_ops_token, expected))


class Reader:
    """ผู้อ่านงาน: ผู้ที่เข้าสู่ระบบแล้ว (actor) หรือ call center ที่ใช้กุญแจของ Ops (ops = True)"""
    def __init__(self, actor: Actor | None, ops: bool):
        self.actor, self.ops = actor, ops


def current_reader(actor: Actor | None = Depends(optional_actor), ops: bool = Depends(is_ops)) -> Reader:
    if actor is None and not ops:
        raise HTTPException(401, MSG_LOGIN_REQUIRED, headers={"WWW-Authenticate": "Bearer"})
    return Reader(actor, ops)
