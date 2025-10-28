"use client";

import { useState, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X } from "lucide-react";

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

// ✅ Xatoliklarni aniqlovchi funksiya
function parseError(e: any): string {
    const data = e?.response?.data ?? e?.data ?? e;
    if (data?.detail) {
        if (typeof data.detail === "string") return data.detail;
        if (Array.isArray(data.detail))
            return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
        return JSON.stringify(data.detail);
    }
    return "❌ Xatolik yuz berdi, iltimos qayta urinib ko‘ring.";
}

// ✅ Modal komponent
function UserCreateModal({
                             isOpen,
                             onClose,
                             onSuccess,
                         }: {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}) {
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<FormValues>({
        resolver: zodResolver(userSchema),
        defaultValues: { username: "", password: "", full_name: "" },
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
            setTimeout(() => {
                onSuccess();
                onClose();
            }, 1500);
        } catch (e) {
            setError(parseError(e));
        } finally {
            setBusy(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />
                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4"
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ type: "spring", damping: 20, stiffness: 300 }}
                    >
                        <Card className="w-full max-w-md border-0 shadow-2xl bg-gradient-to-br from-white to-emerald-50 dark:from-slate-900 dark:to-emerald-950 rounded-2xl">
                            <CardHeader className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white rounded-t-2xl pb-6">
                                <div className="flex justify-between items-center">
                                    <CardTitle className="text-2xl">Yangi foydalanuvchi</CardTitle>
                                    <motion.button
                                        whileHover={{ scale: 1.1 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={onClose}
                                        className="p-1 hover:bg-white/20 rounded-lg"
                                    >
                                        <X size={20} />
                                    </motion.button>
                                </div>
                            </CardHeader>

                            <CardContent className="pt-5 space-y-4">
                                {notice && (
                                    <div className="p-3 bg-green-50 text-green-800 rounded-lg border border-green-200">
                                        {notice}
                                    </div>
                                )}
                                {error && (
                                    <div className="p-3 bg-red-50 text-red-800 rounded-lg border border-red-200">
                                        {error}
                                    </div>
                                )}

                                <form onSubmit={handleSubmit(onCreateUser)} className="space-y-4">
                                    <div>
                                        <label className="text-sm font-medium">Username</label>
                                        <Input
                                            placeholder="foydalanuvchi nomi"
                                            {...register("username")}
                                            className="mt-1 h-10"
                                        />
                                        {errors.username && (
                                            <p className="text-xs text-red-500 mt-1">{errors.username.message}</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium">Parol</label>
                                        <Input
                                            type="password"
                                            placeholder="********"
                                            {...register("password")}
                                            className="mt-1 h-10"
                                        />
                                        {errors.password && (
                                            <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium">To‘liq ism (ixtiyoriy)</label>
                                        <Input
                                            placeholder="F.I.Sh"
                                            {...register("full_name")}
                                            className="mt-1 h-10"
                                        />
                                    </div>

                                    <div className="flex gap-3 pt-4">
                                        <Button
                                            type="button"
                                            onClick={onClose}
                                            variant="outline"
                                            className="flex-1"
                                        >
                                            Bekor qilish
                                        </Button>
                                        <Button
                                            type="submit"
                                            disabled={busy}
                                            className="flex-1 bg-gradient-to-r from-emerald-500 to-blue-500 text-white"
                                        >
                                            {busy ? "⏳ Yaratilmoqda..." : "Yaratish"}
                                        </Button>
                                    </div>
                                </form>
                            </CardContent>
                        </Card>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

// ✅ Asosiy sahifa
export default function UserManagementPage() {
    const [me, setMe] = useState<any>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // ✅ Avtorizatsiya tekshiruvi
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

    // ✅ Yangi user yaratilganda qayta yuklash
    const handleUserCreated = async () => {
        // Backenddan real ro‘yxat olish (agar endpoint mavjud bo‘lsa)
        // const { data } = await api.get("/users/list");
        // setUsers(data);
        // Hozircha mock ma'lumot sifatida yangilamaymiz
    };

    if (!me) return null;

    return (
        <div className="min-h-screen px-6 py-10 space-y-6 bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col md:flex-row md:justify-between md:items-center gap-4"
            >
                <div>
                    <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
                        Foydalanuvchilar
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                        Tizimda ro‘yxatdan o‘tgan barcha foydalanuvchilar
                    </p>
                </div>

                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 px-6 py-3 rounded-lg text-white font-semibold bg-gradient-to-r from-emerald-500 to-blue-500 shadow-lg hover:shadow-xl transition-all"
                >
                    <Plus size={20} /> Yangi foydalanuvchi
                </motion.button>
            </motion.div>

            {/* Users List Card */}
            <Card className="shadow-lg border-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
                <CardHeader className="border-b border-slate-200 dark:border-slate-800">
                    <CardTitle className="text-lg font-semibold">
                        Jami foydalanuvchilar: {users.length}
                    </CardTitle>
                </CardHeader>
                <CardContent className="py-8 text-center text-slate-500">
                    <p>📋 Hozircha foydalanuvchi ro‘yxati mavjud emas</p>
                </CardContent>
            </Card>

            {/* Modal */}
            <UserCreateModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSuccess={handleUserCreated}
            />
        </div>
    );
}
