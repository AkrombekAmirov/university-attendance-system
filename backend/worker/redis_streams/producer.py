# backend/worker/redis_streams/producer.py

import json
import time
from datetime import datetime, timedelta  # 🟢 QO'SHILDI: timedelta
from backend.worker.redis_streams.config import *


class TurniketProducer:
    """
    Hybrid Production Model:
    - Offline → Online : time-based binary search recovery
    - Realtime         : incremental serial/position based polling
    """

    def __init__(self, device, redis_sync, fetcher, status_queue):

        self.device = device
        self.redis = redis_sync
        self.fetcher = fetcher
        self.status_queue = status_queue

        self.last_event_time = device.last_event_time
        self.last_position = device.last_serial_no or 0
        self._current_status = device.sync_status

    # ================= STATUS ================= #

    def _set_status(self, new_status: str):
        if self._current_status == new_status:
            return

        try:
            self.status_queue.put_nowait((self.device.id, new_status))
            self._current_status = new_status
            print(f"📊 [{self.device.name}] STATUS → {new_status}")
        except Exception as e:
            print(f"❌ STATUS QUEUE ERROR [{self.device.name}]: {e}")

    # ================= REDIS PUSH ================= #

    def _push(self, evt: dict):
        self.redis.xadd(
            REDIS_STREAM_RT,
            {
                "device_id": str(self.device.id),
                "event": json.dumps(evt),
                "ts": str(time.time()),
            },
            maxlen=1_000_000,
            approximate=True,
        )

    # ================= UTILS ================= #

    def _parse_time(self, evt: dict) -> datetime | None:
        raw = evt.get("time")
        if not raw:
            return None

        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)

    # 🟢 QO'SHILDI: Bugungi sanadan 30 kun oldingi vaqtni beradi
    def _get_one_month_ago(self) -> datetime:
        return self._day_start(datetime.now() - timedelta(days=30))

    # ================= BINARY SEARCH (RECOVERY ONLY) ================= #

    def _find_start_serial_by_date(self, start_date: datetime, total: int) -> int:

        if total <= 0:
            return 0

        low = 0
        high = total - 1
        result = total

        while low <= high:
            mid = (low + high) // 2

            events = list(
                self.fetcher.paged_fetch_event_range(
                    mid, mid + 1, self.device.name
                )
            )

            if not events or not events[0]:
                low = mid + 1
                continue

            evt = events[0][0]
            evt_time = self._parse_time(evt)

            if not evt_time:
                low = mid + 1
                continue

            if evt_time < start_date:
                low = mid + 1
            else:
                result = mid
                high = mid - 1

        return max(0, result)

    # ================= OFFLINE → ONLINE RECOVERY ================= #

    def _offline_sync(self):

        total = self.fetcher.get_total_events()

        if self.fetcher.last_error:
            self._set_status("offline")
            return False

        self._set_status("syncing")

        one_month_ago = self._get_one_month_ago()  # 🟢 QO'SHILDI

        if self.last_event_time:
<<<<<<< HEAD
            start_date = self._day_start(self.last_event_time)

            # 🟢 QO'SHILDI: DB dagi vaqt 1 oydan eski bo'lsa, qidiruvni 1 oylik limitga tushiramiz
            if start_date < one_month_ago:
                print(f"⚠️ [{self.device.name}] DB vaqti juda eski ({start_date}). 1 oylik qidiruvga o'tkazildi.")
                start_date = one_month_ago

            start = self._find_start_serial_by_date(start_date, total)
=======
            start = self._find_start_serial_by_date(self.last_event_time, total)
>>>>>>> bcc8fb49ad3a69160c569756b6e944ba3662a768
        else:
            start = max(0, total - HISTORY_LIMIT)

        if start >= total:
            self.last_position = total
            self._set_status("online")
            return True

        for batch in self.fetcher.paged_fetch_event_range(
                start, total, self.device.name
        ):
            for evt in batch:
                evt_time = self._parse_time(evt)
<<<<<<< HEAD

                # 🟢 QO'SHILDI: Turniket kutilmaganda "1 yil oldingi" xato sanali event bersa, o'tkazmaymiz
                if evt_time and evt_time < one_month_ago:
=======
                if self.last_event_time and evt_time and evt_time <= self.last_event_time:
>>>>>>> bcc8fb49ad3a69160c569756b6e944ba3662a768
                    continue

                self._push(evt)
                print(f"[{self.device.name}] Pushed offline event: {evt}")
                if evt_time:
                    self.last_event_time = evt_time

        self.last_position = total

        self._set_status("online")
        print(f"🔥 [{self.device.name}] RECOVERY DONE")

        return True

    # ================= REALTIME LOOP (INCREMENTAL ONLY) ================= #

    def _realtime_loop(self):

        while True:

            total = self.fetcher.get_total_events()
            one_month_ago = self._get_one_month_ago()  # 🟢 QO'SHILDI

            if self.fetcher.last_error:
                self._set_status("offline")
                time.sleep(2)
                return  # exit loop → restart recovery

            if total > self.last_position:

                for batch in self.fetcher.paged_fetch_event_range(
                        self.last_position, total, self.device.name
                ):
                    for evt in batch:
                        evt_time = self._parse_time(evt)
<<<<<<< HEAD

                        # 🟢 QO'SHILDI: Jonli rejimda ham xato sanali event chiqib qolsa ushlab qolamiz
                        if evt_time and evt_time < one_month_ago:
=======
                        if self.last_event_time and evt_time and evt_time <= self.last_event_time:
>>>>>>> bcc8fb49ad3a69160c569756b6e944ba3662a768
                            continue

                        self._push(evt)
                        print(f"[{self.device.name}] Pushed realtime event: {evt}")
                        if evt_time:
                            self.last_event_time = evt_time

                self.last_position = total
                self._set_status("online")

            time.sleep(REALTIME_INTERVAL)

    # ================= RUN ================= #

    def run(self):

        while True:
            try:
                ok = self._offline_sync()
                if ok:
                    self._realtime_loop()

            except Exception as e:
                self._set_status("offline")
                print(f"🔥 [{self.device.name}] CRASH → restart: {e}")
                time.sleep(2)