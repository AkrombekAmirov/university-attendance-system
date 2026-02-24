# ---------------------------------------------------------------
# 1. BUILD STAGE
# ---------------------------------------------------------------
FROM node:18-alpine AS builder

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Paketlarni o‘rnatish
COPY package.json package-lock.json* ./
RUN npm ci

# Loyiha kodini ko‘chirish
COPY . .

# Next.js build qilish
# Standalone output kerak (next.config.ts da yoqilgan bo'lishi shart)
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---------------------------------------------------------------
# 2. RUNTIME STAGE (Distroless - No Shell, No Root)
# ---------------------------------------------------------------
# Google Distroless imidji: Shell, Package Manager, va boshqa keraksiz narsalar yo'q.
# Faqat Node.js runtime bor.
FROM gcr.io/distroless/nodejs18-debian12 AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Root bo'lmagan foydalanuvchi yaratish shart emas, Distroless da 'nonroot' bor (uid 65532)
# Lekin fayllarni to'g'ri ko'chirish kerak.

# Kerakli fayllarni builder dan ko'chiramiz
COPY --from=builder --chown=nonroot:nonroot /app/public ./public
COPY --from=builder --chown=nonroot:nonroot /app/.next/standalone ./
COPY --from=builder --chown=nonroot:nonroot /app/.next/static ./.next/static

# Non-root userga o'tish
USER nonroot:nonroot

# Port
EXPOSE 3000

# Serverni ishga tushirish
CMD ["server.js"]
