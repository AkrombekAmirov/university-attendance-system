// frontend/middleware.ts
// ════════════════════════════════════════════════════════════════════════════════
// EARTH'S ULTIMATE FORTRESS v13.0 - MILITARY GRADE DEFENSE
// ════════════════════════════════════════════════════════════════════════════════

import { NextResponse, type NextRequest } from 'next/server';
import { ALLOWED_HOSTS, SECURITY_SECRET } from './lib/security/constants';
import { signData } from './lib/security/crypto';
import { AdaptiveRateLimiter, isIpBanned, banIp } from './lib/security/rate-limiter';
import { analyzeRequest } from './lib/security/analyzer';
import { checkAuth } from './lib/security/auth';
import { isNightLockdownActive, isAllowedDuringNight } from './lib/security/curfew';

const rateLimiter = new AdaptiveRateLimiter();

function applySecurityHeaders(response: NextResponse, threatScore: number) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' data: https:; font-src 'self' data: https:;
    connect-src 'self' ${apiUrl};
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

    // =========================================================================
    // 👁️ RADAR QATLAM: SO'ROVLARNI LOGGA YOZISH (Jangovar Access Log)
    // =========================================================================
    // Axlat fayllar logni to'ldirib yubormasligi uchun oddiy static requestlarni o'tkazib yuboramiz.
    // Eslatma: config matcher orqali ular onsuz ham o'tmaydi, lekin xavfsizlik uchun qoldirildi.
    const isStaticAsset = path.startsWith('/_next') || path.match(/\.(png|jpg|jpeg|gif|ico|svg|css|js|woff2)$/);
    if (!isStaticAsset) {
        const time = new Date().toISOString();
        const userAgent = request.headers.get('user-agent') || 'No UA';
        console.log(`[WAF-ACCESS] ${time} | IP: ${ip.padEnd(15)} | ${method.padEnd(6)} | ${path.padEnd(30)} | UA: ${userAgent}`);
    }
    // =========================================================================

    // 🧱 1-QATLAM: TUNGI KOMENDANTLIK SOATI
    if (isNightLockdownActive() && !isAllowedDuringNight(path, method)) {
        console.log(`[WAF-BLOCKED] ${ip} - Tungi komendantlik soati (${path})`);
        return new NextResponse(null, { status: 403 });
    }

    // 🧱 2-QATLAM: GILYOTINA (IP VA SUBNET QORA RO'YXATI)
    // ⚡ ELITA HIMOYA: Bloklangan IP lar tahlil qilinmasdan, 1 millisekundda uzib tashlanadi.
    if (isIpBanned(ip)) {
        console.log(`[WAF-GILYOTINA] ${ip} - Qora ro'yxatdagi IP kesib tashlandi!`);
        return new NextResponse('Access Denied.', { status: 403 });
    }

    const host = request.headers.get('host') || '';
    if (Math.random() < 0.02) rateLimiter.cleanup();

    if (process.env.NODE_ENV === 'production') {
      const isAllowedHost = ALLOWED_HOSTS.some(allowed => host === allowed || host.endsWith('.' + allowed) || host.startsWith(allowed.split(':')[0]));
      if (!isAllowedHost) {
          console.log(`[WAF-BLOCKED] ${ip} - Noto'g'ri Host Header: ${host}`);
          return new NextResponse(null, { status: 403 });
      }
    }

    // 🧱 3-QATLAM: WAF TAHLILI VA DPI (DEEP PACKET INSPECTION)
    let bodyText = '';
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
        try {
            bodyText = await request.clone().text();
        } catch (err) {
            bodyText = '';
        }
    }
    const analysis = await analyzeRequest(request, ip, bodyText);

    // 🧱 4-QATLAM: INSTANT BAN (Tarpitsiz)
    if (analysis.threatScore >= 1000 || analysis.isHoneypot) {
        banIp(ip, 48);
        console.log(`🚨 [WAF-CRITICAL] ${ip} - Hujum aniqlandi! ThreatScore: ${analysis.threatScore}. IP 48 soatga bloklandi.`);
        return new NextResponse('Not Found', { status: 404 });
    }

    // 🧱 5-QATLAM: COOKIE TRACKING & RATE LIMIT
    let cookieScore = 0;
    const scoreCookie = request.cookies.get('sec_score');
    if (scoreCookie) {
      const [scoreStr, signature] = scoreCookie.value.split('.');
      if (signature && scoreStr && signature === await signData(scoreStr, SECURITY_SECRET)) {
        cookieScore = parseInt(scoreStr, 10) || 0;
      }
    }

    const totalScore = cookieScore + analysis.threatScore;
    const rateCheck = rateLimiter.check(ip, totalScore);

    if (!rateCheck.allowed) {
        console.log(`[WAF-RATE] ${ip} - Sorovlar soni oshib ketdi!`);
        return new NextResponse('Too Many Requests', { status: 429 });
    }

    if (!analysis.safe || totalScore >= 80) {
      console.log(`[WAF-WARNING] ${ip} - Shubhali harakat. ThreatScore oshdi: ${totalScore}`);
      const newScore = Math.min(200, totalScore + 20);
      const newSignature = await signData(newScore.toString(), SECURITY_SECRET);

      const res = new NextResponse('Forbidden', { status: 403 });
      res.cookies.set('sec_score', `${newScore}.${newSignature}`, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
      return res;
    }

    // 🧱 6-QATLAM: AUTENTIFIKATSIYA
    const authResponse = checkAuth(request);
    if (authResponse) return applySecurityHeaders(authResponse, totalScore);

    // 🧱 7-QATLAM: TOZA TRAFIKKA RUXSAT
    const response = NextResponse.next();
    applySecurityHeaders(response, totalScore);
    return response;

  } catch (error) {
    // Agar WAF'ning o'zi xato qilsa (masalan parsingda), jimkina yopamiz
    return new NextResponse(null, { status: 400 });
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|robots.txt|manifest.json|sw.js).*)'],
};