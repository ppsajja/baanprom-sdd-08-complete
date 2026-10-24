"""ทดสอบโหลดเต็มรูปสำหรับการตรวจรับ R1 (เงื่อนไข ค3 ใน docs/acceptance/acceptance-record-r1.md) ไม่ใช่ส่วนของระบบ
AC-07-08 (REQ-QA-003 ฉบับ CR-02): ลูกค้า 500 คนส่ง GET /technicians พร้อมกัน ทุกคำขอได้รายการช่างครบ 95 ใน 100 ไม่เกิน 2 วินาที
AC-09-12: ช่าง 50 คนกดสถานะพร้อมกัน p95 ไม่เกิน 1 วินาที | AC-08-09: ลูกค้า 50 คนยกเลิกพร้อมกัน p95 ไม่เกิน 2 วินาที (ไม่รวมเวลารอ gateway)
เวลาวัดที่ฝั่งผู้ยิงโหลด (Q-24) ตั้งแต่ส่งคำขอจนได้คำตอบครบ ใช้ asyncio กับ httpx ที่มีอยู่แล้วใน requirements.txt (ทีมเลือกเอง แทน locust หรือ k6)
ใช้: python load_test.py --base http://127.0.0.1:8000 [--users 500] [--rounds 3] [--small 50] (--small 0 วัดเฉพาะการค้นหา)
ข้อมูลต้องมาจาก uat_seed.py บนฐานข้อมูลของเครื่องทดสอบ สคริปต์สร้างงานที่ต้องใช้เองผ่าน API
CR-11 (R2): ทุกคำขอต้องมี token ใช้ --db เพื่อออก session ให้บัญชีทดสอบ (uat_auth.py)
CR-13 (Q-68 ปิดใน EV-051): AC-07-08 ฉบับใหม่ "ลูกค้า 500 คนที่ใช้งานอยู่ ค้นหารวม 50 ครั้งต่อวินาที ต่อเนื่อง 5 นาที"
  --rate 50 --duration 300 ยิงแบบเปิด (ส่งตามเวลา ไม่รอคำตอบก่อนส่งคำขอถัดไป) แบบ 500 คำขอในวินาทีเดียวของ R1 ยังวัดได้ด้วย --users"""
import argparse
import asyncio
import statistics
import time

import httpx

from uat_auth import TestTokens

CAT = "ประปา"
TOKENS: TestTokens | None = None


def H(role: str, i: int) -> dict:
    return TOKENS.headers(role, i)


def pct(values: list[float], p: float) -> float:
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round(p / 100 * len(s) + 0.5)) - 1))
    return s[k]


def summary(name: str, times: list[float], oks: list[bool], limit: float, need_per_100: int) -> dict:
    within = sum(1 for t, ok in zip(times, oks) if ok and t <= limit)
    res = {"name": name, "n": len(times), "ok": sum(oks), "p50": statistics.median(times), "p95": pct(times, 95),
           "max": max(times), "within": within, "limit": limit,
           "pass": sum(oks) == len(oks) and within * 100 >= need_per_100 * len(times)}
    print(f"{name}: คำขอ {res['n']} สำเร็จ {res['ok']} p50 {res['p50']:.3f} s p95 {res['p95']:.3f} s "
          f"สูงสุด {res['max']:.3f} s ไม่เกิน {limit:g} s {within} จาก {res['n']} "
          f"เกณฑ์ {need_per_100} ใน 100 ผล {'ผ่าน' if res['pass'] else 'ไม่ผ่าน'}", flush=True)
    return res


async def timed(client: httpx.AsyncClient, method: str, url: str, **kw) -> tuple[float, httpx.Response | None]:
    t0 = time.perf_counter()
    try:
        r = await client.request(method, url, **kw)
    except httpx.HTTPError:
        return time.perf_counter() - t0, None
    return time.perf_counter() - t0, r


async def search_round(base: str, users: int) -> dict:
    limits = httpx.Limits(max_connections=users, max_keepalive_connections=users)
    async with httpx.AsyncClient(base_url=base, timeout=60, limits=limits) as c:
        reqs = [timed(c, "GET", "/technicians", params={"category": CAT, "address_id": i % 30 + 1},
                      headers=H("customer", i % 30 + 1)) for i in range(users)]
        out = await asyncio.gather(*reqs)
    oks = [r is not None and r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0 for _, r in out]
    return summary(f"AC-07-08 (R1) ค้นหาพร้อมกัน {users} คนในวินาทีเดียว", [t for t, _ in out], oks, 2.0, 95)


async def rate_round(base: str, rate: int, duration: int) -> dict:
    """CR-13 (Q-68): ลูกค้า 500 คนที่ใช้งานอยู่ ค้นหารวม rate ครั้งต่อวินาที นาน duration วินาที ส่งตามนาฬิกา (open model)"""
    limits = httpx.Limits(max_connections=1000, max_keepalive_connections=500)
    async with httpx.AsyncClient(base_url=base, timeout=60, limits=limits) as c:
        tasks = []
        t0 = time.perf_counter()
        for i in range(rate * duration):
            due = t0 + i / rate
            wait = due - time.perf_counter()
            if wait > 0:
                await asyncio.sleep(wait)
            cid = i % 30 + 1
            tasks.append(asyncio.create_task(timed(c, "GET", "/technicians", params={"category": CAT, "address_id": cid},
                                                   headers=H("customer", cid))))
        sent_for = time.perf_counter() - t0
        out = await asyncio.gather(*tasks)
    oks = [r is not None and r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0 for _, r in out]
    print(f"ส่งครบ {len(tasks)} คำขอใน {sent_for:.1f} วินาที (เป้า {duration} วินาที)", flush=True)
    return summary(f"AC-07-08 (R2) ค้นหา {rate} ครั้งต่อวินาที นาน {duration} วินาที", [t for t, _ in out], oks, 2.0, 95)


def make_jobs(base: str, n: int, start_customer: int) -> list[dict]:
    """สร้างงานยืนยันแล้ว n งานผ่าน API (ทีละงาน ไม่นับเวลา) คืน job_id และ technician_id"""
    jobs = []
    with httpx.Client(base_url=base, timeout=30) as c:
        cust = start_customer
        while len(jobs) < n:
            cid = cust % 30 + 1
            cust += 1
            techs = c.get("/technicians", params={"category": CAT, "address_id": cid}, headers=H("customer", cid)).json()
            slots = [s["slot_id"] for t in techs for s in t["slots"]]
            if not slots:
                raise SystemExit("ช่วงเวลาว่างไม่พอ ให้รัน uat_seed.py ใหม่บนฐานว่าง")
            r = c.post("/bookings", json={"slot_id": slots[-1], "address_id": cid, "category": CAT}, headers=H("customer", cid))
            if r.status_code == 201:
                jobs.append({"job_id": r.json()["job_id"], "technician_id": r.json()["technician_id"], "customer_id": cid})
    return jobs


async def status_round(base: str, jobs: list[dict]) -> dict:
    async with httpx.AsyncClient(base_url=base, timeout=60) as c:
        out = await asyncio.gather(*[timed(c, "POST", f"/jobs/{j['job_id']}/status",
                                           json={"to_status": "en_route"}, headers=H("technician", j["technician_id"]))
                                     for j in jobs])
    oks = [r is not None and r.status_code == 200 for _, r in out]
    return summary(f"AC-09-12 ช่างกดสถานะพร้อมกัน {len(jobs)} งาน", [t for t, _ in out], oks, 1.0, 95)


async def cancel_round(base: str, jobs: list[dict]) -> dict:
    async with httpx.AsyncClient(base_url=base, timeout=60) as c:
        out = await asyncio.gather(*[timed(c, "POST", f"/jobs/{j['job_id']}/customer-cancel",
                                           headers=H("customer", j["customer_id"])) for j in jobs])
    oks = [r is not None and r.status_code == 200 for _, r in out]
    return summary(f"AC-08-09 ลูกค้ายกเลิกพร้อมกัน {len(jobs)} งาน", [t for t, _ in out], oks, 2.0, 95)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--users", type=int, default=500)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--small", type=int, default=50)
    ap.add_argument("--db", required=True, help="DATABASE_URL ของเครื่องทดสอบ (ออก session ให้บัญชีทดสอบ)")
    ap.add_argument("--rate", type=int, default=0, help="CR-13 จำนวนคำค้นต่อวินาที (0 = ไม่วัดแบบอัตรา)")
    ap.add_argument("--duration", type=int, default=300)
    a = ap.parse_args()
    global TOKENS
    TOKENS = TestTokens(a.db)
    for i in range(1, 31):  # ออก session ก่อนเริ่มจับเวลา
        TOKENS.token("customer", i)
    results = []
    with httpx.Client(base_url=a.base, timeout=30) as c:  # อุ่นเครื่อง 1 คำขอ ไม่นับ
        c.get("/technicians", params={"category": CAT, "address_id": 1}, headers=H("customer", 1))
    if a.rate > 0:
        results.append(asyncio.run(rate_round(a.base, a.rate, a.duration)))
    for i in range(a.rounds):
        print(f"รอบที่ {i + 1}", flush=True)
        results.append(asyncio.run(search_round(a.base, a.users)))
    if a.small > 0:  # --small 0 วัดเฉพาะการค้นหา (ใช้หาจำนวนคนสูงสุดที่ยังผ่านเกณฑ์)
        jobs = make_jobs(a.base, 2 * a.small, 0)
        results.append(asyncio.run(status_round(a.base, jobs[:a.small])))
        results.append(asyncio.run(cancel_round(a.base, jobs[a.small:])))
    ok = all(r["pass"] for r in results)
    print(f"สรุป: {'ผ่านทุกข้อ' if ok else 'มีข้อไม่ผ่าน'}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
