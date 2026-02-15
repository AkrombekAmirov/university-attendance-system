import requests
import json
from requests.auth import HTTPDigestAuth


class TurniketLastSerialFetcher:
    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.auth = HTTPDigestAuth(username, password)
        self.url = f"http://{ip}/ISAPI/AccessControl/AcsEvent?format=json"

    def _post(self, payload: dict) -> dict:
        resp = requests.post(
            self.url,
            auth=self.auth,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_last_serial(self) -> int | None:
        """
        🔹 Turniketdagi eng oxirgi serialNo ni qaytaradi
        🔹 Agar event bo‘lmasa → None
        """

        # 1️⃣ Jami eventlar sonini olish
        total_payload = {
            "AcsEventCond": {
                "searchID": "total",
                "searchResultPosition": 0,
                "maxResults": 1,
                "major": 5,
                "minor": 0,
            }
        }

        data = self._post(total_payload)
        total = int(data.get("AcsEvent", {}).get("totalMatches", 0))

        if total <= 0:
            print("⚠️ Turniketda eventlar yo‘q")
            return None

        # 2️⃣ Oxirgi eventni olish (total - 1)
        last_payload = {
            "AcsEventCond": {
                "searchID": "last",
                "searchResultPosition": total - 1,
                "maxResults": 1,
                "major": 5,
                "minor": 0,
            }
        }

        data = self._post(last_payload)
        events = data.get("AcsEvent", {}).get("InfoList", [])

        if not events:
            print("⚠️ Oxirgi event olinmadi")
            return None

        last_event = events[0]
        serial = last_event.get("serialNo")

        print(
            f"✅ ENG OXIRGI EVENT:\n"
            f"   🕒 time   = {last_event.get('time')}\n"
            f"   👤 user   = {last_event.get('employeeNoString')}\n"
            f"   🔢 serial = {serial}"
        )

        return int(serial) if serial is not None else None
if __name__ == "__main__":
    fetcher = TurniketLastSerialFetcher(
        ip="192.128.1.108",
        username="admin",
        password="abcd2024",
    )

    last_serial = fetcher.get_last_serial()
    print("📌 LAST SERIAL =", last_serial)
