"""AC-02-12 ถึง AC-02-14 จาก identity.feature v1.1 (specs/006-identity, CR-18) หน้าจัดการที่อยู่ของลูกค้า (F-17)
และพิกัดจากข้อความที่อยู่ผ่าน IF-03 (GAP-40 ปิด) REQ-FN-074 REQ-PRV-011 รุ่น 1.4"""
import pytest
from sqlalchemy import select

from app import maps
from app.db.models import SecurityEvent, ServiceAddress
from app.notify.queue import FakeNotifier, set_notifier
from tests.conftest import NOW, H, book


def q(now=NOW):
    return f"?now={now.isoformat()}"


@pytest.fixture()
def sms():
    n = FakeNotifier()
    set_notifier(n)
    yield n
    set_notifier(FakeNotifier())


# รองรับ AC-02-12 (REQ-FN-074): เพิ่มที่อยู่ด้วยข้อความ ระบบหาพิกัดจาก IF-03 หน้าจอไม่เห็นพิกัด ใช้ค้นหาช่างได้
def test_AC_02_12_add_address_geocoded(client, db, seed):
    c = seed["somchai"].id
    r = client.post(f"/me/addresses{q()}", json={"text": "คอนโด 88 ถนนสีลม เขตบางรัก"}, headers=H("customer", c))
    assert r.status_code == 201 and set(r.json()) == {"address_id", "text"}
    a = db.get(ServiceAddress, r.json()["address_id"])
    assert (a.lat, a.lng) == maps.GAZETTEER["บางรัก"]
    rows = client.get("/me/addresses", headers=H("customer", c)).json()
    assert [x["address_id"] for x in rows] == [seed["addr"].id, a.id] and "lat" not in str(rows)
    found = client.get(f"/technicians{q()}&category=ประปา&address_id={a.id}", headers=H("customer", c))
    assert found.status_code == 200 and [t["name"] for t in found.json()] == ["ประสิทธิ์"]


# รองรับ AC-02-13 (REQ-FN-074): หาตำแหน่งไม่พบบอกให้ใส่ชื่อเขต แผนที่ไม่ตอบบอกให้ลองใหม่ ไม่บันทึกที่อยู่ ลงทะเบียนก็ใช้กติกาเดียวกัน
def test_AC_02_13_address_not_found_or_map_down(client, db, seed, sms):
    c = seed["somchai"].id
    before = db.query(ServiceAddress).count()
    r = client.post(f"/me/addresses{q()}", json={"text": "บ้านสวน ไม่บอกเขต"}, headers=H("customer", c))
    assert r.status_code == 422 and r.json()["message"] == "ไม่พบตำแหน่งของที่อยู่นี้ กรุณาใส่ชื่อเขตหรืออำเภอด้วย"
    maps.set_map(maps.MockMap(mode="down"))
    try:
        r = client.post(f"/me/addresses{q()}", json={"text": "เขตสาทร"}, headers=H("customer", c))
    finally:
        maps.set_map(None)
    assert r.status_code == 503 and r.json()["reason"] == "map_down"
    assert db.query(ServiceAddress).count() == before
    # ลงทะเบียนลูกค้าใหม่โดยไม่ส่งพิกัด (หน้าจอ UI-02-02 รุ่นใหม่)
    ch = client.post(f"/auth/otp{q()}", json={"phone": "089-111-3333", "role": "customer"}).json()
    code = next(w for w in sms.otps[-1][1].split() if w.isdigit() and len(w) == 6)
    v = client.post(f"/auth/verify{q()}", json={"challenge_id": ch["challenge_id"], "code": code}).json()
    bad = client.post(f"/auth/register{q()}", json={"challenge_id": v["challenge_id"], "name": "สมใจ", "address_text": "หมู่บ้านไม่มีชื่อเขต"})
    assert bad.status_code == 422 and bad.json()["reason"] == "address_not_found"
    ok = client.post(f"/auth/register{q()}", json={"challenge_id": v["challenge_id"], "name": "สมใจ", "address_text": "ซอยเย็นใจ เขตสาทร"})
    assert ok.status_code == 201


# รองรับ AC-02-14 (REQ-FN-074 REQ-SEC-010): ลบได้เฉพาะที่อยู่ของตัวเองที่ไม่มีงานอ้าง และต้องเหลืออย่างน้อย 1 แห่ง
def test_AC_02_14_delete_address_rules(client, db, seed):
    c = seed["somchai"].id
    assert client.get("/me/addresses", headers=H("customer", c)).json()[0]["can_delete"] is False   # เหลือแห่งเดียว
    r = client.delete(f"/me/addresses/{seed['addr'].id}", headers=H("customer", c))
    assert r.status_code == 409 and r.json()["reason"] == "last_one"
    new = client.post(f"/me/addresses{q()}", json={"text": "เขตปทุมวัน"}, headers=H("customer", c)).json()["address_id"]
    book(client, customer_id=c, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    rows = {x["address_id"]: x["can_delete"] for x in client.get("/me/addresses", headers=H("customer", c)).json()}
    assert rows == {seed["addr"].id: False, new: True}
    assert client.delete(f"/me/addresses/{seed['addr'].id}", headers=H("customer", c)).json()["reason"] == "in_use"
    assert client.delete(f"/me/addresses/{new}", headers=H("customer", seed["other"].id)).status_code == 403
    assert db.scalars(select(SecurityEvent).where(SecurityEvent.endpoint == "DELETE /me/addresses/{id}")).all()
    assert client.delete(f"/me/addresses/{new}", headers=H("customer", c)).json() == {"deleted": new}
