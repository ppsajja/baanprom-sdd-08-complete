"""CR-15 (UC-11 specs/009-rating) ลูกค้าให้คะแนนช่างหลังงานเสร็จ ตามกฎ BR-11 (Q-20 ปิดใน EV-051 คำตอบของ SH-01)
1 ให้คะแนนได้เฉพาะเจ้าของงาน (token) 2 งานต้อง "เสร็จสิ้น" 3 งานละ 1 ครั้ง แก้ไม่ได้ 4 ภายใน 14 วันหลังช่างปิดงาน
5 บัญชีลูกค้าที่เบอร์ตรงกับบัญชีของช่างคนนั้น บันทึกได้ แต่ไม่นับในค่าเฉลี่ย (กันช่างรีวิวตัวเอง)
6 ค่าเฉลี่ยแสดงเมื่อมีอย่างน้อย 3 คะแนน ไม่ใช้เรียงหรือคัดช่าง (REQ-AI-002 ยัง Won't BR-07 ไม่ใช้คะแนน)
ความเห็นเก็บหลังปิดบังเบอร์ อีเมล เลขบัตร (REQ-PRV-012) ไม่แสดงต่อลูกค้าคนอื่นและไม่แสดงต่อช่าง หัวหน้าช่างอ่านได้ทาง Ops"""
from datetime import datetime, timedelta

from sqlalchemy import func, select

from app import config
from app.db.models import Account, Job, JobStatusHistory, Rating
from app.privacy import mask_text

MESSAGES = {
    "not_done": "ให้คะแนนได้เฉพาะงานที่ เสร็จสิ้น แล้ว",
    "already_rated": "งานนี้ให้คะแนนแล้ว",
    "window_passed": f"ให้คะแนนได้ภายใน {config.RATING_WINDOW_DAYS} วันหลังงานเสร็จ",
    "bad_stars": "คะแนนต้องเป็น 1 ถึง 5 ดาว",
}
MSG_THANKS = "ขอบคุณสำหรับคะแนน"


class RatingError(Exception):
    def __init__(self, reason: str):
        self.reason, self.message = reason, MESSAGES[reason]


def done_at(db, job: Job) -> datetime | None:
    return db.scalars(select(JobStatusHistory.at).where(JobStatusHistory.job_id == job.id,
                                                         JobStatusHistory.to_status == "done")
                      .order_by(JobStatusHistory.id.desc())).first()


def rating_of(db, job_id: int) -> Rating | None:
    return db.scalars(select(Rating).where(Rating.job_id == job_id)).first()


def can_rate(db, job: Job, now: datetime) -> bool:
    if job.status != "done" or rating_of(db, job.id) is not None:
        return False
    at = done_at(db, job)
    return at is not None and now - at <= timedelta(days=config.RATING_WINDOW_DAYS)


def _self_review(db, customer_id: int, technician_id: int) -> bool:
    phones = {a.role: a.phone_norm for a in db.scalars(select(Account).where(
        ((Account.role == "customer") & (Account.subject_id == customer_id)) |
        ((Account.role == "technician") & (Account.subject_id == technician_id))))}
    return bool(phones.get("customer")) and phones.get("customer") == phones.get("technician")


def rate(db, job: Job, stars: int, comment: str, now: datetime) -> Rating:
    if not isinstance(stars, int) or not 1 <= stars <= 5:
        raise RatingError("bad_stars")
    if job.status != "done":
        raise RatingError("not_done")
    if rating_of(db, job.id) is not None:
        raise RatingError("already_rated")
    at = done_at(db, job)
    if at is None or now - at > timedelta(days=config.RATING_WINDOW_DAYS):
        raise RatingError("window_passed")
    r = Rating(job_id=job.id, customer_id=job.customer_id, technician_id=job.technician_id, stars=stars,
               comment=mask_text((comment or "").strip())[:config.RATING_COMMENT_MAX],
               counted=not _self_review(db, job.customer_id, job.technician_id), at=now)
    db.add(r)
    db.commit()
    return r


def summaries(db, technician_ids: list[int]) -> dict[int, dict]:
    """REQ-FN-069 ค่าเฉลี่ยทศนิยม 1 ตำแหน่งและจำนวน นับเฉพาะคะแนนที่ counted average เป็น None เมื่อน้อยกว่า 3"""
    out = {t: {"average": None, "count": 0} for t in technician_ids}
    if not technician_ids:
        return out
    rows = db.execute(select(Rating.technician_id, func.count(Rating.id), func.avg(Rating.stars))
                      .where(Rating.technician_id.in_(technician_ids), Rating.counted.is_(True))
                      .group_by(Rating.technician_id)).all()
    for tid, n, avg in rows:
        out[tid] = {"average": round(float(avg), 1) if n >= config.RATING_MIN_COUNT_TO_SHOW else None, "count": n}
    return out


def comments_for(db, technician_id: int) -> list[dict]:
    """มุมมองของหัวหน้าช่าง (SH-06) ผ่านกุญแจของ Ops: เลขงาน ดาว ความเห็นที่ปิดบังแล้ว ไม่มีชื่อหรือเบอร์ลูกค้า"""
    rows = db.scalars(select(Rating).where(Rating.technician_id == technician_id).order_by(Rating.id)).all()
    return [{"job_id": r.job_id, "stars": r.stars, "comment": r.comment, "counted": r.counted, "at": r.at.isoformat()}
            for r in rows]


def erase(db, customer_id: int) -> None:
    """REQ-PRV-012 บรรทัดที่ 3: ลูกค้าขอลบข้อมูล ความเห็นถูกลบ คะแนนดาวคงอยู่แบบไม่ระบุตัว"""
    for r in db.scalars(select(Rating).where(Rating.customer_id == customer_id)):
        r.comment = ""
