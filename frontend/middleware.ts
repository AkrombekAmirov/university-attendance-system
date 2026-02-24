import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { checkRateLimit, analyzeRequest } from './lib/security';

// 🍯 HONEYPOT YO'LLARI (Botlar uchun tuzoq)
const HONEYPOT_PATHS = [
    '/admin_secret', '/wp-login.php', '/.env', '/backup.sql', '/db_backup',
    '/phpmyadmin', '/root', '/administrator', '/api/v1/secret'
];

export function middleware(request: NextRequest) {
    const ip = request.ip || request.headers.get('x-forwarded-for') || 'unknown';
    const path = request.nextUrl.pathname;

    // 1️⃣ HONEYPOT CHECK (Tuzoqqa tushganlarni bloklash)
    if (HONEYPOT_PATHS.some(hp => path.includes(hp))) {
        console.warn(`🚨 HONEYPOT TRIGGERED by IP: ${ip} on path: ${path}`);
        return new NextResponse(null, { status: 403, statusText: "Forbidden" });
    }

    // 2️⃣ RATE LIMITING (DDoS Protection)
    if (!checkRateLimit(ip, { limit: 100, windowMs: 60000 })) { // Limitni biroz oshirdim (60 -> 100)
        console.warn(`⚠️ Rate Limit Exceeded: ${ip}`);
        return new NextResponse(JSON.stringify({ error: "Too Many Requests" }), {
            status: 429,
            headers: { 'Retry-After': '60', 'Content-Type': 'application/json' }
        });
    }

    // 3️⃣ WAF ANALYSIS (Payload Inspection)
    const analysis = analyzeRequest(request);
    if (!analysis.safe) {
        console.warn(`🛡️ WAF BLOCKED: ${ip} - Reason: ${analysis.reason}`);
        return new NextResponse(JSON.stringify({ error: "Security Violation" }), {
            status: 403,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    // 4️⃣ SECURITY HEADERS (CSP YUMSHATILDI)
    // 'unsafe-inline' va 'unsafe-eval' Next.js ishlashi uchun kerak (ayniqsa dev mode da)
    // Productionda 'nonce' ishlatish uchun layout.tsx ni ham o'zgartirish kerak bo'ladi.
    // Hozircha sayt ishlashi uchun yumshoqroq CSP qo'yamiz.
    
    const cspHeader = `
        default-src 'self';
        script-src 'self' 'unsafe-inline' 'unsafe-eval';
        style-src 'self' 'unsafe-inline';
        img-src 'self' blob: data:;
        font-src 'self' data:;
        connect-src 'self' https://api.davomat.uznpu.uz; 
        object-src 'none';
        base-uri 'self';
        form-action 'self';
        frame-ancestors 'none';
        block-all-mixed-content;
        upgrade-insecure-requests;
    `.replace(/\s{2,}/g, ' ').trim();

    const response = NextResponse.next();

    // Headerlarni javobga qo'shamiz
    response.headers.set('Content-Security-Policy', cspHeader);
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
    response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()');

    return response;
}

export const config = {
    matcher: [
        '/((?!_next/static|_next/image|favicon.ico|robots.txt).*)',
    ],
};
