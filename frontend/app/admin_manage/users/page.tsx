"use client";

import { useState, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { api } from "@/lib/api";
import { fetchMe } from "@/lib/me";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// ✅ Validation schema
const userSchema = z.object({
    username: z.string().min(3, "Kamida 3 ta belgi bo‘lishi kerak").max(64),
    password: z.string().min(8, "Parol kamida 8 ta belgidan iborat bo‘lishi kerak"),
    full_name: z.string().optional(),
});

type FormValues = z.infer<typeof userSchema>;

// ✅ Xatolik matnini olish
function parseError(e: any): string {
    const data = e?.response?.data ?? e?.data ?? e;
    if (data?.detail) {
        if (typeof data.detail === "string") return data.detail;
        if (Array.isArray(data.detail)) {
            return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
        }
        return JSON.stringify(data.detail);
    }
    return "❌ Xatolik yuz berdi, iltimos qayta urinib ko‘ring.";
}

export default function UserCreatePage() {
    const [me, setMe] = useState<any>(null);
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // ✅ Foydalanuvchini olish va tekshirish
    useEffect(() => {
        (async () => {
            const info = await fetchMe();
            if (!info) {
                window.location.replace("/auth/login");
                return;
            }
            if (!info.is_superadmin) {
                window.location.replace(info.redirect_path || "/");
                return;
            }
            setMe(info);
        })();
    }, []);

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<FormValues>({
        resolver: zodResolver(userSchema),
        defaultValues: {
            username: "",
            password: "",
            full_name: "",
        },
    });

    const onCreateUser = async (values: FormValues) => {
        setBusy(true);
        setError(null);
        setNotice(null);
        try {
            const form = new FormData();
            form.set("username", values.username);
            form.set("password", values.password);
            if (values.full_name) form.set("full_name", values.full_name);

            const { data } = await api.post("/users/create_simple", form);

            setNotice(`✅ Foydalanuvchi yaratildi: ${data.username}`);
            reset();
        } catch (e) {
            setError(parseError(e));
        } finally {
            setBusy(false);
        }
    };

    const canSubmit = useMemo(() => !!me?.is_superadmin && !busy, [me, busy]);

    if (!me) return null;

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="mx-auto max-w-xl px-6 py-8">
                <Card className="shadow-sm">
                    <CardHeader>
                        <CardTitle>👤 Yangi foydalanuvchi yaratish</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {notice && (
                            <div className="mb-3 rounded border border-green-300 bg-green-50 p-2 text-sm text-green-800">
                                {notice}
                            </div>
                        )}
                        {error && (
                            <div className="mb-3 rounded border border-red-300 bg-red-50 p-2 text-sm text-red-700">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit(onCreateUser)} className="space-y-4">
                            <div>
                                <label className="text-sm font-medium">Username</label>
                                <Input placeholder="foydalanuvchi nomi" {...register("username")} />
                                {errors.username && (
                                    <p className="text-xs text-red-500 mt-1">{errors.username.message}</p>
                                )}
                            </div>

                            <div>
                                <label className="text-sm font-medium">Parol</label>
                                <Input type="password" placeholder="********" {...register("password")} />
                                {errors.password && (
                                    <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>
                                )}
                            </div>

                            <div>
                                <label className="text-sm font-medium">To‘liq ism (ixtiyoriy)</label>
                                <Input placeholder="F.I.Sh" {...register("full_name")} />
                            </div>

                            <Button type="submit" disabled={!canSubmit} className="w-full">
                                {busy ? "⏳ Yaratilmoqda..." : "Foydalanuvchini yaratish"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
