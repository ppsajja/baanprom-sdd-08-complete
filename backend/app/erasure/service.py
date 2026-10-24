"""CR-07 REQ-PRV-010 การลบข้อมูลลูกค้าเมื่อร้องขอ (AC-07-17, AC-07-18)
- ลบเบอร์โทร ที่อยู่ และพิกัด จากตาราง customers และ service_addresses ภายใน 30 วัน (ค่าที่บริษัทเลือก D-00-05)
- ประวัติงานเก็บต่อ 24 เดือน (REQ-DAT-002) ตาราง jobs และ job_status_history อ้างลูกค้าด้วยรหัสอยู่แล้ว ชื่อแทนด้วย "ลูกค้า #รหัส"
- ส่งคำขอลบไป IF-02 และบันทึกวันที่ส่งกับผลตอบ
- จดคำขอลงทะเบียนนอกฐานข้อมูล (erasure ledger) เพื่อลบซ้ำหลังกู้คืนจากสำเนา ห้ามข้อมูลที่ลบแล้วกลับมา
คำขอรับผ่าน call center ซึ่งยืนยันตัวลูกค้าตามขั้นตอนของ SH-05 ก่อนส่งเข้าระบบ (EV-045) จึงเป็น endpoint ของ ops"""
import json
import os
from datetime import datetime, timedelta

from sqlalchemy import select

from app import config
from app.db.models import Customer, ServiceAddress, Job, ErasureRequest
from app.notify.queue import Notifier, NotifierTimeout
from app.privacy import get_logger, log_event

log = get_logger(__name__)

# งานที่ยังไม่ปิด ช่างยังต้องติดต่อลูกค้า (REQ-SEC-004) จึงลบเมื่องานปิด แต่ไม่เกินกำหนด 30 วัน
ACTIVE_STATUSES = ("pending_payment", "confirmed", "rematching", "en_route", "in_progress")
ERASED_PHONE = ""


def request_erasure(db, customer_id: int, now: datetime) -> ErasureRequest:
    req = ErasureRequest(customer_id=customer_id, requested_at=now,
                         due_at=now + timedelta(days=config.ERASURE_DEADLINE_DAYS))
    db.add(req)
    db.commit()
    log_event(log, "erasure_requested", customer_id=customer_id)
    return req


def has_active_job(db, customer_id: int) -> bool:
    return db.scalars(select(Job).where(Job.customer_id == customer_id,
                                        Job.status.in_(ACTIVE_STATUSES))).first() is not None


def anonymize(db, customer: Customer, now: datetime) -> None:
    customer.name = f"ลูกค้า #{customer.id}"
    customer.phone = ERASED_PHONE
    customer.erased_at = now
    for a in db.scalars(select(ServiceAddress).where(ServiceAddress.customer_id == customer.id)):
        a.text, a.lat, a.lng = "", 0.0, 0.0
    # CR-09 (Q-57 SH-05): ข้อความที่ลูกค้าพิมพ์กับผู้ช่วยเป็นข้อมูลของลูกค้า ลบพร้อมกัน คงรหัสและผลไว้
    from app.assistant.records import erase_customer_text
    erase_customer_text(db, customer.id)
    # CR-11 (REQ-PRV-010 กับ REQ-SEC-014): ลบบัญชีที่มีเบอร์ และยกเลิก session ทุกตัว ลูกค้าคนนี้เข้าสู่ระบบด้วยบัญชีเดิมไม่ได้อีก
    from app.auth.service import revoke_customer
    revoke_customer(db, customer.id, now)


def append_ledger(customer_id: int, now: datetime, path: str | None = None) -> None:
    path = path or config.erasure_ledger_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"customer_id": customer_id, "erased_at": now.isoformat()}) + "\n")


def process_due(db, now: datetime, notifier: Notifier, ledger_path: str | None = None) -> list[int]:
    """ทำคำขอที่ยังไม่เสร็จ คืนรายการ customer_id ที่ลบในรอบนี้ เรียกทันทีหลังรับคำขอ และทุก 1 นาทีจาก scheduler"""
    done = []
    for req in db.scalars(select(ErasureRequest).where(ErasureRequest.completed_at.is_(None))).all():
        customer = db.get(Customer, req.customer_id)
        if customer is None:
            req.completed_at = now
            continue
        if customer.erased_at is None:
            if has_active_job(db, customer.id):
                if now >= req.due_at:
                    # เกินกำหนดของบริษัทแล้ว ยังมีงานค้าง ให้คนเวรตาม (คู่มือเหตุการณ์ที่ 5) ยังอยู่ในกรอบ 90 วันของกฎหมาย
                    log_event(log, "erasure_overdue", customer_id=customer.id)
                continue
            anonymize(db, customer, now)
            append_ledger(customer.id, now, ledger_path)
            done.append(customer.id)
        if req.if02_result != "accepted":
            try:
                req.if02_result = notifier.request_erasure(customer.id, timeout_seconds=config.NOTIFY_TIMEOUT_SECONDS)
            except NotifierTimeout:
                req.if02_result = "timeout"  # ลองใหม่รอบถัดไป
            req.if02_sent_at = now
        if req.if02_result == "accepted":
            req.completed_at = now
    db.commit()
    for cid in done:
        log_event(log, "customer_erased", customer_id=cid)
    return done


def reapply_ledger(db, now: datetime, ledger_path: str | None = None) -> list[int]:
    """หลังกู้คืนจากสำเนา: ลบซ้ำทุกลูกค้าที่อยู่ในทะเบียน (REQ-PRV-010 บรรทัดที่ 4)"""
    path = ledger_path or config.erasure_ledger_path()
    again = []
    if not os.path.exists(path):
        return again
    with open(path, encoding="utf-8") as f:
        ids = {json.loads(line)["customer_id"] for line in f if line.strip()}
    for cid in sorted(ids):
        customer = db.get(Customer, cid)
        if customer is not None and customer.erased_at is None:
            anonymize(db, customer, now)
            again.append(cid)
    db.commit()
    return again
