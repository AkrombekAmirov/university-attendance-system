from backend.worker.tasks.limit_event_fetcher import EventFetcher

def get_last_serial_no(ip, username, password):
    client = EventFetcher(ip, username, password)
    total = client.get_total_events()

    if total <= 0:
        return None

    # oxirgi eventni olish
    events = client.paged_fetch_event_range(total - 1, total, "CHECK")
    for batch in events:
        for evt in batch:
            return evt.get("serialNo")

    return None


if __name__ == "__main__":
    ip = "10.130.156.2:9187"
    username = "admin"
    password = "abcd2024"

    last_serial = get_last_serial_no(ip, username, password)
    print("✅ TURNIKET LAST SERIAL NO:", last_serial)
