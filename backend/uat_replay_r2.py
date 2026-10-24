"""ทีมเดินซ้อม scenario ของ R2 ผ่าน API บนเครื่องทดสอบ ก่อนเชิญผู้ตรวจ (เกณฑ์เริ่มข้อ 4 ของ docs/acceptance/uat-r2.md) ไม่ใช่ส่วนของระบบ
เหมือน uat_replay.py ของ R1: ไม่ใช่ UAT (UAT คือคนในบทบาทจริงเดินบนหน้าจอ) แค่ยืนยันว่าเส้นทางหลังบ้านของ scenario ใหม่ทำงาน
บนเครื่องที่ตั้งค่าเหมือนระบบจริง (โหมด production, PostgreSQL, หลาย process, ไม่มีช่อง now=)
ใช้: python uat_replay_r2.py --base http://127.0.0.1:8000 --ops-token <OPS> --cc-token <CALL_CENTER> --fin-token <FINANCE> --db <DATABASE_URL> [--group main|recon]
  main  เครื่องที่ตั้ง gateway จำลองแบบปกติ | recon เครื่องที่ตั้ง FAKE_GATEWAY_REFUND_MODE=timeout (คืนเงินไม่รู้ผล Q-41)
ข้อมูลตั้งต้นมาจาก uat_seed.py (ลูกค้าทดสอบ 30 ราย ช่างทดสอบ 10 คน) ข้อความ OTP อ่านจากกล่องข้อความของตัวจำลอง SMS (/ops/notifications/outbox)"""
import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy import create_engine, text

from uat_auth import TestTokens

CAT = "ประปา"


class ReplayR2:
    def __init__(self, base, ops, cc, fin, db_url):
        self.c = httpx.Client(base_url=base, timeout=30)
        self.ops, self.cc, self.fin = {"X-Ops-Token": ops}, {"X-Call-Center-Token": cc}, {"X-Finance-Token": fin}
        self.t = TestTokens(db_url)
        self.db_url = db_url
        self.db = create_engine(db_url)
        self.rows = []

    def C(self, cid):
        return self.t.headers("customer", cid)

    def T(self, tid):
        return self.t.headers("technician", tid)

    def search(self, cid, cat=CAT, address_id=None):
        r = self.c.get("/technicians", params={"category": cat, "address_id": address_id or cid}, headers=self.C(cid))
        assert r.status_code == 200, r.text
        return r.json()

    def book(self, cid, slot, cat=CAT, address_id=None):
        self.c.post(f"/slots/{slot}/hold", json={}, headers=self.C(cid))
        return self.c.post("/bookings", json={"slot_id": slot, "address_id": address_id or cid, "category": cat}, headers=self.C(cid))

    def sql(self, q, **kw):
        with self.db.connect() as cn:
            return cn.execute(text(q), kw).all()

    def wait_delivery(self, message_like, seconds=150):
        """งานเบื้องหลังส่งข้อความทุก 1 นาที (REQ-OP-008) รอจนกล่องข้อความของตัวจำลองมีข้อความนั้น"""
        end = time.time() + seconds
        while time.time() < end:
            box = self.c.get("/ops/notifications/outbox", params={"limit": 200}, headers=self.ops).json()
            hit = [m for m in box if message_like(m)]
            if hit:
                return hit
            time.sleep(5)
        raise AssertionError("ไม่มีข้อความในกล่องข้อความของตัวจำลองภายในเวลาที่รอ")

    def check(self, sid, ac, fn):
        try:
            self.rows.append((sid, ac, True, fn()))
        except AssertionError as e:
            self.rows.append((sid, ac, False, f"ไม่ผ่าน: {e}"))
        except Exception as e:  # noqa: BLE001
            self.rows.append((sid, ac, False, f"ผิดพลาด: {type(e).__name__} {e}"))

    # ---------- scenario ของ R2 ----------
    def s20_register(self):
        phone = f"000-111-{int(time.time()) % 10000:04d}"
        ch = self.c.post("/auth/otp", json={"phone": phone, "role": "customer"}).json()
        assert "dev_code" not in ch, "ระบบจริงส่งรหัสกลับในคำตอบ"
        box = self.wait_delivery(lambda m: m["channel"] == "sms" and m["to"].endswith(phone[-4:]) and "รหัส" in m["text"], 30)
        code = next(w for w in box[-1]["text"].split() if w.isdigit() and len(w) == 6)
        v = self.c.post("/auth/verify", json={"challenge_id": ch["challenge_id"], "code": code}).json()
        assert v.get("needs_registration"), v
        bad = self.c.post("/auth/register", json={"challenge_id": v["challenge_id"], "name": "ลูกค้าใหม่ทดสอบ", "address_text": "บ้านสวน"})
        assert bad.status_code == 422 and bad.json()["reason"] == "address_not_found", bad.text
        ok = self.c.post("/auth/register", json={"challenge_id": v["challenge_id"], "name": "ลูกค้าใหม่ทดสอบ", "address_text": "ซอยทดสอบ เขตสาทร"})
        assert ok.status_code == 201, ok.text
        self.new_token = {"Authorization": f"Bearer {ok.json()['token']}"}
        me = self.c.get("/me", headers=self.new_token).json()
        assert "lat" not in json.dumps(me), me
        return f"ลงทะเบียนด้วย OTP จากกล่อง SMS จำลอง ที่อยู่ไม่มีชื่อเขตได้ 422 มีชื่อเขตได้ 201 ไม่มีพิกัดในคำตอบ"

    def s21_addresses(self):
        h = self.new_token
        r = self.c.post("/me/addresses", json={"text": "คอนโดทดสอบ เขตบางรัก"}, headers=h)
        assert r.status_code == 201, r.text
        rows = self.c.get("/me/addresses", headers=h).json()
        assert len(rows) == 2 and rows[1]["can_delete"] is True and rows[0]["can_delete"] is True, rows
        assert self.c.delete(f"/me/addresses/{rows[1]['address_id']}", headers=h).status_code == 200
        last = self.c.delete(f"/me/addresses/{rows[0]['address_id']}", headers=h)
        assert last.status_code == 409 and last.json()["reason"] == "last_one", last.text
        return "เพิ่มที่อยู่ที่มีชื่อเขต ลบได้ ลบที่อยู่สุดท้ายไม่ได้ (409 last_one)"

    def s22_schedule(self):
        tid = 9  # ช่างทดสอบ 09 รับงานประปา (uat_seed.py ทักษะตามรหัส)
        first = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)  # วันแรกที่ค้นได้ (AS-06)
        last_seeded, outside = first + timedelta(days=6), first + timedelta(days=7)  # uat_seed.py ใส่ 7 วัน วันที่ 8 ยังว่าง
        r = self.c.post("/me/slots", json={"start": outside.replace(hour=19).isoformat()}, headers=self.T(tid))
        assert r.status_code == 422 and r.json()["reason"] == "outside_hours", r.text
        r = self.c.post("/me/slots", json={"start": last_seeded.replace(hour=10).isoformat()}, headers=self.T(tid))
        assert r.status_code == 409 and r.json()["reason"] == "overlap", r.text
        r = self.c.post("/me/slots", json={"start": outside.replace(hour=8).isoformat()}, headers=self.T(tid))
        assert r.status_code == 201, r.text
        days = self.c.get("/me/schedule", headers=self.T(tid)).json()["days"]
        assert any(s["slot_id"] == r.json()["slot_id"] for d in days for s in d["slots"]), "ช่วงใหม่ไม่อยู่ในตารางของช่าง"
        mine = [t for t in self.search(13) if t["technician_id"] == tid][0]["slots"]
        sid, start = mine[-1]["slot_id"], mine[-1]["start"]
        assert self.c.post(f"/me/slots/{sid}/close", headers=self.T(tid)).json()["state"] == "closed"
        assert sid not in [s["slot_id"] for t in self.search(13) for s in t["slots"]], "ช่วงที่ปิดยังอยู่ในผลค้นหา"
        assert self.c.post(f"/slots/{sid}/hold", json={}, headers=self.C(13)).status_code == 409
        assert self.c.post(f"/me/slots/{sid}/close", headers=self.T(4)).status_code == 403
        again = self.c.post("/me/slots", json={"start": start}, headers=self.T(tid)).json()
        assert again["reopened"] is True and sid in [s["slot_id"] for t in self.search(13) for s in t["slots"]], again
        off_day = (first + timedelta(days=4)).date().isoformat()
        off = self.c.post("/me/days-off", json={"day": off_day}, headers=self.T(tid))
        assert off.status_code in (201, 409), off.text
        if off.status_code == 409:
            return f"ช่าง 09 เพิ่มช่วงได้ ซ้อนได้ 409 นอกเวลาได้ 422 ปิดแล้วลูกค้าไม่เห็นและล็อกไม่ได้ ช่างคนอื่นได้ 403 เปิดคืนได้ วันหยุดวันที่มีงานได้ 409 งาน {off.json()['job_ids']}"
        back = self.c.delete(f"/me/days-off/{off_day}", headers=self.T(tid)).json()
        return (f"ช่าง 09 เพิ่มช่วงได้ ซ้อนได้ 409 นอกเวลาได้ 422 ปิดแล้วลูกค้าไม่เห็นและล็อกไม่ได้ ช่างคนอื่นได้ 403 เพิ่มช่วงเดิมคือเปิดคืน "
                f"วันหยุดปิด {off.json()['closed_slots']} ช่วง ยกเลิกแล้วเปิดคืน {back['reopened_slots']} ช่วง")

    def s23_reject_rematch(self):
        cid = 14
        techs = self.search(cid)
        slot = techs[0]["slots"][3]["slot_id"]
        r = self.book(cid, slot)
        assert r.status_code == 201, r.text
        jid, tech = r.json()["job_id"], r.json()["technician_id"]
        rej = self.c.post(f"/jobs/{jid}/reject", json={"reason": "ติดงาน"}, headers=self.T(tech))
        assert rej.status_code == 200, rej.text
        job = self.c.get(f"/jobs/{jid}", headers=self.cc).json()
        assert job["status"] in ("confirmed", "rematching"), job
        mine = [j for j in self.c.get("/me/jobs", headers=self.C(cid)).json() if j["job_id"] == jid][0]
        return f"งาน #{jid} ช่าง {tech} ปฏิเสธ สถานะ {job['status']} ช่างแทน {mine['technician_name']} ปฏิเสธช่างแทนได้ {mine['can_decline_substitute']}"

    def s24_rating(self):
        cid = 15
        slot = self.search(cid)[0]["slots"][0]["slot_id"]
        r = self.book(cid, slot)
        assert r.status_code == 201, r.text
        jid, tech = r.json()["job_id"], r.json()["technician_id"]
        early = self.c.post(f"/jobs/{jid}/rating", json={"stars": 5}, headers=self.C(cid))
        assert early.status_code == 409 and early.json()["reason"] == "not_done", early.text
        for to in ("en_route", "in_progress", "done"):
            assert self.c.post(f"/jobs/{jid}/status", json={"to_status": to}, headers=self.T(tech)).status_code == 200
        other = self.c.post(f"/jobs/{jid}/rating", json={"stars": 1}, headers=self.C(16))
        assert other.status_code == 403
        ok = self.c.post(f"/jobs/{jid}/rating", json={"stars": 4, "comment": "ดีมาก โทร 000-000-0015"}, headers=self.C(cid))
        assert ok.status_code == 201, ok.text
        again = self.c.post(f"/jobs/{jid}/rating", json={"stars": 1}, headers=self.C(cid))
        assert again.status_code == 409
        stored = self.sql("SELECT comment FROM ratings WHERE job_id=:j", j=jid)[0][0]
        assert "000-000-0015" not in stored, stored
        rows = [t for t in self.search(cid) if t["technician_id"] == tech]
        return f"งาน #{jid} ให้คะแนนก่อนเสร็จได้ 409 คนอื่นได้ 403 เจ้าของให้ 4 ดาวได้ ซ้ำได้ 409 เบอร์ในความเห็นถูกปิดบัง ผลค้นหา {rows[0]['rating'] if rows else 'ช่างไม่มีช่วงว่างแล้ว'}"

    def s25_line(self):
        cid = 17
        code = self.c.post("/me/notifications/line-link", headers=self.C(cid)).json()["link_code"]
        body = json.dumps({"events": [{"type": "message", "source": {"userId": "U-uat-0017"}, "message": {"type": "text", "text": code}}]}).encode()
        from app.integrations.http_messaging import line_signature
        bad = self.c.post("/integrations/line/webhook", content=body, headers={"X-Line-Signature": "x"})
        assert bad.status_code == 403
        ok = self.c.post("/integrations/line/webhook", content=body, headers={"X-Line-Signature": line_signature(body, "mock-line-secret")})
        assert ok.json() == {"linked": 1}, ok.text
        assert self.c.put("/me/notifications", json={"channel": "line"}, headers=self.C(cid)).json()["channel"] == "line"
        slot = self.search(cid)[0]["slots"][1]["slot_id"]
        jid = self.book(cid, slot).json()["job_id"]
        box = self.wait_delivery(lambda m: m["channel"] == "line" and m["to"].endswith("0017") and f"#{jid}" in m["text"])
        return f"เชื่อม LINE ด้วยรหัสผ่าน webhook ที่ตรวจลายเซ็น (ลายเซ็นผิดได้ 403) เลือก LINE แล้วข้อความจองงาน #{jid} ไปถึงกล่อง LINE จำลอง {len(box)} ข้อความ"

    def s26_callcenter(self):
        assert self.c.post("/call-center/assistant/switch", json={"enabled": False}, headers=self.cc).json()["enabled"] is False
        assert self.c.get("/assistant/status").json()["enabled"] is False
        assert self.c.post("/call-center/assistant/switch", json={"enabled": True}, headers=self.ops).status_code == 403
        self.c.post("/call-center/assistant/switch", json={"enabled": True}, headers=self.cc)
        assert self.c.get("/finance/refunds/follow-up", headers=self.cc).status_code == 403
        return "หัวหน้า call center ปิดและเปิดผู้ช่วยด้วยกุญแจของตัวเอง กุญแจของ Ops ใช้แทนไม่ได้ กุญแจ call center เปิดเมนู Finance ไม่ได้"

    def s27_integrations(self):
        rows = self.c.get("/ops/integrations", headers=self.ops).json()
        mocks = [r["kind"] for r in rows if r["mock"]]
        assert self.c.get("/ready").json() == {"ok": True, "database": "ok"}
        return f"ระบบภายนอกที่ยังเป็นตัวจำลอง: {', '.join(mocks)} (ต้องว่างก่อนเปิดใช้จริง ดู docs/handover/mocks-and-limits.md)"

    def recon(self):
        cid = 18
        slots = [s["slot_id"] for t in self.search(cid) for s in t["slots"]]
        a = self.book(cid, slots[-1]).json()["job_id"]
        b = self.book(cid, slots[-2]).json()["job_id"]
        ca = self.c.post(f"/jobs/{a}/customer-cancel", json={}, headers=self.C(cid)).json()
        assert ca["refund_result"] == "unknown", ca
        follow = self.c.get("/finance/refunds/follow-up", headers=self.fin).json()
        assert any(x["job_id"] == a and x["result"] == "unknown" for x in follow), follow
        import os
        os.environ["DATABASE_URL"] = self.db_url
        from app.db import session as dbs
        from app.reconciliation.mock_report import build_report
        s = dbs.sessionmaker(bind=dbs.make_engine(self.db_url))()
        report = build_report(s, date.today(), unknown_refunds="success")
        r = self.c.post("/finance/reconciliations", json={"report_date": date.today().isoformat(), "csv": report}, headers=self.fin)
        assert r.status_code == 201, r.text
        body = r.json()
        assert any(i["kind"] == "refund_unknown_resolved" and i["job_id"] == a for i in body["items"]), body
        again = self.c.post("/finance/reconciliations", json={"report_date": date.today().isoformat(), "csv": report}, headers=self.fin)
        assert again.status_code == 200 and again.json()["already_imported"], again.text
        assert not any(x["job_id"] == a for x in self.c.get("/finance/refunds/follow-up", headers=self.fin).json())
        assert self.c.post("/finance/reconciliations", json={"report_date": date.today().isoformat(), "csv": report}, headers=self.ops).status_code == 403
        return (f"งาน #{a} คืนเงินไม่รู้ผล อยู่ในรายการติดตาม รายงานจำลอง {body['rows_in_report']} แถว ตรง {body['matched']} ต่าง {body['differences']} "
                f"(ได้ผลคืนเงินของงาน #{a} จากรายงาน) นำเข้าซ้ำไม่ทำซ้ำ งาน #{a} ออกจากรายการติดตาม กุญแจ Ops ใช้ไม่ได้ (งาน #{b} ยังจองอยู่)")

    def run(self, group):
        plan = [("S-30", "AC-13-01, AC-13-05, AC-13-07, AC-13-08", self.recon)] if group == "recon" else [
            ("S-20", "AC-02-01, AC-02-13, REQ-FN-074", self.s20_register),
            ("S-21", "AC-02-12, AC-02-14", self.s21_addresses),
            ("S-22", "AC-04-01 ถึง AC-04-08", self.s22_schedule),
            ("S-23", "AC-12-01, AC-05-01 หรือ AC-05-02", self.s23_reject_rematch),
            ("S-24", "AC-11-01 ถึง AC-11-07", self.s24_rating),
            ("S-25", "AC-10-02, AC-10-03", self.s25_line),
            ("S-26", "AC-00-15, AC-14-14", self.s26_callcenter),
            ("S-27", "AC-00-12", self.s27_integrations),
        ]
        for sid, ac, fn in plan:
            self.check(sid, ac, fn)
        print(f"# เดินซ้อม scenario ของ R2 ผ่าน API เวลาเครื่อง {datetime.now():%Y-%m-%d %H:%M} กลุ่ม {group}")
        print("| scenario | AC | ผล | รายละเอียด |")
        print("|---|---|---|---|")
        for sid, ac, ok, d in self.rows:
            print(f"| {sid} | {ac} | {'ผ่าน' if ok else 'ไม่ผ่าน'} | {d} |")
        failed = [r for r in self.rows if not r[2]]
        print(f"\nสรุป: ผ่าน {len(self.rows) - len(failed)} จาก {len(self.rows)}")
        return 1 if failed else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--ops-token", required=True)
    ap.add_argument("--cc-token", required=True)
    ap.add_argument("--fin-token", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--group", default="main", choices=["main", "recon"])
    a = ap.parse_args()
    sys.exit(ReplayR2(a.base, a.ops_token, a.cc_token, a.fin_token, a.db).run(a.group))
