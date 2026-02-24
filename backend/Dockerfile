# ==========================================
# 1-BOSQICH: YIG'UVCHI (Builder)
# ==========================================
FROM python:3.11-slim AS builder

# Tizim paketlarini yangilash va kerakli kutubxonalarni o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalar ro'yxatini ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ==========================================
# 2-BOSQICH: JANGAVAR HOLAT (Runner)
# ==========================================
FROM python:3.11-slim

# Xavfsiz, huquqlari cheklangan foydalanuvchi yaratish
RUN groupadd -g 1001 appuser && useradd -u 1001 -g appuser -s /sbin/nologin appuser

# Zombi-protsesslarni tozalash uchun 'tini' o'rnatamiz
RUN apt-get update && apt-get install -y --no-install-recommends tini libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Builder'dan tayyor kutubxonalarni olib kelish va o'rnatish
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Kodlarni ko'chirish va egalikni o'zgartirish
COPY . .
RUN chown -R appuser:appuser /app

# 💥 SCORCHED EARTH (YONDIRILGAN YER) QOIDASI 💥
# Xaker kodni yorib kirsa ham, terminal (shell) yoki virus tortish asboblari bo'lmaydi
RUN rm -f /bin/sh /bin/bash /usr/bin/wget /usr/bin/curl /usr/bin/nc /bin/dash || true

# Xavfsiz foydalanuvchiga o'tish (Root huquqidan chiqish)
USER appuser

# API uchun port
EXPOSE 8000

# Standart buyruq (API uchun). Worker uchun docker-compose o'zgartiradi
ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]