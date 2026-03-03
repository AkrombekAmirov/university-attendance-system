// frontend/lib/auth.ts
const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// 🟢 NEW: Cookie ga xavfsiz yozish funksiyasi
function setCookie(name: string, value: string, days: number = 1) {
    if (typeof window === "undefined") return;
    const isProd = process.env.NODE_ENV === "production";
    const maxAge = days * 24 * 60 * 60;
    // Xavfsizlik qoidalari bilan Cookie yaratish
    document.cookie = `${name}=${value}; path=/; max-age=${maxAge}; SameSite=Lax; ${isProd ? "Secure;" : ""}`;
}

function deleteCookie(name: string) {
    if (typeof window === "undefined") return;
    document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT;`;
}

// 🟢 FIX: Tokenni ham Cookie ga, ham LocalStorage ga saqlaymiz
export function setAccessToken(t: string) {
    if (typeof window !== "undefined") {
        localStorage.setItem(ACCESS_KEY, t);
        setCookie(ACCESS_KEY, t, 1); // 1 kunlik cookie
    }
}

export function setRefreshToken(t: string) {
    if (typeof window !== "undefined") {
        localStorage.setItem(REFRESH_KEY, t);
        setCookie(REFRESH_KEY, t, 7); // 7 kunlik cookie
    }
}

export function getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(REFRESH_KEY);
}

export function clearTokens() {
    if (typeof window === "undefined") return;
    // Ikkalasini ham tozalash
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    deleteCookie(ACCESS_KEY);
    deleteCookie(REFRESH_KEY);
    
    // User ma'lumotlarini ham tozalab ketamiz
    localStorage.removeItem("user");
}