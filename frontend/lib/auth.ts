const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export function setAccessToken(t: string) {
    localStorage.setItem(ACCESS_KEY, t);
}
export function setRefreshToken(t: string) {
    localStorage.setItem(REFRESH_KEY, t);
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
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
}
