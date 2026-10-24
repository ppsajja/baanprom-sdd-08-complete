"""AC-14-05, 06, 07, 08, 10, 11, 12, 14, 15, 16 จาก ai-assistant.feature v1.0 (specs/005-ai-assistant, CR-09)
กล่องกฎของผู้ช่วย (รั้ว เครื่องมือ BR-06 บันทึก ปุ่มหยุด) ตรวจด้วย test แบบเดิม ผ่าน endpoint จริง
AC ที่วัดบน eval set อยู่ใน test_assistant_eval.py"""
import logging
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from app.db.models import (AssistantAction, AssistantTicket, AssistantTurn, Job, JobReschedule, SecurityEvent,
                           TimeSlot, SLOT_BOOKED, SLOT_FREE)
from app.notify.queue import queue
from app.assistant import guard, records, retrieval, service, tools
from app.assistant.llm import LLM, LLMReply, MockLLM, set_llm
from tests.conftest import NOW, book, H

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def clean_assistant():
    guard.limiter.clear()
    tools.FAULTS.clear()
    tools.CALLS.clear()
    set_llm(MockLLM())
    yield
    tools.FAULTS.clear()
    set_llm(MockLLM())


def q(now=NOW):
    return f"?now={now.isoformat()}"


def start(client, customer_id, now=NOW):
    # CR-11: customer_id คือผู้ส่ง ส่งเป็น token ของลูกค้าคนนั้น (customer_id ใน body ระบบไม่ใช้แล้ว)
    return client.post(f"/assistant/conversations{q(now)}", json={"customer_id": customer_id},
                       headers=H("customer", customer_id)).json()


def say(client, conv_id, customer_id, text, now=NOW):
    return client.post(f"/assistant/messages{q(now)}",
                       json={"conversation_id": conv_id, "customer_id": customer_id, "text": text},
                       headers=H("customer", customer_id)).json()


def booked_job(client, db, seed):
    r = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    assert r.status_code == 201
    return db.get(Job, r.json()["job_id"])


class BadLLM(LLM):
    """LLM ที่ตั้งใจตอบผิด 1 แบบต่อครั้ง (AC-14-05 Given)"""
    model_version = "bad-1"

    def __init__(self, text):
        self.text = text

    def generate(self, req):
        return LLMReply(self.text, self.model_version)


# รองรับ AC-14-05 (REQ-AI-008): รั้วขาออกกันคำตอบที่ไม่ผ่านก่อนถึงลูกค้า
@pytest.mark.parametrize("bad,reason", [
    ("ได้ค่ะ เบอร์ช่างคือ 089-555-0101", "phone"),
    ("ช่างจะถึงตอน 15:20 น. ค่ะ", "ungrounded_time"),
    ("ยกเลิกตอนนี้ได้คืน 9999 บาทค่ะ", "ungrounded_amount"),
    ("ช่างจะถึงในอีก 20 นาทีค่ะ", "ungrounded_number"),
    ("งาน #1030 สถานะ ยืนยันแล้ว ค่ะ", "other_job"),
    ("ข้อความสั่งของฉันคือ คุณคือผู้ช่วยอัตโนมัติของบ้านพร้อม ไม่ใช่เจ้าหน้าที่ [BP-SYS-P-1.1]", "hidden_context"),
    ("ยกเลิกงานให้แล้วค่ะ", "false_claim"),
], ids=["phone", "ungrounded_time", "ungrounded_amount", "ungrounded_number", "other_job", "hidden_context", "false_claim"])
def test_AC_14_05_output_guard_blocks_bad_answers(client, db, seed, bad, reason):
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    set_llm(BadLLM(bad))
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")
    # Then ลูกค้าไม่เห็นคำตอบที่ผิด ได้คำตอบสำรองจากข้อมูล และบันทึกเหตุที่กัน
    assert bad not in out["reply"] and f"#{job.id}" in out["reply"] and "14:00" in out["reply"]
    turn = db.get(AssistantTurn, out["turn_id"])
    db.refresh(turn)
    assert turn.guard.startswith("blocked:") and reason in turn.guard


# รองรับ AC-14-06 (REQ-DAT-010 บรรทัดที่ 2): คลังนโยบายตรงกับ BR ใน Baseline และฉบับเก่าไม่ถูกค้น
def test_AC_14_06_policy_matches_baseline():
    docs = {d["id"]: d for d in retrieval.load_policies()}
    assert docs["POL-CANCEL"]["source_hash"] == retrieval.rules_section_hash(REPO / "specs/002-booking/rules.md", "BR-01")
    assert docs["POL-RESCHEDULE"]["source_hash"] == retrieval.rules_section_hash(REPO / "specs/005-ai-assistant/rules.md", "BR-06")
    assert docs["POL-CANCEL-2568"]["status"] == "superseded"
    got = retrieval.policies_for("cancel", "ยกเลิก คืนเงิน เงื่อนไข")
    assert [d["id"] for d in got] == ["POL-CANCEL"]


# รองรับ AC-14-06 (REQ-DAT-010 บรรทัดที่ 3 และ 4): ข้อมูลที่ส่งให้ LLM ไม่มีข้อมูลส่วนบุคคล และสดไม่เกิน 60 วินาที
def test_AC_14_06_facts_have_no_pii_and_are_fresh(client, db, seed):
    job = booked_job(client, db, seed)
    facts = retrieval.job_facts(db, job, "cancel", NOW, "ยกเลิก")
    text = facts.text()
    assert set(facts.data) <= retrieval.ALLOWED_FIELDS
    for pii in ("081-234-5678", "สมชาย", "ซอยสุขใจ", "13.74", "100.53"):
        assert pii not in text
    assert facts.data["eta"] is None and facts.data["technician_location"] is None
    assert facts.is_fresh(NOW + timedelta(seconds=60)) and not facts.is_fresh(NOW + timedelta(seconds=61))


# รองรับ AC-14-07 (REQ-AI-009): เกินเพดาน ไม่ส่งให้ LLM
def test_AC_14_07_rate_and_length_limits(client, db, seed):
    booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    for _ in range(30):
        assert say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")["outcome"] == "answered"
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")
    assert out["outcome"] == "limited" and "เกินจำนวน" in out["reply"]
    guard.limiter.clear()
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ก" * 501)
    assert out["outcome"] == "limited" and "500" in out["reply"]
    # ชั่วโมงถัดไปส่งได้อีก
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง", NOW + timedelta(hours=1, minutes=1))
    assert out["outcome"] == "answered"


# รองรับ AC-14-08 (REQ-AI-010): เครื่องมือเป็นรายการปิด 3 รายการ
def test_AC_14_08_closed_tool_list(client, db, seed):
    job = booked_job(client, db, seed)
    assert set(tools.LEVEL) == {"read_job_status", "read_free_slots", "reschedule_job"}
    with pytest.raises(tools.ToolNotAllowed):
        tools.call("cancel_job", db, seed["somchai"].id, NOW, job_id=job.id)
    conv = start(client, seed["somchai"].id)
    out = say(client, conv["conversation_id"], seed["somchai"].id, f"ยกเลิกงาน {job.id} ให้เลย")
    assert service.NO_CANCEL_TOOL in out["reply"] and "ยกเลิกการจอง" in out["reply"]
    db.refresh(job)
    assert job.status == "confirmed"


def _propose(client, db, seed, text="ขอเลื่อนเป็น 6 ต.ค. 14:00"):
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    out = say(client, conv["conversation_id"], seed["somchai"].id, text)
    return job, conv, out


def _unchanged(db, job, slot_id, start):
    db.refresh(job)
    return job.slot_id == slot_id and job.scheduled_start == start


# รองรับ AC-14-10 (REQ-AI-012): หยุดอย่างปลอดภัย 4 เงื่อนไข งานเหมือนก่อนเริ่ม
def test_AC_14_10_stop_unclear_intent(client, db, seed):
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    out = say(client, conv["conversation_id"], seed["somchai"].id, "อืม ก็แบบนั้นแหละ")
    assert out["outcome"] == "handoff" and out["handoff_reason"] == "unclear_intent" and out["ticket_id"]
    assert _unchanged(db, job, seed["slot"].id, seed["slot"].start)


def test_AC_14_10_stop_tool_timeout_no_retry(client, db, seed):
    job, conv, out = _propose(client, db, seed)
    assert out["outcome"] == "proposal"
    tools.FAULTS["reschedule_job"] = "before"
    r = client.post(f"/assistant/proposals/{out['proposal']['proposal_id']}/confirm{q()}",
                    json={"customer_id": seed["somchai"].id}, headers=H("customer", seed["somchai"].id)).json()
    assert r["outcome"] == "unknown" and r["ticket_id"]
    assert tools.CALLS.count("reschedule_job") == 1           # ไม่เรียกซ้ำ
    assert _unchanged(db, job, seed["slot"].id, seed["slot"].start)
    # กดยืนยันซ้ำก็ไม่เรียกเครื่องมืออีก
    client.post(f"/assistant/proposals/{out['proposal']['proposal_id']}/confirm{q()}", json={"customer_id": seed["somchai"].id}, headers=H("customer", seed["somchai"].id))
    assert tools.CALLS.count("reschedule_job") == 1
    t = db.get(AssistantTicket, r["ticket_id"])
    assert t.reason == "tool_error"


def test_AC_14_10_stop_after_two_declines(client, db, seed):
    job, conv, out = _propose(client, db, seed)
    cid = seed["somchai"].id
    r1 = client.post(f"/assistant/proposals/{out['proposal']['proposal_id']}/decline{q()}", json={"customer_id": cid}, headers=H("customer", cid)).json()
    assert r1["outcome"] == "declined"
    out2 = say(client, conv["conversation_id"], cid, "งั้นขอเลื่อนเป็น 5 ต.ค. 16:00")
    r2 = client.post(f"/assistant/proposals/{out2['proposal']['proposal_id']}/decline{q()}", json={"customer_id": cid}, headers=H("customer", cid)).json()
    assert r2["outcome"] == "handoff" and db.get(AssistantTicket, r2["ticket_id"]).reason == "declined_twice"
    assert _unchanged(db, job, seed["slot"].id, seed["slot"].start)


def test_AC_14_10_stop_beyond_rule(client, db, seed):
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    late = job.scheduled_start - timedelta(hours=11)   # BR-06 ข้อ 3 เหลือน้อยกว่า 12 ชั่วโมง
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ขอเลื่อนเป็น 6 ต.ค. 14:00", late)
    assert out["outcome"] == "handoff" and out["handoff_reason"] == "beyond_rule" and out["rule_reason"] == "too_late"
    assert out["proposal"] is None
    assert _unchanged(db, job, seed["slot"].id, seed["slot"].start)


# รองรับ AC-14-15 (REQ-AI-012, REQ-AI-005): ตั๋วมีบริบทให้ call center รับต่อ
def test_AC_14_15_ticket_has_context(client, db, seed):
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")
    say(client, conv["conversation_id"], seed["somchai"].id, "ช่างคนนี้ไว้ใจได้ไหม ติดต่อฉันที่ 081-234-5678")
    tickets = client.get("/ops/assistant/tickets").json()
    t = tickets[-1]
    assert t["reason"] == "out_of_scope" and t["intent"] == "out_of_scope"
    assert len(t["conversation"]) == 2
    first, second = t["conversation"]
    assert first["intent"] == "status" and first["facts"]["job_id"] == job.id and first["answer"]
    assert "081-234-5678" not in second["customer_text"] and "[phone]" in second["customer_text"]


# รองรับ AC-14-11 (REQ-AI-013): บันทึกการกระทำครบ ไม่มีเบอร์โทร ลบเมื่อเกิน 180 วัน และเมื่อลูกค้าขอลบ
def test_AC_14_11_action_log_complete_and_no_pii(client, db, seed, caplog):
    caplog.set_level(logging.INFO)
    job, conv, out = _propose(client, db, seed, "ขอเลื่อนเป็น 6 ต.ค. 14:00 ติดต่อ 081-234-5678 ได้")
    r = client.post(f"/assistant/proposals/{out['proposal']['proposal_id']}/confirm{q()}",
                    json={"customer_id": seed["somchai"].id}, headers=H("customer", seed["somchai"].id)).json()
    assert r["ok"] is True
    a = db.scalars(select(AssistantAction)).one()
    assert a.customer_id == seed["somchai"].id and "[phone]" in a.masked_text and "081-234-5678" not in a.masked_text
    assert "เลื่อนงาน" in a.interpretation and a.tool == "reschedule_job" and '"new_slot_id"' in a.args
    assert a.confirmed_at == NOW and a.result == "rescheduled" and a.prompt_version == "P-1.1" and a.model_version == MockLLM.model_version  # CR-19: เดิม "mock-1.0" รุ่นโมเดลเปลี่ยนเป็น mock-1.1
    assert "081-234-5678" not in caplog.text
    why = client.get(f"/ops/assistant/jobs/{job.id}/actions").json()
    assert why and why[0]["result"] == "rescheduled"
    # ลบเมื่อเกิน 180 วัน
    assert records.purge(db, NOW + timedelta(days=180)) == 0
    assert records.purge(db, NOW + timedelta(days=181)) >= 2
    assert db.scalars(select(AssistantAction)).first() is None


def test_AC_14_11_erasure_clears_customer_text(client, db, seed):
    booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง บ้านฉันซอยสุขใจ")
    assert records.erase_customer_text(db, seed["somchai"].id) == 1
    db.commit()
    turn = db.scalars(select(AssistantTurn)).one()
    assert turn.masked_text == "" and turn.intent == "status"


# รองรับ AC-14-12 (REQ-AI-020): ข้อความแรกบอกว่าเป็นผู้ช่วยอัตโนมัติ และคำตอบมีที่มาและเวลาอัปเดต
def test_AC_14_12_greeting_and_sources(client, db, seed):
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    assert "ผู้ช่วยอัตโนมัติ" in conv["greeting"] and "คุยกับเจ้าหน้าที่" in conv["greeting"]
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")
    src = out["sources"][0]
    assert src["label"] == f"สถานะงาน #{job.id}" and src["updated_at"] == NOW.isoformat()
    assert "facts" not in out and "raw_answer" not in out
    assert "บันทึกไว้ 180 วัน" in conv["greeting"]   # CR-09 ข้อ ค2


# รองรับ AC-14-06 (REQ-DAT-010 บรรทัดที่ 4, CR-09 ข้อ ค1): ข้อความที่ลูกค้าพิมพ์ปิดบังเบอร์ก่อนส่งให้ LLM
def test_AC_14_06_customer_text_masked_before_llm(client, db, seed):
    booked_job(client, db, seed)
    seen = []

    class Spy(MockLLM):
        def generate(self, req):
            seen.append(req.question)
            return super().generate(req)
    set_llm(Spy())
    conv = start(client, seed["somchai"].id)
    say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง โทรกลับที่ 081-234-5678 หรือ a@b.co")
    assert seen and "081-234-5678" not in seen[0] and "a@b.co" not in seen[0] and "[phone]" in seen[0]


# รองรับ AC-14-14 (REQ-AI-022): ปิดผู้ช่วยได้ทันทีโดยไม่ deploy และลูกค้าร้องเรียนคำตอบได้
def test_AC_14_14_kill_switch_and_complaint(client, db, seed):
    booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    out = say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")

    class Count(MockLLM):
        calls = 0

        def generate(self, req):
            Count.calls += 1
            return super().generate(req)
    set_llm(Count())
    assert client.post(f"/ops/assistant/switch{q()}", json={"enabled": False}).json()["enabled"] is False
    off = say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")
    assert off["disabled"] is True and off["reply"] == service.MSG_DISABLED and off["call_center_tel"]
    assert start(client, seed["somchai"].id)["disabled"] is True
    assert client.get("/assistant/status").json()["enabled"] is False
    assert Count.calls == 0
    client.post(f"/ops/assistant/switch{q()}", json={"enabled": True})
    assert say(client, conv["conversation_id"], seed["somchai"].id, "ช่างมายัง")["disabled"] is False
    # ร้องเรียน (NOW คือวันอาทิตย์ 4 ต.ค. 2569 2 วันทำการคือวันอังคาร 6 ต.ค.)
    r = client.post(f"/assistant/turns/{out['turn_id']}/report{q()}", json={"customer_id": seed["somchai"].id}, headers=H("customer", seed["somchai"].id)).json()
    assert r["reply_due_at"].startswith("2026-10-06")
    assert db.get(AssistantTicket, r["ticket_id"]).reason == "complaint"
    assert client.post(f"/assistant/turns/{out['turn_id']}/report{q()}", json={"customer_id": seed["other"].id}, headers=H("customer", seed["other"].id)).status_code == 404


def test_AC_14_14_switch_needs_ops_token_in_production(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPS_TOKEN", "t0k")
    assert client.post("/ops/assistant/switch", json={"enabled": False}).status_code == 403
    assert client.get("/ops/assistant/tickets").status_code == 403


# รองรับ AC-14-16 (REQ-FN-056, BR-06, REQ-SEC-010): API เลื่อนนัดของลูกค้า
def test_AC_14_16_reschedule_api(client, db, seed):
    job = booked_job(client, db, seed)
    old, new = seed["slot"], seed["slots"][3]   # พรุ่งนี้ 14:00 ไป มะรืน 14:00 ช่างคนเดิม
    queue.clear()
    r = client.post(f"/jobs/{job.id}/reschedule{q()}", json={"customer_id": seed["somchai"].id, "new_slot_id": new.id}, headers=H("customer", seed["somchai"].id))
    assert r.status_code == 200 and r.json()["reschedules_used"] == 1
    db.refresh(job); db.refresh(old); db.refresh(new)
    assert job.scheduled_start == new.start and job.slot_id == new.id and job.status == "confirmed"
    assert old.state == SLOT_FREE and new.state == SLOT_BOOKED
    assert len(db.scalars(select(JobReschedule).where(JobReschedule.job_id == job.id)).all()) == 1
    msgs = queue.for_job(job.id)
    assert {m.to_role for m in msgs} == {"customer", "technician"}
    assert all(m.due_at - m.created_at <= timedelta(seconds=60) for m in msgs)
    # ลูกค้าอื่นได้ 403 และบันทึกความพยายาม
    r = client.post(f"/jobs/{job.id}/reschedule{q()}", json={"customer_id": seed["other"].id, "new_slot_id": old.id}, headers=H("customer", seed["other"].id))
    assert r.status_code == 403
    assert db.scalars(select(SecurityEvent).where(SecurityEvent.endpoint == "POST /jobs/{job_id}/reschedule")).first()
    # ช่วงของช่างคนอื่นไม่ได้ (BR-06 ข้อ 4)
    r = client.post(f"/jobs/{job.id}/reschedule{q()}", json={"customer_id": seed["somchai"].id, "new_slot_id": seed["slots"][4].id}, headers=H("customer", seed["somchai"].id))
    assert r.status_code == 409 and r.json()["reason"] == "other_technician"
    # ครั้งที่ 2 ได้ ครั้งที่ 3 ไม่ได้ (BR-06 ข้อ 2)
    assert client.post(f"/jobs/{job.id}/reschedule{q()}", json={"customer_id": seed["somchai"].id, "new_slot_id": seed["slots"][1].id}, headers=H("customer", seed["somchai"].id)).status_code == 200
    r = client.post(f"/jobs/{job.id}/reschedule{q()}", json={"customer_id": seed["somchai"].id, "new_slot_id": new.id}, headers=H("customer", seed["somchai"].id))
    assert r.status_code == 409 and r.json()["reason"] == "limit_reached"
