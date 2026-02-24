"use client";

import { useEffect, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { api } from "@/lib/api";
import { fetchMe } from "@/lib/me";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

const predefinedRoles = [
    { code: "RECTOR", name: "Rektor", rank: 1, category: "LEAD" },
    { code: "PRORECTOR", name: "Prorektor", rank: 2, category: "LEAD" },
    { code: "DEAN", name: "Dekan", rank: 3, category: "ORG" },
    { code: "HEAD_OF_DEPARTMENT", name: "Kafedra mudiri", rank: 4, category: "ORG" },
    { code: "CENTER_HEAD", name: "Markaz boshlig'i", rank: 5, category: "SUPPORT" },
    { code: "DIVISION_HEAD", name: "Bo'lim boshlig'i", rank: 6, category: "SUPPORT" },
    { code: "METHODOLOGIST", name: "Uslubchi", rank: 10, category: "STAFF" },
    { code: "WORKER", name: "Ishchi xodim", rank: 15, category: "STAFF" },
    { code: "TECHNICIAN", name: "Texnik xodim", rank: 20, category: "STAFF" },
];

const roleSchema = z.object({
    code: z.string().min(2, "Lavozim kiritilishi shart"),
    name: z.string().min(2, "Nom kiritilishi shart"),
    description: z.string().optional(),
    rank: z.coerce.number().min(1).max(100),
    category: z.string().optional(),
});

type RoleForm = z.infer<typeof roleSchema>;
type Role = {
    id: string;
    code: string;
    name: string;
    description?: string;
    rank: number;
    category?: string;
};

export default function RolesPage() {
    const [roles, setRoles] = useState<Role[]>([]);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);

    // Generic tipni olib tashladik
    const {
        register,
        handleSubmit,
        reset,
        control,
        setValue,
        formState: { errors },
    } = useForm({ resolver: zodResolver(roleSchema) });

    useEffect(() => {
        (async () => {
            try {
                const info = await fetchMe();
                if (!info) return window.location.replace("/auth/login");
                if (!info.is_superadmin)
                    return window.location.replace(info.redirect_path);
                const { data } = await api.get("/organization/roles/list");
                setRoles(data);
            } catch (e) {
                console.error("Failed to fetch roles", e);
            }
        })();
    }, []);

    const onSelectPredefinedRole = (val: string) => {
        const role = predefinedRoles.find((r) => r.code === val);
        if (role) {
            setValue("code", role.code);
            setValue("name", role.name);
            setValue("rank", role.rank);
            setValue("category", role.category);
        }
    };

    async function onSubmit(values: any) {
        setBusy(true);
        setNotice(null);
        setError(null);
        try {
            // FormData o'rniga oddiy JSON yuborish ham mumkin, lekin backend nima kutayotganiga qarab
            // Agar backend form-data kutayotgan bo'lsa:
            const fd = new FormData();
            fd.append("code", values.code);
            fd.append("name", values.name);
            if (values.description) fd.append("description", values.description);
            fd.append("rank", String(values.rank));
            if (values.category) fd.append("category", values.category);

            const { data } = await api.post("/organization/roles/create", fd);
            setRoles((prev) => [data, ...prev]);
            reset();
            setNotice(`Yaratildi: ${data.name} (${data.code})`);
        } catch (e: any) {
            setError(e?.response?.data?.detail || "Xatolik yuz berdi");
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-10">
            <Card>
                <CardHeader>
                    <CardTitle>Yangi Lavozim yaratish</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div>
                            <label>Lavozim turi (tanlang)</label>
                            <Controller
                                control={control}
                                name="code"
                                render={({ field }) => (
                                    <Select onValueChange={onSelectPredefinedRole}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Lavozimni tanlang" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {predefinedRoles.map((role) => (
                                                <SelectItem key={role.code} value={role.code}>
                                                    {role.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                )}
                            />
                            {errors.code && <p className="text-red-500 text-xs">{String(errors.code.message)}</p>}
                        </div>

                        <div>
                            <label>Nom</label>
                            <Input {...register("name")} placeholder="Masalan: Rektor" />
                            {errors.name && <p className="text-red-500 text-xs">{String(errors.name.message)}</p>}
                        </div>

                        <div>
                            <label>Izoh</label>
                            <Input {...register("description")} placeholder="Lavozim izohi" />
                        </div>

                        <div>
                            <label>Daraja (Rank)</label>
                            <Input type="number" {...register("rank")} placeholder="1 = yuqori, 100 = past" />
                            {errors.rank && <p className="text-red-500 text-xs">{String(errors.rank.message)}</p>}
                        </div>

                        <div>
                            <label>Kategoriya</label>
                            <Input {...register("category")} placeholder="Masalan: LEAD, ORG, STAFF" />
                        </div>

                        <Button type="submit" disabled={busy}>
                            {busy ? "Yaratilmoqda..." : "Yaratish"}
                        </Button>
                        {(notice || error) && (
                            <p className={`${notice ? "text-green-600" : "text-red-600"} text-sm`}>
                                {notice || error}
                            </p>
                        )}
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
