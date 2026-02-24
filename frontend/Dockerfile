# ---------------------------------------------------------------
# 1. BUILD STAGE
# ---------------------------------------------------------------
FROM node:18-alpine AS builder

WORKDIR /app

# Paketlarni o‘rnatish (cache uchun alohida qadam)
COPY package.json package-lock.json* ./

# package-lock.json bo'lmasa ham ishlashi uchun npm install ishlatamiz
RUN npm install

# Loyiha kodini ko‘chirish
COPY . .

# Next.js build qilish
RUN npm run build

# ---------------------------------------------------------------
# 2. RUNTIME STAGE
# ---------------------------------------------------------------
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Faqat kerakli fayllarni ko‘chirib o‘tamiz
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
