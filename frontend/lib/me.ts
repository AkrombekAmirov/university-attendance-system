// frontend/lib/me.ts
import { api } from "./api";

export type MeResponse = {
    id: string;
    username: string;
    is_superadmin: boolean;
    roles: string[];
    redirect_path: string;
    full_name?: string;
    email?: string;
};

export async function fetchMe(): Promise<MeResponse | null> {
    try {
        const res = await api.get("/users/auth/me");
        return res.data;
    } catch {
        return null;
    }
}
