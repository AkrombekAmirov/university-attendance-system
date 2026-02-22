# backend/worker/realtime/supervisor.py
from datetime import datetime


def get_direction(minor_code: int) -> str:
    if minor_code in (75, 72):
        return "IN"
    elif minor_code in (21, 22):
        return "OUT"
    return "UNKNOWN"


async def handle_event(service, device, event: dict):
    """
    Eventni:
    1) Konsolga chiqaradi
    2) DB ga yozadi
    3) latest serial + datetime qaytaradi
    """

    time_str = event.get("time")
    serial = event.get("serialNo")

    # 🔹 Time parse + TZ normalize
    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)

    employee_id = event.get("employeeNoString", "-")
    name = event.get("name") or event.get("personName") or "-"
    minor = int(event.get("minor", -1))
    direction = get_direction(minor)

    print(
        f"📅 {time_str} | "
        f"👤 {employee_id} - {name} | "
        f"🧭 {direction} | "
        f"🏷️ {device.name} | "
        f"🔢 Serial: {serial}\n"
        f"{event}"
    )

    # 🔹 ASOSIY QISM — DB GA YOZISH
    await service.process_realtime_event(event, device.id)

    return serial, dt
