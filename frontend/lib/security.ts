import { NextRequest } from 'next/server';

// ==========================================
// 1. ADVANCED RATE LIMITER (Token Bucket)
// ==========================================
// Eslatma: Productionda bu Redis orqali bo'lishi kerak.
// Hozircha konteyner xotirasida ishlaydi (Edge Runtime mos).

interface RateLimitConfig {
    limit: number;      // Maksimal so'rovlar soni
    windowMs: number;   // Vaqt oralig'i (ms)
}

const ipCache = new Map<string, { count: number; resetTime: number }>();
const BLOCK_DURATION = 60 * 60 * 1000; // 1 soat bloklash (qoidabuzarlar uchun)
const blockedIps = new Map<string, number>();

export function checkRateLimit(ip: string, config: RateLimitConfig = { limit: 100, windowMs: 60000 }): boolean {
    const now = Date.now();

    // 1. Bloklangan IP larni tekshirish
    if (blockedIps.has(ip)) {
        const unblockTime = blockedIps.get(ip) || 0;
        if (now < unblockTime) {
            return false; // Hali blokda
        }
        blockedIps.delete(ip); // Blok muddati tugadi
    }

    // 2. Rate Limit hisoblash
    const record = ipCache.get(ip);

    if (!record) {
        ipCache.set(ip, { count: 1, resetTime: now + config.windowMs });
        return true;
    }

    if (now > record.resetTime) {
        // Vaqt oynasi yangilandi
        ipCache.set(ip, { count: 1, resetTime: now + config.windowMs });
        return true;
    }

    record.count += 1;

    if (record.count > config.limit) {
        // Limitdan oshdi -> Bloklash
        blockedIps.set(ip, now + BLOCK_DURATION);
        return false;
    }

    return true;
}

// ==========================================
// 2. HEURISTIC WAF (Attack Signatures)
// ==========================================

const SQL_INJECTION_PATTERNS = [
    /(\%27)|(\')|(\-\-)|(\%23)|(#)/i,
    /((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))/i,
    /\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))/i,
    /((\%27)|(\'))union/i,
    /exec(\s|\+)+(s|x)p\w+/i,
    /UNION\s+SELECT/i,
    /SELECT\s+.*\s+FROM/i,
    /DROP\s+TABLE/i,
    /INSERT\s+INTO/i
];

const XSS_PATTERNS = [
    /<script>/i,
    /javascript:/i,
    /onload=/i,
    /onerror=/i,
    /eval\(/i,
    /document\.cookie/i
];

const RCE_PATTERNS = [
    /\/bin\/sh/i,
    /\/bin\/bash/i,
    /cmd\.exe/i,
    /wget\s/i,
    /curl\s/i,
    /\$\(.*\)/i,
    /php:\/\/input/i
];

const PATH_TRAVERSAL = [
    /\.\.\//,
    /\.\.\\/,
    /\/etc\/passwd/,
    /\/windows\/win\.ini/
];

export function analyzeRequest(req: NextRequest): { safe: boolean; reason?: string } {
    const url = req.nextUrl.toString().toLowerCase();
    const body = ""; // Body ni o'qish streamni buzishi mumkin, shuning uchun asosan URL va Headerlarni tekshiramiz
    const userAgent = req.headers.get('user-agent') || '';

    // 1. URL Scan
    for (const pattern of [...SQL_INJECTION_PATTERNS, ...XSS_PATTERNS, ...RCE_PATTERNS, ...PATH_TRAVERSAL]) {
        if (pattern.test(url)) {
            return { safe: false, reason: "Malicious Payload Detected in URL" };
        }
    }

    // 2. User-Agent Scan (Advanced)
    const badBots = ['sqlmap', 'nikto', 'nmap', 'nessus', 'hydra', 'burp', 'acunetix', 'netsparker', 'wpscan', 'python-requests', 'libwww-perl'];
    if (badBots.some(bot => userAgent.toLowerCase().includes(bot))) {
        return { safe: false, reason: "Malicious User-Agent" };
    }

    // 3. Length Check (Juda uzun URL lar buffer overflow uchun bo'lishi mumkin)
    if (url.length > 2048) {
        return { safe: false, reason: "URL Too Long" };
    }

    return { safe: true };
}

// ==========================================
// 3. NONCE GENERATOR (For CSP)
// ==========================================
export function generateNonce(): string {
    return crypto.randomUUID().replace(/-/g, '');
}
