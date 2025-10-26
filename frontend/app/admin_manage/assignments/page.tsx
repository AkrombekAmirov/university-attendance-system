"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { assignmentSchema } from "@/lib/assignment";
import { z } from "zod";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type FormData = z.infer<typeof assignmentSchema>;

export default function AssignmentCreateForm() {
    const { register, handleSubmit, setValue, reset, watch, formState: { errors } } = useForm<FormData>({
        resolver: zodResolver(assignmentSchema),
        defaultValues: { status: "ACTIVE" },
    });

    const [positions, setPositions] = useState([]);
    const [users, setUsers] = useState([]);

    useEffect(() => {
        api.get("/organization/positions/list").then(res => setPositions(res.data));
        api.get("/users/get_users").then(res => setUsers(res.data));
    }, []);

    const onSubmit = async (data: FormData) => {
        const formData = new FormData();
        Object.entries(data).forEach(([k, v]) => v && formData.append(k, v));
        try {
            await api.post("/organization/assignments/create", formData);
            toast.success("Biriktirish muvaffaqiyatli yaratildi");
            reset();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Xatolik yuz berdi");
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-xl">
            <div>
                <Label>Foydalanuvchi</Label>
                <Select onValueChange={(val) => setValue("user_id", val)}>
                    <SelectTrigger>
                        <SelectValue placeholder="Tanlang" />
                    </SelectTrigger>
                    <SelectContent>
                        {users.map((u) => (
                            <SelectItem key={u.id} value={u.id}>{u.full_name || u.username}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                {errors.user_id && <p className="text-sm text-red-500">{errors.user_id.message}</p>}
            </div>

            <div>
                <Label>Lavozim</Label>
                <Select onValueChange={(val) => setValue("position_id", val)}>
                    <SelectTrigger>
                        <SelectValue placeholder="Tanlang" />
                    </SelectTrigger>
                    <SelectContent>
                        {positions.map((p) => (
                            <SelectItem key={p.id} value={p.id}>{p.title}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                {errors.position_id && <p className="text-sm text-red-500">{errors.position_id.message}</p>}
            </div>

            <div className="flex gap-4">
                <div className="flex-1">
                    <Label>Boshlanish sanasi</Label>
                    <Input type="date" {...register("valid_from")} />
                </div>
                <div className="flex-1">
                    <Label>Tugash sanasi</Label>
                    <Input type="date" {...register("valid_to")} />
                </div>
            </div>

            <div>
                <Label>Holati</Label>
                <Select onValueChange={(val) => setValue("status", val)}>
                    <SelectTrigger>
                        <SelectValue placeholder="ACTIVE" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="ACTIVE">ACTIVE</SelectItem>
                        <SelectItem value="BLOCKED">BLOCKED</SelectItem>
                        <SelectItem value="RESIGNED">RESIGNED</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <Button type="submit" className="w-full">Biriktirish</Button>
        </form>
    );
}
