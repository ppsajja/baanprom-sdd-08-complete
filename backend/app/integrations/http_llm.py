"""CR-19 ตัวจริงของ IF-05 บริการ LLM (ปิดไว้) ยังไม่เลือกผู้ให้บริการ (Won't ใน R2 ดู CR-19) เขียนตามสัญญา IF-05 ใน docs/srs/models.md ส่วน 9
ส่งเฉพาะข้อความสั่ง ข้อมูลที่ค้นมา (ช่องที่ SH-05 อนุญาต Q-56) และคำถามที่ปิดบังแล้ว (REQ-DAT-010 บรรทัดที่ 4)
รุ่นโมเดลคือ http:<LLM_MODEL> ซึ่งไม่ตรงกับรุ่นที่ผ่าน eval (ASSISTANT_ACCEPTED_MODEL) ผู้ช่วยจึงปิดเองจนกว่าจะรัน eval ผ่าน (REQ-AI-023)"""
import json

import httpx

from app import config
from app.assistant.llm import LLM, LLMReply, LLMRequest
from app.integrations import AdapterNotConfigured, missing, setting


class HttpLLM(LLM):
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport

    @property
    def model_version(self) -> str:
        return f"http:{setting('LLM_MODEL', 'none')}"

    def generate(self, req: LLMRequest) -> LLMReply:
        if missing("llm"):
            raise AdapterNotConfigured("IF-05 ยังไม่ตั้ง " + ", ".join(missing("llm")))
        content = json.dumps({"intent": req.intent, "facts": req.facts, "policies": req.policies,
                              "question": req.question}, ensure_ascii=False)
        body = {"model": setting("LLM_MODEL"), "system": req.system_prompt, "max_tokens": 400,
                "messages": [{"role": "user", "content": content}]}
        with httpx.Client(timeout=config.EVAL_P95_SECONDS * 2, transport=self.transport,
                          headers={"Authorization": f"Bearer {setting('LLM_API_KEY')}"}) as c:
            r = c.post(setting("LLM_API_URL"), json=body)
        r.raise_for_status()
        return LLMReply(r.json()["text"], self.model_version)
