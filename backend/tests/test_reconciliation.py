"""AC-13-01 ถึง AC-13-08 จาก reconciliation.feature (specs/010-reconciliation, CR-16) UC-13 Finance กระทบยอดกับรายงานของ gateway
BR-13 จับคู่ด้วยชนิดและ reference รายการต่าง 6 ชนิด การคืนเงินที่ไม่รู้ผล (Q-41) ได้ผลจากรายงาน ระบบไม่ส่งคำขอคืนเงินซ้ำ
รายงานเป็นไฟล์จำลอง (app/reconciliation/mock_report.py) ตามสัญญา IF-01 ส่วน "รายงานประจำวัน\""""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import Job, Payment, ReconciliationRun, Refund, RefundResolution
from app.notify.queue import queue
from app.reconciliation.mock_report import build_report
from tests.conftest import NOW, TOMORROW_14, OPS, H, book

FIN = {"X-Finance-Token": "fin-token-for-tests"}
DAY = NOW.date()


@pytest.fixture()
def finance(monkeypatch):
    monkeypatch.setenv("FINANCE_TOKEN", FIN["X-Finance-Token"])


def q(now=NOW):
    return f"?now={now.isoformat()}"


@pytest.fixture()
def day_data(client, db, seed, gateway, finance):
    """วันเดียวกัน: งาน A จองแล้ว (ตัดเงิน) งาน B ยกเลิก R1 คืนเงินสำเร็จ งาน C ยกเลิก gateway ไม่ตอบคำขอคืนเงิน (unknown)"""
    s = seed["slots"]
    a = book(client, customer_id=seed["somchai"].id, slot_id=s[0].id, address_id=seed["addr"].id).json()["job_id"]
    b = book(client, customer_id=seed["somchai"].id, slot_id=s[3].id, address_id=seed["addr"].id).json()["job_id"]
    c = book(client, customer_id=seed["other"].id, slot_id=s[1].id, address_id=seed["addr_other"].id).json()["job_id"]
    assert client.post(f"/jobs/{b}/customer-cancel{q(NOW + timedelta(hours=1))}", headers=H("customer", seed["somchai"].id)).status_code == 200
    gateway.refund_mode = "timeout"
    assert client.post(f"/jobs/{c}/customer-cancel{q(NOW + timedelta(hours=2))}", headers=H("customer", seed["other"].id)).status_code == 200
    gateway.refund_mode = "approved"
    ref = {j: db.scalars(select(Payment.gateway_ref).where(Payment.job_id == j)).one() for j in (a, b, c)}
    return {"a": a, "b": b, "c": c, "ref": ref}


def post(client, csv, headers=FIN):
    return client.post(f"/finance/reconciliations{q(NOW + timedelta(hours=20))}", json={"report_date": DAY.isoformat(), "csv": csv}, headers=headers)


def kinds(body):
    return sorted((i["kind"], i["job_id"]) for i in body["items"])


# รองรับ AC-13-01 (REQ-FN-070): รายงานตรงกับระบบทุกรายการ
def test_AC_13_01_all_matched(client, db, day_data):
    csv = build_report(db, DAY, unknown_refunds="absent", drop=())
    r = post(client, csv)
    assert r.status_code == 201
    body = r.json()
    # capture 3 รายการ refund ของ B ตรง เหลือ refund ของ C ที่ยังไม่รู้ผลและรายงานไม่มี
    assert body["matched"] == 4 and kinds(body) == [("refund_unknown_still", day_data["c"])]


# รองรับ AC-13-02 ถึง AC-13-04: มีในระบบไม่มีในรายงาน มีในรายงานไม่มีในระบบ ยอดไม่ตรง
def test_AC_13_02_03_04_differences_listed(client, db, day_data):
    ref = day_data["ref"]
    csv = build_report(db, DAY, unknown_refunds="success", drop=(ref[day_data["a"]],), amounts={ref[day_data["b"]]: 300},
                       extra=[("capture", "BP-999-ffffffff", 500, "success")])
    body = post(client, csv).json()
    assert ("missing_in_report", day_data["a"]) in kinds(body)
    assert ("missing_in_system", None) in kinds(body)
    amount = [i for i in body["items"] if i["kind"] == "amount_mismatch"]
    # ยอดของ B ผิดทั้งรายการตัดเงินและรายการคืนเงิน (reference เดียวกัน)
    assert {(i["type"], i["system_amount"], i["report_amount"]) for i in amount} == {("capture", 350, 300), ("refund", 350, 300)}
    assert all(i["kind_th"] for i in body["items"]) and "สมชาย" not in str(body)


# รองรับ AC-13-05 (REQ-FN-071 Q-41): คืนเงินที่ไม่รู้ผล รายงานบอกสำเร็จ ผลเป็นคืนแล้ว แจ้งลูกค้า ออกจากรายการติดตาม
def test_AC_13_05_unknown_refund_resolved_success(client, db, day_data, gateway):
    assert [x["job_id"] for x in client.get("/finance/refunds/follow-up", headers=FIN).json()] == [day_data["c"]]
    calls_before = len(gateway.calls)
    body = post(client, build_report(db, DAY, unknown_refunds="success")).json()
    assert ("refund_unknown_resolved", day_data["c"]) in kinds(body)
    refund = db.scalars(select(Refund).where(Refund.job_id == day_data["c"])).one()
    db.refresh(refund)
    assert refund.result == "approved"
    res = db.scalars(select(RefundResolution)).one()
    assert (res.from_result, res.to_result, res.run_id) == ("unknown", "approved", body["run_id"])
    assert client.get("/finance/refunds/follow-up", headers=FIN).json() == []
    assert any(m.text == f"งาน #{day_data['c']} คืนมัดจำ 350 บาทแล้ว" for m in queue.for_job(day_data["c"]))
    assert len(gateway.calls) == calls_before   # ไม่ส่งคำขอคืนเงินซ้ำ


# รองรับ AC-13-06 (REQ-FN-071): รายงานบอกไม่สำเร็จ ผลเป็นปฏิเสธ ยังอยู่ในรายการติดตาม ถ้ารายงานไม่มี ยังไม่รู้ผล
def test_AC_13_06_unknown_refund_failed_or_absent(client, db, day_data):
    body = post(client, build_report(db, DAY, unknown_refunds="absent")).json()
    assert ("refund_unknown_still", day_data["c"]) in kinds(body)
    refund = db.scalars(select(Refund).where(Refund.job_id == day_data["c"])).one()
    assert refund.result == "unknown"
    body = post(client, build_report(db, DAY, unknown_refunds="failed")).json()
    db.refresh(refund)
    assert refund.result == "declined" and ("refund_unknown_resolved", day_data["c"]) in kinds(body)
    assert [x["result"] for x in client.get("/finance/refunds/follow-up", headers=FIN).json()] == ["declined"]
    assert any("ตรวจสอบเพิ่ม" in m.text for m in queue.for_job(day_data["c"]))


# รองรับ AC-13-07 (REQ-SEC-015): ใช้ได้เฉพาะกุญแจของ Finance
def test_AC_13_07_finance_key_only(client, db, day_data, monkeypatch):
    monkeypatch.setenv("CALL_CENTER_TOKEN", "cc")
    csv = build_report(db, DAY)
    for h in ({}, OPS, {"X-Call-Center-Token": "cc"}, H("customer", 1), {"X-Finance-Token": "wrong"}):
        assert post(client, csv, headers=h).status_code == 403
    assert db.query(ReconciliationRun).count() == 0


# รองรับ AC-13-08 (BR-13 ข้อ 1): ไฟล์ผิดบรรทัดเดียว ไม่นำเข้าอะไร บอกเลขบรรทัด นำเข้าไฟล์เดิมซ้ำ ไม่ทำซ้ำ
def test_AC_13_08_bad_file_and_duplicate_import(client, db, day_data):
    good = build_report(db, DAY, unknown_refunds="success")
    bad = good.replace(",350,", ",350.50,", 1)
    r = post(client, bad)
    assert r.status_code == 422 and r.json()["line"] == 2 and "บรรทัด 2" in r.json()["message"]
    assert db.query(ReconciliationRun).count() == 0 and db.query(RefundResolution).count() == 0
    first = post(client, good)
    again = post(client, good)
    assert first.status_code == 201 and again.status_code == 200 and again.json()["already_imported"] is True
    assert again.json()["run_id"] == first.json()["run_id"]
    assert sum(1 for m in queue.for_job(day_data["c"]) if "คืนมัดจำ 350 บาทแล้ว" in m.text) == 1
    assert client.get(f"/finance/reconciliations/{first.json()['run_id']}", headers=FIN).json()["matched"] == first.json()["matched"]
