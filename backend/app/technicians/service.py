"""REQ-FN-008 ค้นช่างว่างใน 7 วัน | BR-02 ไม่เสนอช่วงที่จองหรือล็อกโดยคนอื่น | BR-03 ระยะไม่เกิน 15 กม."""
from datetime import datetime, timedelta
import math

from sqlalchemy import select

from app import config
from app.db.models import Technician, TimeSlot, ServiceAddress, Job, SLOT_FREE, SLOT_HELD, SLOT_BOOKED


def distance_km(lat1, lng1, lat2, lng2) -> float:
    """ระยะทางโดยประมาณ (IF-03 ในระบบจริงเรียกบริการแผนที่ ตอนนี้ใช้สูตร haversine)"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def release_expired_holds(db, now: datetime) -> None:
    # รองรับ AS-07: ล็อกหมดอายุเองโดยไม่ต้องมีใครปลด ตรวจทุกครั้งที่อ่าน slot
    # CR-07 REQ-QA-010: ถ้าช่วงนั้นมีงาน "รอชำระเงิน" ที่การชำระยัง pending (gateway ไม่ตอบ) ให้ปิดเรื่องเงินก่อนปล่อยช่วง
    from app.payments.service import settle_on_hold_expiry
    from app.payments.gateway import get_gateway
    for slot in db.scalars(select(TimeSlot).where(TimeSlot.state == SLOT_HELD)).all():
        if slot.hold_expires_at and slot.hold_expires_at <= now:
            pending_job = db.scalars(select(Job).where(Job.slot_id == slot.id, Job.status == "pending_payment")).first()
            if pending_job is not None and settle_on_hold_expiry(db, pending_job, slot, get_gateway(), now):
                continue
            slot.state, slot.held_by_customer_id, slot.hold_expires_at = SLOT_FREE, None, None
    db.flush()  # CR-07: คำค้นถัดไป (เช่น นับล็อกของลูกค้าใน REQ-SEC-011) ต้องเห็นล็อกที่เพิ่งปล่อย (autoflush ปิดอยู่)


def slot_visible_to(slot: TimeSlot, customer_id: int | None) -> bool:
    # รองรับ BR-02: ช่วงที่จองแล้วไม่ว่าง ช่วงที่คนอื่นล็อกไว้ก็ไม่ว่าง (ของตัวเองยังเห็น)
    if slot.state == SLOT_BOOKED:
        return False
    if slot.state == SLOT_HELD and slot.held_by_customer_id != customer_id:
        return False
    return True


def search_available(db, category: str, address: ServiceAddress, now: datetime,
                     customer_id: int | None = None) -> list[dict]:
    """คืนรายการช่างพร้อมช่วงเวลาที่ว่างใน SEARCH_DAYS_AHEAD วันถัดไป (AS-06 ไม่รวมวันนี้)
    CR-13 (Q-68): เดิมค้นช่วงเวลาทีละช่าง (1 + จำนวนช่าง คำค้น) ตอนนี้กรองทักษะและระยะจากตารางช่างก่อน
    แล้วค้นช่วงเวลาของช่างที่ผ่านทั้งหมดในคำค้นเดียว ผลและลำดับเหมือนเดิม (ช่างตามรหัส ช่วงเวลาตามเวลาเริ่ม)"""
    release_expired_holds(db, now)
    day_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=config.SEARCH_DAYS_AHEAD)
    techs = []
    for tech in db.scalars(select(Technician).order_by(Technician.id)):
        if category not in [s.strip() for s in tech.skills.split(",")]:
            continue
        # รองรับ BR-03: ช่างที่ไกลเกินระยะให้บริการไม่ปรากฏในผลค้นหา
        if distance_km(tech.base_lat, tech.base_lng, address.lat, address.lng) > config.MAX_SERVICE_DISTANCE_KM:
            continue
        techs.append(tech)
    if not techs:
        return []
    by_tech: dict[int, list] = {t.id: [] for t in techs}
    rows = db.execute(
        select(TimeSlot.id, TimeSlot.technician_id, TimeSlot.start, TimeSlot.end, TimeSlot.state, TimeSlot.held_by_customer_id)
        .where(TimeSlot.technician_id.in_(list(by_tech)), TimeSlot.start >= day_start, TimeSlot.start < day_end)
        .order_by(TimeSlot.technician_id, TimeSlot.start)
    ).all()
    for r in rows:
        # รองรับ BR-02 (slot_visible_to เดิม): ช่วงที่จองแล้วไม่ว่าง ช่วงที่คนอื่นล็อกไว้ก็ไม่ว่าง (ของตัวเองยังเห็น)
        if r.state == SLOT_BOOKED or (r.state == SLOT_HELD and r.held_by_customer_id != customer_id):
            continue
        by_tech[r.technician_id].append({"slot_id": r.id, "start": r.start.isoformat(), "end": r.end.isoformat()})
    return [{"technician_id": t.id, "name": t.name, "slots": by_tech[t.id]} for t in techs if by_tech[t.id]]


def find_alternatives(db, taken: TimeSlot, now: datetime, customer_id: int | None = None) -> list[dict]:
    """AC-07-04 (CR-01): ช่วงที่ว่าง ซึ่งเริ่มห่างจากช่วงที่เลือกไม่เกิน ALTERNATIVE_WINDOW_HOURS ชั่วโมง"""
    release_expired_holds(db, now)
    window = timedelta(hours=config.ALTERNATIVE_WINDOW_HOURS)
    slots = db.scalars(
        select(TimeSlot).where(TimeSlot.start >= taken.start - window, TimeSlot.start <= taken.start + window,
                               TimeSlot.id != taken.id).order_by(TimeSlot.start)
    ).all()
    return [
        {"slot_id": s.id, "technician_id": s.technician_id, "technician_name": s.technician.name,
         "start": s.start.isoformat(), "end": s.end.isoformat()}
        for s in slots if slot_visible_to(s, customer_id)
    ]
