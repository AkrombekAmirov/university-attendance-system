// frontend/lib/security/analyzer.ts
import type { NextRequest } from 'next/server';
import { ALLOWED_METHODS, BLOCKED_COUNTRIES, HONEYPOTS_REGEX, IP_TO_COUNTRY, MALICIOUS_IPS, PATTERNS } from './constants';
import { analyzeBase64Entropy, deepDecode } from './crypto';

export async function analyzeRequest(request: NextRequest, ip: string, bodyText: string = ''): Promise<{ safe: boolean; threatScore: number; reason: string; isHoneypot: boolean }> {
  let url;
  let path = '';
  let search = '';

  try {
    url = request.nextUrl;
    path = deepDecode(url.pathname.toLowerCase()); // Yo'lni ham decode qilamiz, path traversal va obfuscationga qarshi
    search = deepDecode(url.search || '');
  } catch (e) {
    return { safe: false, threatScore: 1000, reason: `Malformed URI Attack Attempt`, isHoneypot: true };
  }

  // BROWSER FINGERPRINTING & HEADER INSPECTION
  const ua = request.headers.get('user-agent')?.toLowerCase() || '';
  const acceptLang = request.headers.get('accept-language') || '';

  if (!acceptLang && ua !== '') { // Agar agent bo'lsa-yu til bo'lmasa = BOT
      return { safe: false, threatScore: 1000, reason: `Missing Accept-Language (Bot Fingerprint)`, isHoneypot: true };
  }

  const botSignatures = ['curl', 'python', 'go-http', 'java', 'nmap', 'zgrab', 'nuclei', 'postman', 'insomnia', 'wget', 'urllib', 'masscan', 'censys', 'shodan', 'libwww'];
  if (botSignatures.some(bot => ua.includes(bot)) || ua === '') {
      return { safe: false, threatScore: 1000, reason: `Known Bot User-Agent`, isHoneypot: true };
  }

  for (const [key, value] of request.headers.entries()) {
      if (value.includes('${jndi:') || value.includes('() {') || value.includes('||')) {
          return { safe: false, threatScore: 1000, reason: `Malicious Payload in Headers (RCE Attempt)`, isHoneypot: true };
      }
  }

  if (path.match(/\.(php|action|json|yml|yaml|xml|sql|tar|gz|zip|env|bak|swp|jsp|aspx|ts)$/i) && !path.includes('manifest.json')) {
      return { safe: false, threatScore: 1000, reason: `Forbidden Extension Scan`, isHoneypot: true };
  }

  // WAF QOIDALARI
  if (!ALLOWED_METHODS.includes(request.method)) return { safe: false, threatScore: 1000, reason: `Invalid HTTP Method`, isHoneypot: true };

  const queryKeys = Array.from(url.searchParams.keys());
  if (path === '/' && queryKeys.length > 2 && queryKeys.some(k => ['h', 'u', 'p', 'r', 'cmd', 'exec', 'rest_route', 'author', 's'].includes(k))) {
      return { safe: false, threatScore: 1000, reason: `Botnet/CMS Beacon Signature`, isHoneypot: true };
  }

  if (path.includes('%00') || search.includes('\0') || bodyText.includes('\0')) return { safe: false, threatScore: 1000, reason: `Null-Byte Injection`, isHoneypot: true };

  // 🟢 ELITA HIMOYA: Regex orqali Honeypot tekshiruvi (obfuscated xujumlarni oldini oladi)
  if (HONEYPOTS_REGEX.some(regex => regex.test(path))) {
    console.warn(`🚨 HONEYPOT TRIGGERED: IP ${ip} targeted ${path}`);
    return { safe: false, threatScore: 1000, reason: `Honeypot Access Triggered`, isHoneypot: true };
  }

  let threatScore = 0;
  if (url.href.length > 1024) threatScore += 50;
  if (search.length > 512) threatScore += 50;

  // 😎 DPI (DEEP PACKET INSPECTION): Parol obyekti yoki POST body si to'liq buffer formatida xujum qidiriqlariga o'raladi.
  let combinedPayload = `${path} | ${search} | ${bodyText} | `;
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