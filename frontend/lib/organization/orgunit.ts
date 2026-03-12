import { api } from "@/lib/api";

export async function getOrganizationId(): Promise<string | null> {
    const res = await api.get("/organization/list");
    return res.data?.[0]?.id || null;
}

export async function getOrgUnitTree(orgId: string): Promise<any[]> {
    try {
        const res = await api.get(`/organization/units/tree/${orgId}`);
        return res.data?.tree || [];
    } catch {
        return [];
    }
}

export async function createOrgUnit(data: FormData) {
    try {
        const res = await api.post("/organization/units/create", data, {
            headers: {
                "Content-Type": "multipart/form-data"
            }
        });
        return res.data;
    } catch (e: any) {
        throw new Error("Bo‘linma yaratilmadi: " + (e.response?.data?.detail || e.message));
    }
}

// ==========================
// ASSIGNMENT / UNASSIGN USER
// ==========================

export interface UnassignUserPayload {
    user_id: string;
    effective_date?: string; // YYYY-MM-DD (optional)
}

/**
 * Userni barcha lavozimlardan to‘liq ozod etadi
 * Backend: POST /organization/assignments/unassign
 */
export async function unassignUserFromAllPositions(
    payload: UnassignUserPayload
): Promise<{ terminated: number }> {
    try {
        const res = await api.post("/organization/assignments/unassign", payload);
        return res.data;
    } catch (e: any) {
        throw new Error("Lavozimdan ozod etib bo‘lmadi: " + (e.response?.data?.detail || e.message));
    }
}