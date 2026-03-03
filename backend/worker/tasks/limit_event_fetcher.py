import requests
import json
import time
from requests.auth import HTTPDigestAuth


class EventFetcher:
    def __init__(self, ip, username, password, batch_size=30):
        self.ip = ip
        self.username = username
        self.password = password
        self.batch_size = batch_size
        self.counter = 0
        self.last_error = False

    def _post(self, payload):
        url = f"http://{self.ip}/ISAPI/AccessControl/AcsEvent?format=json"
        resp = requests.post(
            url,
            auth=HTTPDigestAuth(self.username, self.password),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_total_events(self):
        payload = {
            "AcsEventCond": {
                "searchID": "total",
                "searchResultPosition": 0,
                "maxResults": 1,
                "major": 0,
                "minor": 0
            }
        }
        try:
            data = self._post(payload)
            time.sleep(3)
            self.last_error = False
            # print(int(data.get("AcsEvent", {}).get("totalMatches", 0)), "123132132132132111111111", self.ip)
            return int(data.get("AcsEvent", {}).get("totalMatches", 0))
        except Exception as e:
            print(f"❌ Xatolik get_total_events: {e}")
            self.last_error = True
            return 0

    def fetch_by_position(self, position, limit):
        payload = {
            "AcsEventCond": {
                "searchID": "rangeFetch",
                "searchResultPosition": position,
                "maxResults": limit,
                "major": 0,
                "minor": 0
            }
        }
        try:
            data = self._post(payload)
            return data.get("AcsEvent", {}).get("InfoList", [])
        except Exception as e:
            print(f"❌ Xatolik fetch_by_position: {e}")
            return []

    def get_direction(self, minor_code):
        if minor_code == 1:
            return "OUT"
        elif minor_code == 75:
            return "IN"
        return "Noma'lum"

    def print_event(self, evt):
        self.counter += 1
        time_str = evt.get("time", "")
        employee_id = evt.get("employeeNoString", "")
        name = evt.get("name", "")
        serial = evt.get("serialNo", "")
        reader = evt.get("readerName", "")
        door = evt.get("doorName", "")
        device = evt.get("deviceIndex", "")
        minor = int(evt.get("minor", -1))
        direction = self.get_direction(minor)

        print(
            f"📅 {time_str} | 👤 {employee_id} - {name} | 🚪 {door} | 📌 Reader: {reader} | 🧭 {direction} | 🏷️ Qurilma: {device} | 🔢 Serial: {serial} number = {self.counter}")

    def paged_fetch_event_range(self, start_index, end_index, device_name):
        print(f"🚀 Fetching events from {device_name} {start_index} to {end_index} in batches of {self.batch_size}")
        current = start_index

        while current < end_index:
            actual_limit = min(self.batch_size, end_index - current)
            events = self.fetch_by_position(current, actual_limit)

            # Agar umuman event kelmasa, demak oxiriga yetdik
            if not events:
                print(f"⛔ No more events returned at position {current}")
                break

            # 🧠 1. Eventlarni ro'yxat (batch) ko'rinishida uzatamiz
            yield events

            # 🧠 2. Pointerni faqat QABUL QILINGAN eventlar soniga qarab suramiz
            fetched_count = len(events)
            current += fetched_count

            # 🧠 3. Asosiy Optimizatsiya:
            # Agar biz 30 ta so'rasak-u, turniket 5 ta bersa, demak hozircha bazasida
            # faqat 5 ta yangi event bor. Uni qiynab qolgan 25 tasini so'ramaymiz!
            # Tsiklni to'xtatamiz. Qolganini Producer'ning asosiy (realtime) tsikli hal qiladi.
            if fetched_count < actual_limit:
                print(f"⚠️ Reached end of available events (got {fetched_count}, asked {actual_limit}). Yielding to main loop.")
                break

            # Turniketga "nafas olishi" uchun kichik pauza (0.5 s o'rniga 0.2 s ham yetarli bo'ladi)
            time.sleep(4.2)

        print("✅ Done.")
