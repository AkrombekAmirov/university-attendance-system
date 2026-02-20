# ---------------------------------------------------------------
# 1. BUILD STAGE
# ---------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Tizim kutubxonalari (PostgreSQL driver va kompilyatorlar uchun)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python paketlarini o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------
# 2. RUNTIME STAGE
# ---------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Kerakli kutubxonalar (libpq faqat runtime uchun)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Builder bosqichidan tayyor paketlarni ko‘chirib o‘tamiz
COPY --from=builder /install /usr/local

# Loyiha kodini ko‘chiramiz
COPY . /app/backend

# PYTHONPATH ni to‘g‘rilash (backend papkasi ichida turib, rootni ko‘rish uchun)
ENV PYTHONPATH=/app

# Portni ochish
EXPOSE 8000

# Default command (buni docker-compose da override qilish mumkin)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
