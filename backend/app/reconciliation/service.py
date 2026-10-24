"""CR-16 (UC-13 specs/010-reconciliation) Finance กระทบยอดการชำระและการคืนเงินกับรายงานประจำวันของ gateway (IF-01) ตาม BR-13
รายงาน (ไฟล์ CSV ตามสัญญา IF-01 ส่วน "รายงานประจำวัน"): date,type,reference,amount,status  type = capture | refund status = success | failed
ฝั่งระบบของวัน D: การชำระที่ result = success และ authorized_at อยู่ในวัน D | การคืนเงินที่ส่ง gateway แล้ว (มี reference)
ซึ่งงานถูกยกเลิกในวัน D (เวลาจาก job_status_history เพราะตาราง refunds ไม่มีเวลา และ R2 ไม่แก้ตารางเดิม)
จับคู่ด้วย (type, reference) ผล: matched | missing_in_report | missing_in_system | amount_mismatch | status_mismatch
| refund_unknown_resolved (Q-41: ผลคืนเงินที่ไม่รู้ ได้คำตอบจากรายงาน) | refund_unknown_still (รายงานไม่มี ยังไม่รู้ อยู่ในรายการติดตาม)
ระบบไม่ส่งคำขอคืนเงินซ้ำเอง (REQ-IF-010) รายการต่างทุกตัว Finance ปิดเองตามคู่มือเหตุการณ์ที่ 8 ไม่มีข้อมูลส่วนบุคคลในผล"""
import csv
import hashlib
import io
import re
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.db.models import (Job, JobStatusHistory, Payment, ReconciliationItem, ReconciliationRun, Refund,
                           RefundResolution)
from app.notify.queue import queue
from app.privacy import get_logger, log_event

log = get_logger(__name__)
HEADER = ["date", "type", "reference", "amount", "status"]
KIND_TH = {
    "missing_in_report": "มีในระบบ ไม่มีในรายงาน",
    "missing_in_system": "มีในรายงาน ไม่มีในระบบ",
    "amount_mismatch": "ยอดไม่ตรง",
    "status_mismatch": "ผลไม่ตรง",
    "refund_unknown_resolved": "คืนเงินที่ไม่รู้ผล ได้ผลจากรายงานแล้ว",
    "refund_unknown_still": "คืนเงินที่ไม่รู้ผล รายงานยังไม่มี",
}


class ReportError(Exception):
    def __init__(self, line: int, message: str):
        self.line, self.message = line, message


def parse(text: str, report_date: date) -> list[dict]:
    """ตรวจทั้งไฟล์ก่อน ผิดบรรทัดเดียว ไม่นำเข้าอะไรเลย (AC-13-08)"""
    rows = list(csv.reader(io.StringIO(text.strip())))
    if not rows or [c.strip() for c in rows[0]] != HEADER:
        raise ReportError(1, "หัวตารางต้องเป็น " + ",".join(HEADER))
    out, seen = [], set()
    for n, r in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in r):
            continue
        if len(r) != 5:
            raise ReportError(n, "ต้องมี 5 ช่อง")
        d, typ, ref, amount, status = (c.strip() for c in r)
        if d != report_date.isoformat():
            raise ReportError(n, f"วันที่ต้องเป็น {report_date.isoformat()}")
        if typ not in ("capture", "refund") or status not in ("success", "failed"):
            raise ReportError(n, "type ต้องเป็น capture หรือ refund และ status ต้องเป็น success หรือ failed")
        if not re.fullmatch(r"\d+", amount):
            raise ReportError(n, "ยอดเงินต้องเป็นจำนวนเต็มบาท")
        if (typ, ref) in seen:
            raise ReportError(n, "reference ซ้ำในรายงาน")
        seen.add((typ, ref))
        out.append({"type": typ, "reference": ref, "amount": int(amount), "status": status})
    return out


def _cancel_at(db, job_id: int) -> datetime | None:
    return db.scalars(select(JobStatusHistory.at).where(JobStatusHistory.job_id == job_id,
                                                         JobStatusHistory.to_status.in_(("cancelled", "auto_cancelled")))
                      .order_by(JobStatusHistory.id.desc())).first()


def system_entries(db, day: date) -> dict:
    d0 = datetime(day.year, day.month, day.day)
    d1 = d0 + timedelta(days=1)
    out = {}
    for p in db.scalars(select(Payment).where(Payment.result == "success", Payment.authorized_at >= d0,
                                              Payment.authorized_at < d1)):
        out[("capture", p.gateway_ref)] = {"job_id": p.job_id, "amount": p.amount, "status": "success", "obj": p}
    for r in db.scalars(select(Refund).where(Refund.gateway_ref.is_not(None),
                                             Refund.result.in_(("approved", "declined", "unknown")))):
        at = _cancel_at(db, r.job_id)
        if at is not None and d0 <= at < d1:
            out[("refund", r.gateway_ref)] = {"job_id": r.job_id, "amount": r.amount, "status": r.result, "obj": r}
    return out


def _resolve(db, run: ReconciliationRun, refund: Refund, to_result: str, now: datetime) -> None:
    from app.refund.service import MSG_REFUND_DECLINED
    db.add(RefundResolution(refund_id=refund.id, run_id=run.id, from_result=refund.result, to_result=to_result, at=now))
    refund.result = to_result
    job = db.get(Job, refund.job_id)
    text = (f"งาน #{job.id} คืนมัดจำ {refund.amount} บาทแล้ว" if to_result == "approved"
            else f"งาน #{job.id} {MSG_REFUND_DECLINED}")
    queue.enqueue("customer", job.customer_id, text, job.id, now, db=db)
    log_event(log, "refund_resolved", job_id=job.id, result=to_result, amount=refund.amount)


def reconcile(db, report_date: date, text: str, now: datetime) -> tuple[ReconciliationRun, bool]:
    """คืน (ผลกระทบยอด, นำเข้าไปแล้วหรือยัง) รายงานเดิมของวันเดิมที่นำเข้าแล้ว ไม่ทำซ้ำ (AC-13-08)"""
    digest = hashlib.sha256(text.strip().encode()).hexdigest()
    d0 = datetime(report_date.year, report_date.month, report_date.day)
    old = db.scalars(select(ReconciliationRun).where(ReconciliationRun.report_date == d0,
                                                     ReconciliationRun.report_sha256 == digest)).first()
    if old is not None:
        return old, True
    report = parse(text, report_date)
    run = ReconciliationRun(report_date=d0, report_sha256=digest, rows_in_report=len(report), at=now)
    db.add(run)
    db.flush()
    system = system_entries(db, report_date)
    by_key = {(r["type"], r["reference"]): r for r in report}

    def item(kind, typ, ref, s=None, r=None):
        db.add(ReconciliationItem(run_id=run.id, kind=kind, entry_type=typ, reference=ref,
                                  job_id=s["job_id"] if s else _job_of_ref(db, ref),
                                  system_amount=s["amount"] if s else None, report_amount=r["amount"] if r else None,
                                  system_status=s["status"] if s else None, report_status=r["status"] if r else None))

    matched = diffs = 0
    for (typ, ref), s in sorted(system.items(), key=lambda kv: (kv[0][0], kv[1]["job_id"])):
        r = by_key.pop((typ, ref), None)
        if r is None:
            item("refund_unknown_still" if s["status"] == "unknown" else "missing_in_report", typ, ref, s)
            diffs += 1
        elif r["amount"] != s["amount"]:
            item("amount_mismatch", typ, ref, s, r)
            diffs += 1
        elif typ == "capture":
            if r["status"] == "success":
                matched += 1
            else:
                item("status_mismatch", typ, ref, s, r)
                diffs += 1
        else:
            want = "approved" if r["status"] == "success" else "declined"
            if s["status"] == want:
                matched += 1
            elif s["status"] == "unknown":
                item("refund_unknown_resolved", typ, ref, s, r)
                _resolve(db, run, s["obj"], want, now)
                diffs += 1
            else:
                item("status_mismatch", typ, ref, s, r)
                diffs += 1
    for (typ, ref), r in sorted(by_key.items()):
        item("missing_in_system", typ, ref, None, r)
        diffs += 1
    run.matched, run.differences = matched, diffs
    db.commit()
    log_event(log, "reconciliation_done", count=len(report), result=f"matched={matched} differences={diffs}")
    return run, False


def _job_of_ref(db, ref: str) -> int | None:
    return db.scalars(select(Payment.job_id).where(Payment.gateway_ref == ref)).first()


def run_view(db, run: ReconciliationRun, already: bool = False) -> dict:
    items = db.scalars(select(ReconciliationItem).where(ReconciliationItem.run_id == run.id)
                       .order_by(ReconciliationItem.id)).all()
    counts = {}
    for i in items:
        counts[i.kind] = counts.get(i.kind, 0) + 1
    return {"run_id": run.id, "report_date": run.report_date.date().isoformat(), "rows_in_report": run.rows_in_report,
            "matched": run.matched, "differences": run.differences, "already_imported": already, "counts": counts,
            "items": [{"kind": i.kind, "kind_th": KIND_TH[i.kind], "type": i.entry_type, "reference": i.reference,
                       "job_id": i.job_id, "system_amount": i.system_amount, "report_amount": i.report_amount,
                       "system_status": i.system_status, "report_status": i.report_status} for i in items]}
