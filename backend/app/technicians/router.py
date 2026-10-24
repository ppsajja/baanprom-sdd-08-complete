"""GET /technicians (plan.md ข้อ 4) รองรับ REQ-FN-008
CR-11 (R2): ลูกค้ามาจาก token (REQ-SEC-014) ที่อยู่ให้บริการต้องเป็นของลูกค้าคนนี้ ไม่ใช่ตอบ 403 และบันทึก (REQ-SEC-010)
query customer_id เดิมไม่ใช้แล้ว (รับไว้ไม่ให้หน้าจอรุ่นเดิมพัง) | GET /contact เลขโทร call center สำหรับเส้นทาง A1 (REQ-FN-065)"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import config
from app.auth.deps import current_customer
from app.auth.service import Actor
from app.db.session import get_db
from app.db.models import ServiceAddress
from app.technicians import service
from app.clock import get_now
from app.ops import audit

router = APIRouter()


@router.get("/technicians")
def list_available(category: str, address_id: int, response: Response, actor: Actor = Depends(current_customer),
                   db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    address = db.get(ServiceAddress, address_id)
    if not address:
        raise HTTPException(404, "ไม่พบที่อยู่ให้บริการ")
    if address.customer_id != actor.subject_id:
        raise audit.deny(db, "customer", actor.subject_id, None, "GET /technicians", now)
    result = service.search_available(db, category, address, now, actor.subject_id)
    db.commit()  # CR-07: release_expired_holds อาจปิดเรื่องเงินของงานที่รอชำระ (REQ-QA-010) ต้องบันทึก
    # CR-07 REQ-OP-005: ให้ตัวนับแยก "ตอบว่าง" ได้ (คู่มือเหตุการณ์ที่ 3 ไม่มีช่างว่าง)
    response.headers["x-result-count"] = str(len(result))
    return result


@router.get("/contact")
def contact():
    # CR-08 (Q-28 ปิดใน EV-051, REQ-FN-065): เส้นทาง A1 ไม่มีช่างว่างใน 7 วัน หน้าจอบอกเลขโทรนี้ (ค่าเดียวกับปุ่มโทรของผู้ช่วย)
    return {"call_center_tel": config.call_center_tel()}
