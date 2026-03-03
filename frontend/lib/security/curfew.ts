// frontend/lib/security/curfew.ts

// Tizimdagi qonuniy, ruxsat etilgan asosiy yo'llar (Whitelist)
const ALLOWED_CORE_PATHS = [
    '/',
    '/auth/login',
    '/staff',
    '/admin_manage',
    '/hr',
    '/api/users/auth/login',
    '/api/users/auth/me',
    '/api/users/auth/refresh'
];

export function isNightLockdownActive(): boolean {
    const now = new Date();
    // O'zbekiston vaqti (UTC+5)
    const uztHour = (now.getUTCHours() + 5) % 24;

    // Tungi soat 00:00 dan 05:00 (04:59) gacha
    return uztHour >= 0 && uztHour < 5;
}

export function isAllowedDuringNight(path: string, method: string): boolean {
    const normalizedPath = path.toLowerCase();

    // Next.js ning o'zining ichki fayllariga har doim ruxsat beramiz
    if (normalizedPath.startsWith('/_next') || normalizedPath.includes('favicon.ico')) {
        return true;
    }

    // Tungi vaqtda faqat bizning qonuniy yo'llarimiz ishlashi mumkin
    const isLegitPath = ALLOWED_CORE_PATHS.some(p => normalizedPath === p || normalizedPath.startsWith(p + '/'));

    if (!isLegitPath) {
        return false; // Xakerning /.env, /server kabi narsalari shu yerda o'ladi
    }

    // Tungi vaqtda / ga qilingan POST (xakerlik urunishi) bloklanadi
    if (normalizedPath === '/' && method !== 'GET') {
        return false;
    }

    return true;
}