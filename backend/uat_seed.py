"""ข้อมูลทดสอบสมมติสำหรับการตรวจรับ R1 (docs/acceptance/uat-plan-r1.md ส่วน "ข้อมูลทดสอบ") ไม่ใช่ส่วนของระบบ
ลูกค้าสมมติ 30 ราย ช่างสมมติ 10 คน ช่วงเวลาว่าง 7 วันข้างหน้า วันละ 3 ช่วงต่อช่าง
ไม่มีเบอร์จริงของใคร: เบอร์ทุกเบอร์ขึ้นต้นด้วย 000-000 (REQ-PRV-002 ใช้กับการทดสอบด้วย)
ใช้: DATABASE_URL=<ฐานข้อมูลของเครื่องทดสอบ> python uat_seed.py [--slots-per-day 3]
ฐานข้อมูลต้องว่าง สคริปต์สร้างตารางด้วย migration ล่าสุด (m004) ถ้ามีลูกค้าอยู่แล้วจะหยุดโดยไม่เขียนอะไร"""
import argparse
from datetime import datetime, timedelta

from app.db.session import engine, SessionLocal
from app.db.migrations.m004_r2 import upgrade
from app.db.models import Account, Customer, ServiceAddress, Technician, TimeSlot

CATEGORIES = ["ประปา", "ไฟฟ้า", "แอร์"]
# จุดตั้งต้นของช่างกระจายรอบพื้นที่ทดสอบ ห่างจากที่อยู่ลูกค้าไม่เกิน 15 กิโลเมตร (BR-03)
CENTER = (13.7400, 100.5300)


def seed(slots_per_day: int = 3, days: int = 7) -> dict:
    upgrade(engine)
    db = SessionLocal()
    try:
        if db.query(Customer).count():
            return {"skipped": True}
        customers = []
        for i in range(1, 31):
            c = Customer(name=f"ลูกค้าทดสอบ {i:02d}", phone=f"000-000-{i:04d}")
            db.add(c)
            customers.append(c)
        db.flush()
        for i, c in enumerate(customers):
            db.add(ServiceAddress(customer_id=c.id, text=f"บ้านทดสอบเลขที่ {i + 1}",
                                  lat=CENTER[0] + (i % 5) * 0.004, lng=CENTER[1] + (i // 5) * 0.004))
        techs = []
        for i in range(1, 11):
            skills = ",".join({CATEGORIES[i % 3], CATEGORIES[(i + 1) % 3]})
            t = Technician(name=f"ช่างทดสอบ {i:02d}", skills=skills,
                           base_lat=CENTER[0] - 0.02 + i * 0.004, base_lng=CENTER[1] + 0.01)
            db.add(t)
            techs.append(t)
        db.flush()
        base = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        hours = [0, 3, 6, 9][:slots_per_day]
        n = 0
        for t in techs:
            for d in range(days):
                for h in hours:
                    s = base + timedelta(days=d, hours=h)
                    db.add(TimeSlot(technician_id=t.id, start=s, end=s + timedelta(hours=2)))
                    n += 1
        # ช่วงเวลาวันนี้ อีก 3 ชั่วโมง (scenario ที่ต้องยกเลิกน้อยกว่า 24 ชั่วโมงก่อนนัด และช่างออกเดินทาง)
        today = (datetime.now() + timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
        for t in techs:
            db.add(TimeSlot(technician_id=t.id, start=today, end=today + timedelta(hours=2)))
            n += 1
        # CR-11 (R2): บัญชีเข้าสู่ระบบของลูกค้าทดสอบ (เบอร์เดียวกับในตาราง customers) และช่างทดสอบ 000-000-10nn
        for c in customers:
            db.add(Account(role="customer", subject_id=c.id, phone_norm=c.phone.replace("-", ""), created_at=datetime.now()))
        for t in techs:
            db.add(Account(role="technician", subject_id=t.id, phone_norm=f"000000{1000 + t.id:04d}", created_at=datetime.now()))
        db.commit()
        return {"customers": len(customers), "technicians": len(techs), "slots": n, "accounts": len(customers) + len(techs)}
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots-per-day", type=int, default=3)
    print(seed(ap.parse_args().slots_per_day))
