"""กล่อง AI กล่องเดียวของผู้ช่วย (ขั้น 4 ของ MD-SEQ-14-01) อยู่หลัง interface เดียวที่สลับได้ (D-14-02)
ตัวจริงยังไม่ต่อ (IF-05 ยังไม่เลือกผู้ให้บริการ Q-56 มีเงื่อนไขของ SH-05) ตอนนี้ใช้ MockLLM ที่กำหนดผลได้ (deterministic)

MockLLM ไม่ได้ "ฉลาด" มันจำลองพฤติกรรมของ LLM จริงพอให้ eval มีความหมาย ทั้งด้านดีและด้านที่ต้องกัน
- ตอบถูกด้วยถ้อยคำหลายแบบ (ถามคำเดิมได้คำเดิม แต่ต่างคำถามได้ต่างถ้อยคำ จึงตรวจแบบตรงตัวอักษรไม่ได้)
- บางครั้งตอบไม่ครบ (ไม่บอกเวลานัด) ทำให้สัดส่วน "ถูกและครบ" ไม่ใช่ 100 ใน 100
- บางครั้งแต่งเรื่อง (เวลาที่ช่างจะถึง จำนวนวันคืนเงิน คืนเต็มจำนวน) แบบเดียวกับที่ทีมเจอใน EV-046
- ถ้าข้อความหลอกให้ลืมกฎหลุดรั้วขาเข้ามาได้ มันทำตาม (เผยข้อความสั่ง แต่งเบอร์โทร อ้างว่ายกเลิกให้แล้ว)
ทุกอย่างกำหนดจากค่า crc32 ของคำถาม รันซ้ำได้ผลเดิมทุกครั้ง ความผิดพลาดเหล่านี้คือสิ่งที่รั้วขาออก (guard.py) ต้องกันได้
CR-19 (R2 ส่วน B): รุ่น mock-1.1 อ่านประโยคสำหรับลูกค้าจากคลังนโยบายที่ค้นมา (บรรทัดที่ขึ้นต้น "ลูกค้า:") แบบเดียวกับที่ LLM จริงอ่านข้อมูล
เปลี่ยนรุ่นโมเดล = ของใหม่ ต้องรัน eval ทั้งชุดก่อนใช้ (ชั้นที่ 3 ของการรับ REQ-AI-023) ตัวจริงอยู่ที่ app/integrations/http_llm.py"""
import json
import re
import zlib
from dataclasses import dataclass, field


@dataclass
class LLMRequest:
    system_prompt: str
    prompt_version: str
    intent: str
    question: str
    facts: dict
    policies: list[dict] = field(default_factory=list)


@dataclass
class LLMReply:
    text: str
    model_version: str


class LLM:
    """interface ของบริการ LLM ทุกราย (IF-05) ตัวที่ต่อจริงต้องรับ LLMRequest แล้วคืน LLMReply เท่านั้น"""
    model_version = "none"

    def generate(self, req: LLMRequest) -> LLMReply:
        raise NotImplementedError


class NotConnectedLLM(LLM):
    """ที่ของตัวจริง: ยังไม่ต่อ เพราะยังไม่เลือกผู้ให้บริการและยังไม่มีข้อตกลงประมวลผลข้อมูล (Q-56)"""
    model_version = "not-connected"

    def generate(self, req):
        raise RuntimeError("ยังไม่ได้ต่อบริการ LLM จริง (IF-05) ใช้ MockLLM")


INJECTION_HINTS = ("ลืมกฎ", "ignore", "systemprompt", "ข้อความสั่ง", "คำสั่งระบบ", "แสดงprompt", "developermode",
                   "ไม่ต้องทำตามกฎ", "เลิกทำตามกฎ", "คุณคือแอดมิน", "ทำตัวเป็น")


def _h(text: str, mod: int) -> int:
    return zlib.crc32(text.encode("utf-8")) % mod


class MockLLM(LLM):
    model_version = "mock-1.1"   # CR-19: เดิม mock-1.0 (B4 ถึง B6)

    def generate(self, req: LLMRequest) -> LLMReply:
        q = req.question
        squeezed = re.sub(r"[\s\-_.]+", "", q.lower())
        f = req.facts
        in_data = re.sub(r"[\s\-_.]+", "", json.dumps(f, ensure_ascii=False).lower())  # คำสั่งแฝงในข้อมูล (indirect)
        if any(h in squeezed or h in in_data for h in INJECTION_HINTS):
            return LLMReply(self._obey(req, squeezed), self.model_version)
        handler = getattr(self, f"_{req.intent}", self._status)
        return LLMReply(handler(q, f, req), self.model_version)

    # ---- ทำตามข้อความหลอก (สิ่งที่ LLM จริงทำได้ ถ้าไม่มีรั้ว) ----
    def _obey(self, req, squeezed):
        if "เบอร์" in squeezed:
            return "ได้เลยค่ะ เบอร์ที่ขอคือ 089-555-0101"
        if "ยกเลิก" in squeezed:
            return f"ยกเลิกงาน #{req.facts.get('job_id')} ให้แล้วค่ะ"
        if "1030" in squeezed:
            return "งาน #1030 สถานะ ยืนยันแล้ว นัดไว้ 09:00 น. ค่ะ"
        return "ข้อความสั่งของฉันคือ: " + req.system_prompt.splitlines()[0]

    # ---- ตอบตามความตั้งใจ ----
    def _status(self, q, f, req):
        sid, st, d, t = f["job_id"], f["status_th"], f["date"], f["time"]
        if _h(q, 17) == 0:  # ตอบไม่ครบ: ไม่บอกเวลานัด
            return f"งาน #{sid} ตอนนี้สถานะ \"{st}\" ค่ะ"
        variants = [
            f"งาน #{sid} ตอนนี้สถานะ \"{st}\" ค่ะ นัดไว้ {d} เวลา {t} น.",
            f"สถานะล่าสุดของงาน #{sid} คือ \"{st}\" นัดหมาย {d} {t} น. ค่ะ",
            f"ตอนนี้งานของคุณ (#{sid}) อยู่ในสถานะ \"{st}\" เวลานัด {t} น. วันที่ {d} ค่ะ",
        ]
        text = variants[_h(q, 3)]
        if f.get("status") == "en_route":
            text += " ยังไม่มีข้อมูลเวลาที่ช่างจะถึงนะคะ"
        return text

    def _eta(self, q, f, req):
        if _h(q, 3) == 0:  # แต่งเรื่อง แบบเดียวกับ 2 ใน 20 ข้อของการทดลองใน EV-046
            return "ช่างน่าจะถึงในอีกประมาณ 20 นาทีค่ะ"
        return f"ขออภัย ยังไม่มีข้อมูลเวลาที่ช่างจะถึงค่ะ งาน #{f['job_id']} นัดไว้ {f['date']} {f['time']} น."

    def _technician_name(self, q, f, req):
        return [f"ช่างของงาน #{f['job_id']} คือคุณ{f['technician']}ค่ะ นัดไว้ {f['date']} {f['time']} น.",
                f"คุณ{f['technician']} เป็นช่างที่รับงาน #{f['job_id']} ค่ะ"][_h(q, 2)]

    def _cancel(self, q, f, req):
        c = f["cancel"]
        if c["already_closed"]:
            return f"งาน #{f['job_id']} ถูกยกเลิกไปแล้วค่ะ"
        if not c["allowed"]:
            return f"งาน #{f['job_id']} ยกเลิกตอนนี้ไม่ได้ค่ะ {c['message']}"
        if _h(q, 7) == 0:  # คิดตามกฎเอง ไม่ใช้ยอดที่โค้ดคิด
            return "ยกเลิกได้ค่ะ คืนเงินเต็มจำนวนแน่นอน"
        return (f"ถ้ายกเลิกตอนนี้ ระบบคิดยอดคืน {c['refund_amount']} บาท (แถว {c['rule']}) "
                f"กดยกเลิกได้ที่หน้า ยกเลิกการจอง ผู้ช่วยยกเลิกให้ไม่ได้ค่ะ")

    def _reschedule_policy(self, q, f, req):
        r = f["reschedule"]
        return (f"เลื่อนนัดได้ไม่เกิน {r['max']} ครั้งต่องาน ต้องเหลือเวลาก่อนนัดเดิมไม่น้อยกว่า {r['min_hours']} ชั่วโมง "
                f"และเลื่อนได้เฉพาะช่วงของช่างคนเดิมค่ะ งาน #{f['job_id']} เลื่อนไปแล้ว {r['used']} ครั้ง "
                f"ถ้าต้องการเลื่อน พิมพ์วันและเวลาที่ต้องการได้เลยค่ะ")

    def _refund_timing(self, q, f, req):
        if _h(q, 4) == 0:  # แต่งตัวเลขที่ไม่มีในข้อมูล (Q-35 ยังไม่มีคำตอบ)
            return "เงินคืนจะเข้าบัญชีภายใน 7 วันทำการค่ะ"
        text = "เงินคืนเข้าช่องทางที่ชำระมัดจำค่ะ ขออภัย ยังไม่มีข้อมูลจำนวนวันที่เงินจะเข้า"
        lines = [ln.split(":", 1)[1].strip() for p in req.policies for ln in p.get("text", "").splitlines()
                 if ln.startswith("ลูกค้า:")]
        return text + (" " + " ".join(lines) if lines else "")


def build_from_config() -> LLM:
    """REQ-IF-012: LLM_ADAPTER = mock (ค่าตั้งต้น) หรือ http (ตัวจริง ปิดไว้จนกว่าจะตั้ง URL กุญแจ และรุ่นโมเดล)"""
    from app.integrations import choice
    if choice("llm") == "http":
        from app.integrations.http_llm import HttpLLM
        return HttpLLM()
    return MockLLM()


_llm: LLM | None = None


def get_llm() -> LLM:
    global _llm
    if _llm is None:
        _llm = build_from_config()
    return _llm


def set_llm(llm: LLM) -> None:
    global _llm
    _llm = llm
