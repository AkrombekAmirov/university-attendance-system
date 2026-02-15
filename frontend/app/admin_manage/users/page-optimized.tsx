"use client";

import {useState, useEffect} from "react";
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
import {fetchMe} from "@/lib/me";

// Hooks
import {useUsers, useUserActions} from "@/hooks/useUsers";
import {useDebounce} from "@/hooks/useDebounce";

// Components
import {VirtualizedUserTable} from "@/components/VirtualizedUserTable";

// ========================
// TYPES & SCHEMAS
// ========================

interface User {
    id: string;
    username: string;
    full_name?: string | null;
    passport?: string | null;
    email?: string | null;
    turniked_id?: string | null;
    position_title?: string | null;
    org_unit_name?: string | null;
}

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
    return "So'rovda xatolik yuz berdi.";
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
    onSuccess: (data: CreateUserInput) => Promise<void>
}) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const form = useForm<CreateUserInput>({resolver: zodResolver(createUserSchema)});

    const onSubmit = async (data: CreateUserInput) => {
        setIsSubmitting(true);
        try {
            await onSuccess(data);
            form.reset();
            onClose();
        } catch (e) {
            // Error is handled in the parent
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
                                    <p className="text-red-500 text-sm">{form.formState.errors.username.message}</p>}
                            </div>
                            <div>
                                <Label>Parol</Label>
                                <Input type="password" {...form.register("password")} placeholder="Kamida 8 ta belgi"/>
                                {form.formState.errors.password &&
                                    <p className="text-red-500 text-sm">{form.formState.errors.password.message}</p>}
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
    onSuccess: (data: UpdateUserInput) => Promise<void>
}) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const form = useForm<UpdateUserInput>({resolver: zodResolver(updateUserSchema)});

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

    const onSubmit = async (data: UpdateUserInput) => {
        if (!user) return;
        setIsSubmitting(true);
        try {
            await onSuccess(data);
            onClose();
        } catch (e) {
            // Error is handled in the parent
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
    onSuccess: (data: AssignmentInput) => Promise<void>
}) {
    const [orgUnits, setOrgUnits] = useState<FlattenedUnit[]>([]);
    const [positions, setPositions] = useState<Position[]>([]);
    const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const form = useForm<AssignmentInput>({resolver: zodResolver(assignmentSchema), defaultValues: {status: "ACTIVE"}});

    const loadOrgTree = async () => {
        try {
            const orgRes = await api.get<{ id: string }[]>("/organization/list");
            const orgId = orgRes.data[0]?.id;
            if (!orgId) throw new Error("Tashkilot topilmadi");
            const treeRes = await api.get<{ tree: OrgUnitNode[] }>(`/organization/units/tree/${orgId}`);
            setOrgUnits(flattenUnits(treeRes.data.tree || []));
        } catch (e) {
            toast.error("Bo'limlar yuklanmadi");
        }
    };

    const loadPositions = async (unitId: string) => {
        try {
            const res = await api.get<Position[]>(`/organization/positions/by-unit/${unitId}`);
            setPositions(res.data || []);
            form.setValue("position_id", "");
        } catch (e) {
            setPositions([]);
            toast.error("Lavozimlar yuklanmadi");
        }
    };

    useEffect(() => {
        if (isOpen) {
            loadOrgTree();
            form.reset({status: "ACTIVE"});
            setSelectedUnitId(null);
            setPositions([]);
        }
    }, [isOpen, form]);

    const handleUnitChange = (unitId: string) => {
        setSelectedUnitId(unitId);
        loadPositions(unitId);
    };

    const onSubmit = async (data: AssignmentInput) => {
        if (!user) return;
        setIsLoading(true);
        try {
            await onSuccess(data);
            onClose();
        } catch (e) {
            // Error is handled in the parent
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
                                            <SelectItem value="no-position" disabled>
                                                Lavozimlar topilmadi
                                            </SelectItem>
                                        )}
                                    </SelectContent>
                                </Select>
                                {form.formState.errors.position_id && (
                                    <p className="text-red-500 text-sm mt-1">{form.formState.errors.position_id.message}</p>
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
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const [limit] = useState(50);

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isUpdateOpen, setIsUpdateOpen] = useState(false);
    const [isAssignmentOpen, setIsAssignmentOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);

    // Debounced search
    const debouncedSearch = useDebounce(search, 300);

    // React Query hooks
    const {data: usersData, isLoading, error} = useUsers(debouncedSearch, page, limit);
    const userActions = useUserActions();

    // Init
    useEffect(() => {
        const init = async () => {
            const info = await fetchMe();
            if (!info) return (window.location.href = "/auth/login");
            if (!info.is_superadmin) return (window.location.href = info.redirect_path || "/");
            setMe(info);
        };
        init();
    }, []);

    const users = usersData?.data || [];
    const total = usersData?.total || 0;
    const totalPages = Math.ceil(total / limit);

    const handleEdit = (user: User) => {
        setSelectedUser(user);
        setIsUpdateOpen(true);
    };

    const handleAssign = (user: User) => {
        setSelectedUser(user);
        setIsAssignmentOpen(true);
    };

    const handleUnassign = async (user: User) => {
        if (!user.position_title) {
            toast.info("Bu foydalanuvchi allaqachon lavozimsiz");
            return;
        }

        const ok = window.confirm(
            `${user.full_name || user.username} lavozimdan to'liq ozod etilsinmi?`
        );
        if (!ok) return;

        try {
            await userActions.unassignUser(user.id);
        } catch (e: any) {
            toast.error(e.message || "Xatolik yuz berdi");
        }
    };

    const handleCreateUser = async (data: CreateUserInput) => {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => value && formData.append(key, value));
        await userActions.createUser(formData);
    };

    const handleUpdateUser = async (data: UpdateUserInput) => {
        if (!selectedUser) return;
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== (selectedUser as any)[key]) {
                formData.append(key, value);
            }
        });
        await userActions.updateUser({userId: selectedUser.id, userData: formData});
    };

    const handleAssignUser = async (data: AssignmentInput) => {
        if (!selectedUser) return;
        const formData = new FormData();
        formData.append("user_id", selectedUser.id);
        formData.append("position_id", data.position_id);
        formData.append("status", data.status);
        if (data.valid_from) formData.append("valid_from", data.valid_from);
        if (data.valid_to) formData.append("valid_to", data.valid_to);
        await userActions.assignUser(formData);
    };

    if (!me) return null;

    if (error) {
        return (
            <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
                <div className="text-center py-8">
                    <p className="text-red-500 text-lg">Xatolik yuz berdi. Iltimos, sahifani qayta yuklang.</p>
                </div>
            </div>
        );
    }

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
                    <CardTitle>Jami: {users.length} / {total}</CardTitle>
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

                    {isLoading && users.length === 0 ? (
                        <div className="h-[600px] flex items-center justify-center">
                            <div className="text-center">
                                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
                                <p className="mt-2 text-gray-500">Yuklanmoqda...</p>
                            </div>
                        </div>
                    ) : (
                        <VirtualizedUserTable
                            users={users}
                            onEdit={handleEdit}
                            onAssign={handleAssign}
                            onUnassign={handleUnassign}
                            isUnassigning={userActions.isUnassigning}
                        />
                    )}

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex justify-center items-center gap-2 mt-4">
                            <Button
                                variant="outline"
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                            >
                                Oldingi
                            </Button>
                            <span className="text-sm text-gray-600">
                                Sahifa {page} / {totalPages}
                            </span>
                            <Button
                                variant="outline"
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                            >
                                Keyingi
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            <UserCreateModal 
                isOpen={isCreateOpen} 
                onClose={() => setIsCreateOpen(false)} 
                onSuccess={handleCreateUser}
            />
            <UserEditModal
                isOpen={isUpdateOpen}
                onClose={() => setIsUpdateOpen(false)}
                user={selectedUser}
                onSuccess={handleUpdateUser}
            />
            <UserAssignmentModal
                isOpen={isAssignmentOpen}
                onClose={() => {
                    setIsAssignmentOpen(false);
                    setSelectedUser(null);
                }}
                user={selectedUser}
                onSuccess={handleAssignUser}
            />
        </div>
    );
}
