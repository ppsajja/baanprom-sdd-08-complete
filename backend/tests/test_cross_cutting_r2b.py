"""AC-00-12 ถึง AC-00-16 จาก cross-cutting.feature v1.2 (specs/000-shared, CR-18) ระบบภายนอกที่สลับเป็นของจริงได้ด้วยค่าตั้ง
REQ-IF-012 (interface และตัวจริงตามสัญญา) REQ-OP-009 (รายงานตัวที่ใช้ /ready) REQ-QA-010 รุ่น 1.4 (แผนที่ไม่ตอบ)
REQ-SEC-015 (กุญแจแยกบทบาท GAP-32) และ AC-00-16 (GAP-39 ตัวนับนับการค้นหาจริง)
test ทุกตัวในไฟล์นี้ห้ามออกเครือข่าย: ตัวจริงใช้ httpx.MockTransport และ fixture no_network กันการเรียกจริงทุกทาง"""
import json
from datetime import timedelta

import httpx
import pytest

from app import maps
from app.integrations import AdapterNotConfigured, status
from app.integrations.http_llm import HttpLLM
from app.integrations.http_map import HttpMap
from app.integrations.http_messaging import HttpSmsSender, LineMessagingSender
from app.integrations.http_payment import HttpGateway
from app.assistant.llm import LLMRequest
from app.notify.queue import NotifierTimeout
from app.ops.metrics import metrics
from app.payments.gateway import GatewayTimeout
from tests.conftest import NOW, OPS, H, book

KINDS = ("payment", "sms", "line", "map", "llm")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(self, request):
        raise AssertionError(f"test ออกเครือข่ายจริง: {request.url}")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


def recorder(reply=None, status=200, timeout=False):
    seen = []

    def handler(request: httpx.Request):
        seen.append(request)
        if timeout:
            raise httpx.ReadTimeout("ไม่ตอบ", request=request)
        return httpx.Response(status, json=reply if reply is not None else {"status": "approved"})
    return httpx.MockTransport(handler), seen


def settings(monkeypatch, kind):
    for k in {"payment": ("PAYMENT_API_URL", "PAYMENT_API_KEY"), "sms": ("SMS_API_URL", "SMS_API_KEY"),
              "line": ("LINE_CHANNEL_TOKEN", "LINE_CHANNEL_SECRET"), "map": ("MAP_API_URL", "MAP_API_KEY"),
              "llm": ("LLM_API_URL", "LLM_API_KEY", "LLM_MODEL")}[kind]:
        monkeypatch.setenv(k, "https://provider.example.invalid/v1" if k.endswith("URL") else f"{k.lower()}-value")


# รองรับ AC-00-12 (REQ-IF-012 REQ-OP-009): ค่าตั้งต้นเป็นตัวจำลองทุกตัว เลือกตัวจริงที่ยังตั้งค่าไม่ครบ /ready ตอบ 503
def test_AC_00_12_adapters_switch_by_config(client, monkeypatch):
    rows = client.get("/ops/integrations", headers=OPS).json()
    assert [(r["kind"], r["interface"], r["mock"], r["configured"]) for r in rows] == [
        ("payment", "IF-01", True, True), ("sms", "IF-02", True, True), ("line", "IF-02", True, True),
        ("map", "IF-03", True, True), ("llm", "IF-05", True, True)]
    assert client.get("/ready").status_code == 200
    monkeypatch.setenv("PAYMENT_ADAPTER", "http")
    monkeypatch.setenv("MAP_ADAPTER", "http")
    r = client.get("/ready")
    assert r.status_code == 503 and r.json()["integrations_not_configured"] == ["payment", "map"]
    settings(monkeypatch, "payment")
    settings(monkeypatch, "map")
    assert client.get("/ready").status_code == 200
    by = {x["kind"]: x for x in status()}
    assert by["payment"]["adapter"] == "http" and by["payment"]["mock"] is False and by["payment"]["missing_settings"] == []
    assert "value" not in json.dumps(client.get("/ops/integrations", headers=OPS).json())  # ไม่แสดงค่าของกุญแจ


# รองรับ AC-00-13 (REQ-IF-012 REQ-QA-010): ตัวจริงเรียกตามสัญญา ส่ง reference เดิม ไม่ตอบได้ข้อผิดพลาดชนิดเดียวกับตัวจำลอง
def test_AC_00_13_real_adapters_follow_contract_without_network(monkeypatch):
    with pytest.raises(AdapterNotConfigured):
        HttpGateway().authorize("BP-1-a", 350, 30)
    for kind in KINDS:
        settings(monkeypatch, kind)
    t, seen = recorder({"status": "approved"})
    g = HttpGateway(transport=t)
    assert g.authorize("BP-1-a", 350, 30).status == "approved"
    assert g.refund("BP-1-a", 350, 30).status == "approved"
    assert [(r.method, r.url.path) for r in seen] == [("POST", "/v1/payments/authorize"), ("POST", "/v1/payments/BP-1-a/refunds")]
    assert seen[0].headers["Idempotency-Key"] == "BP-1-a" and seen[1].headers["Idempotency-Key"] == "BP-1-a-refund"
    assert json.loads(seen[0].content) == {"reference": "BP-1-a", "amount": 350}
    with pytest.raises(GatewayTimeout):
        HttpGateway(transport=recorder(timeout=True)[0]).authorize("BP-1-a", 350, 30)
    t, seen = recorder({})
    HttpSmsSender(transport=t).send("081-234-5678", "ทดสอบ", 10)
    LineMessagingSender(transport=t).push("U-1", "ทดสอบ", 10)
    assert [r.url.path for r in seen] == ["/v1/messages", "/v2/bot/message/push"]
    assert json.loads(seen[1].content) == {"to": "U-1", "messages": [{"type": "text", "text": "ทดสอบ"}]}
    with pytest.raises(NotifierTimeout):
        HttpSmsSender(transport=recorder(timeout=True)[0]).send("081", "x", 10)
    t, seen = recorder({"lat": 13.73, "lng": 100.52})
    assert HttpMap(transport=t).geocode("บางรัก") == (13.73, 100.52)
    with pytest.raises(maps.MapTimeout):
        HttpMap(transport=recorder(timeout=True)[0]).distances_km((13.7, 100.5), [(13.8, 100.5)])
    t, seen = recorder({"text": "สวัสดีค่ะ"})
    llm = HttpLLM(transport=t)
    reply = llm.generate(LLMRequest("ระบบ", "P-1.1", "status", "งานถึงไหน", {"job_id": 1}))
    assert reply.text == "สวัสดีค่ะ" and reply.model_version == "http:llm_model-value"
    assert "081" not in seen[0].content.decode()


# รองรับ AC-00-14 (REQ-QA-010 รุ่น 1.4 บรรทัดที่ 5): แผนที่ไม่ตอบ การค้นหายังได้ผลด้วยระยะเส้นตรง และบันทึกเหตุ
def test_AC_00_14_map_down_search_uses_straight_line(client, db, seed, caplog):
    maps.set_map(maps.MockMap(mode="down"))
    try:
        r = client.get(f"/technicians?now={NOW.isoformat()}&category=ประปา&address_id={seed['addr'].id}",
                       headers=H("customer", seed["somchai"].id))
    finally:
        maps.set_map(None)
    assert r.status_code == 200 and [t["name"] for t in r.json()] == ["ประสิทธิ์"]   # ไกลมาก (40 กม.) ยังถูกกัน
    assert '"event": "map_fallback"' in caplog.text


# รองรับ AC-00-15 (REQ-SEC-015 ปิด GAP-32): กุญแจแยกบทบาท ใช้ได้เฉพาะงานของบทบาทนั้น
def test_AC_00_15_role_keys(client, db, seed, monkeypatch):
    monkeypatch.setenv("CALL_CENTER_TOKEN", "cc-key")
    monkeypatch.setenv("FINANCE_TOKEN", "fin-key")
    cc, fin = {"X-Call-Center-Token": "cc-key"}, {"X-Finance-Token": "fin-key"}
    job_id = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id).json()["job_id"]
    assert client.get(f"/jobs/{job_id}", headers=cc).status_code == 200            # call center อ่านงาน
    assert client.post("/call-center/assistant/switch", json={"enabled": False}, headers=cc).json()["enabled"] is False
    assert client.get("/assistant/status").json()["enabled"] is False
    assert client.post("/call-center/assistant/switch", json={"enabled": True}, headers=OPS).status_code == 403
    assert client.post("/call-center/assistant/switch", json={"enabled": True}, headers=fin).status_code == 403
    assert client.get("/finance/refunds/follow-up", headers=cc).status_code == 403
    assert client.get(f"/jobs/{job_id}", headers=fin).status_code == 401           # Finance ไม่ได้อ่านงานของลูกค้า
    monkeypatch.setenv("CALL_CENTER_TOKEN", "")
    assert client.post("/call-center/assistant/switch", json={"enabled": True}, headers={"X-Call-Center-Token": ""}).status_code == 403


# รองรับ AC-00-16 (REQ-OP-005 GAP-39): ตัวนับนับการค้นหาที่เข้าสู่ระบบแล้วและได้ผลจริง แยกจากคำขอที่ถูกปฏิเสธ
def test_AC_00_16_metrics_count_real_searches(client, db, seed):
    metrics.clear()
    for _ in range(3):
        assert client.get(f"/technicians?category=ประปา&address_id={seed['addr'].id}&now={NOW.isoformat()}",
                          headers=H("customer", seed["somchai"].id)).status_code == 200
    client.get(f"/technicians?category=ประปา&address_id={seed['addr'].id}")   # ไม่ได้เข้าสู่ระบบ 401
    client.get(f"/technicians?category=แอร์&address_id={seed['addr'].id}&now={NOW.isoformat()}",
               headers=H("customer", seed["somchai"].id))                      # ไม่มีช่างแอร์ ผลว่าง
    rows = [r for r in client.get("/metrics").json() if r["endpoint"] == "GET /technicians"]
    assert sum(r["requests"] for r in rows) == 5 and sum(r["empty_results"] for r in rows) == 1


class _DownLLM:
    """LLM ตัวจริงที่ไม่ตอบ (เหมือน httpx หมดเวลา)"""
    model_version = "http:test"

    def generate(self, req):
        raise httpx.ReadTimeout("no answer")


# รองรับ AC-00-13 บรรทัดสุดท้าย (REQ-QA-010 GAP-50): LLM ไม่ตอบ ผู้ช่วยตอบด้วยคำตอบสำรองจากโค้ด ไม่ตอบ 500 และบันทึกเหตุ
def test_AC_00_13_llm_down_assistant_uses_code_fallback(client, db, seed, caplog):
    from app.assistant.llm import MockLLM, set_llm
    from tests.test_assistant import booked_job, say, start
    job = booked_job(client, db, seed)
    conv = start(client, seed["somchai"].id)
    set_llm(_DownLLM())
    try:
        out = say(client, conv["conversation_id"], seed["somchai"].id, f"งาน {job.id} ถึงไหนแล้วคะ")
    finally:
        set_llm(MockLLM())
    assert out["outcome"] == "answered" and "ยืนยันแล้ว" in out["reply"]
    assert out["guard"] == "blocked:llm_error"
    assert '"event": "llm_error"' in caplog.text and "ReadTimeout" in caplog.text

