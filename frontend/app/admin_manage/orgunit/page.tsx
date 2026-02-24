"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, ChevronRight, Building2 } from "lucide-react";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import {
    createOrgUnit,
    getOrgUnitTree,
    getOrganizationId,
} from "@/lib/organization/orgunit";

type OrgUnitNode = {
    id: string;
    name: string;
    unit_type: string;
    children?: OrgUnitNode[];
};

function flattenTree(nodes: OrgUnitNode[], prefix = ""): { id: string; label: string }[] {
    let result: { id: string; label: string }[] = [];
    for (const node of nodes) {
        result.push({ id: node.id, label: `${prefix}${node.name} (${node.unit_type})` });
        if (node.children?.length) {
            result = result.concat(flattenTree(node.children, prefix + "— "));
        }
    }
    return result;
}

function parseError(e: any): string {
    const data = e?.response?.data ?? e?.data ?? e;
    if (data?.detail) {
        if (typeof data.detail === "string") return data.detail;
        if (Array.isArray(data.detail))
            return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
        return JSON.stringify(data.detail);
    }
    return "Xatolik yuz berdi, iltimos qayta urinib ko‘ring.";
}

// 🧩 Modern Recursive Unit Card
function UnitCard({ node, depth = 0 }: { node: OrgUnitNode; depth?: number }) {
    const [expanded, setExpanded] = useState(false);
    const hasChildren = !!node.children?.length;

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-white to-slate-50 dark:from-slate-900 dark:to-slate-800 shadow-sm hover:shadow-md transition-all p-4 ${
                depth > 0 ? "ml-6 mt-3" : "mt-2"
            }`}
        >
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                        <Building2 className="text-emerald-600 dark:text-emerald-300" size={18} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-slate-900 dark:text-white">{node.name}</h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400">{node.unit_type}</p>
                    </div>
                </div>

                {hasChildren && (
                    <motion.div
                        animate={{ rotate: expanded ? 90 : 0 }}
                        transition={{ duration: 0.25 }}
                        className="text-slate-400"
                    >
                        <ChevronRight size={18} />
                    </motion.div>
                )}
            </div>

            {hasChildren && (
                <AnimatePresence>
                    {expanded && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                            className="mt-3 space-y-2"
                        >
                            {node.children!.map((child) => (
                                <UnitCard key={child.id} node={child} depth={depth + 1} />
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            )}
        </motion.div>
    );
}

// 🌿 Modal for new OrgUnit creation
function OrgUnitModal({
                          isOpen,
                          onClose,
                          onCreated,
                          orgId,
                          flatUnits,
                      }: {
    isOpen: boolean;
    onClose: () => void;
    onCreated: () => void;
    orgId: string | null;
    flatUnits: { id: string; label: string }[];
}) {
    const [name, setName] = useState("");
    const [unitType, setUnitType] = useState("");
    const [parentId, setParentId] = useState("root");
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleCreate = async () => {
        if (!orgId || !unitType || !name.trim()) {
            setError("Barcha maydonlarni to‘ldiring");
            return;
        }
        setBusy(true);
        setError(null);
        try {
            const formData = new FormData();
            formData.append("organization_id", orgId);
            formData.append("name", name.trim());
            formData.append("unit_type", unitType);
            if (parentId !== "root") formData.append("parent_id", parentId);

            await createOrgUnit(formData);
            setNotice("✅ Bo‘linma yaratildi!");
            setTimeout(() => {
                onCreated();
                onClose();
            }, 900);
        } catch (e: any) {
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
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                    >
                        <Card className="w-full max-w-md shadow-2xl border-0 bg-gradient-to-br from-white to-emerald-50 dark:from-slate-900 dark:to-emerald-950">
                            <CardHeader className="bg-gradient-to-r from-emerald-500 to-blue-500 text-white rounded-t-lg pb-5">
                                <div className="flex justify-between items-center">
                                    <CardTitle className="text-2xl font-semibold">Yangi bo‘linma</CardTitle>
                                    <button onClick={onClose} className="hover:bg-white/20 rounded-lg p-1">
                                        <X size={20} />
                                    </button>
                                </div>
                            </CardHeader>
                            <CardContent className="pt-5 space-y-4">
                                {notice && (
                                    <div className="p-3 bg-emerald-50 text-emerald-700 rounded-lg text-sm">
                                        {notice}
                                    </div>
                                )}
                                {error && (
                                    <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
                                )}

                                <div>
                                    <Label>Bo‘linma nomi</Label>
                                    <Input
                                        placeholder="Masalan: Rektor"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                </div>

                                <div>
                                    <Label>Bo‘linma turi</Label>
                                    <Select value={unitType} onValueChange={setUnitType}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Tanlang" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="RECTORATE">Rektorat</SelectItem>
                                            <SelectItem value="PROREKTOR">Prorektor</SelectItem>
                                            <SelectItem value="FAKULTET">Fakultet</SelectItem>
                                            <SelectItem value="KAFEDRA">Kafedra</SelectItem>
                                            <SelectItem value="MARKAZ">Markaz</SelectItem>
                                            <SelectItem value="BO‘LIM">Bo‘lim</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div>
                                    <Label>Qaysi bo‘linmaga biriktiriladi?</Label>
                                    <Select value={parentId} onValueChange={setParentId}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Tanlang" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="root">Asosiy (ildiz) bo‘linma</SelectItem>
                                            {flatUnits.map((unit) => (
                                                <SelectItem key={unit.id} value={unit.id}>
                                                    {unit.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="flex gap-3 pt-3">
                                    <Button variant="outline" onClick={onClose} className="flex-1">
                                        Bekor qilish
                                    </Button>
                                    <Button
                                        onClick={handleCreate}
                                        disabled={busy}
                                        className="flex-1 bg-gradient-to-r from-emerald-500 to-blue-500 text-white"
                                    >
                                        {busy ? "Yaratilmoqda..." : "Yaratish"}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

export default function OrgUnitPage() {
    const [orgId, setOrgId] = useState<string | null>(null);
    const [units, setUnits] = useState<OrgUnitNode[]>([]);
    const [flatUnits, setFlatUnits] = useState<{ id: string; label: string }[]>([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);

    const fetchData = async () => {
        try {
            setLoading(true);
            const id = await getOrganizationId();
            setOrgId(id);
<<<<<<< HEAD

=======
            
>>>>>>> bcc8fb49ad3a69160c569756b6e944ba3662a768
            if (id) {
                const tree = await getOrgUnitTree(id);
                setUnits(tree);
                setFlatUnits(flattenTree(tree));
            } else {
                console.warn("Organization ID not found");
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

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
                        Bo‘linmalar
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                        Tashkilot tuzilmasini qulay va zamonaviy tarzda ko‘rish
                    </p>
                </div>

                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setModalOpen(true)}
                    className="flex items-center gap-2 px-6 py-3 rounded-lg shadow-lg text-white font-semibold bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-600 hover:to-blue-600"
                >
                    <Plus size={20} />
                    Yangi bo‘linma
                </motion.button>
            </motion.div>

            {/* Main Content */}
            <Card className="shadow-lg border-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
                <CardHeader className="border-b border-slate-200 dark:border-slate-800">
                    <CardTitle className="text-xl font-semibold">
                        Jami: {flatUnits.length} ta bo‘linma
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                    {loading ? (
                        <div className="text-center py-10 text-slate-500">⏳ Yuklanmoqda...</div>
                    ) : units.length === 0 ? (
                        <div className="text-center py-10 text-slate-500">Hozircha bo‘linma mavjud emas</div>
                    ) : (
                        <div className="space-y-3">
                            {units.map((u) => (
                                <UnitCard key={u.id} node={u} />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            <OrgUnitModal
                isOpen={modalOpen}
                onClose={() => setModalOpen(false)}
                onCreated={fetchData}
                orgId={orgId}
                flatUnits={flatUnits}
            />
        </div>
    );
}
