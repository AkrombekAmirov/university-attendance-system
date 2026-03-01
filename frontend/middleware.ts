// frontend/middleware.ts
// ════════════════════════════════════════════════════════════════════════════════
// EARTH'S ULTIMATE FORTRESS v8.0 - WAF + ANTI-CRASH PIPELINE
// ════════════════════════════════════════════════════════════════════════════════

import { NextResponse, type NextRequest } from 'next/server';
import { ALLOWED_HOSTS, SECURITY_SECRET, SECURITY_WEBHOOK } from './lib/security/constants';
import { signData } from './lib/security/crypto';
import { AdaptiveRateLimiter } from './lib/security/rate-limiter';
import { analyzeRequest } from './lib/security/analyzer';
import { checkAuth } from './lib/security/auth';

const rateLimiter = new AdaptiveRateLimiter();

function applySecurityHeaders(response: NextResponse, threatScore: number) {
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' data: https:;
    font-src 'self' data: https:;
    connect-src 'self' https://api.davomat.uznpu.uz http://localhost:8000;
    worker-src 'self' blob:; 
    object-src 'none'; 
    base-uri 'self'; 
    form-action 'self';
    frame-ancestors 'none'; 
    block-all-mixed-content; 
    upgrade-insecure-requests;
  `.replace(/\s{2,}/g, ' ').trim();

  response.headers.set('Content-Security-Policy', cspHeader);
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
  response.headers.set('X-Threat-Score', threatScore.toString());
  return response;
}

export async function middleware(request: NextRequest) {
  // 🛡️ GLOBAL ANTI-CRASH: Agar xaker shunday URL yuborsaki, Next.js uni o'qiy olmay qulasa, biz 400 berib qaytaramiz!
  try {
    const ip = (request.headers.get('x-real-ip') || request.headers.get('x-forwarded-for') || '127.0.0.1').split(',')[0].trim();
    const host = request.headers.get('host') || '';

    if (Math.random() < 0.02) rateLimiter.cleanup();

    if (process.env.NODE_ENV === 'production') {
      const isAllowedHost = ALLOWED_HOSTS.some(allowed => host === allowed || host.endsWith('.' + allowed) || host.startsWith(allowed.split(':')[0]));
      if (!isAllowedHost) return new NextResponse('Forbidden Host', { status: 403 });
    }

    let cookieScore = 0;
    const scoreCookie = request.cookies.get('sec_score');
    if (scoreCookie) {
      const [scoreStr, signature] = scoreCookie.value.split('.');
      if (signature && scoreStr && signature === await signData(scoreStr, SECURITY_SECRET)) {
        cookieScore = parseInt(scoreStr, 10) || 0;
      } else cookieScore = 999;
    }

    if (cookieScore >= 100) {
      await new Promise(r => setTimeout(r, 5000));
      return new NextResponse('Access Denied by WAF', { status: 403 });
    }

    // Tahlil markaziga jo'natish
    const analysis = await analyzeRequest(request, ip);
    const totalScore = cookieScore + analysis.threatScore;

    const rateCheck = rateLimiter.check(ip, totalScore);
    if (!rateCheck.allowed) return new NextResponse('Too Many Requests', { status: 429, headers: { 'Retry-After': '60' } });

    if (!analysis.safe || totalScore >= 80) {
      const newScore = Math.min(200, totalScore + (analysis.isHoneypot ? 50 : 20));
      const newSignature = await signData(newScore.toString(), SECURITY_SECRET);

      if (analysis.isHoneypot || totalScore >= 90) await new Promise(r => setTimeout(r, 3000)); // Tarpit penalty

      // Xakerga hech qachon 404 emas, aynan 403 beriladi
      const res = new NextResponse('Access Denied by WAF', { status: 403 });
      res.cookies.set('sec_score', `${newScore}.${newSignature}`, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
      return res;
    }

    // 🔐 AUTENTIFIKATSIYA
    const authResponse = checkAuth(request);
    if (authResponse) {
      return applySecurityHeaders(authResponse, totalScore);
    }

    // ✅ RUXSAT
    const response = NextResponse.next();
    applySecurityHeaders(response, totalScore);

    const newScore = Math.max(0, cookieScore - 5); // Yaxshi ishlaganlarning gunohi kechiriladi
    if (newScore !== cookieScore) {
      const newSignature = await signData(newScore.toString(), SECURITY_SECRET);
      response.cookies.set('sec_score', `${newScore}.${newSignature}`, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
    }

    return response;

  } catch (error) {
    // 🔴 MUTLAQ QULASH HIMOYASI (Absolute Crash Protection)
    // Agar kodning qayeridadir xato ketsa, server 500 bermaydi, balki xakerni uzib tashlaydi.
    console.error("🚨 WAF PREVENTED A FATAL CRASH: ", error);
    return new NextResponse('Bad Request / Malformed Payload Blocked', { status: 400 });
  }
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|robots.txt|manifest.json|sw.js).*)'],
};