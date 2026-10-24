"""UC-09 ช่างอัปเดตสถานะงาน | REQ-FN-050 รายการงานของช่าง | REQ-FN-051 เปลี่ยนสถานะตาม MD-STM-01
REQ-DAT-002 ประวัติสถานะ | REQ-FN-053 แจ้งลูกค้าภายใน 60 วินาที | REQ-SEC-004 เบอร์ลูกค้าตามช่วงเวลา"""
from datetime import datetime

from sqlalchemy import select

from app import config

from app.db.models import Job, JobStatusHistory, set_status
from app.booking.service import technician_view
from app.notify.queue import queue
from app.jobstatus.transitions import allowed_next, is_allowed, ACTION_LABELS, STATUS_TH


class TransitionNotAllowed(Exception):
    """REQ-FN-051: ลูกศรที่ MD-STM-01 ไม่มี (รวมการย้อนกลับ Q-30) ระบบปฏิเสธ ไม่บันทึกประวัติ"""
    def __init__(self, from_status: str, to_status: str):
        self.from_status, self.to_status = from_status, to_status


class NotOwner(Exception):
    """REQ-FN-050 / REQ-FN-051: งานไม่ใช่ของช่างคนนี้"""


def technician_job_view(job: Job, now: datetime, db=None) -> dict:
    """มุมมองช่าง 1 งาน: ใช้กฎเบอร์โทรเดิมของ UC-07 (technician_view, REQ-SEC-004) แล้วเพิ่มปุ่มที่กดได้
    CR-12: ถ้าส่ง db มา เพิ่มสถานะการตอบรับ (assignment) และปุ่มรับงาน ปฏิเสธงาน (responses) ของ UC-12"""
    data = technician_view(job, now)
    data["next_statuses"] = [
        {"status": s, "label": ACTION_LABELS[s]} for s in allowed_next(job.status)
    ]
    if db is not None:
        from app.matching.service import response_actions, assignment_view
        data["responses"] = response_actions(db, job)
        data["assignment"] = assignment_view(db, job)
    return data


def list_jobs_for_technician(db, technician_id: int, now: datetime) -> list[dict]:
    """REQ-FN-050: งานของช่างคนนี้เท่านั้น เรียงตามเวลานัด
    CR-12: ไม่แสดงงานที่ช่างคนนี้ปฏิเสธหรือไม่ตอบแล้ว (ระหว่างหาช่างใหม่ job.technician_id ยังเป็นคนเดิม)
    CR-12 (Q-32 ปิดใน EV-051): งานที่ปิดแล้ว (เสร็จสิ้น ยกเลิก ยกเลิกอัตโนมัติ) แสดงย้อนหลังไม่เกิน 30 วันนับจากเวลานัด"""
    from datetime import timedelta
    from app.matching.service import released_from
    since = now - timedelta(days=config.TECH_CLOSED_JOBS_DAYS)
    jobs = db.scalars(
        select(Job).where(Job.technician_id == technician_id).order_by(Job.scheduled_start)
    ).all()
    out = []
    for j in jobs:
        if released_from(db, j, technician_id):
            continue
        if j.status in ("done", "cancelled", "auto_cancelled") and j.scheduled_start < since:
            continue
        out.append(technician_job_view(j, now, db))
    return out


def change_status(db, job: Job, technician_id: int, to_status: str, now: datetime) -> Job:
    """REQ-FN-051: เปลี่ยนสถานะตามลูกศรของ MD-STM-01 แล้วบันทึกประวัติ (REQ-DAT-002) และแจ้งลูกค้า (REQ-FN-053)"""
    if job.technician_id != technician_id:
        raise NotOwner()
    if not is_allowed(job.status, to_status):
        raise TransitionNotAllowed(job.status, to_status)
    if to_status == "en_route":
        from app.matching.service import mark_accepted_on_departure
        mark_accepted_on_departure(db, job, now)  # CR-12 BR-07 ข้อ 2 กดออกเดินทาง = รับงาน
    set_status(db, job, to_status, now)  # ที่เดียวทั้งระบบ เขียน job_status_history ให้
    # รองรับ REQ-FN-053: วางข้อความถึงลูกค้าลงคิว due_at = now + 60 วินาที ไม่รอผลส่ง (IF-02)
    text = f"งาน #{job.id} สถานะ {STATUS_TH[to_status]}"
    if to_status == "done":
        # CR-10 (Q-31 ปิดใน EV-048, AC-09-15): เสร็จสิ้นเมื่อช่างปิดงาน ไม่มีขั้นลูกค้ายืนยัน
        # ข้อความบอกช่องทางแจ้งปัญหา (เลขโทรของ call center ไม่ใช่ข้อมูลส่วนบุคคล)
        text += (f" หากงานยังไม่เรียบร้อย แจ้ง call center ที่ {config.call_center_tel()} "
                 f"ภายใน {config.JOB_ISSUE_REPORT_DAYS} วัน")
    queue.enqueue("customer", job.customer_id, text, job.id, now, db=db)
    db.commit()
    return job


def history_for(db, job: Job) -> list[dict]:
    """REQ-DAT-002: ประวัติการเปลี่ยนสถานะเรียงตามเวลา ลูกค้า call center และช่างอ่านจากที่เดียวกัน (REQ-FN-052)"""
    rows = db.scalars(
        select(JobStatusHistory).where(JobStatusHistory.job_id == job.id).order_by(JobStatusHistory.id)
    ).all()
    return [{"from_status": r.from_status, "to_status": r.to_status, "at": r.at.isoformat()} for r in rows]
