import axios, { AxiosError } from "axios";
import {
    getAccessToken,
    getRefreshToken,
    setAccessToken,
    setRefreshToken,
    clearTokens,
} from "./auth";

// Next.js da NEXT_PUBLIC o'zgaruvchilar 'npm run dev' muhitida kutilmaganda undefined bolmasligi uchun
// xavfsiz default (http://localhost:8000) berish muhim.
export const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    withCredentials: true,
});

// Access token is now sent automatically via HttpOnly cookies by the browser.
// We no longer manually attach the Authorization header from localStorage.
api.interceptors.request.use((config) => {
    return config;
});

let refreshing = false;
let queue: Array<() => void> = [];

async function refreshToken(): Promise<string | null> {
    if (refreshing) {
        await new Promise<void>((resolve) => queue.push(resolve));
        return getAccessToken();
    }

    refreshing = true;
    try {
        const refresh = getRefreshToken();
        if (!refresh) throw new Error("No refresh token found");

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await axios.post(
            `${apiUrl}/users/auth/refresh`,
            {}, // No body needed, refresh token is sent automatically via cookies
            { withCredentials: true }
        );

        // Tokens are received entirely via Set-Cookie headers now.
        // We just return a dummy string to signal success to the retry queue
        return "success";
    } catch {
        clearTokens();
        return null;
    } finally {
        refreshing = false;
        queue.forEach((fn) => fn());
        queue = [];
    }
}

// Auto-refresh
api.interceptors.response.use(
    (r) => r,
    async (error: AxiosError) => {
        const req: any = error.config;

        if (error?.response?.status === 401 && !req._retry) {
            req._retry = true;
            const success = await refreshToken();
            if (success) {
                // withCredentials is true, cookies will be resent automatically
                return api(req);
            }
        }
        return Promise.reject(error);
    }
);

// Staff API
export async function fetchMyTree() {
    try {
        const res = await api.get("/turniked/org/my-tree");
        return res.data;
    } catch (err) {
        console.error("❌ fetchMyTree failed:", err);
        throw err;
    }
}

/**
 * Fetch staff list. If unit_id provided → only that department users
 */
// Staff API
export async function fetchMyStaff(params: { unit_id: string }) {
    const res = await api.get("/turniked/org/my-staff", { params });
    return res.data;
}
export async function fetchUnitDaily(unit_id: string, day: string) {
    const res = await api.get(`/turniked/attendance/unit/daily`, {
        params: { unit_id, day }
    });
    return res.data;
}

export async function fetchUnitMonthlyDetailed(
    unit_id: string,
    year: number,
    month: number
) {
    const res = await api.get("/turniked/attendance/unit/monthly/detailed", {
        params: { unit_id, year, month },
    });
    return res.data;
}
// HR API
export async function fetchHrUnits() {
    const res = await api.get("/hr/units");
    return res.data;
}
export async function fetchHrUnitDaily(
    unitId: string,
    day: string
) {
    const res = await api.get("/hr/daily/page", {
        params: { unit_id: unitId, day }
    });
    return res.data;
}
// HR ANALYTICS API (NEW)
export async function fetchHrUnitsSummary(day: string) {
    const res = await api.get("/hr/units/summary", {
        params: { day }
    });
    return res.data;
}


export { axios };
