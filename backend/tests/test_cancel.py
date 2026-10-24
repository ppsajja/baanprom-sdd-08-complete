"""AC-08-01 ถึง AC-08-06 จาก cancel-refund.feature (specs/004-cancel-refund, CR-06)
UC-08 ลูกค้ายกเลิกการจองและรับเงินคืน ใช้ตาราง BR-01 ตัวเดียวกับ AC-07-10 (R3 ยังรอ Q-14 เหมือนเดิม)
CR-10: Q-14 ปิดแล้ว แถว R3 ออกจาก AC-08-06 ไปอยู่ที่ AC-08-12 ใน test_cancel_cr10.py"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import config
from app.db.models import Job, Refund, TimeSlot, set_status, SLOT_FREE, SLOT_BOOKED
from app.notify.queue import queue
from tests.conftest import NOW, TOMORROW_14, book, H


def confirmed_job(client, db, seed):
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert res.status_code == 201
    job = db.get(Job, res.json()["job_id"]); db.refresh(job)
    return job


def quote(client, job_id, customer_id, now):
    # CR-11: customer_id คือผู้ส่ง ส่งเป็น token ของลูกค้าคนนั้น (query customer_id เดิมระบบไม่ใช้แล้ว)
    return client.get(f"/jobs/{job_id}/refund-quote?customer_id={customer_id}&now={now.isoformat()}",
                      headers=H("customer", customer_id))


def cancel(client, job_id, customer_id, now):
    return client.post(f"/jobs/{job_id}/customer-cancel?now={now.isoformat()}", json={"customer_id": customer_id},
                       headers=H("customer", customer_id))


# รองรับ AC-08-01 (REQ-FN-054, REQ-BR-001): ยอดคืนที่แสดงก่อนยืนยันเท่ากับยอดที่คืนจริง
@pytest.mark.parametrize("row,hours_before,expect_refund", [("R1", 48, 350), ("R2", 5, 180)])
def test_AC_08_01_quote_equals_actual_refund(client, db, seed, row, hours_before, expect_refund):
    # Given งานมัดจำ 350 บาท สถานะ ยืนยันแล้ว และเวลานัดอีก <ชั่วโมงก่อนนัด> ชั่วโมง
    job = confirmed_job(client, db, seed)
    now = job.scheduled_start - timedelta(hours=hours_before)
    # When ลูกค้าเปิดหน้ายกเลิก Then เห็นยอดคืน <ยอดคืน> บาท ตามแถว <แถว> และกดยกเลิกได้
    q = quote(client, job.id, seed["somchai"].id, now)
    assert q.status_code == 200 and q.json()["allowed"] is True
    assert q.json()["rule"] == row and q.json()["refund_amount"] == expect_refund
    # When ลูกค้ากดยืนยันยกเลิก Then ยอดคืนจริงเท่ากับที่แสดง
    r = cancel(client, job.id, seed["somchai"].id, now)
    assert r.status_code == 200 and r.json()["refund_amount"] == expect_refund == q.json()["refund_amount"]


# รองรับ AC-08-02 (REQ-FN-054, REQ-DAT-002, REQ-DAT-003)
def test_AC_08_02_cancel_sets_status_history_and_frees_slot(client, db, seed):
    job = confirmed_job(client, db, seed)
    slot = db.get(TimeSlot, job.slot_id); db.refresh(slot)
    assert slot.state == SLOT_BOOKED
    now = job.scheduled_start - timedelta(hours=48)
    # When ลูกค้ายกเลิก
    r = cancel(client, job.id, seed["somchai"].id, now)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    # Then งานมีสถานะ ยกเลิก ประวัติมีแถว ยืนยันแล้ว ไปยัง ยกเลิก และช่วงเวลากลับเป็น ว่าง
    db.refresh(job); db.refresh(slot)
    assert job.status == "cancelled" and slot.state == SLOT_FREE and slot.held_by_customer_id is None
    h = client.get(f"/jobs/{job.id}/history", headers=H("customer", seed["somchai"].id)).json()["history"]
    assert h[-1]["from_status"] == "confirmed" and h[-1]["to_status"] == "cancelled" and h[-1]["at"] == now.isoformat()
    # And ลูกค้าอื่นค้นหาแล้วเห็นช่วงเวลานี้ว่างอีกครั้ง
    found = client.get(f"/technicians?category=ประปา&address_id={seed['addr_other'].id}&customer_id={seed['other'].id}&now={NOW.isoformat()}",
                       headers=H("customer", seed["other"].id)).json()
    assert any(s["slot_id"] == slot.id for t in found for s in t["slots"])


# รองรับ AC-08-03 (REQ-IF-010, REQ-CON-003): คำขอคืนเงินผ่าน Payment Gateway ด้วย reference เดิม
def test_AC_08_03_refund_sent_via_gateway_with_same_ref(client, db, seed, gateway):
    job = confirmed_job(client, db, seed)
    pay_ref = [c for c in gateway.calls if c.startswith("authorize:")][0].split(":", 1)[1]
    r = cancel(client, job.id, seed["somchai"].id, job.scheduled_start - timedelta(hours=48))
    assert r.status_code == 200 and r.json()["refund_result"] == "approved"
    # Then gateway ได้รับคำขอคืนเงิน 1 ครั้ง ด้วย ref ของการชำระเดิม และยอดตาม BR-01
    refund_calls = [c for c in gateway.calls if c.startswith("refund:")]
    assert refund_calls == [f"refund:{pay_ref}:350"]
    refund = db.scalars(select(Refund).where(Refund.job_id == job.id)).one()
    assert refund.gateway_ref == pay_ref and refund.result == "approved" and refund.rule == "R1"


# รองรับ AC-08-04 (REQ-IF-010): ยกเลิกซ้ำไม่ได้ และไม่ส่งคำขอคืนเงินซ้ำ
def test_AC_08_04_second_cancel_rejected_no_double_refund(client, db, seed, gateway):
    job = confirmed_job(client, db, seed)
    now = job.scheduled_start - timedelta(hours=48)
    assert cancel(client, job.id, seed["somchai"].id, now).status_code == 200
    r = cancel(client, job.id, seed["somchai"].id, now)
    assert r.status_code == 409 and "ยกเลิกไปแล้ว" in r.json()["message"]
    assert len([c for c in gateway.calls if c.startswith("refund:")]) == 1
    q = quote(client, job.id, seed["somchai"].id, now).json()
    assert q["allowed"] is False and q["refund_amount"] == 0


# รองรับ AC-08-05 (REQ-FN-055): แจ้งลูกค้าและช่างภายใน 60 วินาที
def test_AC_08_05_notify_customer_and_technician_within_60s(client, db, seed):
    job = confirmed_job(client, db, seed)
    queue.clear()
    now = job.scheduled_start - timedelta(hours=5)
    cancel(client, job.id, seed["somchai"].id, now)
    msgs = queue.for_job(job.id)
    roles = sorted(m.to_role for m in msgs)
    assert roles == ["customer", "technician"]
    for m in msgs:
        assert m.due_at <= now + timedelta(seconds=config.NOTIFY_WITHIN_SECONDS)
    assert any("180" in m.text for m in msgs if m.to_role == "customer")  # R2 ยอดคืนในข้อความถึงลูกค้า


# รองรับ AC-08-06 (REQ-BR-001 R3 พฤติกรรมชั่วคราว Q-14, และ R6): ยกเลิกไม่ได้ ระบบตอบข้อความให้หน้าจอแสดง
@pytest.mark.parametrize("status,rule,text", [
    ("in_progress", "R6", "ยกเลิกไม่ได้"),
])
def test_AC_08_06_not_cancellable_returns_message(client, db, seed, gateway, status, rule, text):
    job = confirmed_job(client, db, seed)
    set_status(db, job, status, NOW); db.commit()
    now = job.scheduled_start - timedelta(hours=1)
    q = quote(client, job.id, seed["somchai"].id, now).json()
    assert q["allowed"] is False and q["rule"] == rule and text in q["message"]
    r = cancel(client, job.id, seed["somchai"].id, now)
    assert r.status_code == 409 and r.json()["rule"] == rule and text in r.json()["message"]
    db.refresh(job); assert job.status == status
    assert not [c for c in gateway.calls if c.startswith("refund:")]


# ลูกค้าคนอื่นยกเลิกงานที่ไม่ใช่ของตัวเองไม่ได้ (REQ-FN-054 ส่วน "งานของตัวเอง" ตรวจใน AC-08-01 ขั้น Given)
def test_AC_08_01_other_customer_cannot_see_or_cancel(client, db, seed, gateway):
    job = confirmed_job(client, db, seed)
    now = job.scheduled_start - timedelta(hours=48)
    # CR-07 (Q-47, GAP-23): รหัสตอบเปลี่ยนจาก 404 เป็น 403 ตาม REQ-SEC-010 ข้อความของ AC-08-01 ไม่เปลี่ยน
    assert quote(client, job.id, seed["other"].id, now).status_code == 403
    assert cancel(client, job.id, seed["other"].id, now).status_code == 403
    db.refresh(job); assert job.status == "confirmed"
