"use client";

import {useState, useEffect, useMemo, useCallback} from "react";
import {useForm, FormProvider} from "react-hook-form";
import {z} from "zod";
import {zodResolver} from "@hookform/resolvers/zod";
import {motion, AnimatePresence} from "framer-motion";
import {Plus, X, Pencil, Link2} from "lucide-react";
import {toast} from "sonner";

// UI Components
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {Label} from "@/components/ui/label";

// Libs
import {api} from "@/lib/api";
import {unassignUserFromAllPositions} from "@/lib/organization/orgunit";
import {fetchMe} from "@/lib/me";

// Types
import {User} from "@/types/user";

// ========================
// TYPES & SCHEMAS
// ========================

interface OrgUnitNode {
    id: string;
    name: string;
    children?: OrgUnitNode[];
}

interface FlattenedUnit {
    id: string;
    name_path: string;
}

interface Position {
    id: string;
    title: string;
}

// Schemas
const createUserSchema = z.object({
    username: z.string().min(3).max(64),
    password: z.string().min(8),
    full_name: z.string().optional(),
    passport: z.string().optional(),
    turniked_id: z.string().optional(),
});

const updateUserSchema = z.object({
    username: z.string().optional(),
    full_name: z.string().optional(),
    passport: z.string().optional(),
    email: z.string().email().optional().nullable(),
    turniked_id: z.string().optional(),
});

const assignmentSchema = z.object({
    position_id: z.string().uuid({message: "Lavozimni tanlang"}),
    valid_from: z.string().optional(),
    valid_to: z.string().optional(),
    status: z.enum(["ACTIVE", "BLOCKED", "RESIGNED"]).default("ACTIVE"),
});

type CreateUserInput = z.infer<typeof createUserSchema>;
type UpdateUserInput = z.infer<typeof updateUserSchema>;
type AssignmentInput = z.infer<typeof assignmentSchema>;

// ========================
// UTILS
// ========================

const parseError = (e: any): string => {
    const data = e?.response?.data ?? e?.data ?? e;
    if (data?.detail) {
        return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }
    return "So‘rovda xatolik yuz berdi.";
};

const flattenUnits = (units: OrgUnitNode[], prefix = ""): FlattenedUnit[] =>
    units.flatMap((unit) => {
        const label = prefix ? `${prefix} › ${unit.name}` : unit.name;
        const current = {id: unit.id, name_path: label};
        const children = unit.children?.length ? flattenUnits(unit.children, label) : [];
        return [current, ...children];
    });

// ========================
// MODALS (Optimized & Reusable)
// ========================

const ModalWrapper = ({isOpen, onClose, children}: {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode
}) => (
    <AnimatePresence>
        {isOpen && (
            <>
                <motion.div
                    className="fixed inset-0 bg-black/40 z-50"
                    initial={{opacity: 0}}
                    animate={{opacity: 1}}
                    exit={{opacity: 0}}
                    onClick={onClose}
                />
                <motion.div
                    className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 overflow-y-auto sm:pt-24"
                    initial={{opacity: 0, scale: 0.95}}
                    animate={{opacity: 1, scale: 1}}
                    exit={{opacity: 0, scale: 0.95}}
                >
                    {children}
                </motion.div>
            </>
        )}
    </AnimatePresence>
);

const BaseModal = ({
                       title,
                       children,
                       onClose,
                       footer,
                   }: {
    title: string;
    children: React.ReactNode;
    onClose: () => void;
    footer: React.ReactNode;
}) => (
    <Card className="w-full max-w-md shadow-xl rounded-xl overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white sticky top-0 z-10">
            <div className="flex justify-between items-center">
                <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                <button
                    onClick={onClose}
                    className="hover:bg-white/20 p-1.5 rounded-full transition-colors"
                    aria-label="Yopish"
                >
                    <X size={18}/>
                </button>
            </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4 max-h-[70vh] overflow-y-auto">
            {children}
        </CardContent>
        <div className="px-6 pb-4">{footer}</div>
    </Card>
);

// --- CREATE USER ---
function UserCreateModal({isOpen, onClose, onSuccess}: {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void
}) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    // Generic tip olib tashlandi
    const form = useForm({resolver: zodResolver(createUserSchema)});

    const onSubmit = async (data: any) => {
        setIsSubmitting(true);
        try {
            const formData = new FormData();
            Object.entries(data).forEach(([key, value]) => value && formData.append(key, value as string));
            await api.post("/users/create_simple", formData);
            toast.success("Foydalanuvchi muvaffaqiyatli yaratildi!");
            form.reset();
            onSuccess();
            onClose();
        } catch (e) {
            toast.error(parseError(e));
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <ModalWrapper isOpen={isOpen} onClose={onClose}>
            <FormProvider {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)}>
                    <BaseModal
                        title="Yangi foydalanuvchi"
                        onClose={onClose}
                        footer={
                            <div className="flex gap-2">
                                <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
                                    Bekor qilish
                                </Button>
                                <Button type="submit" disabled={isSubmitting}
                                        className="flex-1 bg-emerald-600 hover:bg-emerald-700">
                                    {isSubmitting ? "Yaratilmoqda..." : "Yaratish"}
                                </Button>
                            </div>
                        }
                    >
                        <div className="space-y-3">
                            <div>
                                <Label>Username</Label>
                                <Input {...form.register("username")} placeholder="Username"/>
                                {form.formState.errors.username &&
                                    <p className="text-red-500 text-sm">{String(form.formState.errors.username.message)}</p>}
                            </div>
                            <div>
                                <Label>Parol</Label>
                                <Input type="password" {...form.register("password")} placeholder="Kamida 8 ta belgi"/>
                                {form.formState.errors.password &&
                                    <p className="text-red-500 text-sm">{String(form.formState.errors.password.message)}</p>}
                            </div>
                            <div>
                                <Label>To'liq ism</Label>
                                <Input {...form.register("full_name")} placeholder="Ism Familiya"/>
                            </div>
                            <div>
                                <Label>Passport</Label>
                                <Input {...form.register("passport")} placeholder="AA1234567"/>
                            </div>
                            <div>
                                <Label>Turniket ID</Label>
                                <Input {...form.register("turniked_id")} placeholder="12345"/>
                            </div>
                        </div>
                    </BaseModal>
                </form>
            </FormProvider>
        </ModalWrapper>
    );
}

// --- EDIT USER ---
function UserEditModal({isOpen, onClose, user, onSuccess}: {
    isOpen: boolean;
    onClose: () => void;
    user: User | null;
    onSuccess: () => void
}) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    // Generic tip olib tashlandi
    const form = useForm({resolver: zodResolver(updateUserSchema)});

    useEffect(() => {
        if (user && isOpen) {
            form.reset({
                username: user.username || "",
                full_name: user.full_name || "",
                passport: user.passport || "",
                email: user.email || "",
                turniked_id: user.turniked_id || "",
            });
        }
    }, [user, isOpen, form]);

    const onSubmit = async (data: any) => {
        if (!user) return;
        setIsSubmitting(true);
        try {
            const formData = new FormData();
            Object.entries(data).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== (user as any)[key]) {
                    formData.append(key, value as string);
                }
            });
            await api.put(`/users/update_basic/${user.id}`, formData);
            toast.success("Muvaffaqiyatli yangilandi!");
            onSuccess();
            onClose();
        } catch (e) {
            toast.error(parseError(e));
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!user) return null;

    return (
        <ModalWrapper isOpen={isOpen} onClose={onClose}>
            <FormProvider {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)}>
                    <BaseModal
                        title="Foydalanuvchini tahrirlash"
                        onClose={onClose}
                        footer={
                            <div className="flex gap-2">
                                <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
                                    Bekor qilish
                                </Button>
                                <Button type="submit" disabled={isSubmitting}
                                        className="flex-1 bg-blue-600 hover:bg-blue-700">
                                    {isSubmitting ? "Saqlanmoqda..." : "Saqlash"}
                                </Button>
                            </div>
                        }
                    >
                        <div className="space-y-3">
                            <div>
                                <Label>Username</Label>
                                <Input {...form.register("username")} />
                            </div>
                            <div>
                                <Label>To'liq ism</Label>
                                <Input {...form.register("full_name")} />
                            </div>
                            <div>
                                <Label>Passport</Label>
                                <Input {...form.register("passport")} />
                            </div>
                            <div>
                                <Label>Email</Label>
                                <Input type="email" {...form.register("email")} />
                            </div>
                            <div>
                                <Label>Turniket ID</Label>
                                <Input {...form.register("turniked_id")} />
                            </div>
                        </div>
                    </BaseModal>
                </form>
            </FormProvider>
        </ModalWrapper>
    );
}

// --- ASSIGN USER TO POSITION ---
function UserAssignmentModal({isOpen, onClose, user, onSuccess}: {
    isOpen: boolean;
    onClose: () => void;
    user: User | null;
    onSuccess: () => void
}) {
    const [orgUnits, setOrgUnits] = useState<FlattenedUnit[]>([]);
    const [positions, setPositions] = useState<Position[]>([]);
    const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    // Generic tip olib tashlandi
    const form = useForm({resolver: zodResolver(assignmentSchema), defaultValues: {status: "ACTIVE"}});

    const loadOrgTree = useCallback(async () => {
        try {
            const orgRes = await api.get<{ id: string }[]>("/organization/list");
            const orgId = orgRes.data[0]?.id;
            if (!orgId) throw new Error("Tashkilot topilmadi");
            const treeRes = await api.get<{ tree: OrgUnitNode[] }>(`/organization/units/tree/${orgId}`);
            setOrgUnits(flattenUnits(treeRes.data.tree || []));
        } catch (e) {
            toast.error("Bo'limlar yuklanmadi");
        }
    }, []);

    const loadPositions = useCallback(async (unitId: string) => {
        try {
            const res = await api.get<Position[]>(`/organization/positions/by-unit/${unitId}`);
            setPositions(res.data || []);
            form.setValue("position_id", "");
        } catch (e) {
            setPositions([]);
            toast.error("Lavozimlar yuklanmadi");
        }
    }, [form]);

    useEffect(() => {
        if (isOpen) {
            loadOrgTree();
            form.reset({status: "ACTIVE"});
            setSelectedUnitId(null);
            setPositions([]);
        }
    }, [isOpen, loadOrgTree, form]);

    const handleUnitChange = (unitId: string) => {
        setSelectedUnitId(unitId);
        loadPositions(unitId);
    };

    const onSubmit = async (data: any) => {
        if (!user) return;
        setIsLoading(true);
        try {
            const formData = new FormData();
            formData.append("user_id", user.id);
            formData.append("position_id", data.position_id);
            formData.append("status", data.status);
            if (data.valid_from) formData.append("valid_from", data.valid_from);
            if (data.valid_to) formData.append("valid_to", data.valid_to);

            await api.post("/organization/assignments/create", formData);
            toast.success("Foydalanuvchi lavozimga biriktirildi!");
            onSuccess();
            onClose();
        } catch (e) {
            toast.error(parseError(e));
        } finally {
            setIsLoading(false);
        }
    };

    if (!user) return null;

    return (
        <ModalWrapper isOpen={isOpen} onClose={onClose}>
            <FormProvider {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)}>
                    <BaseModal
                        title={`${user.full_name || user.username} – lavozim biriktirish`}
                        onClose={onClose}
                        footer={
                            <div className="flex gap-2">
                                <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
                                    Bekor qilish
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={isLoading || !selectedUnitId || !form.watch("position_id")}
                                    className="flex-1 bg-gradient-to-r from-emerald-500 to-blue-500 text-white"
                                >
                                    {isLoading ? "Biriktirilmoqda..." : "Biriktirish"}
                                </Button>
                            </div>
                        }
                    >
                        <div className="space-y-4">
                            {/* Bo'lim */}
                            <div>
                                <Label>Bo'lim</Label>
                                <Select onValueChange={handleUnitChange} value={selectedUnitId || undefined}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Bo'lim tanlang..."/>
                                    </SelectTrigger>
                                    <SelectContent>
                                        {orgUnits.map((unit) => (
                                            <SelectItem key={unit.id} value={unit.id}>
                                                {unit.name_path}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Lavozim */}
                            <div>
                                <Label>Lavozim</Label>
                                <Select
                                    onValueChange={(v) => form.setValue("position_id", v)}
                                    value={form.watch("position_id") || undefined}
                                    disabled={!selectedUnitId}
                                >
                                    <SelectTrigger>
                                        <SelectValue
                                            placeholder={
                                                !selectedUnitId
                                                    ? "Avval bo'lim tanlang"
                                                    : positions.length === 0
                                                        ? "Lavozim mavjud emas"
                                                        : "Lavozim tanlang..."
                                            }
                                        />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {positions.map((pos) => (
                                            <SelectItem key={pos.id} value={pos.id}>
                                                {pos.title}
                                            </SelectItem>
                                        ))}
                                        {positions.length === 0 && selectedUnitId && (
                                            // ✅ XATO Tuzatildi: value="no-position" — hech qanday ma'noga ega emas, lekin valid!
                                            <SelectItem value="no-position" disabled>
                                                Lavozimlar topilmadi
                                            </SelectItem>
                                        )}
                                    </SelectContent>
                                </Select>
                                {form.formState.errors.position_id && (
                                    <p className="text-red-500 text-sm mt-1">{String(form.formState.errors.position_id.message)}</p>
                                )}
                            </div>

                            {/* Sanalar */}
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <Label>Boshlanish sanasi</Label>
                                    <Input type="date" {...form.register("valid_from")} />
                                </div>
                                <div>
                                    <Label>Tugash sanasi (ixtiyoriy)</Label>
                                    <Input type="date" {...form.register("valid_to")} />
                                </div>
                            </div>

                            {/* Holat */}
                            <div>
                                <Label>Holati</Label>
                                <Select
                                    value={form.watch("status")}
                                    onValueChange={(v) => form.setValue("status", v as any)}
                                >
                                    <SelectTrigger>
                                        <SelectValue/>
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="ACTIVE">Faol</SelectItem>
                                        <SelectItem value="BLOCKED">Bloklangan</SelectItem>
                                        <SelectItem value="RESIGNED">Ishdan ketgan</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </BaseModal>
                </form>
            </FormProvider>
        </ModalWrapper>
    );
}

// ========================
// MAIN PAGE
// ========================

export default function UserManagementPage() {
    const [me, setMe] = useState<any>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isUpdateOpen, setIsUpdateOpen] = useState(false);
    const [isAssignmentOpen, setIsAssignmentOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);

    // Init
    useEffect(() => {
        const init = async () => {
            const info = await fetchMe();
            if (!info) return (window.location.href = "/auth/login");
            if (!info.is_superadmin) return (window.location.href = info.redirect_path || "/");
            setMe(info);
            try {
                const {data} = await api.get<User[]>("/users/list_full");
                setUsers(data);
            } catch (e) {
                toast.error("Foydalanuvchilar ro'yxati yuklanmadi");
            } finally {
                setLoading(false);
            }
        };
        init();
    }, []);

    const reloadUsers = useCallback(async () => {
        try {
            const {data} = await api.get<User[]>("/users/list_full");
            setUsers(data);
        } catch (e) {
            toast.error("Ro'yxat yangilanmadi");
        }
    }, []);

    const filteredUsers = useMemo(() => {
        const q = search.toLowerCase().trim();
        if (!q) return users;
        return users.filter(
            (u) =>
                u.full_name?.toLowerCase().includes(q) ||
                u.username.toLowerCase().includes(q) ||
                u.passport?.toLowerCase().includes(q) ||
                u.email?.toLowerCase().includes(q) ||
                u.turniked_id?.toLowerCase().includes(q) ||
                u.position_title?.toLowerCase().includes(q) ||
                u.org_unit_name?.toLowerCase().includes(q)
        );
    }, [users, search]);

    // handleUnassignUser ni komponent ichiga ko'chirdik
    const handleUnassignUser = async (user: User) => {
        if (!user.position_title) {
            toast.info("Bu foydalanuvchi allaqachon lavozimsiz");
            return;
        }

        const ok = window.confirm(
            `${user.full_name || user.username} lavozimdan to‘liq ozod etilsinmi?`
        );
        if (!ok) return;

        try {
            await unassignUserFromAllPositions({
                user_id: user.id,
                // effective_date: "2026-02-02", // ixtiyoriy, hozir kerak emas
            });

            toast.success("Foydalanuvchi lavozimdan to‘liq ozod etildi");
            await reloadUsers();
        } catch (e: any) {
            toast.error(e.message || "Xatolik yuz berdi");
        }
    };

    if (!me) return null;

    return (
        <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <h1 className="text-2xl font-bold text-gray-900">Foydalanuvchilar</h1>
                <Button onClick={() => setIsCreateOpen(true)}
                        className="bg-emerald-600 hover:bg-emerald-700 w-full sm:w-auto">
                    <Plus size={18} className="mr-2"/> Yangi foydalanuvchi
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Jami: {filteredUsers.length} / {users.length}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="mb-4 flex flex-col sm:flex-row gap-2">
                        <Input
                            placeholder="Qidirish: ism, username, bo'lim..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="flex-1"
                        />
                        {search && (
                            <Button variant="outline" onClick={() => setSearch("")} className="whitespace-nowrap">
                                Tozalash
                            </Button>
                        )}
                    </div>

                    {loading ? (
                        <p className="text-center py-8 text-gray-500">Yuklanmoqda...</p>
                    ) : filteredUsers.length === 0 ? (
                        <p className="text-center py-8 text-gray-500">Hech narsa topilmadi</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                <tr className="bg-gray-50 text-left">
                                    {["F.I.Sh", "Username", "Lavozim", "Bo'lim", "Turniket ID", "Email", "Harakatlar"].map((h) => (
                                        <th key={h} className="p-3 font-medium text-gray-700">{h}</th>
                                    ))}
                                </tr>
                                </thead>
                                <tbody>
                                {filteredUsers.map((u) => (
                                    <tr key={u.id} className="border-b hover:bg-gray-50 transition-colors">
                                        <td className="p-3 font-medium">{u.full_name || "-"}</td>
                                        <td className="p-3 text-gray-600">{u.username}</td>
                                        <td className="p-3">{u.position_title || "-"}</td>
                                        <td className="p-3">{u.org_unit_name || "-"}</td>
                                        <td className="p-3">{u.turniked_id || "-"}</td>
                                        <td className="p-3 text-gray-600">{u.email || "-"}</td>
                                        <td className="p-3">
                                            <div className="flex gap-2 justify-end">

                                                {/* 🔓 UNASSIGN BUTTON */}
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    disabled={!u.position_title}
                                                    onClick={() => handleUnassignUser(u)}
                                                    className="border-red-300 text-red-600 hover:bg-red-50"
                                                >
                                                    <X size={14} className="mr-1"/>
                                                    Ozod etish
                                                </Button>

                                                {/* 🔗 ASSIGN */}
                                                <Button
                                                    size="sm"
                                                    className="bg-purple-600 hover:bg-purple-700 text-white"
                                                    onClick={() => {
                                                        setSelectedUser(u);
                                                        setIsAssignmentOpen(true);
                                                    }}
                                                >
                                                    <Link2 size={14} className="mr-1"/> Biriktirish
                                                </Button>

                                                {/* ✏️ EDIT */}
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => {
                                                        setSelectedUser(u);
                                                        setIsUpdateOpen(true);
                                                    }}
                                                >
                                                    <Pencil size={14} className="mr-1"/> Tahrirlash
                                                </Button>

                                            </div>
                                        </td>

                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            <UserCreateModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} onSuccess={reloadUsers}/>
            <UserEditModal
                isOpen={isUpdateOpen}
                onClose={() => setIsUpdateOpen(false)}
                user={selectedUser}
                onSuccess={reloadUsers}
            />
            <UserAssignmentModal
                isOpen={isAssignmentOpen}
                onClose={() => {
                    setIsAssignmentOpen(false);
                    setSelectedUser(null);
                }}
                user={selectedUser}
                onSuccess={reloadUsers}
            />
        </div>
    );
}
