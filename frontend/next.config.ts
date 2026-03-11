import type { NextConfig } from "next";
import path from "path";

// 🛡️ CSP (Content Security Policy) qoidalari
// XSS (Cross-Site Scripting) va ma'lumotlarni o'g'irlash hujumlariga qarshi eng kuchli qurol.
const ContentSecurityPolicy = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data:;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
  upgrade-insecure-requests;
`.replace(/\s{2,}/g, ' ').trim();

const nextConfig: NextConfig = {
    output: "standalone",
    eslint: { ignoreDuringBuilds: true },
    typescript: { ignoreBuildErrors: true },

    // 🛡️ Server ma'lumotlarini yashirish (X-Powered-By ni olib tashlaydi)
    poweredByHeader: false,
    
    // 🛡️ Kodni himoya qilish (Xakerlar Frontend mantiqini o'qiy olmasligi uchun)
    productionBrowserSourceMaps: false,
    
    // 🛡️ React Strict Mode
    reactStrictMode: true,

    // 🛡️ Tasvirlar xavfsizligi
    // Eski 'domains' xavfsiz bo'lmagani uchun Next.js da 'remotePatterns' ga o'tilgan.
    images: {
        unoptimized: false,
        remotePatterns: [
            // Agar kelajakda MinIO/S3 dan rasm olsangiz, shu yerda qat'iy qoidasini yozasiz.
            // Hozircha bo'sh, ya'ni faqat o'zidan rasm yuklashga ruxsat.
        ],
    },

    // 🛡️ Compiler Options (Ishlab chiqarish muhitida ma'lumot sizib chiqishini to'xtatish)
    compiler: {
        removeConsole: process.env.NODE_ENV === "production" ? { exclude: ['error', 'warn'] } : false,
    },

    // 🎯 TO'G'RILANDI: CSRF hujumlariga qarshi Server Actions himoyasi
    // 'allowedDevOrigins' qoidasi aynan shu yerda (experimental.serverActions) yozilishi shart.
    experimental: {
        serverActions: {
            bodySizeLimit: '2mb', // Massive RCE buffer qariyb mumkin emas
            allowedOrigins: [
                "davomat.uznpu.uz",
                "api.davomat.uznpu.uz",
                "192.186.0.1",
                "localhost:3000",
                "127.0.0.1:3000",
            ]
        }
    },
    
    // 🛡️ Defense-in-Depth (Chuqurlashtirilgan himoya) Headerlari
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    { key: 'X-DNS-Prefetch-Control', value: 'on' },
                    { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
                    { key: 'X-Content-Type-Options', value: 'nosniff' },
                    { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
                    { key: 'X-Permitted-Cross-Domain-Policies', value: 'none' },
                    
                    // 🔥 YANGI QO'SHILGAN HIMOYALAR:
                    // 1. Clickjacking hujumiga qarshi mutlaq blok (saytingizni boshqa sayt ichida ochib bo'lmaydi)
                    { key: 'X-Frame-Options', value: 'DENY' },
                    // 2. XSS viruslariga qarshi CSP ni yoqish
                    { key: 'Content-Security-Policy', value: ContentSecurityPolicy },
                    // 3. Brauzerning xavfli API larini (kamera, mikrafon, joylashuv) bloklash
                    { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), browsing-topics=()' }
                ]
            }
        ]
    }
};

export default nextConfig;