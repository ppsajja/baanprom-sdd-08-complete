"""AC-14-17 ถึง AC-14-19 จาก ai-assistant.feature v1.1 (specs/005-ai-assistant, CR-19) และ test เพิ่มของ AC-14-10 (F-16)
REQ-AI-023 ชั้นที่ 3 ของการรับ: รุ่นโมเดลต้องเป็นรุ่นที่ผ่าน eval ล่าสุด | Q-65 ระยะเวลาเงินคืนขึ้นกับธนาคารผู้ออกบัตร
REQ-FN-075 call center เลื่อนนัดกลับเมื่อผู้ช่วยเลื่อนผิด ไม่นับครั้งของ BR-06 (GAP-31 ปิด)"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.assistant import service, tools
from app.assistant import evaluation as ev
from app.assistant.llm import LLM, LLMReply, MockLLM, set_llm
from app.booking.service import reschedules_used
from app.db.models import Job, JobReschedule, NotificationMessage, TimeSlot
from tests.conftest import NOW, TOMORROW_14, H, book
from tests.test_assistant import _propose, booked_job, q, say, start


@pytest.fixture(autouse=True)
def fresh_llm():
    set_llm(MockLLM())
    tools.FAULTS.clear()
    tools.CALLS.clear()
    yield
    set_llm(MockLLM())
    tools.FAULTS.clear()


class NewModel(MockLLM):
    model_version = "mock-2.0"


# รองรับ AC-14-17 (REQ-AI-023): ระบบจริงเปลี่ยนรุ่นโมเดลที่ยังไม่ผ่าน eval ผู้ช่วยปิดเอง บอกเหตุ เปิดได้เมื่อบันทึกรุ่นที่ผ่าน
def test_AC_14_17_unaccepted_model_disables_assistant(client, db, seed, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert client.get("/assistant/status").json()["enabled"] is True
    set_llm(NewModel())
    st = client.get("/assistant/status").json()
    assert st["enabled"] is False and st["message"] == service.MSG_MODEL_NOT_ACCEPTED
    assert (st["model_version"], st["accepted_model"]) == ("mock-2.0", "mock-1.1")
    monkeypatch.setenv("ASSISTANT_ACCEPTED_MODEL", "mock-2.0")   # หลังรัน eval ทั้งชุดผ่าน Ops lead ตั้งรุ่นที่รับ
    assert client.get("/assistant/status").json()["enabled"] is True


# รองรับ AC-14-18 (Q-65): คำถามจำนวนวันเงินคืน บอกว่ายังไม่มีข้อมูลจำนวนวัน และระยะเวลาขึ้นกับธนาคารผู้ออกบัตร
def test_AC_14_18_refund_timing_mentions_issuing_bank(client, db, seed):
    job = booked_job(client, db, seed)
    client.post(f"/jobs/{job.id}/customer-cancel{q()}", headers=H("customer", seed["somchai"].id))
    conv = start(client, seed["somchai"].id)
    out = say(client, conv["conversation_id"], seed["somchai"].id, "เงินคืนเข้าบัญชีกี่วันคะ")
    assert "ยังไม่มีข้อมูล" in out["reply"] and "ธนาคารผู้ออกบัตร" in out["reply"]
    items = [i for i in ev.load("qa") if i.get("topic") == "refund_days"]
    assert len(items) == 5 and all("ธนาคารผู้ออกบัตร" in i["expect"]["must"] and i["version"] == "1.2" for i in items)
    res = ev.run_all("P-1.1")
    row = [c for c in res["summary"]["criteria"] if c["ac"] == "AC-14-18"][0]
    assert row["pass"] and row["got"] == row["total"] == 5


# รองรับ AC-14-10 (REQ-AI-012 F-16): เครื่องมือเลื่อนนัดทำไปแล้วแต่ไม่ได้คำตอบ ไม่เรียกซ้ำ ตั๋วส่งต่อ reference กันเลื่อนซ้ำ
def test_AC_14_10_tool_timeout_after_effect_not_called_again(client, db, seed):
    job, conv, out = _propose(client, db, seed)
    pid = out["proposal"]["proposal_id"]
    tools.FAULTS["reschedule_job"] = "after"
    r = client.post(f"/assistant/proposals/{pid}/confirm{q()}", json={}, headers=H("customer", seed["somchai"].id)).json()
    assert r["outcome"] == "unknown" and r["ticket_id"]
    client.post(f"/assistant/proposals/{pid}/confirm{q()}", json={}, headers=H("customer", seed["somchai"].id))
    assert tools.CALLS.count("reschedule_job") == 1
    db.expire_all()
    rows = db.scalars(select(JobReschedule).where(JobReschedule.job_id == job.id)).all()
    assert [x.reference for x in rows] == [f"P-{pid}"]       # เลื่อนไปแล้ว 1 ครั้ง ไม่ซ้ำ call center เห็นจากบันทึก


# รองรับ AC-14-19 (REQ-FN-075 ปิด GAP-31): call center เลื่อนนัดกลับ ช่วงเดิมกลับมา ไม่นับครั้งของ BR-06 แจ้งสองฝ่าย
def test_AC_14_19_call_center_reverts_reschedule(client, db, seed, monkeypatch):
    monkeypatch.setenv("CALL_CENTER_TOKEN", "cc-key")
    cc = {"X-Call-Center-Token": "cc-key"}
    job, conv, out = _propose(client, db, seed)
    client.post(f"/assistant/proposals/{out['proposal']['proposal_id']}/confirm{q()}", json={}, headers=H("customer", seed["somchai"].id))
    db.expire_all()
    job = db.get(Job, job.id)
    assert job.slot_id != seed["slot"].id and reschedules_used(db, job) == 1
    r = client.post(f"/call-center/jobs/{job.id}/revert-reschedule{q()}", headers=cc)
    assert r.status_code == 200 and r.json()["slot_id"] == seed["slot"].id
    db.expire_all()
    job = db.get(Job, job.id)
    assert job.scheduled_start == seed["slot"].start and reschedules_used(db, job) == 1
    assert db.get(TimeSlot, seed["slot"].id).state == "booked"
    sent = db.scalars(select(NotificationMessage).where(NotificationMessage.job_id == job.id,
                                                        NotificationMessage.text.like("%แก้นัดกลับ%"))).all()
    assert sorted(m.to_role for m in sent) == ["customer", "technician"]   # แจ้งสองฝ่ายผ่านคิว (ส่งภายใน 60 วินาทีตาม REQ-OP-008)
    again = client.post(f"/call-center/jobs/{job.id}/revert-reschedule{q()}", headers=cc)
    assert again.status_code == 409 and again.json()["reason"] == "no_reschedule"
    assert client.post(f"/call-center/jobs/{job.id}/revert-reschedule{q()}", headers=H("customer", seed["somchai"].id)).status_code == 403
