"""คำสั่งช่วยตรวจ OAT ของ R2 บนเครื่องทดสอบ (docs/acceptance/oat-plan-r2.md) ไม่ใช่ส่วนของระบบ ทุกคำสั่งพิมพ์ผลที่วัดได้จริง
ใช้: python oat_r2.py <คำสั่ง> --base <URL> --db <DATABASE_URL> --ops-token <OPS> [อาร์กิวเมนต์เพิ่ม]
  pager <port> <ไฟล์>        เครื่องรับ webhook ของคนเวร (แทนบริการจริงที่ Ops lead เลือก) เขียนทุกข้อความลงไฟล์
  traffic                    OAT-2 คำขอ 100 ครั้งต่อนาที ล้มเหลว 10 (จองตอน gateway จำลองปฏิเสธ ได้ 402) นาน 6 นาที
  map-down | line-down | sms-down | gateway-down   OAT-5 ตรวจทีละระบบภายนอกที่ไม่ตอบ (หลังบ้านต้องตั้งตัวจำลองให้ไม่ตอบก่อน)
  book-only                  OAT-9 จอง 2 งานแล้วจบทันที (ก่อนงานเบื้องหลังรอบถัดไปส่งข้อความ)
  delivered <งาน,งาน>        OAT-9 รอจนข้อความของงานเหล่านั้นส่งแล้ว (หลังเริ่มหลังบ้านใหม่)
  security <log ...>         OAT-6 ค้นข้อมูลส่วนบุคคลใน log นับบันทึกการปฏิเสธ และตรวจกุญแจแยกบทบาท"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from sqlalchemy import create_engine, text

from uat_auth import TestTokens


def pager(port: int, out: str) -> None:
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("content-length", 0)))
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps({"received_at": datetime.now().isoformat(timespec="seconds"),
                                    "body": json.loads(body or b"{}")}, ensure_ascii=False) + "\n")
            self.send_response(200); self.end_headers()

        def log_message(self, *a):
            pass
    HTTPServer(("127.0.0.1", port), H).serve_forever()


class Oat:
    def __init__(self, base, db, ops):
        self.c = httpx.Client(base_url=base, timeout=40)
        self.t = TestTokens(db)
        self.db = create_engine(db)
        self.ops = {"X-Ops-Token": ops}

    def C(self, i):
        return self.t.headers("customer", i)

    def sql(self, q, **kw):
        with self.db.connect() as cn:
            return cn.execute(text(q), kw).all()

    def slots(self, cid, cat="ประปา"):
        r = self.c.get("/technicians", params={"category": cat, "address_id": cid}, headers=self.C(cid)).json()
        return [s["slot_id"] for t in r for s in t["slots"]]

    def traffic(self, minutes=6, per_minute=100, fail=10):
        # รอให้เริ่มต้นนาทีใหม่ ตัวนับของ REQ-OP-005 นับตามนาที
        time.sleep(60 - datetime.now().second + 1)
        print("traffic start", datetime.now().isoformat(timespec="seconds"))
        free = self.slots(1)
        for m in range(minutes):
            t0 = time.time()
            codes = {}
            for i in range(per_minute):
                if i < fail:
                    sid = free.pop()
                    r = self.c.post("/bookings", json={"slot_id": sid, "address_id": 2 + (i % 20), "category": "ประปา"}, headers=self.C(2 + (i % 20)))
                else:
                    r = self.c.get("/technicians", params={"category": "ประปา", "address_id": 1}, headers=self.C(1))
                codes[r.status_code] = codes.get(r.status_code, 0) + 1
            print(f"minute {m + 1} {datetime.now():%H:%M} codes {codes} done {datetime.now():%H:%M:%S}")
            time.sleep(max(0, 60 - (time.time() - t0)))
        print("traffic end", datetime.now().isoformat(timespec="seconds"))

    def book(self, cid, slot):
        self.c.post(f"/slots/{slot}/hold", json={}, headers=self.C(cid))
        return self.c.post("/bookings", json={"slot_id": slot, "address_id": cid, "category": "ประปา"}, headers=self.C(cid))

    def map_down(self):
        t0 = time.time()
        r = self.c.get("/technicians", params={"category": "ประปา", "address_id": 3}, headers=self.C(3))
        print(f"แผนที่ไม่ตอบ: ค้นหาได้ {r.status_code} ช่าง {len(r.json())} คน ใช้เวลา {time.time() - t0:.2f} วินาที")
        a = self.c.post("/me/addresses", json={"text": "ซอยทดสอบ เขตสาทร"}, headers=self.C(3))
        print(f"เพิ่มที่อยู่ระหว่างแผนที่ไม่ตอบ: {a.status_code} {a.json().get('message')}")

    def line_down(self):
        from app.integrations.http_messaging import line_signature
        cid = 4
        code = self.c.post("/me/notifications/line-link", headers=self.C(cid)).json()["link_code"]
        body = json.dumps({"events": [{"type": "message", "source": {"userId": "U-oat-0004"}, "message": {"type": "text", "text": code}}]}).encode()
        self.c.post("/integrations/line/webhook", content=body, headers={"X-Line-Signature": line_signature(body, "mock-line-secret")})
        self.c.put("/me/notifications", json={"channel": "line"}, headers=self.C(cid))
        jid = self.book(cid, self.slots(cid)[0]).json()["job_id"]
        print(f"ลูกค้า 04 เลือก LINE แล้วจองงาน #{jid} รอรอบส่งข้อความของงานเบื้องหลัง")
        for _ in range(30):
            rows = self.sql("SELECT d.channel, d.result, d.fallback FROM notification_deliveries d JOIN notification_messages m ON m.id = d.message_id "
                            "WHERE m.job_id = :j AND m.to_role = 'customer' ORDER BY d.id", j=jid)
            if any(r[0] == "sms" for r in rows):
                print("บันทึกการส่งของลูกค้า:", [tuple(r) for r in rows])
                return
            time.sleep(5)
        print("ไม่พบการส่ง SMS แทนภายใน 150 วินาที")

    def sms_down(self):
        jid = self.book(5, self.slots(5)[0]).json()["job_id"]
        print(f"จองงาน #{jid} ขณะ SMS ไม่ตอบ รอ 2 รอบของงานเบื้องหลัง")
        time.sleep(130)
        rows = self.sql("SELECT to_role, attempts, delivered_at IS NOT NULL, gave_up FROM notification_messages WHERE job_id = :j ORDER BY id", j=jid)
        print("ข้อความของงาน (ผู้รับ ครั้งที่ลอง ส่งแล้ว เลิกส่ง):", [tuple(r) for r in rows])
        n = self.sql("SELECT count(*) FROM notification_messages WHERE job_id = :j", j=jid)[0][0]
        print(f"จำนวนข้อความของงานนี้ {n} (ไม่สร้างซ้ำ) ส่งซ้ำทุก 5 นาที ไม่เกิน 6 ครั้ง (REQ-QA-010)")

    def gateway_down(self):
        cid = 6
        slot = self.slots(cid)[0]
        self.c.post(f"/slots/{slot}/hold", json={}, headers=self.C(cid))
        codes = [self.c.post("/bookings", json={"slot_id": slot, "address_id": cid, "category": "ประปา"}, headers=self.C(cid)).status_code for _ in range(3)]
        jobs = self.sql("SELECT id, status FROM jobs WHERE slot_id = :s", s=slot)
        pays = self.sql("SELECT gateway_ref, result FROM payments WHERE job_id IN (SELECT id FROM jobs WHERE slot_id = :s)", s=slot)
        print(f"gateway ไม่ตอบ: กดยืนยัน 3 ครั้ง ได้ {codes} งาน {[tuple(j) for j in jobs]} การชำระ {[tuple(p) for p in pays]}")

    def book_only(self):
        ids = [self.book(c, self.slots(c)[i]).json()["job_id"] for i, c in enumerate((7, 8))]
        n = self.sql("SELECT count(*) FROM notification_messages WHERE job_id IN :a AND delivered_at IS NULL".replace(":a", "(" + ",".join(map(str, ids)) + ")"))[0][0]
        print(f"จองงาน {ids} ข้อความที่ยังไม่ส่ง {n} ข้อความ เวลา {datetime.now():%H:%M:%S}")
        print("JOBS=" + ",".join(map(str, ids)))

    def delivered(self, jobs):
        ids = "(" + jobs + ")"
        for _ in range(36):
            rows = self.sql(f"SELECT count(*), sum(CASE WHEN delivered_at IS NOT NULL THEN 1 ELSE 0 END) FROM notification_messages WHERE job_id IN {ids}")
            total, done = rows[0][0], rows[0][1] or 0
            if total and done == total:
                print(f"หลังเริ่มหลังบ้านใหม่: ข้อความของงาน {jobs} ส่งแล้ว {done} จาก {total} เวลา {datetime.now():%H:%M:%S}")
                return
            time.sleep(5)
        print(f"หลังเริ่มหลังบ้านใหม่: ส่งแล้ว {done} จาก {total} (ไม่ครบภายใน 3 นาที)")

    def security(self, logs, cc, fin):
        names = [r[0] for r in self.sql("SELECT name FROM customers")]
        addrs = [r[0] for r in self.sql("SELECT text FROM service_addresses")]
        text_all = "".join(open(p, encoding="utf-8", errors="replace").read() for p in logs)
        lines = sum(1 for p in logs for _ in open(p, encoding="utf-8", errors="replace"))
        app_lines = sum(1 for p in logs for x in open(p, encoding="utf-8", errors="replace") if x.startswith('{"event"'))
        found = {"เบอร์ 000-000-": text_all.count("000-000-"), "ชื่อลูกค้า": sum(text_all.count(n) for n in names if n),
                 "ที่อยู่": sum(text_all.count(a) for a in addrs if a), "พิกัด 13.7": text_all.count("13.74"), "LINE U-": text_all.count("U-oat")}
        print(f"log {len(logs)} ไฟล์ {lines} บรรทัด เป็น log ของแอป (JSON) {app_lines} บรรทัด ค้นพบ: {found}")
        before = self.sql("SELECT count(*) FROM security_events WHERE kind = 'denied'")[0][0]
        jid = self.sql("SELECT id FROM jobs ORDER BY id LIMIT 1")[0][0]
        r = [self.c.get(f"/jobs/{jid}/refund-quote", headers=self.C(30)).status_code,
             self.c.post(f"/jobs/{jid}/rating", json={"stars": 1}, headers=self.C(30)).status_code,
             self.c.delete("/me/addresses/1", headers=self.C(30)).status_code]
        after = self.sql("SELECT count(*) FROM security_events WHERE kind = 'denied'")[0][0]
        print(f"คำขอต่องานและที่อยู่ของคนอื่น 3 ครั้ง ได้ {r} บันทึกการปฏิเสธเพิ่ม {after - before} รายการ")
        keys = {"call center เปิด /finance": self.c.get("/finance/refunds/follow-up", headers={"X-Call-Center-Token": cc}).status_code,
                "Finance เปิด /call-center": self.c.get("/call-center/assistant/tickets", headers={"X-Finance-Token": fin}).status_code,
                "Ops เปิด /finance": self.c.get("/finance/refunds/follow-up", headers=self.ops).status_code,
                "Finance เปิด /finance": self.c.get("/finance/refunds/follow-up", headers={"X-Finance-Token": fin}).status_code}
        print("กุญแจแยกบทบาท:", keys)


if __name__ == "__main__":
    if sys.argv[1] == "pager":
        pager(int(sys.argv[2]), sys.argv[3]); sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--base", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--ops-token", required=True)
    ap.add_argument("--cc-token", default="")
    ap.add_argument("--fin-token", default="")
    a = ap.parse_args()
    o = Oat(a.base, a.db, a.ops_token)
    if a.cmd == "security":
        o.security(a.rest, a.cc_token, a.fin_token)
    elif a.cmd == "delivered":
        o.delivered(a.rest[0])
    else:
        getattr(o, a.cmd.replace("-", "_"))()
