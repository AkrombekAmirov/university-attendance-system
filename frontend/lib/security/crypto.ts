// frontend/lib/security/crypto.ts
export function generateNonce(): string {
  return btoa(crypto.randomUUID()).replace(/[^a-zA-Z0-9]/g, '').slice(0, 24);
}

export async function signData(data: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const signature = await crypto.subtle.sign('HMAC', keyMaterial, encoder.encode(data));
  return Array.from(new Uint8Array(signature)).map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
}

export function analyzeBase64Entropy(str: string): { isSuspicious: boolean; entropy: number } {
  if (!/^[A-Za-z0-9+/=]{20,}$/.test(str)) return { isSuspicious: false, entropy: 0 };
  const freq: Record<string, number> = {};
  for (const char of str) freq[char] = (freq[char] || 0) + 1;
  let entropy = 0; const len = str.length;
  for (const char in freq) { const p = freq[char] / len; entropy -= p * Math.log2(p); }
  return { isSuspicious: entropy > 5.0, entropy };
}

// 🛡️ CRASH-PROOF URI DECODER
export function deepDecode(str: string, maxDepth: number = 3): string {
  let decoded = String(str || '');
  for (let i = 0; i < maxDepth; i++) {
    try {
      const prev = decoded;
      // Agar URI da muammo bo'lsa qulab tushmaydi, js engine o'zi try catch orqali ushlab qoladi
      decoded = decodeURIComponent(decoded.replace(/\+/g, '%20'));
      if (prev === decoded) break;
    } catch (error) {
      // 🚨 Agar qulasa, uni tozalab, originalni qaytaradi, tizim ishlayveradi!
      break;
    }
  }
  return decoded;
}