"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "react-hot-toast";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const toastId = "position-create-toast";

// ⚙️ Faqat superadmin foydalanadi
// Backendda role_id talab qilinadi, lekin endi bitta static qiymat uzatiladi:
const DEFAULT_ROLE_ID = "11111111-1111-1111-1111-111111111111";

const positionSchema = z.object({
    org_unit_id: z.string().uuid({ message: "Bo‘linma tanlanmagan" }),
    title: z.string().min(2, "Lavozim nomi kamida 2 ta belgidan iborat bo‘lishi kerak"),
    quota: z.coerce.number().min(1, "Kvota kamida 1 bo‘lishi kerak"),
    is_unique: z.boolean().optional(),
    parent_position_id: z.string().uuid().optional(),
});

type FormData = z.infer<typeof positionSchema>;

export default function PositionCreatePage() {
    const router = useRouter();
    const { token } = useAuth();

    const [orgUnits, setOrgUnits] = useState<any[]>([]);
    const [positions, setPositions] = useState<any[]>([]);
    const [orgId, setOrgId] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const {
        register,
        handleSubmit,
        setValue,
        reset,
        formState: { errors },
    } = useForm<FormData>({
        resolver: zodResolver(positionSchema),
    });

    // 🔁 Bo‘linmalarni daraxt shaklidan flatten qilish
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
                    api.get("/organization/positions/list"), // parent uchun
                ]);

                setOrgUnits(flattenUnits(unitTreeRes.data.tree || []));
                setPositions(positionsRes.data || []);
            } catch (err) {
                toast.error("Ma'lumotlarni yuklashda xatolik", { id: toastId });
            }
        };

        fetchData();
    }, []);

    const onSubmit = async (data: FormData) => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("org_unit_id", data.org_unit_id);
            formData.append("role_id", DEFAULT_ROLE_ID); // 🔐 endi statik
            formData.append("title", data.title);
            formData.append("quota", String(data.quota));
            formData.append("is_unique", String(data.is_unique ?? true));
            if (data.parent_position_id) {
                formData.append("parent_position_id", data.parent_position_id);
            }

            await api.post("/organization/positions/create", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            toast.success("Lavozim muvaffaqiyatli yaratildi", { id: toastId });
            reset();
            router.push("/admin_manage/positions");
        } catch (err: any) {
            const detail =
                err?.response?.data?.detail ??
                (Array.isArray(err?.response?.data) && err.response.data[0]?.msg) ??
                "Xatolik yuz berdi";
            toast.error(detail, { id: toastId });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto mt-12 space-y-8 p-6 bg-white rounded-2xl shadow-sm border border-gray-100">
            <h1 className="text-3xl font-semibold text-gray-800">🧩 Yangi lavozim yaratish</h1>
            <p className="text-gray-500 text-sm">
                Faqat superadmin tomonidan yaratiladi. Bo‘linmani tanlang, nom bering va kvotani belgilang.
            </p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Bo‘linma */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">🏢 Bo‘linma</label>
                    <Select onValueChange={(v) => setValue("org_unit_id", v)}>
                        <SelectTrigger className="w-full">
                            <SelectValue placeholder="Bo‘linmani tanlang" />
                        </SelectTrigger>
                        <SelectContent>
                            {orgUnits.map((unit) => (
                                <SelectItem key={unit.id} value={unit.id}>
                                    {unit.name_path}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    {errors.org_unit_id && (
                        <p className="text-red-500 text-sm mt-1">{errors.org_unit_id.message}</p>
                    )}
                </div>

                {/* Lavozim nomi */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">💼 Lavozim nomi</label>
                    <Input
                        placeholder="Masalan, Fakultet dekani yoki Kafedra mudiri"
                        {...register("title")}
                    />
                    {errors.title && (
                        <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
                    )}
                </div>

                {/* Kvota */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">👥 Kvota</label>
                    <Input
                        type="number"
                        min={1}
                        placeholder="Nechta lavozim bo‘lishi mumkin"
                        {...register("quota")}
                    />
                    {errors.quota && (
                        <p className="text-red-500 text-sm mt-1">{errors.quota.message}</p>
                    )}
                </div>

                {/* Yagona lavozim */}
                <div className="flex items-center gap-2">
                    <Checkbox
                        id="is_unique"
                        onCheckedChange={(checked) => setValue("is_unique", Boolean(checked))}
                    />
                    <label htmlFor="is_unique" className="text-sm text-gray-700">
                        🔒 Bu lavozim yagona (bir kishilik)
                    </label>
                </div>

                {/* Parent Position */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        📈 Rahbar lavozim (agar mavjud bo‘lsa)
                    </label>
                    <Select onValueChange={(v) => setValue("parent_position_id", v)}>
                        <SelectTrigger className="w-full">
                            <SelectValue placeholder="Tanlang (ixtiyoriy)" />
                        </SelectTrigger>
                        <SelectContent>
                            {positions.map((pos) => (
                                <SelectItem key={pos.id} value={pos.id}>
                                    {pos.title}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <Button
                    type="submit"
                    className="w-full text-white text-base font-medium py-2"
                    disabled={loading}
                >
                    {loading ? "Yaratilmoqda..." : "✅ Lavozimni yaratish"}
                </Button>
            </form>
        </div>
    );
}
