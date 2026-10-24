"""ทีมเดินซ้อม scenario ของการตรวจรับ R1 ผ่าน API บนเครื่องทดสอบ ก่อนเชิญผู้ตรวจ (เกณฑ์เริ่มข้อ 5 ของ docs/acceptance/uat-plan-r1.md)
ไม่ใช่ UAT: UAT คือคนในบทบาทจริงเดินบนหน้าจอ สคริปต์นี้แค่ยืนยันว่าเส้นทางหลังบ้านของทุก scenario ทำงานบนเครื่องที่ตั้งค่าเหมือนระบบจริง
(โหมด production, PostgreSQL, ไม่มีช่อง now=) ถ้าพังที่นี่ ห้ามเชิญผู้ตรวจ
ใช้: python uat_replay.py --base http://127.0.0.1:8000 --ops-token <OPS_TOKEN> --db <DATABASE_URL> [--group main|declined]
  main     ใช้กับเครื่องที่ตั้งค่า gateway จำลองแบบปกติ
  declined ใช้กับเครื่องที่ตั้ง FAKE_GATEWAY_REFUND_MODE=declined (scenario ของ AC-08-11)
ข้อมูลตั้งต้นมาจาก uat_seed.py (ลูกค้าทดสอบ 30 ราย ช่างทดสอบ 10 คน)
CR-11 (R2): ทุกคำขอแนบ token ของผู้ส่งผ่าน uat_auth.py (scenario ของ R1 ไม่เปลี่ยน ผู้ส่งยังอ่านจาก customer_id ที่สคริปต์ใส่)"""
import argparse
import sys
from datetime import datetime, timedelta

import httpx
from sqlalchemy import create_engine, text

from uat_auth import TestTokens, auth_hook

CAT = "ประปา"


class Replay:
    def __init__(self, base: str, token: str, db_url: str):
        self.c = httpx.Client(base_url=base, timeout=30,
                              event_hooks={"request": [auth_hook(TestTokens(db_url), token)]})
        self.ops = {"X-Ops-Token": token}
        self.db = create_engine(db_url)
        self.rows: list[tuple[str, str, bool, str]] = []

    # ---------- ตัวช่วย ----------
    def search(self, customer_id: int, category: str = CAT) -> list[dict]:
        r = self.c.get("/technicians", params={"category": category, "address_id": customer_id, "customer_id": customer_id})
        r.raise_for_status()
        return r.json()

    def free_slot(self, customer_id: int, category: str = CAT, skip: int = 0) -> int:
        slots = [s["slot_id"] for t in self.search(customer_id, category) for s in t["slots"]]
        return slots[skip]

    def book(self, customer_id: int, slot_id: int, category: str = CAT) -> httpx.Response:
        self.c.post(f"/slots/{slot_id}/hold", json={"customer_id": customer_id})
        return self.c.post("/bookings", json={"customer_id": customer_id, "slot_id": slot_id,
                                              "address_id": customer_id, "category": category})

    def today_slot(self, technician_id: int) -> int:
        # หน้าค้นหาไม่แสดงวันนี้ (AS-06) scenario ที่ต้องนัดภายใน 24 ชั่วโมงจึงอ่านช่วงเวลาวันนี้ที่ uat_seed.py ใส่ไว้
        with self.db.connect() as cn:
            return cn.execute(text("SELECT id FROM time_slots WHERE technician_id = :t AND state = 'free' "
                                   "AND start < :end ORDER BY start LIMIT 1"),
                              {"t": technician_id, "end": datetime.now() + timedelta(hours=20)}).scalar()

    def tech_of(self, job_id: int) -> int:
        return self.c.get(f"/jobs/{job_id}").json()["technician_id"]

    def status(self, job_id: int, tech: int, to: str) -> httpx.Response:
        return self.c.post(f"/jobs/{job_id}/status", json={"technician_id": tech, "to_status": to})

    def check(self, sid: str, ac: str, fn) -> None:
        try:
            detail = fn()
            self.rows.append((sid, ac, True, detail))
        except AssertionError as e:
            self.rows.append((sid, ac, False, f"ไม่ผ่าน: {e}"))
        except Exception as e:  # noqa: BLE001
            self.rows.append((sid, ac, False, f"ผิดพลาด: {type(e).__name__} {e}"))

    # ---------- scenario ----------
    def s01_book(self):
        q = self.c.get("/deposit-quote", params={"category": CAT}).json()
        assert q["estimate_amount"] == 700 and q["deposit_amount"] == 350, q
        slot = self.free_slot(1)
        r = self.book(1, slot)
        assert r.status_code == 201, r.text
        j = r.json()
        assert j["status"] == "confirmed" and j["deposit_amount"] == 350, j
        self.job1, self.slot1 = j["job_id"], slot
        return f"งาน #{j['job_id']} ยืนยันแล้ว มัดจำ 350 ราคาประเมิน 700"

    def s02_not_offered_again(self):
        slots = [s["slot_id"] for t in self.search(2) for s in t["slots"]]
        assert self.slot1 not in slots
        return f"ช่วงเวลา {self.slot1} ไม่อยู่ในผลค้นหาของลูกค้าทดสอบ 02 ({len(slots)} ช่วงที่ว่าง)"

    def s03_taken_alternatives(self):
        slot = self.free_slot(3)
        assert self.c.post(f"/slots/{slot}/hold", json={"customer_id": 3}).status_code == 200
        r = self.c.post(f"/slots/{slot}/hold", json={"customer_id": 4})
        assert r.status_code == 409 and r.json()["reason"] == "slot_taken", r.text
        alts = r.json()["alternatives"]
        assert alts, "ไม่มีช่วงใกล้เคียง"
        r2 = self.c.post(f"/slots/{alts[0]['slot_id']}/hold", json={"customer_id": 4})
        assert r2.status_code == 200 and r2.json()["hold_expires_at"], r2.text
        return f"ช่วง {slot} ถูกล็อกโดยลูกค้า 03 ลูกค้า 04 ได้ 409 พร้อมช่วงใกล้เคียง {len(alts)} ช่วง ล็อกช่วงใกล้เคียงได้ (API ส่งเวลาสิ้นสุดล็อก)"

    def s04_hold_limit(self):
        a, b = self.free_slot(5), self.free_slot(5, skip=1)
        assert self.c.post(f"/slots/{a}/hold", json={"customer_id": 5}).status_code == 200
        r = self.c.post(f"/slots/{b}/hold", json={"customer_id": 5})
        assert r.status_code == 409 and r.json()["reason"] == "hold_limit", r.text
        return "ล็อกช่วงที่สองได้ 409 hold_limit พร้อมข้อความ"

    def s05_job_status_flow(self):
        tech = self.tech_of(self.job1)
        jobs = self.c.get(f"/technicians/{tech}/jobs").json()
        assert any(j["job_id"] == self.job1 for j in jobs)
        assert all("customer_phone" not in j for j in jobs if j["job_id"] == self.job1), "เบอร์โผล่ก่อน 2 ชั่วโมง"
        for to in ("en_route", "in_progress", "done"):
            r = self.status(self.job1, tech, to)
            assert r.status_code == 200, r.text
        assert self.c.get(f"/jobs/{self.job1}").json()["status"] == "done"
        hist = self.c.get(f"/jobs/{self.job1}/history").json()["history"]
        assert [h["to_status"] for h in hist][-3:] == ["en_route", "in_progress", "done"], hist
        msgs = [m["text"] for m in self.c.get("/notifications/queue", headers=self.ops).json()
                if m["job_id"] == self.job1 and m["to_role"] == "customer"]
        assert any("เสร็จสิ้น" in t and "call center" in t and "ภายใน 7 วัน" in t for t in msgs), msgs
        assert not any("000-000-00" in t for t in msgs)  # เบอร์ลูกค้าทดสอบ (เลขของ call center 02-000-0000 ไม่ใช่ข้อมูลลูกค้า)
        return f"ช่าง {tech} กดสามปุ่ม สถานะเสร็จสิ้น ประวัติครบ ข้อความเสร็จสิ้นบอก call center ภายใน 7 วัน"

    def s06_cancel_r1(self):
        slot = self.free_slot(6, skip=-1)  # ช่วงท้ายสุดของ 7 วัน (นัดเกิน 24 ชั่วโมง)
        r = self.book(6, slot)
        assert r.status_code == 201, r.text
        jid = r.json()["job_id"]
        q = self.c.get(f"/jobs/{jid}/refund-quote", params={"customer_id": 6}).json()
        assert q["allowed"] and q["rule"] == "R1" and q["refund_amount"] == 350, q
        c = self.c.post(f"/jobs/{jid}/customer-cancel", json={"customer_id": 6}).json()
        assert c["status"] == "cancelled" and c["refund_amount"] == 350 and c["refund_result"] == "approved", c
        slots = [s["slot_id"] for t in self.search(7) for s in t["slots"]]
        assert slot in slots, "ช่วงเวลาไม่กลับเป็นว่าง"
        self.job6 = jid
        return f"งาน #{jid} R1 คืน 350 ผล approved ช่วงเวลากลับมาในผลค้นหา"

    def s07_cancel_r2(self):
        tech = 1  # ช่างทดสอบ 01 มีทักษะไฟฟ้า
        slot = self.today_slot(tech)
        assert slot, "ไม่มีช่วงเวลาวันนี้จาก uat_seed.py"
        r = self.book(8, slot, "ไฟฟ้า")
        assert r.status_code == 201, r.text
        jid = r.json()["job_id"]
        q = self.c.get(f"/jobs/{jid}/refund-quote", params={"customer_id": 8}).json()
        assert q["rule"] == "R2" and q["refund_amount"] == 200, q
        c = self.c.post(f"/jobs/{jid}/customer-cancel", json={"customer_id": 8}).json()
        assert c["refund_amount"] == 200, c
        return f"งาน #{jid} ไฟฟ้า มัดจำ 400 นัดภายใน 24 ชั่วโมง R2 คืน 200"

    def s08_cancel_r3(self):
        slot = self.free_slot(9)
        r = self.book(9, slot)
        assert r.status_code == 201, r.text
        jid = r.json()["job_id"]
        tech = self.tech_of(jid)
        assert self.status(jid, tech, "en_route").status_code == 200
        q = self.c.get(f"/jobs/{jid}/refund-quote", params={"customer_id": 9}).json()
        assert q["allowed"] and q["rule"] == "R3" and q["refund_amount"] == 250 and "ค่าเดินทาง" in q["note"], q
        c = self.c.post(f"/jobs/{jid}/customer-cancel", json={"customer_id": 9}).json()
        assert c["status"] == "cancelled" and c["refund_amount"] == 250, c
        tmsg = [m["text"] for m in self.c.get("/notifications/queue", headers=self.ops).json()
                if m["job_id"] == jid and m["to_role"] == "technician"]
        assert any("ระหว่างที่คุณกำลังเดินทาง" in t for t in tmsg), tmsg
        return f"งาน #{jid} ช่างออกเดินทางแล้ว ลูกค้ายกเลิก R3 คืน 250 ช่างได้ข้อความ"

    def s09_cancel_r6(self):
        q = self.c.get(f"/jobs/{self.job1}/refund-quote", params={"customer_id": 1}).json()
        assert q["allowed"] is False, q
        return f"งาน #{self.job1} เสร็จสิ้นแล้ว ยกเลิกไม่ได้ ข้อความ: {q['message']}"

    def s10_other_customer(self):
        r1 = self.c.get(f"/jobs/{self.job6}/refund-quote", params={"customer_id": 10})
        r2 = self.c.post(f"/jobs/{self.job6}/customer-cancel", json={"customer_id": 10})
        r3 = self.c.get("/jobs/999999/refund-quote", params={"customer_id": 10})
        assert r1.status_code == r2.status_code == r3.status_code == 403
        assert r1.json() == r3.json(), "คำตอบของงานคนอื่นกับงานที่ไม่มีต่างกัน"
        with self.db.connect() as cn:
            n = cn.execute(text("SELECT count(*) FROM security_events WHERE kind = 'denied' AND actor_id = 10")).scalar()
        assert n >= 3, n
        return f"ลูกค้า 10 ได้ 403 ทั้งงานคนอื่นและงานที่ไม่มี คำตอบเหมือนกัน บันทึก {n} รายการ"

    def s11_production_settings(self):
        assert self.c.get("/docs").status_code == 404 and self.c.get("/openapi.json").status_code == 404
        assert self.c.get("/metrics").status_code in (401, 403)
        assert self.c.get("/metrics", headers=self.ops).status_code == 200
        assert self.c.get("/ops/refunds/follow-up").status_code in (401, 403)
        slot = self.free_slot(11)
        r = self.c.post(f"/slots/{slot}/hold?now=2020-01-01T00:00:00", json={"customer_id": 11}).json()
        assert r["hold_expires_at"][:4] != "2020", r
        return "ไม่มี /docs /openapi.json endpoint ของ ops ต้องมีกุญแจ ช่อง now= ถูกเพิกเฉย"

    def s12_assistant_switch(self):
        st = self.c.get("/assistant/status").json()
        return f"ผู้ช่วยตอนนี้ enabled={st['enabled']} (ตรวจแยกตามส่วนผู้ช่วยของแผน ไม่นับในผลของ 002 ถึง 004)"

    def declined(self):
        slot = self.free_slot(12, skip=-1)
        r = self.book(12, slot)
        assert r.status_code == 201, r.text
        jid = r.json()["job_id"]
        c = self.c.post(f"/jobs/{jid}/customer-cancel", json={"customer_id": 12}).json()
        assert c["status"] == "cancelled" and c["refund_result"] == "declined" and "ตรวจสอบเพิ่ม" in c["refund_message"], c
        rows = self.c.get("/ops/refunds/follow-up", headers=self.ops).json()
        assert any(x["job_id"] == jid and x["result"] == "declined" for x in rows), rows
        return f"งาน #{jid} gateway ปฏิเสธคำขอคืนเงิน งานยังยกเลิก ลูกค้าเห็นข้อความตรวจสอบเพิ่ม รายการอยู่ใน follow-up ของ Finance"

    def run(self, group: str) -> int:
        if group == "declined":
            self.check("S-14", "AC-08-11", self.declined)
        else:
            for sid, ac, fn in [
                ("S-01", "AC-07-01, AC-07-11, AC-07-19", self.s01_book),
                ("S-02", "AC-07-02", self.s02_not_offered_again),
                ("S-03", "AC-07-04", self.s03_taken_alternatives),
                ("S-04", "AC-07-14", self.s04_hold_limit),
                ("S-05", "AC-09-01 ถึง 04, AC-09-07, AC-09-08, AC-09-10, AC-09-15", self.s05_job_status_flow),
                ("S-06", "AC-08-01 ถึง 03, AC-08-05", self.s06_cancel_r1),
                ("S-07", "AC-07-10 R2", self.s07_cancel_r2),
                ("S-08", "AC-08-12", self.s08_cancel_r3),
                ("S-09", "AC-08-06", self.s09_cancel_r6),
                ("S-10", "AC-08-10", self.s10_other_customer),
                ("S-11", "AC-00-06, AC-00-07", self.s11_production_settings),
                ("S-12", "UC-14 (ตรวจแยก)", self.s12_assistant_switch),
            ]:
                self.check(sid, ac, fn)
        print(f"# เดินซ้อม scenario ผ่าน API เวลาเครื่อง {datetime.now():%Y-%m-%d %H:%M} กลุ่ม {group}")
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
    ap.add_argument("--db", required=True)
    ap.add_argument("--group", default="main", choices=["main", "declined"])
    a = ap.parse_args()
    sys.exit(Replay(a.base, a.ops_token, a.db).run(a.group))
