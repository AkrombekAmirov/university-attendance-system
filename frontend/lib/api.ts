import axios, { AxiosError } from "axios";
import {
    getAccessToken,
    getRefreshToken,
    setAccessToken,
    setRefreshToken,
    clearTokens,
} from "./auth";

export const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    withCredentials: true,
});

// Inject access token into header
api.interceptors.request.use((config) => {
    const token = getAccessToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
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

        const res = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/users/auth/refresh`,
            new URLSearchParams({ refresh_token: refresh }),
            { withCredentials: true }
        );

        const { access_token, refresh_token } = res.data;
        if (access_token) setAccessToken(access_token);
        if (refresh_token) setRefreshToken(refresh_token);

        return access_token ?? null;
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
            const newToken = await refreshToken();
            if (newToken) {
                req.headers.Authorization = `Bearer ${newToken}`;
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