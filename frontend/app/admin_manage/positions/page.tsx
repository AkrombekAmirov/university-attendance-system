"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, Briefcase, Building2, Layers3 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

import { api } from "@/lib/api";
import { toast } from "react-hot-toast";
import { useAuth } from "@/hooks/useAuth";

const DEFAULT_ROLE_ID = "11111111-1111-1111-1111-111111111111";

const positionSchema = z.object({
    org_unit_id: z.string().uuid({ message: "Bo‘linma tanlanmagan" }),
    title: z.string().min(2, "Lavozim nomi kamida 2 ta belgidan iborat bo‘lishi kerak"),
    quota: z.coerce.number().min(1, "Kvota kamida 1 bo‘lishi kerak"),
    is_unique: z.boolean().optional(),
    parent_position_id: z.string().uuid().optional(),
});
type FormData = z.infer<typeof positionSchema>;

// --- 💼 Modal for Creating Position ---
function PositionModal({
                           isOpen,
                           onClose,
                           onCreated,
                           orgUnits,
                           positions,
                           onSubmit,
                           register,
                           setValue,
                           errors,
                           loading,
                       }: any) {
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
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                    >
                        <Card className="w-full max-w-md shadow-2xl border-0 bg-gradient-to-br from-white to-emerald-50 dark:from-slate-900 dark:to-emerald-950">
                            <CardHeader className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white rounded-t-lg pb-5">
                                <div className="flex justify-between items-center">
                                    <CardTitle className="text-2xl font-semibold">
                                        Yangi lavozim
                                    </CardTitle>
                                    <button onClick={onClose} className="hover:bg-white/20 rounded-lg p-1">
                                        <X size={20} />
                                    </button>
                                </div>
                            </CardHeader>

                            <CardContent className="pt-5 space-y-4">
                                <form onSubmit={onSubmit} className="space-y-5">
                                    {/* Bo‘linma */}
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                                            <Building2 size={14} className="inline mr-1" /> Bo‘linma
                                        </label>
                                        <Select onValueChange={(v) => setValue("org_unit_id", v)}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Bo‘linmani tanlang" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {orgUnits.map((unit: any) => (
                                                    <SelectItem key={unit.id} value={unit.id}>
                                                        {unit.name_path}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        {errors.org_unit_id && (
                                            <p className="text-red-500 text-xs mt-1">
                                                {errors.org_unit_id.message}
                                            </p>
                                        )}
                                    </div>

                                    {/* Lavozim nomi */}
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                                            <Briefcase size={14} className="inline mr-1" /> Lavozim nomi
                                        </label>
                                        <Input
                                            placeholder="Masalan: Kafedra mudiri"
                                            {...register("title")}
                                            className="h-10 rounded-lg border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-emerald-500"
                                        />
                                        {errors.title && (
                                            <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>
                                        )}
                                    </div>

                                    {/* Kvota */}
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                                            👥 Kvota
                                        </label>
                                        <Input
                                            type="number"
                                            min={1}
                                            placeholder="Nechta lavozim bo‘lishi mumkin"
                                            {...register("quota")}
                                            className="h-10 rounded-lg border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-emerald-500"
                                        />
                                        {errors.quota && (
                                            <p className="text-red-500 text-xs mt-1">{errors.quota.message}</p>
                                        )}
                                    </div>

                                    {/* Yagona lavozim */}
                                    <div className="flex items-center gap-2 mt-3">
                                        <Checkbox
                                            id="is_unique"
                                            onCheckedChange={(checked) =>
                                                setValue("is_unique", Boolean(checked))
                                            }
                                        />
                                        <label htmlFor="is_unique" className="text-sm text-slate-700">
                                            🔒 Bu lavozim yagona (bir kishilik)
                                        </label>
                                    </div>

                                    {/* Parent */}
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                                            <Layers3 size={14} className="inline mr-1" /> Rahbar lavozim
                                        </label>
                                        <Select
                                            onValueChange={(v) => setValue("parent_position_id", v)}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Tanlang (ixtiyoriy)" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {positions.map((pos: any) => (
                                                    <SelectItem key={pos.id} value={pos.id}>
                                                        {pos.title}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="flex gap-3 pt-4">
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={onClose}
                                            className="flex-1"
                                        >
                                            Bekor qilish
                                        </Button>
                                        <Button
                                            type="submit"
                                            disabled={loading}
                                            className="flex-1 bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-600 hover:to-blue-600 text-white"
                                        >
                                            {loading ? "Yaratilmoqda..." : "Yaratish"}
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

// --- 💎 Main Page ---
export default function PositionCreatePage() {
    const router = useRouter();
    const { token } = useAuth();

    const [orgUnits, setOrgUnits] = useState<any[]>([]);
    const [positions, setPositions] = useState<any[]>([]);
    const [orgId, setOrgId] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);

    const {
        register,
        handleSubmit,
        setValue,
        reset,
        formState: { errors },
    } = useForm<FormData>({
        resolver: zodResolver(positionSchema),
    });

    // Bo‘linma daraxtini flatten qilish
    const flattenUnits = (units: any[], prefix = ""): any[] =>
        units.flatMap((unit) => {
            const label = prefix ? `${prefix} › ${unit.name}` : unit.name;
            const flattened = [{ id: unit.id, name_path: label }];
            if (unit.children?.length) {
                flattened.push(...flattenUnits(unit.children, label));
            }
            return flattened;
        });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const orgRes = await api.get("/organization/list");
                const org = orgRes.data[0];
                if (!org) throw new Error("Tashkilot topilmadi");
                setOrgId(org.id);

                const [unitTreeRes, positionsRes] = await Promise.all([
                    api.get(`/organization/units/tree/${org.id}`),
                    api.get("/organization/positions/list"),
                ]);

                setOrgUnits(flattenUnits(unitTreeRes.data.tree || []));
                setPositions(positionsRes.data || []);
            } catch (err) {
                toast.error("Ma'lumotlarni yuklashda xatolik");
            }
        };
        fetchData();
    }, []);

    const onSubmit = handleSubmit(async (data) => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("org_unit_id", data.org_unit_id);
            formData.append("role_id", DEFAULT_ROLE_ID);
            formData.append("title", data.title);
            formData.append("quota", String(data.quota));
            formData.append("is_unique", String(data.is_unique ?? true));
            if (data.parent_position_id) {
                formData.append("parent_position_id", data.parent_position_id);
            }

            await api.post("/organization/positions/create", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            toast.success("Lavozim muvaffaqiyatli yaratildi");
            reset();
            setModalOpen(false);
            router.refresh();
        } catch (err: any) {
            const detail =
                err?.response?.data?.detail ??
                (Array.isArray(err?.response?.data) && err.response.data[0]?.msg) ??
                "Xatolik yuz berdi";
            toast.error(detail);
        } finally {
            setLoading(false);
        }
    });

    return (
        <div className="space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col md:flex-row md:justify-between md:items-center gap-4"
            >
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
                        Lavozimlar
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                        Tizimdagi lavozimlarni boshqarish
                    </p>
                </div>

                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setModalOpen(true)}
                    className="flex items-center gap-2 px-6 py-3 rounded-lg shadow-lg text-white font-semibold bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-600 hover:to-blue-600"
                >
                    <Plus size={20} />
                    Yangi lavozim
                </motion.button>
            </motion.div>

            {/* Lavozim ro‘yxati (bo‘sh joy uchun placeholder) */}
            <Card className="shadow-lg border-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
                <CardHeader className="border-b border-slate-200 dark:border-slate-800">
                    <CardTitle className="text-xl font-semibold">
                        Jami: {positions.length} ta lavozim
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 text-slate-500 text-center">
                    {positions.length === 0
                        ? "Hozircha lavozimlar mavjud emas"
                        : "Lavozimlar ro‘yxati keyingi bosqichda ko‘rsatiladi"}
                </CardContent>
            </Card>

            <PositionModal
                isOpen={modalOpen}
                onClose={() => setModalOpen(false)}
                onCreated={() => router.refresh()}
                orgUnits={orgUnits}
                positions={positions}
                onSubmit={onSubmit}
                register={register}
                setValue={setValue}
                errors={errors}
                loading={loading}
            />
        </div>
    );
}
