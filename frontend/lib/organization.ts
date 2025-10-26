const BASE = "/organization";

export async function fetchOrganizations() {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/list`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return res.ok ? res.json() : [];
}

export async function createOrganization(data: FormData) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/create`, {
        method: "POST",
        body: data,
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    if (!res.ok) throw new Error("Tashkilotni yaratib bo‘lmadi");
    return res.json();
}
