// frontend/middleware.ts
// ════════════════════════════════════════════════════════════════════════════════
// EARTH'S ULTIMATE FORTRESS v10.0 - "NIGHT LOCKDOWN" EDITION
// ════════════════════════════════════════════════════════════════════════════════

import { NextResponse, type NextRequest } from 'next/server';
import { ALLOWED_HOSTS, SECURITY_SECRET } from './lib/security/constants';
import { signData } from './lib/security/crypto';
import { AdaptiveRateLimiter, isIpBanned, banIp } from './lib/security/rate-limiter';
import { analyzeRequest } from './lib/security/analyzer';
import { checkAuth } from './lib/security/auth';
import { isNightLockdownActive, isAllowedDuringNight } from './lib/security/curfew'; // 🟢 YANGI QO'SHILDI

const rateLimiter = new AdaptiveRateLimiter();

function applySecurityHeaders(response: NextResponse, threatScore: number) {
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' data: https:; font-src 'self' data: https:;
    connect-src 'self' https://api.davomat.uznpu.uz http://localhost:8000;
    worker-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self';
    frame-ancestors 'none'; block-all-mixed-content; upgrade-insecure-requests;
  `.replace(/\s{2,}/g, ' ').trim();

  response.headers.set('Content-Security-Policy', cspHeader);
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  return response;
}

export async function middleware(request: NextRequest) {
  try {
    const ip = (request.headers.get('x-real-ip') || request.headers.get('x-forwarded-for') || '127.0.0.1').split(',')[0].trim();
    const path = request.nextUrl.pathname;
    const method = request.method;

    // =====================================================================
    // 🛑 1-QATLAM: "ZERO-TRUST" TUNGI PROTOKOL (00:00 - 05:00 UZT)
    // =====================================================================
    if (isNightLockdownActive()) {
        if (!isAllowedDuringNight(path, method)) {
            // Xaker .env yoki /server izlasa, darhol uzamiz! (Tizimga og'irlik tushmaydi)
            return new NextResponse(null, { status: 403 });
        }
    }

    // =====================================================================
    // 🛡️ 2-QATLAM: GILYOTINA (IP qora ro'yxati)
    // =====================================================================
    if (isIpBanned(ip)) {
        return new NextResponse(null, { status: 403 });
    }

    const host = request.headers.get('host') || '';
    if (Math.random() < 0.02) rateLimiter.cleanup();

    if (process.env.NODE_ENV === 'production') {
      const isAllowedHost = ALLOWED_HOSTS.some(allowed => host === allowed || host.endsWith('.' + allowed) || host.startsWith(allowed.split(':')[0]));
      if (!isAllowedHost) return new NextResponse(null, { status: 403 });
    }

    // =====================================================================
    // 🛡️ 3-QATLAM: WAF TAHLILI (DPI & Payload tekshiruvi)
    // =====================================================================
    let cookieScore = 0;
    const scoreCookie = request.cookies.get('sec_score');
    if (scoreCookie) {
      const [scoreStr, signature] = scoreCookie.value.split('.');
      if (signature && scoreStr && signature === await signData(scoreStr, SECURITY_SECRET)) {
        cookieScore = parseInt(scoreStr, 10) || 0;
      }
    }

    const analysis = await analyzeRequest(request, ip);
    const totalScore = cookieScore + analysis.threatScore;

    const rateCheck = rateLimiter.check(ip, totalScore);
    if (!rateCheck.allowed) return new NextResponse('Too Many Requests', { status: 429 });

    if (!analysis.safe || totalScore >= 80) {
      if (analysis.isHoneypot || totalScore >= 100) {
          banIp(ip, 48); // Qopqonga tushganlarni endi 48 soatga (2 kunga) bloklaymiz
      }

      const newScore = Math.min(200, totalScore + (analysis.isHoneypot ? 50 : 20));
      const newSignature = await signData(newScore.toString(), SECURITY_SECRET);

      const res = new NextResponse('Forbidden', { status: 403 });
      res.cookies.set('sec_score', `${newScore}.${newSignature}`, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
      return res;
    }

    // =====================================================================
    // 🔐 4-QATLAM: AUTENTIFIKATSIYA VA RUXSAT
    // =====================================================================
    const authResponse = checkAuth(request);
    if (authResponse) return applySecurityHeaders(authResponse, totalScore);

    const response = NextResponse.next();
    applySecurityHeaders(response, totalScore);
    return response;

  } catch (error) {
    // Xaker tizimni qulatmoqchi bo'lsa, hech qanday xato qaytarmaymiz.
    return new NextResponse('Bad Request', { status: 400 });
  }
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|robots.txt|manifest.json|sw.js).*)'],
};