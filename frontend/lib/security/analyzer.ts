// frontend/lib/security/analyzer.ts
import type { NextRequest } from 'next/server';
import { ALLOWED_METHODS, BLOCKED_COUNTRIES, HONEYPOTS, IP_TO_COUNTRY, MALICIOUS_IPS, MAX_QUERY_LENGTH, MAX_URL_LENGTH, MINER_FINGERPRINTS, PATTERNS } from './constants';
import { analyzeBase64Entropy, deepDecode } from './crypto';

export async function analyzeRequest(request: NextRequest, ip: string): Promise<{ safe: boolean; threatScore: number; reason: string; isHoneypot: boolean }> {
  let url;
  let path = '';
  let search = '';

  // 🛡️ DYNAMIC URL PARSER (Next.js ni qulashidan asrash uchun)
  try {
    url = request.nextUrl;
    path = url.pathname.toLowerCase();
    search = deepDecode(url.search || '');
  } catch (e) {
    return { safe: false, threatScore: 100, reason: `Malformed URI Attack Attempt`, isHoneypot: false };
  }

  let threatScore = 0;
  let isHoneypot = false;

  // Header va Method tekshiruvi
  if (!ALLOWED_METHODS.includes(request.method)) return { safe: false, threatScore: 100, reason: `Invalid Method: ${request.method}`, isHoneypot: false };

  const userAgent = request.headers.get('user-agent') || '';
  if (!userAgent || userAgent.trim() === '') return { safe: false, threatScore: 100, reason: `Missing User-Agent (Bot)`, isHoneypot: false };

  // 🛡️ Null-Byte Injection
  if (path.includes('%00') || search.includes('\0')) return { safe: false, threatScore: 100, reason: `Null-Byte Injection`, isHoneypot: false };

  // IP va Geo blok
  if (BLOCKED_COUNTRIES.has(IP_TO_COUNTRY[ip] || 'UNKNOWN')) return { safe: false, threatScore: 100, reason: `Blocked Geo`, isHoneypot: false };
  if (MALICIOUS_IPS.has(ip)) return { safe: false, threatScore: 100, reason: `Known Malicious IP`, isHoneypot: false };

  // Honeypot qopqonlari
  if (HONEYPOTS.some(hp => path.includes(hp.toLowerCase())) || path.endsWith('.php') || path.endsWith('.env')) {
    console.error(`🚨 HONEYPOT TRIGGERED by ${ip} on ${path}`);
    return { safe: false, threatScore: 100, reason: `Honeypot Access`, isHoneypot: true };
  }

  // Hajm tekshiruvi (Hackerlar DDoS qilishini oldini olish)
  if (url.href.length > MAX_URL_LENGTH) threatScore += 50;
  if (search.length > MAX_QUERY_LENGTH) threatScore += 50;

  // 🛡️ DPI: Payload yig'ish (URL, Query, Headers, Body)
  let combinedPayload = `${path} | ${search} | `;

  request.headers.forEach((value, key) => {
      if (key.toLowerCase() !== 'cookie') combinedPayload += `${key}:${value} | `;
  });

  // Body Inspection (Agar hajmi judayam katta bo'lmasa)
  const contentLength = Number(request.headers.get('content-length') || 0);
  if (contentLength > 0 && contentLength < 500000 && ['POST', 'PUT', 'PATCH'].includes(request.method) && !request.headers.get('content-type')?.includes('multipart/form-data')) {
    try {
      const clonedReq = request.clone();
      const bodyText = await clonedReq.text();
      combinedPayload += bodyText.slice(0, 8192); // Max 8KB DPI skaneri
    } catch (e) {
      // Ignored, stream cannot be read
    }
  }

  // 🛡️ Mantiqiy Pattern Skaneri
  for (const [category, patterns] of Object.entries(PATTERNS)) {
    for (const pattern of patterns) {
      if (typeof pattern === 'object' && 'pattern' in pattern) {
        if (pattern.pattern.test(combinedPayload)) {
          const { isSuspicious, entropy } = analyzeBase64Entropy(search);
          if (isSuspicious || entropy > pattern.entropy) {
            threatScore += 80;
            console.error(`🚨 WAF DETECTED: High-Entropy Payload (${category}) from ${ip}`);
          }
        }
      } else if (pattern.test(combinedPayload)) {
        threatScore += category === 'miner' ? 90 : 60;
      }
    }
  }

  if (MINER_FINGERPRINTS.some(fp => fp.test(userAgent))) threatScore += 90;
  if (/\.\.\//.test(path) || /%2e%2e/.test(path)) threatScore += 100; // Path Traversal uchun darhol blok!

  return { safe: threatScore < 80, threatScore, reason: `Score: ${threatScore}`, isHoneypot };
}