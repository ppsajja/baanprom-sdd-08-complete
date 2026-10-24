"""CR-15 endpoint ของ UC-11 (specs/009-rating/plan.md ข้อ 4)
POST /jobs/{id}/rating (ลูกค้าเจ้าของงาน) GET /me/rating (ช่าง ค่าเฉลี่ยของตัวเอง) GET /ops/technicians/{id}/ratings (Ops หัวหน้าช่าง)"""
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import current_customer, current_technician
from app.auth.service import Actor
from app.clock import get_now
from app.db.session import get_db
from app.ops import audit
from app.ops.guard import require_ops
from app.privacy import get_logger, log_event
from app.rating import service

router = APIRouter()
log = get_logger(__name__)


class RatingIn(BaseModel):
    stars: int
    comment: str = Field(default="", max_length=1000)


@router.post("/jobs/{job_id}/rating", status_code=201)
def rate(job_id: int, body: RatingIn, actor: Actor = Depends(current_customer), db: Session = Depends(get_db),
         now: datetime = Depends(get_now)):
    # รองรับ REQ-FN-068 BR-11 ข้อ 1 ถึง 5 | REQ-SEC-010 งานของคนอื่นตอบ 403 และบันทึก
    job = audit.job_of_customer(db, job_id, actor.subject_id, "POST /jobs/{id}/rating", now)
    try:
        r = service.rate(db, job, body.stars, body.comment, now)
    except service.RatingError as e:
        return JSONResponse({"reason": e.reason, "message": e.message},
                            status_code=422 if e.reason == "bad_stars" else 409)
    log_event(log, "job_rated", job_id=job.id, technician_id=job.technician_id, count=r.stars)
    return {"job_id": job.id, "stars": r.stars, "message": service.MSG_THANKS}


@router.get("/me/rating")
def my_rating(actor: Actor = Depends(current_technician), db: Session = Depends(get_db)):
    # REQ-FN-069: ช่างเห็นค่าเฉลี่ยและจำนวนของตัวเอง ไม่เห็นความเห็นและไม่รู้ว่าใครให้ (REQ-PRV-012)
    return service.summaries(db, [actor.subject_id])[actor.subject_id]


@router.get("/ops/technicians/{technician_id}/ratings", dependencies=[Depends(require_ops)])
def ratings_for_head(technician_id: int, db: Session = Depends(get_db)):
    return {"technician_id": technician_id, "summary": service.summaries(db, [technician_id])[technician_id],
            "ratings": service.comments_for(db, technician_id)}
