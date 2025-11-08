import requests
from requests.auth import HTTPDigestAuth
import json, time
from datetime import datetime
from typing import Optional

class TurniketClient:
    def __init__(self, ip, username, password, device_name, device_sn):
        self.ip = ip
        self.username = username
        self.password = password
        self.device_name = device_name
        self.device_sn = device_sn

        self.batch_size = 1000
        self.last_total = None  # event count snapshot

    def _post(self, payload):
        url = f"http://{self.ip}/ISAPI/AccessControl/AcsEvent?format=json"
        r = requests.post(
            url,
            auth=HTTPDigestAuth(self.username, self.password),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=8
        )
        r.raise_for_status()
        return r.json()

    def get_total_events(self) -> int:
        payload = {
            "AcsEventCond": {
                "searchID":"count",
                "searchResultPosition":0,
                "maxResults":1,
                "major":5, "minor":0
            }
        }
        data = self._post(payload)
        return int(data["AcsEvent"]["totalMatches"])

    def fetch_events(self, pos, limit):
        payload = {
            "AcsEventCond": {
                "searchID":"resume",
                "searchResultPosition":pos,
                "maxResults":min(limit, self.batch_size),
                "major":5, "minor":0
            }
        }
        data = self._post(payload)
        return data.get("AcsEvent",{}).get("InfoList",[]) or []

    def map(self, e: dict):
        dt = datetime.fromisoformat(e["time"])
        return {
            "datetime": dt,
            "date": dt.date(),
            "time": dt.time(),
            "user_code": e.get("employeeNoString"),
            "name": e.get("name"),
            "card": e.get("cardNo"),
            "serial": e.get("serialNo"),
            "direction": "IN" if e.get("minor") in [75,72]
                        else "OUT" if e.get("minor") in [21,22]
                        else "UNKNOWN",
            "device_name": self.device_name,
            "device_sn": self.device_sn
        }

    def fetch_latest(self, diff):
        total = self.get_total_events()
        start = max(0, total - diff)

        events = []
        for pos in range(start, total, self.batch_size):
            events += self.fetch_events(pos, self.batch_size)

        return [self.map(e) for e in events]

    def watch(self):
        print(f"📡 [{self.device_name}] real‑time started…")
        self.last_total = self.get_total_events()

        while True:
            try:
                total = self.get_total_events()

                if total > self.last_total:
                    diff = total - self.last_total
                    events = self.fetch_latest(min(diff, 500))
                    self.last_total = total

                    if events:
                        yield events

                time.sleep(1)

            except Exception as e:
                print(f"🚨 [{self.device_name}] network issue: {e}")
                time.sleep(5)
