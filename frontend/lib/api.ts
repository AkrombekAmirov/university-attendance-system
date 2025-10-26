import axios, { AxiosError } from "axios";
import {
    getAccessToken,
    getRefreshToken,
    setAccessToken,
    setRefreshToken,
    clearTokens,
} from "./auth";

// Bosh axios instance
export const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    withCredentials: true,
});

// Har so'rovga access token qo'shish
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// 401 bo'lsa avtomatik refresh va qayta urinish
let refreshing = false;
let waiters: Array<() => void> = [];

async function refreshAccessToken(): Promise<string | null> {
    if (refreshing) {
        await new Promise<void>((resolve) => waiters.push(resolve));
        return getAccessToken();
    }
    refreshing = true;
    try {
        const refresh = getRefreshToken();
        if (!refresh) throw new Error("No refresh token");

        const res = await axios.post(
            (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/users/auth/refresh",
            new URLSearchParams({ refresh_token: refresh }),
            { withCredentials: true }
        );

        const newAccess = res.data?.access_token as string | undefined;
        const newRefresh = res.data?.refresh_token as string | undefined;

        if (newAccess) setAccessToken(newAccess);
        if (newRefresh) setRefreshToken(newRefresh);
        return newAccess ?? null;
    } catch {
        clearTokens();
        return null;
    } finally {
        refreshing = false;
        waiters.forEach((fn) => fn());
        waiters = [];
    }
}

api.interceptors.response.use(
    (r) => r,
    async (error: AxiosError) => {
        const original: any = error.config || {};
        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;
            const newAccess = await refreshAccessToken();
            if (newAccess) {
                original.headers = { ...(original.headers || {}), Authorization: `Bearer ${newAccess}` };
                return api(original);
            }
        }
        return Promise.reject(error);
    }
);
