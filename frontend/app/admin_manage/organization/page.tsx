"use client";

import { useEffect, useState } from "react";
import { createOrganization, fetchOrganizations } from "@/lib/organization";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function OrganizationPage() {
    const [organizations, setOrganizations] = useState([]);
    const [name, setName] = useState("");
    const [code, setCode] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchOrganizations().then(setOrganizations);
    }, []);

    const handleSubmit = async () => {
        const formData = new FormData();
        formData.append("name", name);
        formData.append("code", code);

        try {
            setLoading(true);
            const org = await createOrganization(formData);
            const [organizations, setOrganizations] = useState<OrganizationType[]>([]);
            setName("");
            setCode("");
        } catch (err: unknown) {
            if (err instanceof Error) {
                alert("Xatolik: " + err.message);
            } else {
                alert("Noma’lum xatolik yuz berdi");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 space-y-6 max-w-xl mx-auto">
            <h2 className="text-xl font-bold">Tashkilot yaratish</h2>

            <div className="space-y-4">
                <div>
                    <Label htmlFor="name">Nomi</Label>
                    <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div>
                    <Label htmlFor="code">Kodi</Label>
                    <Input id="code" value={code} onChange={(e) => setCode(e.target.value)} />
                </div>
                <Button onClick={handleSubmit} disabled={loading}>
                    {loading ? "Yaratilmoqda..." : "Tashkilot yaratish"}
                </Button>
            </div>

            <h3 className="font-semibold mt-10">Mavjud tashkilotlar:</h3>
            <ul className="space-y-2 list-disc pl-6">
                {organizations.map((org: any) => (
                    <li key={org.id}>
                        <strong>{org.name}</strong> – {org.code}
                    </li>
                ))}
            </ul>
        </div>
    );
}
