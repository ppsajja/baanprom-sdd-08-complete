"""CR-18 ตัวจริงของ IF-03 บริการแผนที่ (ปิดไว้) ตามสัญญา IF-03 ใน docs/srs/models.md ส่วน 9
ส่งข้อความที่อยู่ (หาพิกัด) และพิกัด (หาระยะทาง) เท่านั้น ไม่ส่งชื่อหรือเบอร์ (REQ-PRV-011 รุ่น 1.4)
รอไม่เกิน MAP_TIMEOUT_SECONDS (5 วินาที REQ-QA-010) ไม่ตอบถือเป็น MapTimeout ผู้เรียกใช้ระยะเส้นตรงแทน"""
import httpx

from app import config
from app.integrations import AdapterNotConfigured, missing, setting
from app.maps import MapService, MapTimeout


class HttpMap(MapService):
    name = "http"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport

    def _client(self) -> httpx.Client:
        if missing("map"):
            raise AdapterNotConfigured("IF-03 ยังไม่ตั้ง " + ", ".join(missing("map")))
        return httpx.Client(base_url=setting("MAP_API_URL"), timeout=config.MAP_TIMEOUT_SECONDS,
                            transport=self.transport, headers={"Authorization": f"Bearer {setting('MAP_API_KEY')}"})

    def geocode(self, text: str):
        try:
            with self._client() as c:
                r = c.get("/geocode", params={"q": text})
        except httpx.TimeoutException as e:
            raise MapTimeout() from e
        if r.status_code == 404:
            return None
        r.raise_for_status()
        d = r.json()
        return float(d["lat"]), float(d["lng"])

    def distances_km(self, origin, destinations):
        try:
            with self._client() as c:
                r = c.post("/distances", json={"origin": {"lat": origin[0], "lng": origin[1]},
                                               "destinations": [{"lat": a, "lng": b} for a, b in destinations]})
        except httpx.TimeoutException as e:
            raise MapTimeout() from e
        r.raise_for_status()
        return [float(x) for x in r.json()["km"]]
