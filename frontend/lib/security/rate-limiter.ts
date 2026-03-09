// frontend/lib/security/rate-limiter.ts
import { BASE_RATE_LIMIT, WINDOW_MS } from './constants';

// Agar Global kesh bo'lmasa, Node.js Memory saqlaymiz (Next.js Edge uchun ham ishlaydi)
const BANNED_SUBNETS = new Map<string, number>();
const BANNED_IPS = new Map<string, number>();

// IPv4 dan C-Class tarmog'ini ajratib olish (Masalan: 192.168.1.55 -> 192.168.1)
function getSubnet(ip: string): string {
    const parts = ip.split('.');
    if (parts.length === 4) {
        return `${parts[0]}.${parts[1]}.${parts[2]}`;
    }
    return ip; // Agar IPv6 bo'lsa yoki noto'g'ri bo'lsa o'zini qaytaramiz
}

export function banIp(ip: string, durationHours: number = 48) {
    const expTime = Date.now() + (durationHours * 60 * 60 * 1000);
    BANNED_IPS.set(ip, expTime);

    // 🟢 ELITA HIMOYA: Agar xaker IP-sini tinmay o'zgartirsa, uning butun mahallasini (Subnet) bloklaymiz.
    // Xakerlar proxy o'zgartirganda ko'pincha bitta provayderning bitta tarmog'i atrofida aylanadi.
    const subnet = getSubnet(ip);
    BANNED_SUBNETS.set(subnet, expTime);

    // Xotira tolib ketmasligi uchun vaqti o'tganlarni tozalab turamiz
    if (BANNED_IPS.size > 10000) BANNED_IPS.clear();
}

export function isIpBanned(ip: string): boolean {
    const now = Date.now();

    // 1. Aniq IP tekshiruvi
    const ipExp = BANNED_IPS.get(ip);
    if (ipExp && now <= ipExp) return true;
    if (ipExp && now > ipExp) BANNED_IPS.delete(ip);

    // 2. Subnet tekshiruvi (IP ro'tatsiyasiga qarshi asosiy qurol)
    const subnet = getSubnet(ip);
    const subnetExp = BANNED_SUBNETS.get(subnet);
    if (subnetExp && now <= subnetExp) return true;
    if (subnetExp && now > subnetExp) BANNED_SUBNETS.delete(subnet);

    return false;
}

export class AdaptiveRateLimiter {
  private windows = new Map<string, { count: number; timestamp: number; threatScore: number }>();

  check(ip: string, threatScore: number = 0): { allowed: boolean; remaining: number } {
    const now = Date.now();
    const window = this.windows.get(ip);

    if (window && now - window.timestamp > WINDOW_MS) this.windows.delete(ip);

    // Tahdid darajasi yuqori bo'lganlarga deyarli umuman so'rov berilmaydi
    const dynamicLimit = Math.max(1, BASE_RATE_LIMIT - Math.floor(threatScore / 2));

    if (!window) {
      this.windows.set(ip, { count: 1, timestamp: now, threatScore });
      return { allowed: true, remaining: dynamicLimit - 1 };
    }

    if (window.count >= dynamicLimit) return { allowed: false, remaining: 0 };

    window.count++;
    window.threatScore = Math.max(window.threatScore, threatScore);
    return { allowed: true, remaining: dynamicLimit - window.count };
  }

  cleanup() {
    const now = Date.now();
    for (const [ip, window] of this.windows.entries()) {
      if (now - window.timestamp > WINDOW_MS * 2) this.windows.delete(ip);
    }
  }
}