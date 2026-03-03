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
    // Malformed URI yuborgani uchun u avtomatik Tarpitga tushadi
    return { safe: false, threatScore: 1000, reason: `Malformed URI Attack Attempt`, isHoneypot: true };
  }

  // =====================================================================
  // 🕵️ 1-QATLAM: BROWSER FINGERPRINTING (BOTLARNI QIRISH)
  // =====================================================================
  const ua = request.headers.get('user-agent')?.toLowerCase() || '';
  const acceptLang = request.headers.get('accept-language') || '';

  // QOIDA 1: Haqiqiy brauzerlar doim Tilni (Accept-Language) yuboradi. Python/Go/Nuclei botlari bunga erinadi!
  if (!acceptLang) {
      return { safe: false, threatScore: 1000, reason: `Missing Accept-Language (Bot Fingerprint)`, isHoneypot: true };
  }

  // QOIDA 2: Arzon botlarning User-Agent ni darhol fosh qilish
  const botSignatures = ['curl', 'python', 'go-http', 'java', 'nmap', 'zgrab', 'nuclei', 'postman', 'insomnia', 'wget', 'urllib'];
  if (botSignatures.some(bot => ua.includes(bot)) || ua === '') {
      return { safe: false, threatScore: 1000, reason: `Known Bot User-Agent`, isHoneypot: true };
  }

  // QOIDA 3: Ruxsat etilmagan kengaytmalar (PHP, ENV, SQL) - hech qanday Next.js sayti bularni ishlatmaydi!
  if (path.match(/\.(php|action|json|yml|yaml|xml|sql|tar|gz|zip|env|bak|swp)$/i)) {
      return { safe: false, threatScore: 1000, reason: `Forbidden Extension Scan`, isHoneypot: true };
  }

  // =====================================================================
  // 🛡️ 2-QATLAM: AN'ANAVIY WAF QOIDALARI
  // =====================================================================
  if (!ALLOWED_METHODS.includes(request.method)) return { safe: false, threatScore: 1000, reason: `Invalid HTTP Method`, isHoneypot: true };

  const queryKeys = Array.from(url.searchParams.keys());

  // Zombi Botnet / WordPress Skaner qopqoni
  if (path === '/' && queryKeys.length > 2 && queryKeys.some(k => ['h', 'u', 'p', 'r', 'cmd', 'exec', 'rest_route', 'author'].includes(k))) {
      return { safe: false, threatScore: 1000, reason: `Botnet/CMS Beacon Signature`, isHoneypot: true };
  }

  if (path.includes('%00') || search.includes('\0')) return { safe: false, threatScore: 1000, reason: `Null-Byte Injection`, isHoneypot: true };

  if (BLOCKED_COUNTRIES.has(IP_TO_COUNTRY[ip] || 'UNKNOWN')) return { safe: false, threatScore: 100, reason: `Blocked Geo`, isHoneypot: false };

  // Qopqonlarni tekshirish (1000 ball beriladi - to'g'ridan-to'g'ri o'lim)
  if (HONEYPOTS.some(hp => path.includes(hp.toLowerCase()))) {
    return { safe: false, threatScore: 1000, reason: `Honeypot Access`, isHoneypot: true };
  }

  let threatScore = 0;
  if (url.href.length > 1024) threatScore += 50;
  if (search.length > 512) threatScore += 50;

  let combinedPayload = `${path} | ${search} | `;
  request.headers.forEach((value, key) => {
      if (key.toLowerCase() !== 'cookie') combinedPayload += `${key}:${value} | `;
  });

  for (const [category, patterns] of Object.entries(PATTERNS)) {
    for (const pattern of patterns) {
      if (typeof pattern === 'object' && 'pattern' in pattern) {
        if (pattern.pattern.test(combinedPayload)) {
          const { isSuspicious, entropy } = analyzeBase64Entropy(search);
          if (isSuspicious || entropy > pattern.entropy) return { safe: false, threatScore: 1000, reason: `High Entropy Payload`, isHoneypot: true };
        }
      } else if (pattern.test(combinedPayload)) {
        threatScore += category === 'miner' ? 100 : 80;
      }
    }
  }

  if (/\.\.\//.test(path) || /%2e%2e/.test(path)) return { safe: false, threatScore: 1000, reason: `Path Traversal`, isHoneypot: true };

  return { safe: threatScore < 80, threatScore, reason: `Score: ${threatScore}`, isHoneypot: false };
}