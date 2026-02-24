"use client";

import { useEffect, useState } from "react";
import { createOrganization, fetchOrganizations } from "@/lib/organization";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// Type e'lon qilamiz
interface OrganizationType {
    id: string;
    name: string;
    code: string;
}

export default function OrganizationPage() {
    // State to'g'ri tip bilan
    const [organizations, setOrganizations] = useState<OrganizationType[]>([]);
    const [name, setName] = useState("");
    const [code, setCode] = useState("");
    const [loading, setLoading] = useState(false);

    // Tashkilotlarni yuklash funksiyasi
    const loadOrganizations = async () => {
        try {
            const data = await fetchOrganizations();
            setOrganizations(data);
        } catch (error) {
            console.error("Failed to fetch organizations", error);
        }
    };

    useEffect(() => {
        loadOrganizations();
    }, []);

    const handleSubmit = async () => {
        const formData = new FormData();
        formData.append("name", name);
        formData.append("code", code);

        try {
            setLoading(true);
            await createOrganization(formData);
<<<<<<< HEAD

            // Muvaffaqiyatli yaratilgandan so'ng ro'yxatni yangilaymiz
            await loadOrganizations();

=======
            
            // Muvaffaqiyatli yaratilgandan so'ng ro'yxatni yangilaymiz
            await loadOrganizations();
            
>>>>>>> bcc8fb49ad3a69160c569756b6e944ba3662a768
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
                {organizations.map((org) => (
                    <li key={org.id}>
                        <strong>{org.name}</strong> – {org.code}
                    </li>
                ))}
            </ul>
        </div>
    );
}
