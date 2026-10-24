"""สร้างไฟล์รายงานประจำวันของ gateway แบบจำลอง (IF-01) จากข้อมูลในฐานข้อมูลของเครื่องทดสอบ ใช้ซ้อม UC-13 ใน UAT และ OAT ไม่ใช่ส่วนของระบบ
ใช้: DATABASE_URL=<ฐานของเครื่องทดสอบ> python gateway_report_mock.py --date 2026-12-10 [--unknown success|failed|absent]
     [--drop <reference>] [--amount <reference>=<ยอด>] [--extra <reference>=<ยอด>] > report.csv
ระบบจริงได้ไฟล์นี้จาก gateway (สัญญา IF-01 ส่วน "รายงานประจำวัน") ห้ามสร้างเองแทนรายงานจริง"""
import argparse
from datetime import date

from app.db.session import SessionLocal
from app.reconciliation.mock_report import build_report

ap = argparse.ArgumentParser()
ap.add_argument("--date", required=True)
ap.add_argument("--unknown", default="success", choices=("success", "failed", "absent"))
ap.add_argument("--drop", action="append", default=[])
ap.add_argument("--amount", action="append", default=[])
ap.add_argument("--extra", action="append", default=[])
a = ap.parse_args()
db = SessionLocal()
amounts = {k: int(v) for k, v in (x.split("=") for x in a.amount)}
extra = [("capture", k, int(v), "success") for k, v in (x.split("=") for x in a.extra)]
print(build_report(db, date.fromisoformat(a.date), a.unknown, tuple(a.drop), amounts, None, extra), end="")
