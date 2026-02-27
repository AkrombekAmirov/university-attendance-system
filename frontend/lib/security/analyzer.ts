// frontend/lib/security/analyzer.ts
import type { NextRequest } from 'next/server';
import { ALLOWED_METHODS, BLOCKED_COUNTRIES, HONEYPOTS, IP_TO_COUNTRY, MALICIOUS_IPS, MAX_QUERY_LENGTH, MAX_URL_LENGTH, MINER_FINGERPRINTS, PATTERNS } from './constants';
import { analyzeBase64Entropy, deepDecode } from './crypto';

export async function analyzeRequest(request: NextRequest, ip: string): Promise<{ safe: boolean; threatScore: number; reason: string; isHoneypot: boolean }> {
  const url = request.nextUrl;
  const path = url.pathname.toLowerCase();

  // 🟢 NEW: Chuqur yechish (Recursive Decode)
  const search = deepDecode(url.search || '');

  let threatScore = 0;
  let isHoneypot = false;

  // 1. Strict Validation & Header checks
  if (!ALLOWED_METHODS.includes(request.method)) return { safe: false, threatScore: 100, reason: `Invalid Method: ${request.method}`, isHoneypot: false };

  // 🟢 NEW: Missing User-Agent (Botlarni ushlash)
  const userAgent = request.headers.get('user-agent') || '';
  if (!userAgent || userAgent.trim() === '') return { safe: false, threatScore: 100, reason: `Missing User-Agent (Bot)`, isHoneypot: false };

  // 🟢 NEW: Null-Byte Injection check
  if (path.includes('%00') || search.includes('\0')) return { safe: false, threatScore: 100, reason: `Null-Byte Injection`, isHoneypot: false };

  // 2. IP & Geo
  if (BLOCKED_COUNTRIES.has(IP_TO_COUNTRY[ip] || 'UNKNOWN')) return { safe: false, threatScore: 100, reason: `Blocked Geo`, isHoneypot: false };
  if (MALICIOUS_IPS.has(ip)) return { safe: false, threatScore: 100, reason: `Known IP`, isHoneypot: false };

  // 3. Honeypot (Dynamic check)
  if (HONEYPOTS.some(hp => path.includes(hp.toLowerCase())) || path.endsWith('.php') || path.endsWith('.env')) {
    console.error(`🚨 HONEYPOT HIT by ${ip} on ${path}`);
    return { safe: false, threatScore: 100, reason: `Honeypot`, isHoneypot: true };
  }

  // 4. Size Limits
  if (url.href.length > MAX_URL_LENGTH) threatScore += 30;
  if (search.length > MAX_QUERY_LENGTH) threatScore += 40;

  // 5. 🛡️ DPI: Payload yig'ish (URL, Query, Headers, Body)
  let combinedPayload = `${path} | ${search} | `;

  request.headers.forEach((value, key) => {
      if (key.toLowerCase() !== 'cookie') combinedPayload += `${key}:${value} | `;
  });

  if (['POST', 'PUT', 'PATCH'].includes(request.method) && !request.headers.get('content-type')?.includes('multipart/form-data')) {
    try {
      const clonedReq = request.clone();
      const bodyText = await clonedReq.text();
      combinedPayload += bodyText.slice(0, 8192); // Max 8KB DPI
    } catch (e) {}
  }

  // 6. 🛡️ Pattern Matching
  for (const [category, patterns] of Object.entries(PATTERNS)) {
    for (const pattern of patterns) {
      if (typeof pattern === 'object' && 'pattern' in pattern) {
        if (pattern.pattern.test(combinedPayload)) {
          const { isSuspicious, entropy } = analyzeBase64Entropy(search);
          if (isSuspicious || entropy > pattern.entropy) {
            threatScore += 70;
            console.error(`🚨 DPI ALERT: High-Entropy Payload (${category}) from ${ip}`);
          }
        }
      } else if (pattern.test(combinedPayload)) {
        threatScore += category === 'miner' ? 90 : 60;
      }
    }
  }

  if (MINER_FINGERPRINTS.some(fp => fp.test(userAgent))) threatScore += 90;
  if (/\.\.\//.test(path) || /%2e%2e/.test(path)) threatScore += 75;

  return { safe: threatScore < 80, threatScore, reason: `Score: ${threatScore}`, isHoneypot };
}