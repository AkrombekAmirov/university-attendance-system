from __future__ import annotations
import sys
import os
import json
import logging
from datetime import datetime
from loguru import logger
import structlog
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

    # 🔹 Loguru default chiqishlarini tozalash
    logger.remove()

    # 🔹 1. Konsol chiqish (dev mode uchun rangli)
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=settings.LOG_LEVEL,
    )

    # 🔹 2. Fayl chiqishi (rotation + retention)
    log_path = settings.LOG_FILE_PATH
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger.add(
        log_path,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,   # “10 MB”
        retention=settings.LOG_RETENTION, # “10 days”
        compression="zip",
        encoding="utf-8",
        serialize=False,  # False: dev, True: JSON log
        enqueue=True,     # Thread-safe writing
        backtrace=False,
        diagnose=False,
    )

    # 🔹 Structlog sozlamasi
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(indent=None, ensure_ascii=False),
        ],
    )

    # 🔹 Root loggingni Loguru bilan integratsiya qilish
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Root logging uchun loguru ga uzatish
            try:
                level = logger.level(record.levelname).name
            except Exception:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]

    # 🔹 Log test chiqishi
    logger.info("✅ Logging initialized.")
    logger.debug(f"Logging level: {settings.LOG_LEVEL}")
    logger.debug(f"Log file: {settings.LOG_FILE_PATH}")

    return logger


# ===============================
# 3️⃣ Foydalanish uchun logger obyekt
# ===============================

logger_ = setup_logging()
