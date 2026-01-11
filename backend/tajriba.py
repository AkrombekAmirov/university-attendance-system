import requests
from requests.auth import HTTPDigestAuth
import json, time, os
from datetime import datetime

# Device Settings
DEVICE_IP = "192.128.1.215"
USERNAME = "admin"
PASSWORD = "abcd2024"

DEVICE_NAME = "Turniket A1"
DEVICE_SN = "SN2023XYZ"

SERIAL_FILE = "last_serial.txt"
BATCH_SIZE = 1000  # stable Hikvision limit
MAX_CATCHUP = 50000  # safety limit: 50k events max per recovery

##########################
# Serial Storage Helpers
##########################
#
# def read_last_serial():
#     try:
#         return int(open(SERIAL_FILE).read())
#     except:
#         return None

def save_last_serial(s):
    with open(SERIAL_FILE, "w") as f:
        f.write(str(s))

##########################
# API helpers
##########################

def get_total_events():
    url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"
    payload = {
        "AcsEventCond": {"searchID":"count","searchResultPosition":0,"maxResults":1,"major":5,"minor":0}
    }
    resp = requests.post(url, auth=HTTPDigestAuth(USERNAME,PASSWORD),
                         headers={"Content-Type":"application/json"},
                         data=json.dumps(payload))
    return int(resp.json()["AcsEvent"]["totalMatches"])

def fetch_events(pos, limit):
    limit = min(limit, BATCH_SIZE)
    url = f"http://{DEVICE_IP}/ISAPI/AccessControl/AcsEvent?format=json"

    payload = {
        "AcsEventCond": {
            "searchID":"resume",
            "searchResultPosition":pos,
            "maxResults":limit,
            "major":5,"minor":0
        }
    }
    resp = requests.post(url, auth=HTTPDigestAuth(USERNAME,PASSWORD),
                         headers={"Content-Type":"application/json"},
                         data=json.dumps(payload))
    return resp.json().get("AcsEvent",{}).get("InfoList",[])

##########################
# Business Logic Helpers
##########################

def get_direction(minor):
    return "KIRDI" if minor in [75,72] else "CHIQMADI" if minor in [21,22] else "NOANIQ"

def print_event(e):
    dt = datetime.fromisoformat(e["time"])
    date = dt.strftime("%Y-%m-%d"); t = dt.strftime("%H:%M:%S")

    print(f"{e.get('employeeNoString','-')}, {date}, default-group, {date}, {t}, "
          f"{get_direction(e.get('minor'))}, {DEVICE_NAME}, {DEVICE_SN}, "
          f"{e.get('name','-')}, {e.get('cardNo','-')}, {date} {t}, serial={e['serialNo']}")

#################################
# Real-time engine + auto catchup
#################################

def watch_turniket_realtime():
    print("📡 Real-time started...")
    last_total = get_total_events()

    while True:
        try:
            total = get_total_events()

            if total > last_total:
                diff = total - last_total
                fetch_latest_events(min(diff, 500))
                last_total = total

            time.sleep(2)

        except Exception as e:
            print(f"🚨 Network down: {e}")
            time.sleep(5)

#################################
# Fetch latest block
#################################

def fetch_latest_events(limit):
    total = get_total_events()
    start = max(0, total - limit)

    for pos in range(start, total, BATCH_SIZE):
        events = fetch_events(pos, BATCH_SIZE)
        for e in events:
            print_event(e)
            save_last_serial(e["serialNo"])

#################################
# Main
#################################


watch_turniket_realtime()