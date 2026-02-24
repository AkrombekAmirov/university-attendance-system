# ==========================================
# 1-BOSQICH: KUTUBXONALARNI O'RNATISH (Deps)
# ==========================================
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ==========================================
# 2-BOSQICH: KODNI YIG'ISH (Builder)
# ==========================================
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Next.js ilovasini "standalone" rejimida qurish
RUN npm run build

# ==========================================
# 3-BOSQICH: JANGAVAR HOLAT (Runner)
# ==========================================
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

# Xavfsiz foydalanuvchi yaratish
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Faqat ishlashi uchun kerakli bo'lgan yig'ilgan fayllarni ko'chirish
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 💥 SCORCHED EARTH (YONDIRILGAN YER) QOIDASI 💥
# Alpine OS dagi barcha shell va tarmoq utilitalarini yo'q qilish
RUN rm -f /bin/sh /bin/ash /usr/bin/wget /usr/bin/curl /usr/bin/nc || true

# Xavfsiz foydalanuvchiga o'tish
USER nextjs

EXPOSE 3000
ENV PORT 3000

# Standalone rejimida ishlash
CMD ["node", "server.js"]