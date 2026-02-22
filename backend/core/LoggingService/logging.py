from __future__ import annotations
import sys
import os
import json
import logging
from datetime import datetime
import structlog
from loguru import logger
from backend.core.config import get_settings


# ===============================
# 1️⃣ Maxfiy ma’lumotlarni yashirish filtri
# ===============================

SENSITIVE_KEYS = {"password", "token", "secret", "key", "authorization"}


def sanitize_record(record: dict) -> dict:
    """Maxfiy ma’lumotlarni logdan tozalaydi."""
    for key in list(record.keys()):
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            record[key] = "***HIDDEN***"
    return record


# ===============================
# 2️⃣ Loguru + Structlog konfiguratsiyasi
# ===============================

def setup_logging():
    settings = get_settings()

    logger.remove()

    # ===============================
    # 1️⃣ STDOUT (production uchun asosiy)
    # ===============================
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        enqueue=True,         # thread-safe
        backtrace=False,
        diagnose=False,
        colorize=False,       # productionda rang kerak emas
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | "
               "{level:<8} | "
               "{name}:{function}:{line} - "
               "{message}",
    )

    # ===============================
    # 2️⃣ FILE LOG (faqat agar yoqilgan bo‘lsa)
    # ===============================
    if getattr(settings, "ENABLE_FILE_LOG", False):

        log_path = settings.LOG_FILE_PATH
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        logger.add(
            log_path,
            level=settings.LOG_LEVEL,
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="zip",
            encoding="utf-8",
            serialize=False,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            delay=True,  # 🔑 file handle faqat kerak bo‘lganda ochiladi
        )

    # ===============================
    # 3️⃣ Uvicorn access logni o‘chirish (performance)
    # ===============================
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = False

    # ===============================
    # 4️⃣ Requests debug loglarni o‘chirish
    # ===============================
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    logger.info("✅ Logging initialized.")

    return logger



# ===============================
# 3️⃣ Foydalanish uchun logger obyekt
# ===============================

logger_ = setup_logging()
