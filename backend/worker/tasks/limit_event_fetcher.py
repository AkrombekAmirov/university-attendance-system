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
                "major": 5,
                "minor": 0
            }
        }
        try:
            data = self._post(payload)
            return int(data.get("AcsEvent", {}).get("totalMatches", 0))
        except Exception as e:
            print(f"❌ Xatolik get_total_events: {e}")
            return 0

    def fetch_by_position(self, position, limit):
        payload = {
            "AcsEventCond": {
                "searchID": "rangeFetch",
                "searchResultPosition": position,
                "maxResults": limit,
                "major": 5,
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

    def paged_fetch_event_range(self, start_index, end_index):
        print(f"🚀 Fetching events from {start_index} to {end_index} in batches of {self.batch_size}")
        current = start_index

        while current < end_index:
            actual_limit = min(self.batch_size, end_index - current)
            events = self.fetch_by_position(current, actual_limit)

            if not events:
                print(f"⛔ No more events returned at position {current}")
                break

            # 🧠 Har bir `events` listini generator sifatida tashqariga uzatamiz
            yield events

            if len(events) < actual_limit and (current + len(events)) < end_index:
                remaining = end_index - (current + len(events))
                print(f"⚠️ Only {len(events)} events returned. Retrying remaining {remaining} events...")
                time.sleep(1)
                extra_events = self.fetch_by_position(current + len(events), remaining)
                for evt in extra_events:
                    if "time" in evt:
                        self.print_event(evt)
                        yield extra_events
                # if extra_events:
                #     self.print_event(extra_events)
                #     yield extra_events  # ✅ Qo‘shimcha eventlar ham uzatiladi
                current += len(events) + len(extra_events)
            else:
                current += actual_limit

            time.sleep(0.5)

        print("✅ Done.")
