# backend/worker/realtime/single_turniket_runner.py
import json
import time
import requests
from requests.auth import HTTPDigestAuth


class EventFetcher:
    def __init__(self, device, batch_size=1000):
        self.device = device
        self.batch_size = batch_size

    def _post(self, payload):
        url = f"http://{self.device.ip_address}/ISAPI/AccessControl/AcsEvent?format=json"
        r = requests.post(
            url,
            auth=HTTPDigestAuth(self.device.username, self.device.password),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def get_total(self) -> int:
        payload = {
            "AcsEventCond": {
                "searchID": "count",
                "searchResultPosition": 0,
                "maxResults": 1,
                "major": 5,
                "minor": 0
            }
        }
        data = self._post(payload)
        return int(data["AcsEvent"]["totalMatches"])

    def fetch_range(self, start, end):
        for pos in range(start, end, self.batch_size):
            payload = {
                "AcsEventCond": {
                    "searchID": "resume",
                    "searchResultPosition": pos,
                    "maxResults": self.batch_size,
                    "major": 5,
                    "minor": 0
                }
            }
            data = self._post(payload)
            for event in data.get("AcsEvent", {}).get("InfoList", []):
                yield event

            # 🔐 Hikvision himoyasi (majburiy)
            time.sleep(0.3)
