// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    output: "standalone",
    
    // 🛡️ Server ma'lumotlarini yashirish
    poweredByHeader: false,
    
    // 🛡️ Kodni himoya qilish (Source Maps o'chiriladi)
    productionBrowserSourceMaps: false,
    
    // 🛡️ React Strict Mode
    reactStrictMode: true,

    // 🛡️ Tasvirlar xavfsizligi
    images: {
        domains: [], 
        unoptimized: false,
    },

    // 🛡️ Compiler Options (console.log larni o'chirish)
    compiler: {
        removeConsole: process.env.NODE_ENV === "production" ? { exclude: ['error', 'warn'] } : false,
    },

    allowedDevOrigins: [
        "davomat.uznpu.uz",
        "api.davomat.uznpu.uz",
        "192.186.0.1",
        "localhost",
        "127.0.0.1",
    ],
    
    // 🛡️ Qo'shimcha Headerlar
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    { key: 'X-DNS-Prefetch-Control', value: 'on' },
                    { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
                    { key: 'X-Content-Type-Options', value: 'nosniff' },
                    { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
                    { key: 'X-Permitted-Cross-Domain-Policies', value: 'none' }
                ]
            }
        ]
    }
};

export default nextConfig;
