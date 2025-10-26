const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BASE = `${API_URL}/organization`;

export async function getOrganizationId(): Promise<string | null> {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/list`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Tashkilotlar ro‘yxatini olishda xato");
    const data = await res.json();
    return data?.[0]?.id || null;
}

export async function getOrgUnitTree(orgId: string): Promise<any[]> {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/units/tree/${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data?.tree || [];
}

export async function createOrgUnit(data: FormData) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/units/create`, {
        method: "POST",
        body: data,
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error("Bo‘linma yaratilmadi: " + text);
    }
    return res.json();
}
