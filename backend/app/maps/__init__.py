"""CR-18 IF-03 บริการแผนที่ (ปิด GAP-40 ตามที่ตัดสินใน EV-053)
- หาพิกัดจากข้อความที่อยู่ (geocode) ตอนลูกค้าลงทะเบียนหรือเพิ่มที่อยู่ หน้าจอไม่ส่งพิกัดเอง (เลิกพิกัดกลางของ AS-16)
- ระยะทางของ BR-03 และ BR-07 คำนวณผ่าน interface นี้ ตัวจำลอง (MockMap) ใช้ระยะเส้นตรงจากพิกัด (สูตร haversine เดิม)
- REQ-QA-010: แผนที่ไม่ตอบภายใน 5 วินาที ระบบใช้ระยะเส้นตรงที่คำนวณเองแทน และบันทึก map_fallback (ไม่ล้มทั้งคำขอ)
ตัวจริงอยู่ที่ app/integrations/http_map.py เลือกด้วย MAP_ADAPTER"""
import math

from app.privacy import get_logger, log_event

log = get_logger(__name__)


class MapTimeout(Exception):
    """IF-03 ไม่ตอบภายใน MAP_TIMEOUT_SECONDS"""


class MapService:
    name = "none"

    def geocode(self, text: str) -> tuple[float, float] | None:
        raise NotImplementedError

    def distances_km(self, origin: tuple[float, float], destinations: list[tuple[float, float]]) -> list[float]:
        raise NotImplementedError


def straight_km(lat1, lng1, lat2, lng2) -> float:
    """ระยะเส้นตรงบนผิวโลก (haversine) สูตรเดิมของ R1 ใช้เป็นตัวจำลองและเป็นทางสำรองเมื่อแผนที่ไม่ตอบ"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ตำแหน่งกลางของเขตในพื้นที่ให้บริการทดสอบ (ข้อมูลสมมติ ค่าประมาณ ใช้กับตัวจำลองเท่านั้น)
GAZETTEER = {
    "บางรัก": (13.7300, 100.5240), "ปทุมวัน": (13.7440, 100.5220), "สาทร": (13.7200, 100.5300),
    "คลองเตย": (13.7100, 100.5600), "วัฒนา": (13.7400, 100.5800), "ห้วยขวาง": (13.7760, 100.5790),
    "จตุจักร": (13.8280, 100.5590), "บางนา": (13.6680, 100.6050), "ดินแดง": (13.7700, 100.5530),
    "พญาไท": (13.7800, 100.5420), "ราชเทวี": (13.7580, 100.5340), "บางกะปิ": (13.7650, 100.6470),
    "ลาดพร้าว": (13.8030, 100.6070), "ยานนาวา": (13.6960, 100.5380), "บางซื่อ": (13.8090, 100.5370),
}


class MockMap(MapService):
    """ตัวจำลอง: หาพิกัดจากชื่อเขตที่อยู่ในข้อความ (GAZETTEER) ระยะทางเป็นเส้นตรงจากพิกัด mode = ok | down"""
    name = "mock"

    def __init__(self, mode: str = "ok"):
        self.mode, self.calls = mode, 0

    def geocode(self, text):
        self.calls += 1
        if self.mode == "down":
            raise MapTimeout()
        for area, point in GAZETTEER.items():
            if area in (text or ""):
                return point
        return None

    def distances_km(self, origin, destinations):
        self.calls += 1
        if self.mode == "down":
            raise MapTimeout()
        return [straight_km(origin[0], origin[1], a, b) for a, b in destinations]


def _build() -> MapService:
    """เครื่องทดสอบตั้ง MOCK_MAP_MODE = down เพื่อซ้อม OAT-5 (แผนที่ไม่ตอบ) ระบบจริงต้องไม่ใช้ตัวจำลอง"""
    import os
    from app.integrations import choice
    if choice("map") == "http":
        from app.integrations.http_map import HttpMap
        return HttpMap()
    return MockMap(mode=os.getenv("MOCK_MAP_MODE", "ok"))


_map: MapService | None = None


def get_map() -> MapService:
    global _map
    if _map is None:
        _map = _build()
    return _map


def set_map(m: MapService | None) -> None:
    global _map
    _map = m


def distances_km(origin: tuple[float, float], destinations: list[tuple[float, float]]) -> list[float]:
    """ระยะจาก origin ถึงทุกจุด ถ้าแผนที่ไม่ตอบ ใช้ระยะเส้นตรง (REQ-QA-010 รุ่น 1.4 บรรทัดที่ 5)"""
    if not destinations:
        return []
    try:
        return get_map().distances_km(origin, destinations)
    except MapTimeout:
        log_event(log, "map_fallback", count=len(destinations))
        return [straight_km(origin[0], origin[1], a, b) for a, b in destinations]


def distance_km(lat1, lng1, lat2, lng2) -> float:
    return distances_km((lat2, lng2), [(lat1, lng1)])[0]


def geocode(text: str) -> tuple[float, float] | None:
    """None = หาไม่พบ ผู้เรียกบอกลูกค้าให้ใส่ชื่อเขตหรืออำเภอ แผนที่ไม่ตอบ ส่ง MapTimeout ต่อให้ผู้เรียกตอบ 503"""
    return get_map().geocode(text)
