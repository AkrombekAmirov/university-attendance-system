"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Plus,
    X,
    Briefcase,
    Building2,
    Layers3,
    Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Select,
    SelectTrigger,
    SelectContent,
    SelectItem,
    SelectValue,
} from "@/components/ui/select";

import { api } from "@/lib/api";
import { toast } from "react-hot-toast";
import { useAuth } from "@/hooks/useAuth";

/* ============================================================================
   CONSTANTS & SCHEMA
============================================================================ */

const DEFAULT_ROLE_ID = "11111111-1111-1111-1111-111111111111";

const positionSchema = z.object({
    org_unit_id: z.string().uuid(),
    title: z.string().min(2),
    quota: z.coerce.number().min(1),
    is_unique: z.boolean().optional(),
    parent_position_id: z.string().uuid().optional(),
});

type FormData = z.infer<typeof positionSchema>;

/* ============================================================================
   HELPERS
============================================================================ */

const Field = ({ label, icon, children }: any) => (
    <div className="space-y-1">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
            {icon} {label}
        </label>
        {children}
    </div>
);

const Error = ({ children }: any) => (
    <p className="text-xs text-red-500 mt-1">{children}</p>
);

/* ============================================================================
   PREMIUM MODAL
============================================================================ */

function PositionCreateModal({
                                 open,
                                 onClose,
                                 onSave,
                                 orgUnits,
                                 positions,
                                 loading,
                             }: any) {
    // Generic tipni olib tashladik, TypeScript o'zi aniqlaydi
    const {
        register,
        handleSubmit,
        setValue,
        reset,
        formState: { errors },
    } = useForm({
        resolver: zodResolver(positionSchema),
        defaultValues: {
            quota: 1,
            is_unique: false,
        },
    });

    // Modal yopilganda formani tozalash
    useEffect(() => {
        if (!open) reset();
    }, [open, reset]);

    const onSubmit = (data: any) => {
        onSave(data);
    };

    return (
        <AnimatePresence>
            {open && (
                <>
                    <motion.div
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
                        onClick={onClose}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    />

                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center px-4"
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.96 }}
                    >
                        <Card className="w-full max-w-lg border-0 shadow-2xl bg-gradient-to-br from-white to-emerald-50 dark:from-slate-900 dark:to-emerald-950">
                            <CardHeader className="pb-6 border-b">
                                <div className="flex justify-between items-center">
                                    <CardTitle className="text-2xl font-bold flex items-center gap-2">
                                        <Sparkles className="text-emerald-500" />
                                        Yangi lavozim
                                    </CardTitle>
                                    <button onClick={onClose} className="hover:bg-slate-100 p-1 rounded-full">
                                        <X size={20} />
                                    </button>
                                </div>
                                <p className="text-sm text-slate-500 mt-1">
                                    Tizimga yangi professional rol qo‘shish
                                </p>
                            </CardHeader>

                            <CardContent className="pt-6 space-y-5">
                                <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

                                    {/* Org Unit */}
                                    <Field label="Bo‘linma" icon={<Building2 size={14} />}>
                                        <Select onValueChange={(v) => setValue("org_unit_id", v)}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Bo‘linmani tanlang" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {orgUnits
                                                    .filter((u: any) => u.id)
                                                    .map((u: any) => (
                                                        <SelectItem
                                                            key={`unit-${u.id}`}
                                                            value={String(u.id)}
                                                        >
                                                            {u.name_path}
                                                        </SelectItem>
                                                    ))}
                                            </SelectContent>
                                        </Select>
                                        {errors.org_unit_id && <Error>{String(errors.org_unit_id.message)}</Error>}
                                    </Field>

                                    {/* Title */}
                                    <Field label="Lavozim nomi" icon={<Briefcase size={14} />}>
                                        <Input
                                            {...register("title")}
                                            placeholder="Masalan: Kafedra mudiri"
                                        />
                                        {errors.title && <Error>{String(errors.title.message)}</Error>}
                                    </Field>

                                    {/* Quota */}
                                    <Field label="Kvota">
                                        <Input
                                            type="number"
                                            min={1}
                                            {...register("quota")}
                                            placeholder="Nechta xodim bo‘lishi mumkin"
                                        />
                                        {errors.quota && <Error>{String(errors.quota.message)}</Error>}
                                    </Field>

                                    {/* Unique */}
                                    <div className="flex items-center gap-3 pt-2">
                                        <Checkbox
                                            id="is_unique"
                                            onCheckedChange={(v) =>
                                                setValue("is_unique", Boolean(v))
                                            }
                                        />
                                        <label htmlFor="is_unique" className="text-sm text-slate-600 cursor-pointer select-none">
                                            Bu lavozim yagona (bir kishilik)
                                        </label>
                                    </div>

                                    {/* Parent */}
                                    <Field label="Rahbar lavozim" icon={<Layers3 size={14} />}>
                                        <Select
                                            onValueChange={(v) => setValue("parent_position_id", v)}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Ixtiyoriy" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {positions
                                                    .filter((p: any) => p.id)
                                                    .map((p: any) => (
                                                        <SelectItem
                                                            key={`pos-${p.id}`}
                                                            value={String(p.id)}
                                                        >
                                                            {p.title}
                                                        </SelectItem>
                                                    ))}
                                            </SelectContent>
                                        </Select>
                                    </Field>

                                    {/* Actions */}
                                    <div className="flex gap-3 pt-6">
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
                                            className="flex-1 bg-gradient-to-r from-emerald-500 to-blue-500 text-white"
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

/* ============================================================================
   MAIN PAGE
============================================================================ */

export default function PositionCreatePage() {
    const router = useRouter();
    const { token } = useAuth();

    const [orgUnits, setOrgUnits] = useState<any[]>([]);
    const [positions, setPositions] = useState<any[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    const flattenUnits = (units: any[], prefix = ""): any[] =>
        units.flatMap((u) => {
            const name = prefix ? `${prefix} › ${u.name}` : u.name;
            return [
                { id: u.id, name_path: name },
                ...(u.children ? flattenUnits(u.children, name) : []),
            ];
        });

    useEffect(() => {
        const loadData = async () => {
            try {
                // API chaqiruvlari
                // Hozircha mock data yoki real API
                // Agar API ishlamasa, bo'sh array qaytaradi
                try {
                    const orgRes = await api.get("/organization/list");
                    if (orgRes.data && orgRes.data.length > 0) {
                        const org = orgRes.data[0];
                        const [unitRes, posRes] = await Promise.all([
                            api.get(`/organization/units/tree/${org.id}`),
                            api.get("/organization/positions/list"),
                        ]);
                        setOrgUnits(flattenUnits(unitRes.data.tree || []));
                        setPositions(posRes.data || []);
                    }
                } catch (innerErr) {
                    console.warn("API data fetch failed, using empty state", innerErr);
                }
            } catch {
                toast.error("Ma’lumotlarni yuklashda xatolik");
            }
        };

        loadData();
    }, []);

    const handleSave = async (data: FormData) => {
        setLoading(true);
        try {
            const fd = new FormData();
            fd.append("org_unit_id", data.org_unit_id);
            fd.append("role_id", DEFAULT_ROLE_ID);
            fd.append("title", data.title);
            fd.append("quota", String(data.quota));
            fd.append("is_unique", String(data.is_unique ?? false));
            if (data.parent_position_id) {
                fd.append("parent_position_id", data.parent_position_id);
            }

            await api.post("/organization/positions/create", fd);
            toast.success("Lavozim yaratildi 🎉");
            setModalOpen(false);
            router.refresh();
        } catch (e: any) {
            toast.error(e?.response?.data?.detail ?? "Xatolik yuz berdi");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
                        Lavozimlar
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Tizimdagi rollar va ierarxiyani boshqarish
                    </p>
                </div>

                <Button
                    onClick={() => setModalOpen(true)}
                    className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white px-6 py-3"
                >
                    <Plus className="mr-2" /> Yangi lavozim
                </Button>
            </header>

            <Card className="border-0 shadow-lg">
                <CardContent className="py-10 text-center text-slate-500">
                    Jami {positions.length} ta lavozim mavjud
                </CardContent>
            </Card>

            <PositionCreateModal
                open={modalOpen}
                onClose={() => setModalOpen(false)}
                onSave={handleSave}
                orgUnits={orgUnits}
                positions={positions}
                loading={loading}
            />
        </div>
    );
}
