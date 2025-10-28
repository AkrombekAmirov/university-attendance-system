"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, UserRound, Briefcase, CalendarRange, ShieldCheck, Building2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { assignmentSchema } from "@/lib/assignment";
import { z } from "zod";
import { api } from "@/lib/api";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

type FormData = z.infer<typeof assignmentSchema>;

// ✅ Assignment modal with tree select
function AssignmentModal({
                             isOpen,
                             onClose,
                             onCreated,
                             users
                         }: any) {
    const { register, handleSubmit, setValue, reset, formState: { errors } } = useForm<FormData>({
        resolver: zodResolver(assignmentSchema),
        defaultValues: { status: "ACTIVE" },
    });

    const [loading, setLoading] = useState(false);
    const [orgId, setOrgId] = useState("");
    const [units, setUnits] = useState<any[]>([]);
    const [positions, setPositions] = useState<any[]>([]);
    const [unitPositions, setUnitPositions] = useState<any[]>([]);
    const [selectedUnit, setSelectedUnit] = useState("");

    // ✅ flatten tree (same as position modal)
    const flattenUnits = (units: any[], prefix = ""): any[] =>
        units.flatMap((unit) => {
            const label = prefix ? `${prefix} › ${unit.name}` : unit.name;
            const flattened = [{ id: unit.id, name_path: label }];
            if (unit.children?.length) {
                flattened.push(...flattenUnits(unit.children, label));
            }
            return flattened;
        });

    // ✅ load organization + tree on open
    useEffect(() => {
        if (!isOpen) return;

        const load = async () => {
            try {
                const orgRes = await api.get("/organization/list");
                const org = orgRes.data[0];
                setOrgId(org.id);

                const treeRes = await api.get(`/organization/units/tree/${org.id}`);
                setUnits(flattenUnits(treeRes.data.tree));
            } catch {
                toast.error("Bo‘limlar yuklanmadi");
            }
        };
        load();
    }, [isOpen]);

    // ✅ When unit selected → load its positions
    const handleUnitSelect = async (unitId: string) => {
        setSelectedUnit(unitId);
        setValue("position_id", "");
        try {
            const r = await api.get(`/organization/positions/by-unit/${unitId}`);
            setUnitPositions(r.data);
        } catch {
            toast.error("Lavozimlar yuklanmadi");
        }
    };

    // ✅ Submit assignment
    const onSubmit = async (data: FormData) => {
        const fd = new FormData();
        Object.entries(data).forEach(([k, v]) => v && fd.append(k, v));

        try {
            setLoading(true);
            await api.post("/organization/assignments/create", fd);
            toast.success("Biriktirildi");
            reset();
            onCreated();
            onClose();
        } catch (err: any) {
            toast.error(err.response?.data?.detail);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div className="fixed inset-0 bg-black/40 z-40" onClick={onClose}/>
            <motion.div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <Card className="w-full max-w-md shadow-xl">
                    <CardHeader className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white">
                        <div className="flex justify-between items-center">
                            <CardTitle className="text-xl font-semibold">Yangi biriktirish</CardTitle>
                            <button onClick={onClose}><X/></button>
                        </div>
                    </CardHeader>

                    <CardContent className="space-y-4 pt-4">
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

                            {/* USER */}
                            <div>
                                <Label><UserRound className="inline mr-1" /> Foydalanuvchi</Label>
                                <Select onValueChange={(v) => setValue("user_id", v)}>
                                    <SelectTrigger><SelectValue placeholder="Tanlang"/></SelectTrigger>
                                    <SelectContent>
                                        {users.map((u: any) => (
                                            <SelectItem key={u.id} value={u.id}>{u.full_name || u.username}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* UNIT TREE SELECT */}
                            <div>
                                <Label><Building2 className="inline mr-1"/> Bo‘lim</Label>
                                <Select onValueChange={(v) => handleUnitSelect(v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Bo‘lim tanlang"/>
                                    </SelectTrigger>
                                    <SelectContent>
                                        {units.map((u) => (
                                            <SelectItem key={u.id} value={u.id}>
                                                {u.name_path}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* POSITIONS */}
                            <div>
                                <Label><Briefcase className="inline mr-1" /> Lavozim</Label>
                                <Select onValueChange={(v) => setValue("position_id", v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder={selectedUnit ? "Lavozim tanlang" : "Avval bo‘lim tanlang"} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {unitPositions.length > 0 ? (
                                            unitPositions.map((p) => (
                                                <SelectItem key={p.id} value={p.id}>{p.title}</SelectItem>
                                            ))
                                        ) : (
                                            <div className="text-xs text-center p-2">Lavozimlar yo‘q</div>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* DATES */}
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <Label>Boshlanish</Label>
                                    <Input type="date" {...register("valid_from")} />
                                </div>
                                <div>
                                    <Label>Tugash</Label>
                                    <Input type="date" {...register("valid_to")} />
                                </div>
                            </div>

                            {/* STATUS */}
                            <div>
                                <Label><ShieldCheck className="inline mr-1"/> Holati</Label>
                                <Select onValueChange={(v) => setValue("status", v)} defaultValue="ACTIVE">
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="ACTIVE">ACTIVE</SelectItem>
                                        <SelectItem value="BLOCKED">BLOCKED</SelectItem>
                                        <SelectItem value="RESIGNED">RESIGNED</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="flex gap-2">
                                <Button type="button" variant="outline" onClick={onClose}>Bekor</Button>
                                <Button disabled={loading} className="flex-1 bg-gradient-to-r from-emerald-500 to-blue-500 text-white">
                                    {loading ? "Saqlanyapti..." : "Biriktirish"}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </motion.div>
        </AnimatePresence>
    );
}

// 🌈 Main PAGE
export default function AssignmentCreatePage() {
    const [users, setUsers] = useState<any[]>([]);
    const [modalOpen, setModalOpen] = useState(false);

    useEffect(() => {
        api.get("/users/get_users").then((res) => setUsers(res.data));
    }, []);

    return (
        <div className="space-y-6">
            <motion.div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
                        Foydalanuvchi biriktirish
                    </h1>
                    <p className="text-slate-500">Lavozimga biriktirish</p>
                </div>

                <Button onClick={() => setModalOpen(true)} className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white">
                    <Plus /> Yangi biriktirish
                </Button>
            </motion.div>

            <Card><CardContent className="text-center p-6">Biriktirishlar ro‘yxati keyinchalik</CardContent></Card>

            <AssignmentModal
                isOpen={modalOpen}
                onClose={() => setModalOpen(false)}
                onCreated={() => {}}
                users={users}
            />
        </div>
    );
}
