// app/(protected)/admin_manage/reporting-links/page.tsx

"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { api } from "@/lib/api";

const schema = z.object({
    parent_position_id: z.string().uuid({ message: "Iltimos, rahbar lavozimni tanlang." }),
    child_position_id: z.string().uuid({ message: "Iltimos, bo‘ysunuvchi lavozimni tanlang." }),
});

type FormValues = z.infer<typeof schema>;

interface PositionOption {
    id: string;
    title: string;
    unit_name: string;
}

export default function CreateReportingLinkPage() {
    const [positions, setPositions] = useState<PositionOption[]>([]);
    const {
        register,
        handleSubmit,
        setValue,
        formState: { errors, isSubmitting },
    } = useForm<FormValues>({ resolver: zodResolver(schema) });

    useEffect(() => {
        // Lavozimlar ro'yxatini yuklab olish
        api.get("/organization/positions/list")
            .then((res) => setPositions(res.data))
            .catch(() => toast.error("Lavozimlarni yuklab bo‘lmadi"));
    }, []);

    const onSubmit = async (data: FormValues) => {
        const formData = new FormData();
        formData.append("parent_position_id", data.parent_position_id);
        formData.append("child_position_id", data.child_position_id);

        try {
            await api.post("/organization/reporting/create", formData);
            toast.success("Bo‘ysunish aloqasi muvaffaqiyatli yaratildi!");
        } catch (error: any) {
            toast.error(error?.response?.data?.detail || "Xatolik yuz berdi");
        }
    };

    return (
        <div className="max-w-xl mx-auto mt-10 p-4 border rounded-xl shadow">
            <h1 className="text-xl font-semibold mb-4">Rahbar-Bo‘ysunuvchi Aloqasini Yaratish</h1>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Rahbar lavozim tanlash */}
                <div>
                    <label className="block mb-1 font-medium">Rahbar lavozim</label>
                    <Select onValueChange={(val) => setValue("parent_position_id", val)}>
                        <SelectTrigger>
                            <SelectValue placeholder="Tanlang..." />
                        </SelectTrigger>
                        <SelectContent>
                            {positions.map((pos) => (
                                <SelectItem key={pos.id} value={pos.id}>
                                    {pos.title} — {pos.unit_name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    {errors.parent_position_id && (
                        <p className="text-sm text-red-500 mt-1">{errors.parent_position_id.message}</p>
                    )}
                </div>

                {/* Bo‘ysunuvchi lavozim tanlash */}
                <div>
                    <label className="block mb-1 font-medium">Bo‘ysunuvchi lavozim</label>
                    <Select onValueChange={(val) => setValue("child_position_id", val)}>
                        <SelectTrigger>
                            <SelectValue placeholder="Tanlang..." />
                        </SelectTrigger>
                        <SelectContent>
                            {positions.map((pos) => (
                                <SelectItem key={pos.id} value={pos.id}>
                                    {pos.title} — {pos.unit_name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    {errors.child_position_id && (
                        <p className="text-sm text-red-500 mt-1">{errors.child_position_id.message}</p>
                    )}
                </div>

                <Button type="submit" disabled={isSubmitting}>
                    Saqlash
                </Button>
            </form>
        </div>
    );
}
