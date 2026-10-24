"""AC-10-01 ถึง AC-10-07 จาก notifications.feature (specs/011-notifications, CR-17) UC-10 รับการแจ้งเตือน
ตัวส่งที่เลือกช่องทาง (ChannelRouter) กับตัวจำลอง MockSms MockLine ผ่าน interface IF-02 ช่องทางตั้งต้น SMS LINE ต้องเชื่อมก่อน
LINE ไม่สำเร็จส่ง SMS แทนในรอบเดียวกัน OTP ส่ง SMS เสมอ (BR-12)"""
import json
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import NotificationDelivery, NotificationPreference
from app.integrations.http_messaging import line_signature
from app.notify.channels import ChannelRouter, MockLine, MockSms
from app.notify.queue import queue, set_notifier, FakeNotifier
from tests.conftest import NOW, H, book


@pytest.fixture()
def router():
    r = ChannelRouter(MockSms(), MockLine())
    set_notifier(r)
    yield r
    set_notifier(FakeNotifier())


def q(now=NOW):
    return f"?now={now.isoformat()}"


def deliver(router, now=NOW + timedelta(seconds=30)):
    return queue.deliver_due(router, now)


def link_line(client, role, subject_id, user="U-line-0001", now=NOW):
    code = client.post(f"/me/notifications/line-link{q(now)}", headers=H(role, subject_id)).json()["link_code"]
    body = json.dumps({"events": [{"type": "message", "source": {"userId": user}, "message": {"type": "text", "text": code}}]}).encode()
    r = client.post(f"/integrations/line/webhook{q(now)}", content=body,
                    headers={"X-Line-Signature": line_signature(body, "mock-line-secret"), "Content-Type": "application/json"})
    return r


# รองรับ AC-10-01 (REQ-FN-072): ค่าตั้งต้นส่ง SMS ถึงทั้งลูกค้าและช่าง บันทึกช่องทาง
def test_AC_10_01_default_sms(client, db, seed, router):
    assert client.get("/me/notifications", headers=H("customer", seed["somchai"].id)).json()["channel"] == "sms"
    H("technician", seed["prasit"].id)  # ช่างมีบัญชีที่บ้านพร้อมออกให้ (REQ-FN-060) เบอร์ของบัญชีคือเบอร์รับข้อความ
    book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert deliver(router) == 2
    to = sorted(m["to"] for m in router.sms.outbox)
    assert "081-234-5678" in to and len(router.line.outbox) == 0
    rows = db.scalars(select(NotificationDelivery)).all()
    assert sorted((r.to_role, r.channel, r.result) for r in rows) == [("customer", "sms", "sent"), ("technician", "sms", "sent")]


# รองรับ AC-10-02 (REQ-FN-072 BR-12 ข้อ 1 และ 2): เชื่อม LINE แล้วเลือก LINE ข้อความไป LINE ไม่ไป SMS
def test_AC_10_02_link_and_choose_line(client, db, seed, router):
    c = seed["somchai"].id
    assert link_line(client, "customer", c).json() == {"linked": 1}
    r = client.put(f"/me/notifications{q()}", json={"channel": "line"}, headers=H("customer", c))
    assert r.status_code == 200 and r.json() == {"channel": "line", "line_linked": True, "channels": ["sms", "line"]}
    book(client, customer_id=c, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    deliver(router)
    assert [m["to"] for m in router.line.outbox] == ["U-line-0001"]
    assert all(m["to"] != "081-234-5678" for m in router.sms.outbox)


# รองรับ AC-10-03 (BR-12 ข้อ 1 ถึง 3): ยังไม่เชื่อมเลือก LINE ไม่ได้ ลายเซ็นผิดไม่ผูก รหัสหมดอายุไม่ผูก
def test_AC_10_03_line_requires_valid_link(client, db, seed, router):
    c = seed["somchai"].id
    r = client.put(f"/me/notifications{q()}", json={"channel": "line"}, headers=H("customer", c))
    assert r.status_code == 409 and r.json()["message"] == "กรุณาเชื่อมบัญชี LINE ก่อนเลือกรับข้อความทาง LINE"
    code = client.post(f"/me/notifications/line-link{q()}", headers=H("customer", c)).json()["link_code"]
    body = json.dumps({"events": [{"type": "message", "source": {"userId": "U-x"}, "message": {"text": code}}]}).encode()
    assert client.post(f"/integrations/line/webhook{q()}", content=body, headers={"X-Line-Signature": "bad"}).status_code == 403
    late = NOW + timedelta(minutes=11)
    ok_sig = {"X-Line-Signature": line_signature(body, "mock-line-secret")}
    assert client.post(f"/integrations/line/webhook{q(late)}", content=body, headers=ok_sig).json() == {"linked": 0}
    assert client.get("/me/notifications", headers=H("customer", c)).json()["line_linked"] is False


# รองรับ AC-10-04 (REQ-FN-073): LINE ไม่ตอบ ส่ง SMS แทนในรอบเดียวกัน ข้อความถือว่าส่งแล้ว
def test_AC_10_04_line_down_falls_back_to_sms(client, db, seed, router):
    c = seed["somchai"].id
    link_line(client, "customer", c)
    client.put(f"/me/notifications{q()}", json={"channel": "line"}, headers=H("customer", c))
    router.line.mode = "down"
    book(client, customer_id=c, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert deliver(router) == 2
    rows = db.scalars(select(NotificationDelivery).where(NotificationDelivery.to_role == "customer")).all()
    assert [(r.channel, r.result, r.fallback) for r in rows] == [("line", "failed", False), ("sms", "sent", True)]
    assert any(m["to"] == "081-234-5678" for m in router.sms.outbox)
    assert all(m.delivered_at for m in queue.items)


# รองรับ AC-10-05 (REQ-FN-072 บรรทัดที่ 3): OTP ส่ง SMS เสมอ แม้ลูกค้าเลือก LINE
def test_AC_10_05_otp_always_sms(client, db, seed, router):
    c = seed["somchai"].id
    link_line(client, "customer", c)
    client.put(f"/me/notifications{q()}", json={"channel": "line"}, headers=H("customer", c))
    r = client.post(f"/auth/otp{q()}", json={"phone": "081-234-5678", "role": "customer"})
    assert r.status_code == 202
    assert [m["to"] for m in router.sms.outbox] == ["081-234-5678"] and len(router.line.outbox) == 0


# รองรับ AC-10-06 (REQ-FN-072, F-20): ช่างเลือก LINE ได้เอง ข้อความงานใหม่บอกเวลาที่ต้องตอบรับ
def test_AC_10_06_technician_line_and_new_job_text(client, db, seed, router):
    t = seed["prasit"].id
    link_line(client, "technician", t, user="U-tech-0001")
    assert client.put(f"/me/notifications{q()}", json={"channel": "line"}, headers=H("technician", t)).status_code == 200
    book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    deliver(router)
    tech_msgs = [m for m in router.line.outbox if m["to"] == "U-tech-0001"]
    assert len(tech_msgs) == 1 and tech_msgs[0]["text"].startswith("มีงานใหม่ #") and "ภายใน 30 นาที" in tech_msgs[0]["text"]


# รองรับ AC-10-07 (REQ-PRV-010 REQ-PRV-002): ลบข้อมูลลูกค้า รหัส LINE หาย บันทึกการส่งไม่มีข้อความหรือเบอร์
def test_AC_10_07_erasure_and_no_pii_in_delivery_log(client, db, seed, router):
    c = seed["somchai"].id
    link_line(client, "customer", c)
    book(client, customer_id=c, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    deliver(router)
    assert set(NotificationDelivery.__table__.columns.keys()) == {"id", "message_id", "to_role", "to_id", "channel", "result", "fallback", "at"}
    job_done_free = client.post(f"/ops/erasure-requests{q(NOW + timedelta(days=3))}", json={"customer_id": c})
    assert job_done_free.status_code == 202
    from app.erasure.service import process_due
    from app.db.models import Job
    for j in db.scalars(select(Job)).all():
        j.status = "done"
    db.commit()
    process_due(db, NOW + timedelta(days=3), router)
    db.expire_all()
    pref = db.scalars(select(NotificationPreference).where(NotificationPreference.subject_id == c,
                                                           NotificationPreference.role == "customer")).one()
    assert pref.line_user_id is None and pref.channel == "sms"
    assert router.sms.erasures == [c]
