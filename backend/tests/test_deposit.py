"""AC-07-11 จาก booking.feature v1.3 (CR-03, T-12) ยอดมัดจำที่แสดงก่อนยืนยันเท่ากับยอดที่ตัดจริง"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import config
from app.db.models import Payment, Technician, TimeSlot
from tests.conftest import NOW, TOMORROW_14, book, H


# รองรับ AC-07-11 (REQ-BR-002)
@pytest.mark.parametrize("category,expected", [("ประปา", 350), ("ไฟฟ้า", 400), ("แอร์", 500)],
                         ids=["plumbing-350", "electric-400", "aircon-500"])
def test_AC_07_11_deposit_shown_equals_charged(client, db, seed, gateway, category, expected):
    # Given ลูกค้าเลือกประเภทงาน และล็อกช่วงเวลาของช่างที่มีทักษะนั้นไว้
    tech = Technician(name="สมหมาย", skills=category, base_lat=13.7050, base_lng=100.5300)
    db.add(tech)
    db.flush()
    slot = TimeSlot(technician_id=tech.id, start=TOMORROW_14 + timedelta(days=2),
                    end=TOMORROW_14 + timedelta(days=2, hours=2))
    db.add(slot)
    db.commit()
    r = client.post(f"/slots/{slot.id}/hold?now={NOW.isoformat()}", json={"customer_id": seed["somchai"].id},
                    headers=H("customer", seed["somchai"].id))
    assert r.status_code == 200
    # When ระบบแสดงหน้ายืนยัน (หน้าจอขอยอดจาก GET /deposit-quote)
    quote = client.get(f"/deposit-quote?category={category}")
    # Then หน้ายืนยันแสดงยอดมัดจำตามตารางราคาประเมิน
    assert quote.status_code == 200
    assert quote.json()["deposit_amount"] == expected
    # When ลูกค้ากดยืนยัน และ Payment Gateway ตอบ approved
    gateway.mode = "approved"
    res = book(client, customer_id=seed["somchai"].id, slot_id=slot.id, address_id=seed["addr"].id, category=category)
    assert res.status_code == 201, res.text
    # Then รายการชำระมัดจำมียอดเท่ากับที่แสดง
    payment = db.scalar(select(Payment).where(Payment.job_id == res.json()["job_id"]))
    assert payment.amount == quote.json()["deposit_amount"] == res.json()["deposit_amount"]


# รองรับ REQ-BR-002 (AS-10): ประเภทงานที่ไม่อยู่ในตารางราคาประเมิน ไม่มียอดให้แสดงและจองไม่ได้ ไม่มีการเดายอด
def test_AC_07_11_unknown_category_has_no_guessed_deposit(client, db, seed, gateway):
    assert "ทาสี" not in config.DEPOSIT_BY_CATEGORY
    assert client.get("/deposit-quote?category=ทาสี").status_code == 422
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id, category="ทาสี")
    assert res.status_code == 422
    assert not any(c.startswith("authorize") for c in gateway.calls)
