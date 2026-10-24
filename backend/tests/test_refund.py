"""AC-07-10 Scenario Outline จาก booking.feature (T-06) ทีละแถวของ BR-01
R3 ข้าม (รอ Q-14) ตาม D-07-04 แต่ยังตรวจพฤติกรรมชั่วคราวว่าปฏิเสธจริง"""
from datetime import timedelta

import pytest

from app.db.models import Job, set_status
from tests.conftest import NOW, book, H


def make_confirmed_job(client, db, seed):
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert res.status_code == 201
    job = db.get(Job, res.json()["job_id"]); db.refresh(job)
    return job


def cancel(client, job_id, by, now):
    # CR-07 (GAP-23): POST /jobs/{id}/cancel ถูกปิด (REQ-SEC-010, OWASP API9:2023) แก้เฉพาะ helper ส่วน When นี้
    # ลูกค้าเป็นผู้ยกเลิก = POST /jobs/{id}/customer-cancel ในนามเจ้าของงาน | ระบบเป็นผู้ยกเลิก (R4, R5) = เรียก cancel_job
    # ภายในระบบ เพราะ R1 ไม่มี endpoint ให้คนนอกสั่งยกเลิกในนามระบบ Given และ Then ของ AC-07-10 ไม่เปลี่ยน
    from app.db import session as db_session
    from app.payments.gateway import get_gateway
    from app.refund import service
    s = db_session.SessionLocal()
    job = s.get(Job, job_id)
    if by == "customer":
        s.close()
        return client.post(f"/jobs/{job_id}/customer-cancel?now={now.isoformat()}", json={"customer_id": job.customer_id},
                           headers=H("customer", job.customer_id))
    try:
        d, refund = service.cancel_job(s, job, by, now, get_gateway())
        return _Result(200, {"job_id": job.id, "status": job.status, "rule": d.rule,
                             "refund_amount": refund.amount if refund else 0})
    except service.CancelRejected as e:
        return _Result(409, {"rule": e.decision.rule, "outcome": e.decision.outcome, "message": e.message})
    finally:
        s.close()


class _Result:
    def __init__(self, status_code, body):
        self.status_code, self._body, self.text = status_code, body, str(body)

    def json(self):
        return self._body


# รองรับ AC-07-10 (REQ-BR-001, BR-01)
@pytest.mark.parametrize("row,status,hours_before,by,expect_status,expect_refund", [
    ("R1", "confirmed", 48, "customer", "cancelled", 350),
    ("R2", "confirmed", 5, "customer", "cancelled", 180),
    ("R4", "rematching", 20, "system", "cancelled", 350),
    ("R5", "pending_payment", 30, "system", "auto_cancelled", 0),
])
def test_AC_07_10_refund(client, db, seed, row, status, hours_before, by, expect_status, expect_refund):
    # Given งานมัดจำ 350 บาท สถานะ <สถานะ> และเวลานัดอีก <ชั่วโมงก่อนนัด> ชั่วโมง
    job = make_confirmed_job(client, db, seed)
    assert job.deposit_amount == 350
    set_status(db, job, status, NOW); db.commit()
    now = job.scheduled_start - timedelta(hours=hours_before)
    # When <ผู้ยกเลิก> ยกเลิกงาน
    r = cancel(client, job.id, by, now)
    # Then ผลคือ <ผล> และยอดคืน <ยอดคืน> บาท ตามแถว <แถว>
    assert r.status_code == 200, r.text
    assert r.json()["rule"] == row
    assert r.json()["status"] == expect_status
    assert r.json()["refund_amount"] == expect_refund


# รองรับ AC-07-10 แถว R6: ยกเลิกไม่ได้
def test_AC_07_10_refund_R6_not_allowed(client, db, seed):
    job = make_confirmed_job(client, db, seed)
    set_status(db, job, "in_progress", NOW); db.commit()
    r = cancel(client, job.id, "customer", job.scheduled_start)
    assert r.status_code == 409 and r.json()["rule"] == "R6"
    db.refresh(job); assert job.status == "in_progress"


# รองรับ AC-07-10 แถว R3: CR-10 (Q-14 ปิดใน EV-048) แถวนี้ไม่ข้ามแล้ว ยอดคืน = มัดจำ 350 หักค่าเดินทาง 100 = 250
# test เดิมของพฤติกรรมชั่วคราว (test_AC_07_10_refund_R3_temporary_behaviour) ถูกลบตามตาราง "test เดิมที่เปลี่ยน" ของ CR-10
def test_AC_07_10_refund_R3(client, db, seed):
    # Given งานมัดจำ 350 บาท สถานะ "ช่างกำลังเดินทาง" และเวลานัดอีก 1 ชั่วโมง
    job = make_confirmed_job(client, db, seed)
    set_status(db, job, "en_route", NOW); db.commit()
    # When ลูกค้ายกเลิกงาน
    r = cancel(client, job.id, "customer", job.scheduled_start - timedelta(hours=1))
    # Then ผลคือ "ยกเลิก" และยอดคืน 250 บาท ตามแถว R3
    assert r.status_code == 200, r.text
    assert r.json()["rule"] == "R3" and r.json()["status"] == "cancelled" and r.json()["refund_amount"] == 250
