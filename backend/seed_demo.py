"""ใส่ข้อมูลสมมติสำหรับเปิดดูระบบทั้งระบบบนเครื่องนักพัฒนา (ไม่ใช่ส่วนของระบบ ห้ามใช้กับฐานข้อมูลจริง) รัน: python seed_demo.py
R2 (B7): ลูกค้า 2 คน ช่าง 3 คน มีบัญชีเข้าสู่ระบบครบ ตารางเวลา 7 วัน งานที่เสร็จสิ้นแล้ว 1 งาน (ให้คะแนนได้ และใช้ลองจองช่างคนเดิม)
เบอร์ทุกเบอร์เป็นเบอร์สมมติ เข้าสู่ระบบด้วยเบอร์ในตารางข้างล่าง โหมด development หน้าจอแสดงรหัส OTP ให้เอง (dev_code)
ลูกค้า 081-234-5678 (สมชาย) 089-111-2222 (สมศรี) | ช่าง 086-555-0101 (ประสิทธิ์) 086-555-0102 (สมหมาย) 086-555-0103 (วิชัย)"""
from datetime import datetime, timedelta

from app.db.session import engine, SessionLocal
from app.db.migrations.m005_r2b import upgrade
from app.db.models import (Account, Customer, Job, JobAssignment, JobStatusHistory, Payment, ServiceAddress, Technician,
                           TimeSlot, SLOT_BOOKED)

upgrade(engine)
db = SessionLocal()
if db.query(Customer).count():
    print("already seeded")
else:
    now = datetime.now()
    people = [("สมชาย", "081-234-5678", "บ้านเลขที่ 12 ซอยสุขใจ เขตสาทร", (13.7200, 100.5300)),
              ("สมศรี", "089-111-2222", "คอนโด 88 ถนนสีลม เขตบางรัก", (13.7300, 100.5240))]
    customers = []
    for name, phone, text, (lat, lng) in people:
        c = Customer(name=name, phone=phone); db.add(c); db.flush()
        db.add(ServiceAddress(customer_id=c.id, text=text, lat=lat, lng=lng))
        db.add(Account(role="customer", subject_id=c.id, phone_norm=phone.replace("-", ""), created_at=now))
        customers.append(c)
    techs = []
    for i, (name, skills, lat) in enumerate([("ประสิทธิ์", "ประปา,ไฟฟ้า", 13.705), ("สมหมาย", "ประปา", 13.720),
                                             ("วิชัย", "ประปา,แอร์", 13.690)], start=1):
        t = Technician(name=name, skills=skills, base_lat=lat, base_lng=100.53); db.add(t); db.flush()
        db.add(Account(role="technician", subject_id=t.id, phone_norm=f"08655501{i:02d}", created_at=now))
        techs.append(t)
    base = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    for t in techs:
        for d in range(7):
            for h in (0, 3, 5, 7):
                s = base + timedelta(days=d, hours=h)
                db.add(TimeSlot(technician_id=t.id, start=s, end=s + timedelta(hours=2)))
    # งานที่เสร็จสิ้นเมื่อวานของสมชายกับประสิทธิ์ (ลองให้คะแนน UC-11 และจองช่างคนเดิม CR-08)
    y = (now - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    slot = TimeSlot(technician_id=techs[0].id, start=y, end=y + timedelta(hours=2), state=SLOT_BOOKED); db.add(slot); db.flush()
    job = Job(customer_id=customers[0].id, technician_id=techs[0].id, slot_id=slot.id, address_id=1, category="ประปา",
              status="done", deposit_amount=350, scheduled_start=y, created_at=y - timedelta(days=2)); db.add(job); db.flush()
    db.add(Payment(job_id=job.id, amount=350, gateway_ref=f"BP-{job.id}-demo0001", result="success", authorized_at=y - timedelta(days=2)))
    for a, b, at in ((None, "pending_payment", y - timedelta(days=2)), ("pending_payment", "confirmed", y - timedelta(days=2)),
                     ("confirmed", "en_route", y - timedelta(minutes=30)), ("en_route", "in_progress", y), ("in_progress", "done", y + timedelta(hours=1))):
        db.add(JobStatusHistory(job_id=job.id, from_status=a, to_status=b, at=at))
    db.add(JobAssignment(job_id=job.id, technician_id=techs[0].id, slot_id=slot.id, offered_at=y - timedelta(days=2),
                         respond_by=y - timedelta(days=2) + timedelta(minutes=30), response="accepted", responded_at=y - timedelta(days=2)))
    db.commit()
    print("seeded: ลูกค้า 2 ช่าง 3 ช่วงเวลา", 3 * 7 * 4, "งานที่เสร็จสิ้น 1")
