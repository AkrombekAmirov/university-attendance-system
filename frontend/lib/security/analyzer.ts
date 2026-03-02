// frontend/lib/security/analyzer.ts
import type { NextRequest } from 'next/server';
import { ALLOWED_METHODS, BLOCKED_COUNTRIES, HONEYPOTS, IP_TO_COUNTRY, MALICIOUS_IPS, MAX_QUERY_LENGTH, MAX_URL_LENGTH, MINER_FINGERPRINTS, PATTERNS } from './constants';
import { analyzeBase64Entropy, deepDecode } from './crypto';

export async function analyzeRequest(request: NextRequest, ip: string): Promise<{ safe: boolean; threatScore: number; reason: string; isHoneypot: boolean }> {
  let url;
  let path = '';
  let search = '';

  try {
    url = request.nextUrl;
    path = url.pathname.toLowerCase();
    search = deepDecode(url.search || '');
  } catch (e) {
    return { safe: false, threatScore: 100, reason: `Malformed URI Attack Attempt`, isHoneypot: false };
  }

  let threatScore = 0;
  let isHoneypot = false;

  if (!ALLOWED_METHODS.includes(request.method)) return { safe: false, threatScore: 100, reason: `Invalid HTTP Method`, isHoneypot: false };

  // 🟢 BOTNET SIGNATURE CHECK: / ekaniga qaramay ichida tushunarsiz parametrlar kelsa
  const queryKeys = Array.from(url.searchParams.keys());
  if (path === '/' && queryKeys.length > 2) {
      const isBotnet = queryKeys.some(k => ['h', 'u', 'p', 'r', 'cmd', 'exec'].includes(k));
      if (isBotnet) return { safe: false, threatScore: 100, reason: `Botnet Beacon Signature`, isHoneypot: true }; // 100 ball darhol ban beradi!
  }

  // 🟢 AGGRESSIVE EXTENSION BLOCKING: Bizning Next.js saytimizda .php, .action, .json yo'q! Kirdimi demak 100% xaker!
  if (path.match(/\.(php|action|json|yml|yaml|xml|sql|tar|gz|zip)$/i)) {
      return { safe: false, threatScore: 100, reason: `Forbidden Extension Scan`, isHoneypot: true };
  }

  const userAgent = request.headers.get('user-agent') || '';
  if (!userAgent || userAgent.trim() === '') return { safe: false, threatScore: 100, reason: `Missing User-Agent (Bot)`, isHoneypot: false };

  if (path.includes('%00') || search.includes('\0')) return { safe: false, threatScore: 100, reason: `Null-Byte Injection`, isHoneypot: false };

  if (BLOCKED_COUNTRIES.has(IP_TO_COUNTRY[ip] || 'UNKNOWN')) return { safe: false, threatScore: 100, reason: `Blocked Geo`, isHoneypot: false };
  if (MALICIOUS_IPS.has(ip)) return { safe: false, threatScore: 100, reason: `Known Malicious IP`, isHoneypot: false };

  if (HONEYPOTS.some(hp => path.includes(hp.toLowerCase()))) {
    return { safe: false, threatScore: 100, reason: `Honeypot Access`, isHoneypot: true };
  }

  if (url.href.length > 1024) threatScore += 50;
  if (search.length > 512) threatScore += 50;

  let combinedPayload = `${path} | ${search} | `;
  request.headers.forEach((value, key) => {
      if (key.toLowerCase() !== 'cookie') combinedPayload += `${key}:${value} | `;
  });

  // Tizimga ortiqcha yuk tushmasligi uchun BODY o'qish hajmi cheklandi (Faqat xavfli metodlarda)
  if (['POST', 'PUT'].includes(request.method)) {
    try {
      const clonedReq = request.clone();
      const bodyText = await clonedReq.text();
      combinedPayload += bodyText.slice(0, 4096);
    } catch (e) {}
  }

  for (const [category, patterns] of Object.entries(PATTERNS)) {
    for (const pattern of patterns) {
      if (typeof pattern === 'object' && 'pattern' in pattern) {
        if (pattern.pattern.test(combinedPayload)) {
          const { isSuspicious, entropy } = analyzeBase64Entropy(search);
          if (isSuspicious || entropy > pattern.entropy) threatScore += 100; // Darhol Ban
        }
      } else if (pattern.test(combinedPayload)) {
        threatScore += category === 'miner' ? 100 : 80;
      }
    }
  }

  if (MINER_FINGERPRINTS.some(fp => fp.test(userAgent))) threatScore += 100;
  if (/\.\.\//.test(path) || /%2e%2e/.test(path)) threatScore += 100;

  return { safe: threatScore < 80, threatScore, reason: `Score: ${threatScore}`, isHoneypot };
}