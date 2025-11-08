# from requests.auth import HTTPDigestAuth
# from datetime import datetime
# import requests
# import json
# import time
#
# # Qurilma sozlamalari
# DEVICE_IP = "192.128.1.213"
# USERNAME = "admin"
# PASSWORD = "abcd2024"
#
# # Qurilma haqida (statik yoki API orqali olib kelsa ham bo‘ladi)
# DEVICE_NAME = "Turniket A1"
# DEVICE_SN = "SN2023XYZ"
#
# # Minor kodlarni kirish/chiqish ma'nosiga aylantirish
# def get_direction(minor):
#     if minor in [75, 72]:
#         return "KIRDI"
#     elif minor in [21, 22]:
#         return "CHIQMADI"
#     else:
#         return "NOANIQ"
#
# # PersonGroup bazasi bo‘lmasa, default beriladi
# def get_group_id(person_id):
#     # TODO: bazadan person_id orqali aniqlasa bo‘ladi
#     return "default-group"
#
# # Real-time kuzatuvchi
# def watch_turniket_realtime():
#     print("📡 Real-time kuzatuv boshlandi...\n")
#     last_total = None
#
#     while True:
#         try:
#             count_url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
#             count_payload = {
#                 "AcsEventCond": {
#                     "searchID": "latest",
#                     "searchResultPosition": 0,
#                     "maxResults": 1,
#                     "major": 5,
#                     "minor": 0
#                 }
#             }
#
#             count_resp = requests.post(
#                 count_url,
#                 auth=HTTPDigestAuth(USERNAME, PASSWORD),
#                 headers={"Content-Type": "application/json"},
#                 data=json.dumps(count_payload)
#             )
#
#             data = count_resp.json()
#             total = int(data["AcsEvent"]["totalMatches"])
#
#             if last_total is None:
#                 last_total = total
#             elif total > last_total:
#                 new_events = total - last_total
#                 fetch_latest_events(new_events)
#                 last_total = total
#
#             time.sleep(3)
#
#         except Exception as e:
#             print(f"❌ Xatolik: {e}")
#             time.sleep(10)
#
# # Oxirgi N ta eventni olish va formatlash
# def fetch_latest_events(limit=40):
#     url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
#     start_index = max(0, get_total_events() - limit)
#
#     payload = {
#         "AcsEventCond": {
#             "searchID": "real_time",
#             "searchResultPosition": start_index,
#             "maxResults": limit,
#             "major": 5,
#             "minor": 0
#         }
#     }
#
#     resp = requests.post(
#         url,
#         auth=HTTPDigestAuth(USERNAME, PASSWORD),
#         headers={"Content-Type": "application/json"},
#         data=json.dumps(payload)
#     )
#
#     events = resp.json()["AcsEvent"]["InfoList"]
#
#     for evt in events:
#         raw_time = evt.get("time", "")
#         dt = datetime.fromisoformat(raw_time)
#
#         person_id = evt.get("employeeNoString", "-")
#         card_no = evt.get("cardNo", "-")
#         person_name = evt.get("name", "-")
#         minor = evt.get("minor", 0)
#
#         date_str = dt.strftime("%Y-%m-%d")
#         time_str = dt.strftime("%H:%M:%S")
#
#         group_id = get_group_id(person_id)
#         direction = get_direction(minor)
#         timecontrol = f"{date_str} {time_str}"
#         serial = evt.get("serialNo", 0)
#
#         print(f"{person_id}, {date_str}, {group_id}, {date_str}, {time_str}, {direction}, "
#               f"{DEVICE_NAME}, {DEVICE_SN}, {person_name}, {card_no}, {timecontrol}", f"{serial}++++")
#
# # Umumiy event sonini olish
# def get_total_events():
#     url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
#     payload = {
#         "AcsEventCond": {
#             "searchID": "count",
#             "searchResultPosition": 0,
#             "maxResults": 1,
#             "major": 5,
#             "minor": 0
#         }
#     }
#
#     resp = requests.post(
#         url,
#         auth=HTTPDigestAuth(USERNAME, PASSWORD),
#         headers={"Content-Type": "application/json"},
#         data=json.dumps(payload)
#     )
#
#     return int(resp.json()["AcsEvent"]["totalMatches"])
#
# # ⏯ Ishga tushirish
# if __name__ == "__main__":
#     fetch_latest_events()
import requests
from requests.auth import HTTPDigestAuth
import json, time, os
from datetime import datetime

# Device Settings
# DEVICE_IP = "192.128.1.211"
# USERNAME = "admin"
# PASSWORD = "abcd2024"
#
# DEVICE_NAME = "Turniket A1"
# DEVICE_SN = "SN2023XYZ"
#
# SERIAL_FILE = "last_serial.txt"
# BATCH_SIZE = 1000  # stable Hikvision limit
# MAX_CATCHUP = 50000  # safety limit: 50k events max per recovery
#
# ##########################
# # Serial Storage Helpers
# ##########################
# #
# def read_last_serial():
#     try:
#         return int(open(SERIAL_FILE).read())
#     except:
#         return None
#
# def save_last_serial(s):
#     with open(SERIAL_FILE, "w") as f:
#         f.write(str(s))
#
# ##########################
# # API helpers
# ##########################
#
# def get_total_events():
#     url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
#     payload = {
#         "AcsEventCond": {"searchID":"count","searchResultPosition":0,"maxResults":1,"major":5,"minor":0}
#     }
#     resp = requests.post(url, auth=HTTPDigestAuth(USERNAME,PASSWORD),
#                          headers={"Content-Type":"application/json"},
#                          data=json.dumps(payload))
#     return int(resp.json()["AcsEvent"]["totalMatches"])
#
# def fetch_events(pos, limit):
#     limit = min(limit, BATCH_SIZE)
#     url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
#
#     payload = {
#         "AcsEventCond": {
#             "searchID":"resume",
#             "searchResultPosition":pos,
#             "maxResults":limit,
#             "major":5,"minor":0
#         }
#     }
#     resp = requests.post(url, auth=HTTPDigestAuth(USERNAME,PASSWORD),
#                          headers={"Content-Type":"application/json"},
#                          data=json.dumps(payload))
#     return resp.json().get("AcsEvent",{}).get("InfoList",[])
#
# ##########################
# # Business Logic Helpers
# ##########################
#
# def get_direction(minor):
#     return "KIRDI" if minor in [75,72] else "CHIQMADI" if minor in [21,22] else "NOANIQ"
#
# def print_event(e):
#     dt = datetime.fromisoformat(e["time"])
#     date = dt.strftime("%Y-%m-%d"); t = dt.strftime("%H:%M:%S")
#
#     print(f"{e.get('employeeNoString','-')}, {date}, default-group, {date}, {t}, "
#           f"{get_direction(e.get('minor'))}, {DEVICE_NAME}, {DEVICE_SN}, "
#           f"{e.get('name','-')}, {e.get('cardNo','-')}, {date} {t}, serial={e['serialNo']}")
#
# #################################
# # Real-time engine + auto catchup
# #################################
#
# def watch_turniket_realtime():
#     print("📡 Real-time started...")
#     last_total = get_total_events()
#
#     while True:
#         try:
#             total = get_total_events()
#
#             if total > last_total:
#                 diff = total - last_total
#                 fetch_latest_events(min(diff, 500))
#                 last_total = total
#
#             time.sleep(2)
#
#         except Exception as e:
#             print(f"🚨 Network down: {e}")
#             time.sleep(5)
#
# #################################
# # Fetch latest block
# #################################
#
# def fetch_latest_events(limit):
#     total = get_total_events()
#     start = max(0, total - limit)
#
#     for pos in range(start, total, BATCH_SIZE):
#         events = fetch_events(pos, BATCH_SIZE)
#         for e in events:
#             print_event(e)
#             save_last_serial(e["serialNo"])
#
# #################################
# # Main
# #################################
#
# if __name__ == "__main__":
#     print("✅ Recovery complete, switching to realtime...\n")
#     watch_turniket_realtime()
# import requests
# from requests.auth import HTTPDigestAuth
# import json
# from datetime import datetime
#
# # Sozlamalar
# DEVICE_IP = "192.128.1.213"
# USERNAME = "admin"
# PASSWORD = "abcd2024"
#
# DEVICE_NAME = "Turniket A1"
# DEVICE_SN = "SN2023XYZ"
#
# # Aniqlangan oraliq
# START_INDEX = 28206
# END_INDEX = 30206
# BATCH_SIZE = 1000  # Hikvision maxResults limiti
#
# def get_direction(minor):
#     if minor in [75, 72]: return "KIRDI"
#     if minor in [21, 22]: return "CHIQDI"
#     return "NOANIQ"
#
# def print_event(e):
#     dt = datetime.fromisoformat(e["time"])
#     date = dt.strftime("%Y-%m-%d")
#     time_s = dt.strftime("%H:%M:%S")
#
#     print(f"{e.get('employeeNoString','-')}, {date}, default-group, {date}, {time_s}, "
#           f"{get_direction(e.get('minor'))}, {DEVICE_NAME}, {DEVICE_SN}, "
#           f"{e.get('name','-')}, {e.get('cardNo','-')}, {date} {time_s}, serial={e['serialNo']}")
#
# def fetch_by_position(position, limit):
#     url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
#     payload = {
#         "AcsEventCond": {
#             "searchID": "rangeFetch",
#             "searchResultPosition": position,
#             "maxResults": limit,
#             "major": 5,
#             "minor": 0
#         }
#     }
#     resp = requests.post(url,
#                          auth=HTTPDigestAuth(USERNAME, PASSWORD),
#                          headers={"Content-Type": "application/json"},
#                          data=json.dumps(payload),
#                          timeout=10)
#     return resp.json().get("AcsEvent", {}).get("InfoList", [])
#
# def fetch_event_range():
#     print(f"▶️ Fetching from position {START_INDEX} to {END_INDEX}...\n")
#     current = START_INDEX
#
#     while current < END_INDEX:
#         batch_limit = min(BATCH_SIZE, END_INDEX - current)
#         events = fetch_by_position(current, batch_limit)
#
#         if not events:
#             print("⛔ No more events received.")
#             break
#
#         for e in events:
#             if "time" in e:
#                 print_event(e)
#
#         current += batch_limit
#
#     print("✅ Done.")
#
# if __name__ == "__main__":
#     fetch_event_range()
import requests
import json
import time
from requests.auth import HTTPDigestAuth
from datetime import datetime

# 🔧 Qurilma sozlamalari
DEVICE_IP = "192.128.1.211"
USERNAME = "admin"
PASSWORD = "abcd2024"


# ✅ Qurilmadagi umumiy eventlar sonini olish
def get_total_events():
    url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
    payload = {
        "AcsEventCond": {
            "searchID": "total",
            "searchResultPosition": 0,  # 💡 BU QATORNI QO‘SHISH MUHIM
            "maxResults": 1,
            "major": 5,
            "minor": 0
        }
    }
    try:
        resp = requests.post(
            url,
            auth=HTTPDigestAuth(USERNAME, PASSWORD),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        print("🛠️ Javob matni:", resp.text)

        data = resp.json()
        if "AcsEvent" in data and "totalMatches" in data["AcsEvent"]:
            return data["AcsEvent"]["totalMatches"]
        else:
            print("⚠️ AcsEvent yoki totalMatches topilmadi!")
            return 0
    except Exception as e:
        print(f"❌ Xatolik get_total_events: {e}")
        return 0


# ✅ Ma’lum indeksdan boshlab `limit` ta eventni olish
def fetch_by_position(position, limit):
    url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
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
        resp = requests.post(url, auth=HTTPDigestAuth(USERNAME, PASSWORD),
                             headers={"Content-Type": "application/json"},
                             data=json.dumps(payload), timeout=10)
        return resp.json().get("AcsEvent", {}).get("InfoList", [])
    except Exception as e:
        print(f"❌ Xatolik fetch_by_position: {e}")
        return []


def get_direction(minor_code: int) -> str:
    if minor_code == 1:
        return "OUT"
    elif minor_code == 75:
        return "IN"
    else:
        return "Noma'lum"
s = 0

# ✅ Har bir eventni konsolga chiqarish
def print_event(evt):
    global s
    s = s + 1
    time_str = evt.get("time", "")
    employee_id = evt.get("employeeNoString", "")
    name = evt.get("name", "")
    serial = evt.get("serialNo", "")
    reader = evt.get("readerName", "")
    door = evt.get("doorName", "")
    device = evt.get("deviceIndex", "")
    minor = int(evt.get("minor", -1))
    direction = get_direction(minor)

    print(
        f"📅 {time_str} | 👤 {employee_id} - {name} | 🚪 {door} | 📌 Reader: {reader} | 🧭 {direction} | 🏷️ Qurilma: {device} | 🔢 Serial: {serial} number = {s}")


# ✅ Asosiy funksiya: oraliqdagi eventlarni batch bilan olib boradi
def paged_fetch_event_range(start_index, end_index, batch_size=100):
    print(f"🚀 Fetching events from {start_index} to {end_index} in batches of {batch_size}")
    current = start_index

    while current < end_index:
        actual_limit = min(batch_size, end_index - current)
        events = fetch_by_position(current, actual_limit)

        if not events:
            print(f"⛔ No more events returned at position {current}")
            break

        for evt in events:
            if "time" in evt:
                print_event(evt)

        # 🔁 Oxirgi batchda kamroq event bo‘lsa, yana urinish
        if len(events) < actual_limit and (current + len(events)) < end_index:
            remaining = end_index - (current + len(events))
            print(f"⚠️ Only {len(events)} events returned. Retrying remaining {remaining} events...")
            time.sleep(1)
            extra_events = fetch_by_position(current + len(events), remaining)
            for evt in extra_events:
                if "time" in evt:
                    print_event(evt)
            current += len(events) + len(extra_events)
        else:
            current += actual_limit

        time.sleep(0.5)  # optional: qurilma yuklanmasligi uchun delay

    print("✅ Done.")


# ✅ Ishga tushirish
if __name__ == "__main__":
    total = get_total_events()
    if total > 0:
        start_index = max(0, total - 680)
        paged_fetch_event_range(start_index, total, batch_size=100)
    else:
        print("⚠️ Qurilmadan umumiy event soni olinmadi.")
