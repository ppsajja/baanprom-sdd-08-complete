"""AC-00-09 ถึง AC-00-11 จาก cross-cutting.feature v1.1 (CR-13, Q-67 ปิดใน EV-051)
REQ-OP-008 คิวข้อความไม่หายเมื่อหลังบ้านเริ่มใหม่ และรันหลังบ้านหลาย process ได้"""
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import NotificationMessage, SchedulerLease
from app.notify.queue import FakeNotifier, queue
from app.ops import lease
from app.ops.metrics import Metrics, combined, flush_to_db
from tests.conftest import NOW, OPS, book


# รองรับ AC-00-09 (REQ-OP-008 บรรทัดที่ 1)
def test_AC_00_09_queued_messages_survive_restart(client, db, seed):
    # Given จองสำเร็จ มีข้อความ 2 ข้อความในคิว ยังไม่ส่ง
    r = book(client, customer_id=seed["somchai"].id, slot_id=seed["slot"].id, address_id=seed["addr"].id)
    job_id = r.json()["job_id"]
    assert len(db.scalars(select(NotificationMessage).where(NotificationMessage.job_id == job_id)).all()) == 2
    # When หลังบ้านเริ่มใหม่ (สร้างแอปใหม่บนฐานข้อมูลเดิม)
    from app.main import create_app
    with TestClient(create_app()) as fresh:
        # Then GET /notifications/queue ยังเห็นทั้ง 2 ข้อความ
        rows = [m for m in fresh.get("/notifications/queue", headers=OPS).json() if m["job_id"] == job_id]
        assert sorted(m["to_role"] for m in rows) == ["customer", "technician"]
    # And ตัวส่งรอบถัดไปส่งครบ และไม่ส่งซ้ำ
    n = FakeNotifier()
    assert queue.deliver_due(n, NOW + timedelta(seconds=30)) == 2
    assert queue.deliver_due(n, NOW + timedelta(minutes=10)) == 0 and len(n.sent) == 2


# รองรับ AC-00-10 (REQ-OP-008 บรรทัดที่ 2): งานเบื้องหลังทำที่ process เดียว และมีคนรับต่อเมื่อ process นั้นดับ
def test_AC_00_10_one_process_holds_the_scheduler_lease(db):
    a, b = "host:1", "host:2"
    assert lease.acquire(db, a, NOW) is True
    assert lease.acquire(db, b, NOW + timedelta(seconds=10)) is False
    assert lease.acquire(db, a, NOW + timedelta(seconds=60)) is True       # ต่ออายุ
    # When process a ดับ ไม่ต่ออายุ เกิน 90 วินาที Then process b รับต่อ
    assert lease.acquire(db, b, NOW + timedelta(seconds=60 + 91)) is True
    assert db.get(SchedulerLease, "tick").holder == b


# รองรับ AC-00-11 (REQ-OP-008 บรรทัดที่ 3, REQ-OP-005): ตัวนับรวมทุก process
def test_AC_00_11_metrics_from_two_processes_add_up(client, db):
    p1, p2 = Metrics(), Metrics()
    for _ in range(3):
        p1.record("GET /technicians", 200, 10.0, NOW)
    p2.record("GET /technicians", 500, 30.0, NOW)
    # When แต่ละ process ส่งยอดของนาทีที่จบแล้ว
    assert flush_to_db(db, p1, NOW + timedelta(minutes=1)) == 1
    assert flush_to_db(db, p2, NOW + timedelta(minutes=1)) == 1
    # Then ยอดรวมของนาทีนั้นคือ 4 คำขอ ล้มเหลว 1 และนาทีปัจจุบันของ process ที่ตอบรวมด้วย
    p1.record("GET /technicians", 200, 5.0, NOW + timedelta(minutes=1))
    rows = {b["minute"]: b for b in combined(db, p1).as_dicts()}
    assert rows[NOW.isoformat()]["requests"] == 4 and rows[NOW.isoformat()]["failures"] == 1
    assert rows[NOW.isoformat()]["max_ms"] == 30.0
    assert rows[(NOW + timedelta(minutes=1)).isoformat()]["requests"] == 1
