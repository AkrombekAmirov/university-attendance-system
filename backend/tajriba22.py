# from backend.worker.tasks.limit_event_fetcher import EventFetcher
#
# def get_last_serial_no(ip, username, password):
#     client = EventFetcher(ip, username, password)
#     total = client.get_total_events()
#
#     if total <= 0:
#         return None
#
#     # oxirgi eventni olish
#     events = client.paged_fetch_event_range(total - 1, total, "CHECK")
#     for batch in events:
#         for evt in batch:
#             return evt.get("serialNo")
#
#     return None
#
#
# if __name__ == "__main__":
#     ip = "10.130.156.2:9187"
#     username = "admin"
#     password = "abcd2024"
#
#     last_serial = get_last_serial_no(ip, username, password)
#     print("✅ TURNIKET LAST SERIAL NO:", last_serial)
import requests
from requests.auth import HTTPDigestAuth
import json

import time
import requests
from requests.auth import HTTPDigestAuth
import json

import time
import requests
from requests.auth import HTTPDigestAuth
import json


def forensic_test():
    ip = "192.128.1.212"
    username = "admin"
    password = "abcd2024"
    auth = HTTPDigestAuth(username, password)
    url = f"http://{ip}/ISAPI/AccessControl/AcsEvent?format=json"

    # Search ID ni aylantirish uchun
    search_id_counter = 1

    def get_search_id():
        nonlocal search_id_counter
        search_id_counter = (search_id_counter % 64) + 1
        return str(search_id_counter)

    print("🔍 1. Tizimdagi jami voqealar soni tekshirilmoqda...")

    # Dastlabki jami sonni aniqlab olamiz
    payload = {
        "AcsEventCond": {
            "searchID": get_search_id(),
            "searchResultPosition": 0,
            "maxResults": 1,
            "major": 0,
            "minor": 0
        }
    }

    try:
        res = requests.post(url, json=payload, auth=auth, timeout=5)
        if res.status_code != 200:
            print(f"❌ Xatolik: {res.status_code}")
            return

        current_total = res.json().get("AcsEvent", {}).get("totalMatches", 0)
        print(f"✅ Boshlang'ich Holat: Tizimda aniq {current_total} ta voqea bor.")
    except Exception as e:
        print(f"🔌 Ulanish xatosi: {e}")
        return

    print("\n" + "=" * 50)
    print("🚀 2. MIKROSKOP REJIMI YONDI")
    print("🚶‍♂️ Iltimos, borib turniketdan o'ting...")
    print("=" * 50 + "\n")

    while True:
        try:
            # 1. Faqat jami sonni tekshiramiz (eng tezkor so'rov)
            check_payload = {
                "AcsEventCond": {
                    "searchID": get_search_id(),
                    "searchResultPosition": 0,
                    "maxResults": 1,
                    "major": 0,
                    "minor": 0
                }
            }
            res_check = requests.post(url, json=check_payload, auth=auth, timeout=3).json()
            new_total = res_check.get("AcsEvent", {}).get("totalMatches", 0)

            # 2. Agar son oshgan bo'lsa, demak kimdir o'tdi!
            if new_total > current_total:
                diff = new_total - current_total
                print(f"💡 DIQQAT! Tizim xotirasida {diff} ta yangi voqea paydo bo'ldi! (Jami: {new_total})")

                # 3. Aynan o'sha qo'shilgan yangi voqealarni indeks orqali tortib olamiz
                fetch_payload = {
                    "AcsEventCond": {
                        "searchID": get_search_id(),
                        "searchResultPosition": current_total,  # Eski sonimizdan boshlab
                        "maxResults": min(diff, 30),  # Qancha qo'shilgan bo'lsa shunchasini olamiz (maksimum 30)
                        "major": 0,
                        "minor": 0
                    }
                }
                res_fetch = requests.post(url, json=fetch_payload, auth=auth, timeout=3).json()
                events = res_fetch.get("AcsEvent", {}).get("InfoList", [])

                for ev in events:
                    name = ev.get("name", "Noma'lum")
                    time_v = ev.get("time", "")
                    major = ev.get("major")
                    print(f"✅ USHLANDI: Vaqt: {time_v} | Ism: {name} | Major: {major}")

                # Jami sonni yangilaymiz
                current_total = new_total

            # Sekinroq qadam bilan tekshiramiz
            time.sleep(1)

        except requests.exceptions.RequestException:
            pass  # Kichik uzilishlarni inobatga olmaslik

if __name__ == "__main__":
    forensic_test()