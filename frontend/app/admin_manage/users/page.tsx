"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, Pencil } from "lucide-react";

import { api } from "@/lib/api";
import { fetchMe } from "@/lib/me";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/* ---------------------------------------------------
   VALIDATION SCHEMAS
--------------------------------------------------- */

const createSchema = z.object({
    username: z.string().min(3).max(64),
    password: z.string().min(8),
    full_name: z.string().optional(),
    passport: z.string().optional(),
    turniked_id: z.string().optional(),
});

const updateSchema = z.object({
    username: z.string().optional(),
    full_name: z.string().optional(),
    passport: z.string().optional(),
    email: z.string().email().optional().nullable(),
    turniked_id: z.string().optional(),
});

/* ---------------------------------------------------
   ERROR PARSER
--------------------------------------------------- */
function parseError(e: any): string {
    const data = e?.response?.data ?? e?.data ?? e;
    if (data?.detail) {
        return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }
    return "❌ Xatolik yuz berdi.";
}

/* ---------------------------------------------------
   CREATE MODAL
--------------------------------------------------- */
function UserCreateModal({ isOpen, onClose, onSuccess }: any) {
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, reset } = useForm({
        resolver: zodResolver(createSchema),
        defaultValues: {
            username: "",
            password: "",
            full_name: "",
            passport: "",
            turniked_id: "",
        },
    });

    const onCreate = async (values: any) => {
        setBusy(true);
        setError(null);
        setNotice(null);

        try {
            const form = new FormData();
            form.set("username", values.username);
            form.set("password", values.password);
            if (values.full_name) form.set("full_name", values.full_name);
            if (values.passport) form.set("passport", values.passport);
            if (values.turniked_id) form.set("turniked_id", values.turniked_id);

            await api.post("/users/create_simple", form);

            setNotice("✔️ Foydalanuvchi yaratildi.");
            reset();

            setTimeout(() => {
                onSuccess();
                onClose();
            }, 900);
        } catch (e) {
            setError(parseError(e));
        } finally {
            setBusy(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
            >
                <div className="fixed inset-0 bg-black/30" onClick={onClose} />

                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0.9 }}
                    className="relative z-50 w-full max-w-md"
                >
                    <Card className="rounded-xl shadow-xl">
                        <CardHeader className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white rounded-t-xl">
                            <div className="flex justify-between items-center">
                                <CardTitle>Yangi foydalanuvchi</CardTitle>
                                <button onClick={onClose}><X /></button>
                            </div>
                        </CardHeader>

                        <CardContent className="pt-4 space-y-4">
                            {notice && <div className="p-3 bg-green-100">{notice}</div>}
                            {error && <div className="p-3 bg-red-100">{error}</div>}

                            <form className="space-y-4" onSubmit={handleSubmit(onCreate)}>
                                <Input {...register("username")} placeholder="Username" />
                                <Input {...register("password")} placeholder="Parol" type="password" />
                                <Input {...register("full_name")} placeholder="To‘liq ism" />
                                <Input {...register("passport")} placeholder="Passport" />
                                <Input {...register("turniked_id")} placeholder="Turniket ID" />

                                <div className="flex gap-3 pt-3">
                                    <Button type="button" onClick={onClose} variant="outline" className="flex-1">
                                        Bekor qilish
                                    </Button>
                                    <Button type="submit" disabled={busy} className="flex-1">
                                        {busy ? "⏳..." : "Yaratish"}
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}

/* ---------------------------------------------------
   UPDATE MODAL
--------------------------------------------------- */
function UserEditModal({ isOpen, onClose, user, onSuccess }: any) {
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, setValue } = useForm({
        resolver: zodResolver(updateSchema),
        defaultValues: {
            username: "",
            full_name: "",
            passport: "",
            email: "",
            turniked_id: "",
        },
    });

    useEffect(() => {
        if (user) {
            setValue("username", user.username || "");
            setValue("full_name", user.full_name || "");
            setValue("passport", user.passport || "");
            setValue("email", user.email || "");
            setValue("turniked_id", user.turniked_id || "");
        }
    }, [user, setValue]);

    const onUpdate = async (values: any) => {
        if (!user) return;

        setBusy(true);
        setError(null);
        setNotice(null);

        try {
            const form = new FormData();

            if (values.username !== user.username) form.set("username", values.username);
            if (values.full_name !== user.full_name) form.set("full_name", values.full_name);
            if (values.passport !== user.passport) form.set("passport", values.passport);
            if (values.email !== user.email) form.set("email", values.email);
            if (values.turniked_id !== user.turniked_id) form.set("turniked_id", values.turniked_id);

            await api.put(`/users/update_basic/${user.id}`, form, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            setNotice("✔️ Muvaffaqiyatli yangilandi!");

            setTimeout(() => {
                onSuccess();
                onClose();
            }, 1200);
        } catch (e) {
            setError(parseError(e));
        } finally {
            setBusy(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
            >
                <div className="fixed inset-0 bg-black/30" onClick={onClose} />

                <motion.div
                    initial={{ scale: 0.92 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0.92 }}
                    className="relative z-50 w-full max-w-md"
                >
                    <Card className="rounded-xl shadow-xl bg-white">
                        <CardHeader className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-t-xl">
                            <div className="flex justify-between items-center">
                                <CardTitle className="text-xl">Foydalanuvchini tahrirlash</CardTitle>
                                <button onClick={onClose}><X size={20} /></button>
                            </div>
                        </CardHeader>

                        <CardContent className="pt-4 space-y-4">
                            {notice && <div className="p-3 bg-green-100">{notice}</div>}
                            {error && <div className="p-3 bg-red-100">{error}</div>}

                            <form onSubmit={handleSubmit(onUpdate)} className="space-y-4">
                                <Input {...register("username")} placeholder="Username" />
                                <Input {...register("full_name")} placeholder="To‘liq ism" />
                                <Input {...register("passport")} placeholder="Passport" />
                                <Input {...register("email")} placeholder="Email" />
                                <Input {...register("turniked_id")} placeholder="Turniket ID" />

                                <div className="flex gap-3 pt-3">
                                    <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                                        Bekor qilish
                                    </Button>
                                    <Button type="submit" disabled={busy} className="flex-1">
                                        {busy ? "⏳ Saqlanmoqda..." : "Saqlash"}
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}

/* ---------------------------------------------------
   MAIN PAGE
--------------------------------------------------- */
export default function UserManagementPage() {
    const [me, setMe] = useState(null as any);
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isUpdateOpen, setIsUpdateOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<any>(null);

    useEffect(() => {
        (async () => {
            const info = await fetchMe();
            if (!info) return (window.location.href = "/auth/login");
            if (!info.is_superadmin) return (window.location.href = info.redirect_path || "/");

            setMe(info);

            const { data } = await api.get("/users/list_full");
            setUsers(data);
            setLoading(false);
        })();
    }, []);

    const reloadUsers = async () => {
        const { data } = await api.get("/users/list_full");
        setUsers(data);
    };

    if (!me) return null;

    return (
        <div className="min-h-screen px-6 py-10 space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Foydalanuvchilar</h1>

                <Button
                    onClick={() => setIsCreateOpen(true)}
                    className="flex items-center gap-2"
                >
                    <Plus size={18} /> Qo‘shish
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Jami: {users.length}</CardTitle>
                </CardHeader>

                <CardContent>
                    {loading ? (
                        <p className="text-center py-6">⏳ Yuklanmoqda...</p>
                    ) : (
                        <table className="w-full text-sm">
                            <thead>
                            <tr className="bg-slate-100">
                                <th className="p-3">F.I.Sh</th>
                                <th className="p-3">Username</th>
                                <th className="p-3">Lavozim</th>
                                <th className="p-3">Bo‘lim</th>
                                <th className="p-3">Turniket ID</th>
                                <th className="p-3">Email</th>
                                <th className="p-3 w-20">Tahrirlash</th>
                            </tr>
                            </thead>

                            <tbody>
                            {users.map((u) => (
                                <tr key={u.id} className="border-b">
                                    <td className="p-3">{u.full_name || "-"}</td>
                                    <td className="p-3">{u.username}</td>
                                    <td className="p-3">{u.position_title || "-"}</td>
                                    <td className="p-3">{u.org_unit_name || "-"}</td>
                                    <td className="p-3">{u.turniked_id || "-"}</td>
                                    <td className="p-3">{u.email || "-"}</td>
                                    <td className="p-3 text-right">
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => {
                                                setSelectedUser(u);
                                                setIsUpdateOpen(true);
                                            }}
                                            className="flex items-center gap-2"
                                        >
                                            <Pencil size={14} /> Edit
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    )}
                </CardContent>
            </Card>

            <UserCreateModal
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
                onSuccess={reloadUsers}
            />

            <UserEditModal
                isOpen={isUpdateOpen}
                onClose={() => setIsUpdateOpen(false)}
                user={selectedUser}
                onSuccess={reloadUsers}
            />
        </div>
    );
}
