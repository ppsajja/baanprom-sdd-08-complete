"""CR-07 REQ-OP-005 บรรทัดที่ 1: นับจำนวนคำขอ เวลาตอบ และคำขอที่ล้มเหลว แยกตาม endpoint ทุก 1 นาที
endpoint นับตามแม่แบบของ path (เช่น /jobs/{job_id}/status) ไม่ใช่ path จริง เพื่อไม่ให้เลขงานกลายเป็นแถวใหม่
"ล้มเหลว" = คำตอบ 5xx (ฝั่งเราผิด) และ 402 (ชำระไม่สำเร็จ ซึ่งเป็นอาการแรกของเหตุการณ์ที่ 1 ในคู่มือ)
คำตอบ 4xx อื่นเป็นความผิดของผู้ขอ ไม่นับเป็นล้มเหลว แต่ 403 ถูกนับแยกใน security_events (REQ-SEC-010)
ตัวเก็บอยู่ในหน่วยความจำ (ทีมเลือกเอง เหมือน notify/queue.py) ระบบจริงส่งออกให้เครื่องมือเฝ้าดูผ่าน GET /metrics
CR-13 (Q-67 ปิดใน EV-051, REQ-OP-008): เมื่อรันหลาย process แต่ละ process นับในหน่วยความจำของตัวเอง แล้วทุกนาที
ส่งยอดของนาทีที่จบแล้วไปบวกในตาราง metric_minutes (flush_to_db) GET /metrics และการเตือนอ่านยอดรวม (combined)
ยอดของนาทีปัจจุบันที่ยังไม่ส่ง หายได้เมื่อ process ดับ (Ops lead ยอมรับใน EV-051 ไม่เกิน 1 นาทีต่อ process)"""
from collections import defaultdict

from sqlalchemy import func
from dataclasses import dataclass, asdict
from datetime import datetime

from app import config

FAILURE_STATUSES = {402}


@dataclass
class Bucket:
    endpoint: str
    minute: str          # เวลาเริ่มของนาที ISO 8601
    requests: int = 0
    failures: int = 0
    empty_results: int = 0   # GET /technicians ตอบ 200 แต่ไม่มีช่าง (คู่มือเหตุการณ์ที่ 3)
    total_ms: float = 0.0
    max_ms: float = 0.0


def minute_of(at: datetime) -> datetime:
    # ช่องละ METRIC_BUCKET_SECONDS = 60 วินาที คือตัดวินาทีทิ้ง
    assert config.METRIC_BUCKET_SECONDS == 60
    return at.replace(second=0, microsecond=0)


def is_failure(status_code: int) -> bool:
    return status_code >= 500 or status_code in FAILURE_STATUSES


class Metrics:
    def __init__(self) -> None:
        self.buckets: dict[tuple[str, datetime], Bucket] = {}

    def record(self, endpoint: str, status_code: int, ms: float, at: datetime, empty: bool = False) -> None:
        key = (endpoint, minute_of(at))
        b = self.buckets.get(key)
        if b is None:
            b = self.buckets[key] = Bucket(endpoint=endpoint, minute=key[1].isoformat())
        b.requests += 1
        b.failures += 1 if is_failure(status_code) else 0
        b.empty_results += 1 if empty else 0
        b.total_ms += ms
        b.max_ms = max(b.max_ms, ms)

    def per_minute_totals(self) -> dict[datetime, tuple[int, int]]:
        """รวมทุก endpoint ต่อนาที: (คำขอ, ล้มเหลว) ใช้ตัดสินการเตือนใน alerts.py"""
        totals: dict[datetime, list[int]] = defaultdict(lambda: [0, 0])
        for (_, minute), b in self.buckets.items():
            totals[minute][0] += b.requests
            totals[minute][1] += b.failures
        return {m: (r, f) for m, (r, f) in totals.items()}

    def as_dicts(self) -> list[dict]:
        out = []
        for b in sorted(self.buckets.values(), key=lambda x: (x.minute, x.endpoint)):
            d = asdict(b)
            d["avg_ms"] = round(b.total_ms / b.requests, 2) if b.requests else 0.0
            del d["total_ms"]
            out.append(d)
        return out

    def clear(self) -> None:
        self.buckets.clear()


metrics = Metrics()


def flush_to_db(db, m: Metrics, now: datetime) -> int:
    """CR-13: ส่งยอดของนาทีที่จบแล้ว (ก่อนนาทีของ now) ไปบวกในตาราง แล้วลบออกจากหน่วยความจำ คืนจำนวนแถวที่ส่ง"""
    from app.db.models import MetricMinute
    current = minute_of(now)
    done = [(k, b) for k, b in m.buckets.items() if k[1] < current]
    if not done:
        return 0
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    for (endpoint, minute), b in done:
        stmt = insert(MetricMinute).values(endpoint=endpoint, minute=minute, requests=b.requests, failures=b.failures,
                                           empty_results=b.empty_results, total_ms=b.total_ms, max_ms=b.max_ms)
        t = MetricMinute.__table__.c
        stmt = stmt.on_conflict_do_update(index_elements=["endpoint", "minute"], set_={
            "requests": t.requests + b.requests, "failures": t.failures + b.failures,
            "empty_results": t.empty_results + b.empty_results, "total_ms": t.total_ms + b.total_ms,
            "max_ms": func.greatest(t.max_ms, b.max_ms) if dialect == "postgresql" else func.max(t.max_ms, b.max_ms)})
        db.execute(stmt)
    db.commit()
    for k, _ in done:
        m.buckets.pop(k, None)
    return len(done)


def combined(db, m: Metrics, since: datetime | None = None) -> Metrics:
    """CR-13: ยอดรวมของทุก process = แถวในตาราง (นาทีที่จบแล้ว) บวกยอดที่ยังอยู่ในหน่วยความจำของ process นี้"""
    from sqlalchemy import select, inspect
    from app.db.models import MetricMinute
    out = Metrics()
    if inspect(db.get_bind()).has_table("metric_minutes"):
        q = select(MetricMinute)
        if since is not None:
            q = q.where(MetricMinute.minute >= since)
        for r in db.scalars(q).all():
            out.buckets[(r.endpoint, r.minute)] = Bucket(endpoint=r.endpoint, minute=r.minute.isoformat(),
                                                         requests=r.requests, failures=r.failures,
                                                         empty_results=r.empty_results, total_ms=r.total_ms,
                                                         max_ms=r.max_ms)
    for k, b in m.buckets.items():
        if since is not None and k[1] < since:
            continue
        cur = out.buckets.get(k)
        if cur is None:
            out.buckets[k] = Bucket(**asdict(b))
            continue
        cur.requests += b.requests
        cur.failures += b.failures
        cur.empty_results += b.empty_results
        cur.total_ms += b.total_ms
        cur.max_ms = max(cur.max_ms, b.max_ms)
    return out
