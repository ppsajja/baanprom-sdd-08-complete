"""CR-16 ตัวจำลองรายงานประจำวันของ gateway (IF-01) ใช้ใน test เครื่องทดสอบ UAT และ OAT ไม่ใช่ส่วนที่ระบบจริงใช้
สร้างจากข้อมูลในระบบเองแล้วให้ "ทำให้ต่าง" ได้ทีละรายการ เพื่อซ้อมทุกชนิดของรายการต่าง
unknown_refunds = ผลจริงที่ gateway ทำกับคำขอคืนเงินที่ระบบไม่รู้ผล: success | failed | absent (ไม่อยู่ในรายงาน)"""
from datetime import date

from app.reconciliation.service import HEADER, system_entries


def build_report(db, day: date, unknown_refunds: str = "success", drop: tuple = (), amounts: dict | None = None,
                 statuses: dict | None = None, extra: list | None = None) -> str:
    amounts, statuses = amounts or {}, statuses or {}
    lines = [",".join(HEADER)]
    for (typ, ref), s in sorted(system_entries(db, day).items(), key=lambda kv: kv[1]["job_id"]):
        if ref in drop:
            continue
        if typ == "capture":
            status = "success"
        elif s["status"] == "unknown":
            if unknown_refunds == "absent":
                continue
            status = unknown_refunds
        else:
            status = "success" if s["status"] == "approved" else "failed"
        status = statuses.get(ref, status)
        lines.append(f"{day.isoformat()},{typ},{ref},{amounts.get(ref, s['amount'])},{status}")
    for typ, ref, amount, status in extra or []:
        lines.append(f"{day.isoformat()},{typ},{ref},{amount},{status}")
    return "\n".join(lines) + "\n"
