"""ลำดับ 5 ขั้นของผู้ช่วย (MD-SEQ-14-01) และการยืนยันเลื่อนนัด (MD-SEQ-14-02) ไฟล์นี้เป็นโค้ดธรรมดาทั้งหมด
ขั้น 1 รับคำถาม (ใครถาม เปิดไหม เพดาน) | ขั้น 2 รั้วขาเข้าและจำแนกความตั้งใจ | ขั้น 3 ค้นข้อมูลจริง
ขั้น 4 LLM แต่งคำตอบ (กล่อง AI กล่องเดียว) | ขั้น 5 รั้วขาออก แล้วบันทึก
ข้อความที่ลูกค้าเห็นซึ่งไม่ได้มาจาก LLM อยู่ที่นี่ที่เดียว (รายการ "ต้องตรง" ของ UI-14-01)"""
import logging
import time
from datetime import datetime

from sqlalchemy import select

from app import config
from app.db.models import AssistantConversation, AssistantProposal, AssistantSetting, AssistantTurn
from app.booking.service import RescheduleRejected
from app.ops import audit
from app.privacy import log_event, mask_text
from app.assistant import agent, guard, handoff, prompts, records, retrieval, tools
from app.assistant.intents import classify, FORBIDDEN
from app.assistant.llm import LLM, LLMReply, LLMRequest, get_llm

_log = logging.getLogger(__name__)

GREETING = ("สวัสดีค่ะ ฉันคือผู้ช่วยอัตโนมัติของบ้านพร้อม ไม่ใช่เจ้าหน้าที่ ตอบได้ 5 เรื่อง คือ สถานะงาน ชื่อช่าง "
            "การยกเลิก การเลื่อนนัด และการคืนเงิน ต้องการคุยกับเจ้าหน้าที่ กดปุ่ม คุยกับเจ้าหน้าที่ ได้ทุกเมื่อ "
            "บทสนทนานี้ถูกบันทึกไว้ 180 วันเพื่อตรวจสอบคุณภาพ")  # CR-09 ข้อ ค2 (REQ-CMP-001 รายการ PDPA ข้อ 2)
MSG_OUT_OF_SCOPE = ("ขออภัย เรื่องนี้ขอส่งต่อเจ้าหน้าที่นะคะ ผู้ช่วยตอบได้เฉพาะเรื่องสถานะงาน ชื่อช่าง การยกเลิก "
                    "การเลื่อนนัด และการคืนเงิน")
MSG_FORBIDDEN = {
    "forbidden_phone": "ขออภัย ผู้ช่วยให้เบอร์โทรไม่ได้ค่ะ ถ้าต้องการติดต่อช่าง กดปุ่ม คุยกับเจ้าหน้าที่",
    "forbidden_refund_deal": ("ขออภัย ผู้ช่วยตกลงคืนเงินไม่ได้ค่ะ ยอดคืนเป็นไปตามเงื่อนไขของระบบ ดูยอดได้ที่หน้า "
                              "ยกเลิกการจอง ถ้าต้องการร้องเรียน กดปุ่ม คุยกับเจ้าหน้าที่"),
    "forbidden_promise": "ขออภัย ผู้ช่วยรับปากเวลาที่ช่างจะถึงไม่ได้ เพราะยังไม่มีข้อมูลเวลาถึง บอกได้เฉพาะเวลานัดค่ะ",
}
MSG_INJECTION = "ขออภัย ผู้ช่วยทำตามคำขอนี้ไม่ได้ค่ะ ถามเรื่องงานของคุณได้ 5 เรื่อง หรือกดปุ่ม คุยกับเจ้าหน้าที่"
MSG_UNCLEAR = "ขออภัย ผู้ช่วยยังไม่เข้าใจคำถาม ขอส่งต่อเจ้าหน้าที่นะคะ"
MSG_NOT_FOUND = "ไม่พบงานนี้ในบัญชีของคุณค่ะ"
MSG_NO_JOB = "ยังไม่พบงานในบัญชีของคุณค่ะ"
MSG_HANDOFF = "ส่งต่อเจ้าหน้าที่แล้วค่ะ เจ้าหน้าที่จะเห็นบทสนทนานี้ คุณไม่ต้องเล่าใหม่"
MSG_LIMIT = "ส่งข้อความเกินจำนวนที่กำหนดในชั่วโมงนี้ กรุณากดปุ่ม คุยกับเจ้าหน้าที่"
MSG_TOO_LONG = "ข้อความยาวเกินไป กรุณาพิมพ์สั้นลงไม่เกิน {n} ตัวอักษร"
MSG_DISABLED = "ผู้ช่วยปิดชั่วคราว กรุณาติดต่อเจ้าหน้าที่"
MSG_RESCHEDULED = "เลื่อนนัดแล้วค่ะ งาน #{job} นัดใหม่ {when} ระบบจะแจ้งคุณและช่างภายใน 60 วินาที"
MSG_DECLINED = "ยกเลิกคำขอเลื่อนนัดแล้วค่ะ นัดเดิมยังอยู่"
MSG_TOOL_TIMEOUT = "ขออภัย ระบบเลื่อนนัดไม่ตอบ ยังไม่ทราบผล ขอส่งต่อเจ้าหน้าที่ตรวจสอบนะคะ"
MSG_EXPIRED = "สรุปนี้หมดอายุแล้ว พิมพ์ขอเลื่อนนัดใหม่ได้ค่ะ"
NO_CANCEL_TOOL = "ผู้ช่วยยกเลิกให้ไม่ได้ค่ะ"
MSG_REFUND_BANK = "ระยะเวลาที่เงินเข้าบัญชีขึ้นกับธนาคารผู้ออกบัตร"  # CR-19 (Q-65)
MSG_MODEL_NOT_ACCEPTED = "ผู้ช่วยปิดชั่วคราว (รุ่นโมเดลยังไม่ผ่านการตรวจ) กรุณาติดต่อเจ้าหน้าที่"


# ---- REQ-AI-022 ปุ่มหยุด: ค่าอยู่ในฐานข้อมูล เปลี่ยนได้ทันที ไม่ต้อง deploy ----

def model_accepted() -> bool:
    """CR-19 REQ-AI-023 (ชั้นที่ 3): รุ่นโมเดลที่ใช้อยู่ต้องเป็นรุ่นที่ผ่าน eval ล่าสุด (ASSISTANT_ACCEPTED_MODEL)
    เปลี่ยนโมเดลหรือสลับเป็นตัวจริงโดยยังไม่รัน eval ผู้ช่วยปิดเอง ไม่ต้องรอให้คนจำได้
    มีผลในโหมด production (ระบบจริงและเครื่องตรวจรับ) โหมด test และ development ลองโมเดลอื่นได้ เพื่อวัดก่อนรับ"""
    if config.app_env() != "production":
        return True
    return get_llm().model_version == config.assistant_accepted_model()


def is_enabled(db) -> bool:
    row = db.get(AssistantSetting, "enabled")
    return (row is None or row.value == "true") and model_accepted()


def set_enabled(db, enabled: bool, now: datetime) -> None:
    row = db.get(AssistantSetting, "enabled")
    if row is None:
        db.add(AssistantSetting(key="enabled", value="true" if enabled else "false", updated_at=now))
    else:
        row.value, row.updated_at = ("true" if enabled else "false"), now
    db.commit()


def disabled_out() -> dict:
    return {"disabled": True, "reply": MSG_DISABLED, "call_center_tel": config.call_center_tel()}


def start(db, customer_id: int, now: datetime) -> dict:
    if not is_enabled(db):
        return disabled_out()
    conv = AssistantConversation(customer_id=customer_id, started_at=now)
    db.add(conv)
    db.commit()
    return {"disabled": False, "conversation_id": conv.id, "greeting": GREETING}


# ---- คำตอบสำรองที่สร้างจากข้อมูลด้วยโค้ด (ใช้เมื่อรั้วขาออกกันคำตอบของ LLM REQ-AI-008) ----

def fallback(intent: str, d: dict) -> str:
    sid, when = d["job_id"], f"{d['date']} {d['time']} น."
    if intent == "eta":
        return f"ขออภัย ยังไม่มีข้อมูลเวลาที่ช่างจะถึงค่ะ งาน #{sid} นัดไว้ {when}"
    if intent == "technician_name":
        return f"ช่างของงาน #{sid} คือคุณ{d['technician']}ค่ะ นัดไว้ {when}"
    if intent == "cancel":
        c = d["cancel"]
        if c["already_closed"]:
            return f"งาน #{sid} ถูกยกเลิกไปแล้วค่ะ"
        if not c["allowed"]:
            return f"งาน #{sid} ยกเลิกตอนนี้ไม่ได้ค่ะ {c['message']}"
        return (f"ถ้ายกเลิกตอนนี้ ระบบคิดยอดคืน {c['refund_amount']} บาท (แถว {c['rule']}) กดยกเลิกได้ที่หน้า "
                f"ยกเลิกการจอง {NO_CANCEL_TOOL}")
    if intent == "reschedule_policy":
        r = d["reschedule"]
        return (f"เลื่อนนัดได้ไม่เกิน {r['max']} ครั้งต่องาน ต้องเหลือเวลาก่อนนัดเดิมไม่น้อยกว่า {r['min_hours']} ชั่วโมง "
                f"งาน #{sid} เลื่อนไปแล้ว {r['used']} ครั้ง")
    if intent == "refund_timing":
        # CR-19 (Q-65): บอกว่าระยะเวลาขึ้นกับธนาคารผู้ออกบัตร ข้อความเดียวกับประโยคสำหรับลูกค้าใน policies/refund-timing.md
        return f"เงินคืนเข้าช่องทางที่ชำระมัดจำค่ะ ขออภัย ยังไม่มีข้อมูลจำนวนวันที่เงินจะเข้า {MSG_REFUND_BANK}"
    text = f"งาน #{sid} สถานะ \"{d['status_th']}\" นัดไว้ {when}"
    return text + (" ยังไม่มีข้อมูลเวลาที่ช่างจะถึง" if d["status"] == "en_route" else "")


def _out(turn: AssistantTurn | None, reply: str, outcome: str, intent: str, **extra) -> dict:
    out = {"disabled": False, "turn_id": turn.id if turn else None, "reply": reply, "outcome": outcome,
           "intent": intent, "sources": [], "proposal": None, "ticket_id": None, "slots": []}
    out.update(extra)
    return out


def handle_message(db, conv: AssistantConversation, text: str, now: datetime, version: str | None = None,
                   llm: LLM | None = None, use_output_guard: bool = True) -> dict:
    t0 = time.perf_counter()
    version = version or config.assistant_prompt_version()
    llm = llm or get_llm()

    def log_turn(intent, outcome, reply, facts=None, model="none", guard_result="not_checked"):
        return records.write_turn(db, conv, text, intent, outcome, facts, version, model, guard_result, reply, now,
                                  (time.perf_counter() - t0) * 1000)

    def stop(intent, reason, reply, outcome="handoff", job_id=None, **extra):
        turn = log_turn(intent, outcome, reply)
        ticket = handoff.create_ticket(db, conv, reason, intent, now, turn.id, job_id)
        db.commit()
        return _out(turn, reply, outcome, intent, ticket_id=ticket.id, handoff_reason=reason, **extra)

    # ขั้น 1 เปิดไหม เพดานไหม (REQ-AI-022, REQ-AI-009)
    if not is_enabled(db):
        return disabled_out()
    if len(text) > config.ASSISTANT_MAX_MESSAGE_CHARS:
        turn = log_turn("too_long", "limited", MSG_TOO_LONG.format(n=config.ASSISTANT_MAX_MESSAGE_CHARS))
        db.commit()
        return _out(turn, turn.answer, "limited", "too_long")
    if not guard.limiter.allow(conv.customer_id, now):
        turn = log_turn("rate_limited", "limited", MSG_LIMIT)
        db.commit()
        return _out(turn, MSG_LIMIT, "limited", "rate_limited")
    # ขั้น 2 รั้วขาเข้าและจำแนกความตั้งใจ (REQ-AI-008, REQ-AI-005, REQ-AI-007, REQ-AI-012)
    if guard.detect_injection(text):
        turn = log_turn("injection", "refused", MSG_INJECTION)
        db.commit()
        return _out(turn, MSG_INJECTION, "refused", "injection")
    intent = classify(text, version)
    if intent.name == "unclear":
        return stop("unclear", "unclear_intent", MSG_UNCLEAR)
    if intent.name == "handoff_request":
        return stop("handoff_request", "customer_request", MSG_HANDOFF)
    if intent.name == "out_of_scope":
        return stop("out_of_scope", "out_of_scope", MSG_OUT_OF_SCOPE)
    if intent.name in FORBIDDEN:
        turn = log_turn(intent.name, "refused", MSG_FORBIDDEN[intent.name])
        db.commit()
        return _out(turn, MSG_FORBIDDEN[intent.name], "refused", intent.name)
    # ขั้น 3 ค้นข้อมูลจริง เฉพาะงานของผู้ถาม (REQ-DAT-010, REQ-SEC-010)
    job, found = retrieval.resolve_job(db, conv.customer_id, intent.job_id, conv.context_job_id)
    if found == "not_owned":
        audit.deny(db, "customer", conv.customer_id, intent.job_id, "POST /assistant/messages", now)
        turn = log_turn(intent.name, "not_found", MSG_NOT_FOUND)
        db.commit()
        return _out(turn, MSG_NOT_FOUND, "not_found", intent.name)
    if job is None:
        turn = log_turn(intent.name, "no_data", MSG_NO_JOB)
        db.commit()
        return _out(turn, MSG_NO_JOB, "no_data", intent.name)
    conv.context_job_id = job.id
    if intent.name == "reschedule":
        return _reschedule(db, conv, job, text, now, version, llm, log_turn, stop)
    facts = retrieval.job_facts(db, job, intent.name, now, intent.normalized)
    if not facts.is_fresh(now):  # REQ-DAT-010 บรรทัดที่ 3
        facts = retrieval.job_facts(db, job, intent.name, now, intent.normalized)
    # ขั้น 4 LLM แต่งคำตอบ (กล่อง AI) ได้ข้อความสั่งรุ่นนี้ ข้อมูลที่ค้นมา และคำถาม เท่านั้น
    # CR-09 ข้อ ค1 (Q-56 SH-05): ข้อความของลูกค้าที่ส่งให้ LLM ปิดบังเบอร์ อีเมล เลขบัตรก่อน
    req = LLMRequest(prompts.system_prompt(version), version, intent.name, mask_text(text), facts.data,
                     [{"id": p["id"], "text": p["text"]} for p in facts.policies])
    try:
        reply = llm.generate(req)
    except Exception as exc:  # GAP-50 (REQ-QA-010): LLM ไม่ตอบหรือตอบผิด ใช้คำตอบสำรองจากโค้ด ไม่ตอบ 500
        log_event(_log, "llm_error", conversation_id=conv.id, intent=intent.name, reason=type(exc).__name__,
                  model_version=getattr(llm, "model_version", ""))
        reply = LLMReply("", getattr(llm, "model_version", ""))
    answer = reply.text
    # ขั้น 5 รั้วขาออก (REQ-AI-008)
    reasons = (guard.check_answer(answer, facts, version) if use_output_guard else []) if answer else ["llm_error"]
    guard_result = "passed" if not reasons else "blocked:" + ",".join(reasons)
    if reasons:
        answer = fallback(intent.name, facts.data)
    if intent.name == "cancel" and NO_CANCEL_TOOL not in answer and any(w in text for w in ("ให้เลย", "ยกเลิกให้")):
        answer += " " + NO_CANCEL_TOOL  # ASI01: ไม่มีเครื่องมือยกเลิก ชี้ไปที่หน้ายกเลิกการจอง
    outcome = "no_data" if intent.name in ("eta", "refund_timing") else "answered"
    turn = log_turn(intent.name, outcome, answer, facts.data, reply.model_version, guard_result)
    db.commit()
    return _out(turn, answer, outcome, intent.name, sources=facts.sources, guard=guard_result,
                raw_answer=reply.text, facts=facts.data)


def _reschedule(db, conv, job, text, now, version, llm, log_turn, stop) -> dict:
    """agent เลื่อนนัด (REQ-AI-010 ถึง 012) ไม่มีข้อมูลใดเปลี่ยนในขั้นนี้ เปลี่ยนได้หลัง confirm() เท่านั้น"""
    r = agent.plan_reschedule(db, conv, job, text, now)
    if r["outcome"] == "beyond_rule":
        return stop("reschedule", "beyond_rule", r["reply"], job_id=job.id, rule_reason=r["reason"])
    if r["outcome"] == "tool_error":
        return stop("reschedule", "tool_error", r["reply"], job_id=job.id)
    slots = [{"slot_id": s.id, "start": s.start.isoformat()} for s in r.get("slots", [])][:3]
    if r["outcome"] == "clarify":
        turn = log_turn("reschedule", "clarify", r["reply"], {"job_id": job.id, "slots": slots})
        db.commit()
        return _out(turn, r["reply"], "clarify", "reschedule", slots=slots)
    p = r["proposal"]
    out = agent.proposal_out(db, p)
    turn = log_turn("reschedule", "proposal", r["reply"], out)
    db.commit()
    return _out(turn, r["reply"], "proposal", "reschedule", proposal=out)


def _proposal(db, proposal_id: int, customer_id: int):
    p = db.get(AssistantProposal, proposal_id)
    if p is None or p.customer_id != customer_id:
        return None
    return p


def confirm(db, proposal_id: int, customer_id: int, now: datetime, version: str | None = None) -> dict:
    """ลูกค้ากด "ยืนยันเลื่อนนัด" (ระดับ 2) เรียกเครื่องมือเลื่อนนัดครั้งเดียว ด้วยค่าเดียวกับสรุป"""
    version = version or config.assistant_prompt_version()
    p = _proposal(db, proposal_id, customer_id)
    if p is None:
        return {"ok": False, "reply": MSG_NOT_FOUND, "outcome": "not_found"}
    conv = db.get(AssistantConversation, p.conversation_id)
    if p.status != "pending":
        return {"ok": False, "reply": MSG_EXPIRED, "outcome": p.status}
    if now > p.expires_at:
        p.status, p.decided_at = "expired", now
        db.commit()
        return {"ok": False, "reply": MSG_EXPIRED, "outcome": "expired"}
    p.status = "confirming"
    first_turn = db.scalars(select(AssistantTurn).where(AssistantTurn.conversation_id == conv.id,
                                                        AssistantTurn.intent == "reschedule")
                            .order_by(AssistantTurn.id.desc())).first()
    asked = first_turn.masked_text if first_turn else ""
    interpretation = f"เลื่อนงาน #{p.job_id} จาก {agent.fmt(p.old_start)} เป็น {agent.fmt(p.new_start)} ช่างคนเดิม"
    args = {"job_id": p.job_id, "new_slot_id": p.new_slot_id, "reference": f"P-{p.id}"}
    model = get_llm().model_version
    try:
        tools.call("reschedule_job", db, customer_id, now, proposal=p)
    except tools.ToolTimeout:
        db.rollback()
        p = db.get(AssistantProposal, proposal_id)
        p.status, p.decided_at = "unknown", now
        records.write_action(db, p, asked, interpretation, "reschedule_job", args, "unknown", version, model, now)
        t = handoff.create_ticket(db, conv, "tool_error", "reschedule", now, None, p.job_id)
        db.commit()
        return {"ok": False, "reply": MSG_TOOL_TIMEOUT, "outcome": "unknown", "ticket_id": t.id}
    except RescheduleRejected as e:
        p.status, p.decided_at = "failed", now
        records.write_action(db, p, asked, interpretation, "reschedule_job", args, f"rejected:{e.reason}", version,
                             model, now)
        ticket_id = None
        if e.beyond_rule:
            ticket_id = handoff.create_ticket(db, conv, "beyond_rule", "reschedule", now, None, p.job_id).id
        db.commit()
        return {"ok": False, "reply": e.message, "outcome": "failed", "ticket_id": ticket_id}
    except tools.ToolError:
        p.status, p.decided_at = "failed", now
        t = handoff.create_ticket(db, conv, "tool_error", "reschedule", now, None, p.job_id)
        db.commit()
        return {"ok": False, "reply": MSG_TOOL_TIMEOUT, "outcome": "failed", "ticket_id": t.id}
    p.status, p.decided_at = "confirmed", now
    records.write_action(db, p, asked, interpretation, "reschedule_job", args, "rescheduled", version, model, now)
    db.commit()
    return {"ok": True, "outcome": "confirmed", "job_id": p.job_id, "new_start": p.new_start.isoformat(),
            "reply": MSG_RESCHEDULED.format(job=p.job_id, when=agent.fmt(p.new_start))}


def decline(db, proposal_id: int, customer_id: int, now: datetime) -> dict:
    """ลูกค้ากด "ไม่ใช่" ครบ 2 ครั้งในบทสนทนาเดียว = หยุดและส่งต่อ (REQ-AI-012 เงื่อนไขที่ 3)"""
    p = _proposal(db, proposal_id, customer_id)
    if p is None or p.status != "pending":
        return {"ok": False, "reply": MSG_EXPIRED, "outcome": "not_pending"}
    conv = db.get(AssistantConversation, p.conversation_id)
    p.status, p.decided_at = "declined", now
    conv.declines += 1
    if conv.declines >= config.ASSISTANT_MAX_DECLINES:
        t = handoff.create_ticket(db, conv, "declined_twice", "reschedule", now, None, p.job_id)
        db.commit()
        return {"ok": True, "outcome": "handoff", "reply": MSG_DECLINED + " " + MSG_HANDOFF, "ticket_id": t.id}
    db.commit()
    return {"ok": True, "outcome": "declined", "reply": MSG_DECLINED}


def request_handoff(db, conv: AssistantConversation, now: datetime) -> dict:
    t = handoff.create_ticket(db, conv, "customer_request", "handoff_request", now, None, conv.context_job_id)
    db.commit()
    return {"ticket_id": t.id, "reply": MSG_HANDOFF}


def report(db, turn_id: int, customer_id: int, now: datetime) -> dict | None:
    """ปุ่ม "คำตอบนี้ไม่ถูกต้อง" (REQ-AI-022) สร้างตั๋วร้องเรียน ตอบกลับภายใน 2 วันทำการ"""
    turn = db.get(AssistantTurn, turn_id)
    if turn is None or turn.customer_id != customer_id:
        return None
    conv = db.get(AssistantConversation, turn.conversation_id)
    t = handoff.create_ticket(db, conv, "complaint", turn.intent, now, turn.id, conv.context_job_id)
    db.commit()
    return {"ticket_id": t.id, "reply_due_at": t.reply_due_at.isoformat(),
            "reply": "รับเรื่องแล้วค่ะ เจ้าหน้าที่จะตอบกลับภายใน 2 วันทำการ"}
