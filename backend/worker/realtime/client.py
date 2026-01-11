import requests, json, time
from datetime import datetime
from requests.auth import HTTPDigestAuth


class TurniketClient:
    BATCH_SIZE = 1000

    def __init__(self, device):
        self.device = device
        self.auth = HTTPDigestAuth(device.username, device.password)

    def _post(self, payload):
        url = f"http://{self.device.ip_address}/ISAPI/AccessControl/AcsEvent?format=json"
        return requests.post(
            url,
            auth=self.auth,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )

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
        r = self._post(payload)
        r.raise_for_status()
        return int(r.json()["AcsEvent"]["totalMatches"])

    def fetch_latest(self, diff: int):
        total = self.get_total()
        start = max(0, total - diff)

        for pos in range(start, total, self.BATCH_SIZE):
            payload = {
                "AcsEventCond": {
                    "searchID": "resume",
                    "searchResultPosition": pos,
                    "maxResults": self.BATCH_SIZE,
                    "major": 5,
                    "minor": 0
                }
            }
            r = self._post(payload)
            r.raise_for_status()
            for e in r.json().get("AcsEvent", {}).get("InfoList", []):
                yield self.map_event(e)

    @staticmethod
    def map_event(e: dict) -> dict:
        dt = datetime.fromisoformat(e["time"])
        return {
            "employeeNoString": e.get("employeeNoString"),
            "time": dt,
            "serial": e.get("serialNo"),
            "direction": (
                "IN" if e.get("minor") in (75, 72)
                else "OUT" if e.get("minor") in (21, 22)
                else "UNKNOWN"
            ),
            "raw": e
        }
