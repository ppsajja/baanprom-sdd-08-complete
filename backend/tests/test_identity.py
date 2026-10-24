"""AC-02-01 ถึง AC-02-11 และ AC-01-01 ถึง AC-01-03 จาก identity.feature (specs/006-identity, CR-11)
UC-02 ลูกค้าลงทะเบียนและเข้าสู่ระบบด้วยเบอร์โทรและ OTP | UC-01 ช่างเข้าสู่ระบบด้วยบัญชีที่บ้านพร้อมออกให้
REQ-SEC-013 (OTP 5 นาที ลองผิด 5 ครั้ง) REQ-SEC-014 (ตัวตนมาจาก token เท่านั้น) REQ-SEC-010 มีผลจริง (GAP-24)"""
import logging
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import Account, AuthSession, Customer, Job, OtpChallenge, SecurityEvent, ServiceAddress
from app.notify.queue import FakeNotifier, set_notifier
from tests.conftest import NOW, OPS, TOMORROW_14, H, book

NEW_PHONE = "089-111-2222"


@pytest.fixture()
def sms():
    n = FakeNotifier()
    set_notifier(n)
    yield n
    set_notifier(FakeNotifier())


def q(now=NOW):
    return f"?now={now.isoformat()}"


def otp(client, phone, role="customer", now=NOW):
    return client.post(f"/auth/otp{q(now)}", json={"phone": phone, "role": role})


def verify(client, challenge_id, code, now=NOW):
    return client.post(f"/auth/verify{q(now)}", json={"challenge_id": challenge_id, "code": code})


def code_in(sms: FakeNotifier) -> str:
    """อ่านรหัสจากข้อความที่ IF-02 จำลองได้รับ (ทางเดียวกับที่ลูกค้าเห็นบนโทรศัพท์)"""
    text = sms.otps[-1][1]
    return next(w for w in text.split() if w.isdigit() and len(w) == 6)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register_new(client, sms, phone=NEW_PHONE, now=NOW):
    ch = otp(client, phone, now=now).json()
    v = verify(client, ch["challenge_id"], code_in(sms), now).json()
    r = client.post(f"/auth/register{q(now)}", json={"challenge_id": v["challenge_id"], "name": "สมศรี",
                                                     "address_text": "บ้านเลขที่ 9 ซอยสุขใจ", "lat": 13.7410, "lng": 100.5310})
    return r


# รองรับ AC-02-01 (REQ-FN-058, REQ-SEC-013, REQ-PRV-011)
def test_AC_02_01_new_customer_registers_with_phone_and_otp(client, db, seed, sms):
    # Given เบอร์ 089-111-2222 ยังไม่เคยลงทะเบียน
    # When ลูกค้าขอรหัส OTP
    r = otp(client, NEW_PHONE)
    # Then ระบบตอบว่าส่งรหัสแล้ว รหัสหมดอายุใน 5 นาที และระบบส่งข้อความผ่าน IF-02 ไปที่เบอร์นั้น 1 ข้อความ
    assert r.status_code == 202
    assert r.json()["expires_at"] == (NOW + timedelta(minutes=5)).isoformat()
    assert [p for p, _ in sms.otps] == [NEW_PHONE]
    # When ลูกค้ากรอกรหัสที่ได้รับ
    v = verify(client, r.json()["challenge_id"], code_in(sms))
    # Then ระบบขอชื่อและที่อยู่ให้บริการ (ยังไม่มีบัญชี)
    assert v.status_code == 200 and v.json()["needs_registration"] is True and "token" not in v.json()
    # When ลูกค้ากรอกชื่อ "สมศรี" และที่อยู่ 1 แห่ง
    reg = client.post(f"/auth/register{q()}", json={"challenge_id": v.json()["challenge_id"], "name": "สมศรี",
                                                    "address_text": "บ้านเลขที่ 9 ซอยสุขใจ", "lat": 13.741, "lng": 100.531})
    # Then ลูกค้าเข้าสู่ระบบแล้ว และหน้าข้อมูลของฉันมีชื่อและที่อยู่ 1 แห่ง ไม่มีพิกัด
    assert reg.status_code == 201
    me = client.get(f"/me{q()}", headers=bearer(reg.json()["token"])).json()
    assert me["role"] == "customer" and me["name"] == "สมศรี"
    assert [a["text"] for a in me["addresses"]] == ["บ้านเลขที่ 9 ซอยสุขใจ"] and "lat" not in me["addresses"][0]
    cust = db.get(Customer, me["subject_id"]); db.refresh(cust)
    assert cust.phone == NEW_PHONE
    # And ใช้รหัสเดิมลงทะเบียนซ้ำไม่ได้
    again = client.post(f"/auth/register{q()}", json={"challenge_id": v.json()["challenge_id"], "name": "x",
                                                      "address_text": "y", "lat": 13.7, "lng": 100.5})
    assert again.status_code == 410


# รองรับ AC-02-02 (REQ-FN-059, REQ-SEC-014)
def test_AC_02_02_registered_customer_logs_in(client, db, seed, sms):
    first = register_new(client, sms)
    assert first.status_code == 201
    # Given ลูกค้าที่ลงทะเบียนแล้ว เมื่อรหัสครั้งแรกเกิน 60 วินาที ขอรหัสใหม่
    later = NOW + timedelta(minutes=2)
    ch = otp(client, NEW_PHONE, now=later).json()
    # When กรอกรหัสที่ถูกต้อง
    v = verify(client, ch["challenge_id"], code_in(sms), later)
    # Then เข้าสู่ระบบในนามลูกค้าคนเดิม session มีอายุ 30 วัน
    assert v.status_code == 200 and v.json()["role"] == "customer"
    assert v.json()["subject_id"] == first.json()["subject_id"] and v.json()["name"] == "สมศรี"
    assert v.json()["expires_at"] == (later + timedelta(days=30)).isoformat()
    # And ระบบไม่สร้างลูกค้าซ้ำ
    assert len(db.scalars(select(Customer).where(Customer.phone == NEW_PHONE)).all()) == 1


# รองรับ AC-02-03 (REQ-SEC-013 บรรทัดที่ 1: OTP หมดอายุใน 5 นาที)
def test_AC_02_03_otp_expires_after_5_minutes(client, db, seed, sms):
    ch = otp(client, NEW_PHONE).json()
    code = code_in(sms)
    # When ลูกค้ากรอกรหัสที่ถูกต้องเมื่อครบ 5 นาที
    r = verify(client, ch["challenge_id"], code, NOW + timedelta(minutes=5))
    # Then ระบบตอบว่ารหัสหมดอายุ และไม่ออก session
    assert r.status_code == 410 and r.json()["reason"] == "expired" and r.json()["message"] == "รหัสหมดอายุแล้ว กรุณาขอรหัสใหม่"
    assert db.scalars(select(AuthSession)).first() is None
    # And ก่อนครบ 5 นาทีหนึ่งวินาทียังใช้ได้ (ขอบของเกณฑ์)
    ch2 = otp(client, NEW_PHONE, now=NOW + timedelta(minutes=6)).json()
    ok = verify(client, ch2["challenge_id"], code_in(sms), NOW + timedelta(minutes=10, seconds=59))
    assert ok.status_code == 200


# รองรับ AC-02-04 (REQ-SEC-013 บรรทัดที่ 2: ลองผิดได้ 5 ครั้ง)
def test_AC_02_04_five_wrong_codes_lock_the_challenge(client, db, seed, sms):
    ch = otp(client, NEW_PHONE).json()
    right = code_in(sms)
    wrong = "000000" if right != "000000" else "111111"
    # When ลูกค้ากรอกรหัสผิด 4 ครั้ง
    left = [verify(client, ch["challenge_id"], wrong).json()["attempts_left"] for _ in range(4)]
    # Then ระบบบอกจำนวนครั้งที่เหลือ 4 3 2 1
    assert left == [4, 3, 2, 1]
    # When กรอกผิดครั้งที่ 5
    fifth = verify(client, ch["challenge_id"], wrong)
    # Then รหัสนี้ใช้ไม่ได้อีก แม้กรอกรหัสที่ถูก ต้องขอรหัสใหม่
    assert fifth.status_code == 410 and fifth.json()["reason"] == "locked"
    assert verify(client, ch["challenge_id"], right).json()["reason"] == "locked"
    assert db.get(OtpChallenge, ch["challenge_id"]).wrong_attempts == 5


# รองรับ AC-02-05 (REQ-SEC-013 บรรทัดที่ 3: ขอใหม่ได้ทุก 60 วินาที ไม่เกิน 5 ครั้งต่อชั่วโมง)
def test_AC_02_05_resend_limits_and_old_code_replaced(client, db, seed, sms):
    first = otp(client, NEW_PHONE).json()
    old_code = code_in(sms)
    # When ขอรหัสใหม่หลัง 30 วินาที Then ระบบให้รอ
    soon = otp(client, NEW_PHONE, now=NOW + timedelta(seconds=30))
    assert soon.status_code == 429 and soon.json()["reason"] == "too_soon" and soon.json()["retry_after_seconds"] == 30
    # When ขอใหม่หลัง 60 วินาที Then ได้รหัสใหม่ และรหัสเก่าใช้ไม่ได้
    second = otp(client, NEW_PHONE, now=NOW + timedelta(seconds=60)).json()
    assert verify(client, first["challenge_id"], old_code, NOW + timedelta(seconds=61)).json()["reason"] == "expired"
    # When ขอครบ 5 ครั้งในชั่วโมงเดียว Then ครั้งที่ 6 ถูกปฏิเสธ
    for i in range(2, 5):
        assert otp(client, NEW_PHONE, now=NOW + timedelta(minutes=2 * i)).status_code == 202
    sixth = otp(client, NEW_PHONE, now=NOW + timedelta(minutes=20))
    assert sixth.status_code == 429 and sixth.json()["reason"] == "too_many"
    assert len(sms.otps) == 5 and second["challenge_id"] != first["challenge_id"]


# รองรับ AC-02-06 (REQ-SEC-014): ตัวตนมาจาก token เท่านั้น
def test_AC_02_06_identity_comes_from_token_only(client, db, seed, gateway, sms):
    somchai, other = seed["somchai"].id, seed["other"].id
    # When ไม่มี token Then ทุก endpoint ของลูกค้าตอบ 401
    assert client.get(f"/technicians?category=ประปา&address_id={seed['addr'].id}{q()[0:0]}").status_code == 401
    assert client.post(f"/slots/{seed['slot'].id}/hold{q()}", json={"customer_id": somchai}).status_code == 401
    # When ลูกค้า "คนอื่น" ส่ง token ของตัวเอง แต่ใส่ customer_id ของสมชายใน body
    r = client.post(f"/slots/{seed['slots'][1].id}/hold{q()}", json={"customer_id": somchai}, headers=H("customer", other))
    # Then ล็อกเป็นของเจ้าของ token ไม่ใช่ของสมชาย
    assert r.status_code == 200
    from app.db.models import TimeSlot
    slot = db.get(TimeSlot, seed["slots"][1].id); db.refresh(slot)
    assert slot.held_by_customer_id == other
    # And จองด้วยที่อยู่ของลูกค้าอื่นไม่ได้ (403 และบันทึก)
    b = client.post(f"/bookings{q()}", json={"slot_id": seed["slot"].id, "address_id": seed["addr"].id, "category": "ประปา"},
                    headers=H("customer", other))
    assert b.status_code == 403
    assert db.scalars(select(SecurityEvent).where(SecurityEvent.endpoint == "POST /bookings")).first().actor_id == other
    # When ลูกค้าออกจากระบบ Then token เดิมใช้ไม่ได้ทันที
    reg = register_new(client, sms)
    token = reg.json()["token"]
    assert client.get(f"/me{q()}", headers=bearer(token)).status_code == 200
    assert client.post(f"/auth/logout{q()}", headers=bearer(token)).status_code == 200
    assert client.get(f"/me{q()}", headers=bearer(token)).status_code == 401
    # When session หมดอายุ (30 วัน) Then ตอบ 401
    reg2 = verify(client, otp(client, NEW_PHONE, now=NOW + timedelta(minutes=5)).json()["challenge_id"], code_in(sms),
                  NOW + timedelta(minutes=5)).json()
    assert client.get(f"/me{q(NOW + timedelta(days=29))}", headers=bearer(reg2["token"])).status_code == 200
    assert client.get(f"/me{q(NOW + timedelta(days=30, minutes=5))}", headers=bearer(reg2["token"])).status_code == 401


# รองรับ AC-02-07 (REQ-SEC-010 มีผลจริง ปิด GAP-24): GET /jobs/{id} และ /history
def test_AC_02_07_job_and_history_need_owner_assignee_or_call_center(client, db, seed):
    res = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    job_id = res.json()["job_id"]
    for path in (f"/jobs/{job_id}", f"/jobs/{job_id}/history"):
        # Then ไม่มี token ได้ 401
        assert client.get(path).status_code == 401
        # And ลูกค้าคนอื่นได้ 403 เหมือนขอเลขงานที่ไม่มี และไม่เห็นสถานะ
        other = client.get(path, headers=H("customer", seed["other"].id))
        missing = client.get(path.replace(str(job_id), "99999"), headers=H("customer", seed["other"].id))
        assert other.status_code == missing.status_code == 403 and other.json() == missing.json()
        assert "status" not in other.json()
        # And เจ้าของงาน ช่างผู้รับมอบหมาย และ call center (กุญแจของ Ops) อ่านได้
        assert client.get(path, headers=H("customer", seed["somchai"].id)).status_code == 200
        assert client.get(path, headers=H("technician", seed["prasit"].id)).status_code == 200
        assert client.get(path, headers=OPS).status_code == 200
        # And ช่างคนอื่นได้ 403
        assert client.get(path, headers=H("technician", seed["far"].id)).status_code == 403
    denied = db.scalars(select(SecurityEvent).where(SecurityEvent.kind == "denied")).all()
    assert len(denied) == 6 and {e.endpoint for e in denied} == {"GET /jobs/{job_id}", "GET /jobs/{job_id}/history"}


# รองรับ AC-02-08 (REQ-SEC-013, REQ-PRV-002): รหัสและเบอร์ไม่อยู่ใน log และฐานข้อมูลเก็บเฉพาะค่าแฮช
def test_AC_02_08_no_code_or_phone_in_log_or_db(client, db, seed, sms, caplog):
    caplog.set_level(logging.INFO)
    reg = register_new(client, sms)
    assert reg.status_code == 201
    code = code_in(sms)
    assert NEW_PHONE not in caplog.text and NEW_PHONE.replace("-", "") not in caplog.text
    assert code not in caplog.text and reg.json()["token"] not in caplog.text
    rows = db.scalars(select(OtpChallenge)).all()
    assert rows and all(r.code_hash != code and len(r.code_hash) == 64 for r in rows)
    sessions = db.scalars(select(AuthSession)).all()
    assert all(s.token_hash != reg.json()["token"] for s in sessions)


# รองรับ AC-02-09 (REQ-PRV-010 กับ REQ-SEC-014): ลูกค้าขอลบข้อมูล บัญชีและ session หายด้วย
def test_AC_02_09_erasure_removes_account_and_sessions(client, db, seed, sms, monkeypatch, tmp_path):
    monkeypatch.setenv("ERASURE_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    reg = register_new(client, sms)
    cid, token = reg.json()["subject_id"], reg.json()["token"]
    # When call center ส่งคำขอลบข้อมูลของลูกค้าคนนี้ (ไม่มีงานค้าง)
    r = client.post(f"/ops/erasure-requests{q()}", json={"customer_id": cid})
    assert r.status_code == 202 and r.json()["completed_at"]
    # Then token เดิมใช้ไม่ได้ บัญชีที่มีเบอร์ถูกลบ
    assert client.get(f"/me{q()}", headers=bearer(token)).status_code == 401
    assert db.scalars(select(Account).where(Account.subject_id == cid, Account.role == "customer")).first() is None
    # And เบอร์เดิมขอ OTP แล้วกลายเป็นการลงทะเบียนใหม่ ไม่ได้ข้อมูลเดิมคืน
    ch = otp(client, NEW_PHONE, now=NOW + timedelta(minutes=2)).json()
    v = verify(client, ch["challenge_id"], code_in(sms), NOW + timedelta(minutes=2)).json()
    assert v["needs_registration"] is True


# รองรับ AC-02-10 (REQ-FN-058, Q-29): หลายที่อยู่ เลือกที่อยู่ตอนค้นหา และใช้ที่อยู่ของคนอื่นไม่ได้
def test_AC_02_10_multiple_addresses_choose_when_searching(client, db, seed):
    me = H("customer", seed["somchai"].id)
    r = client.post(f"/me/addresses{q()}", json={"text": "คอนโดริมน้ำ", "lat": 13.7300, "lng": 100.5250}, headers=me)
    assert r.status_code == 201
    addrs = client.get(f"/me{q()}", headers=me).json()["addresses"]
    assert [a["text"] for a in addrs] == ["บ้านเลขที่ 12 ซอยสุขใจ", "คอนโดริมน้ำ"]
    found = client.get(f"/technicians?category=ประปา&address_id={r.json()['address_id']}&now={NOW.isoformat()}", headers=me)
    assert found.status_code == 200 and [t["name"] for t in found.json()] == ["ประสิทธิ์"]
    stolen = client.get(f"/technicians?category=ประปา&address_id={seed['addr_other'].id}&now={NOW.isoformat()}", headers=me)
    assert stolen.status_code == 403


# รองรับ AC-02-11 (REQ-SEC-012 กับ REQ-SEC-013): ระบบจริงไม่ส่งรหัสกลับในคำตอบ
def test_AC_02_11_production_never_returns_the_code(client, db, seed, sms, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    r = client.post("/auth/otp", json={"phone": NEW_PHONE, "role": "customer"})
    assert r.status_code == 202 and "dev_code" not in r.json() and len(sms.otps) == 1


# รองรับ AC-01-01 (REQ-FN-060): ช่างเข้าสู่ระบบด้วยเบอร์ที่บ้านพร้อมลงทะเบียนไว้
def test_AC_01_01_technician_logs_in_with_issued_account(client, db, seed, sms):
    tech = seed["prasit"].id
    # Given Ops ออกบัญชีให้ช่าง "ประสิทธิ์" ด้วยเบอร์ 086-555-0101
    a = client.post(f"/ops/technicians/{tech}/account{q()}", json={"phone": "086-555-0101"}, headers=OPS)
    assert a.status_code == 201
    # When ช่างขอรหัสและกรอกรหัสที่ได้รับ
    ch = otp(client, "086-555-0101", role="technician").json()
    v = verify(client, ch["challenge_id"], code_in(sms))
    # Then เข้าสู่ระบบในนามช่าง "ประสิทธิ์" session มีอายุ 12 ชั่วโมง และเปิดรายการงานของตัวเองได้
    assert v.status_code == 200 and v.json()["role"] == "technician" and v.json()["subject_id"] == tech
    assert v.json()["expires_at"] == (NOW + timedelta(hours=12)).isoformat()
    jobs = client.get(f"/technicians/{tech}/jobs{q()}", headers=bearer(v.json()["token"]))
    assert jobs.status_code == 200
    # And ครบ 12 ชั่วโมงต้องเข้าสู่ระบบใหม่
    late = client.get(f"/technicians/{tech}/jobs{q(NOW + timedelta(hours=12))}", headers=bearer(v.json()["token"]))
    assert late.status_code == 401


# รองรับ AC-01-02 (REQ-FN-060, REQ-SEC-013): เบอร์ที่ไม่มีบัญชีช่าง ตอบเหมือนกัน แต่ไม่ส่งข้อความและเข้าไม่ได้
def test_AC_01_02_unknown_technician_phone_gets_same_answer_but_no_sms(client, db, seed, sms):
    client.post(f"/ops/technicians/{seed['prasit'].id}/account{q()}", json={"phone": "086-555-0101"}, headers=OPS)
    known = otp(client, "086-555-0101", role="technician")
    unknown = otp(client, "086-555-0199", role="technician")
    assert known.status_code == unknown.status_code == 202
    assert set(known.json()) - {"dev_code"} == set(unknown.json()) - {"dev_code"}
    assert [p for p, _ in sms.otps] == ["086-555-0101"]
    for guess in ("000000", "123456"):
        r = verify(client, unknown.json()["challenge_id"], guess)
        assert r.status_code == 401 and r.json()["reason"] == "wrong_code"


# รองรับ AC-01-03 (REQ-SEC-010, REQ-SEC-014): ช่างใช้ได้เฉพาะเมนูและงานของตัวเอง
def test_AC_01_03_technician_token_limited_to_own_menu_and_jobs(client, db, seed):
    prasit = H("technician", seed["prasit"].id)
    other_list = client.get(f"/technicians/{seed['far'].id}/jobs{q()}", headers=prasit)
    assert other_list.status_code == 403
    assert db.scalars(select(SecurityEvent)).first().endpoint == "GET /technicians/{technician_id}/jobs"
    # token ของช่างใช้กับเมนูของลูกค้าไม่ได้ และ token ของลูกค้าใช้กับเมนูของช่างไม่ได้
    assert client.get(f"/me/jobs{q()}", headers=prasit).status_code == 403
    assert client.get(f"/technicians/{seed['prasit'].id}/jobs{q()}", headers=H("customer", seed["somchai"].id)).status_code == 403
