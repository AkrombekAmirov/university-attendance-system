// frontend/lib/security/rate-limiter.ts
import { BASE_RATE_LIMIT, WINDOW_MS } from './constants';

export class AdaptiveRateLimiter {
  private windows = new Map<string, { count: number; timestamp: number; threatScore: number }>();

  check(ip: string, threatScore: number = 0): { allowed: boolean; remaining: number } {
    const now = Date.now();
    const window = this.windows.get(ip);

    // Oynani tozalash
    if (window && now - window.timestamp > WINDOW_MS) this.windows.delete(ip);

    // Xakerlik alomatlari bor IP larga ruxsat etilgan limitni keskin kamaytirish
    const dynamicLimit = Math.max(5, BASE_RATE_LIMIT - Math.floor(threatScore / 5));

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