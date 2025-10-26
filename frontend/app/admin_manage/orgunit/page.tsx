"use client";

import { useEffect, useState } from "react";
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
import {
    createOrgUnit,
    getOrgUnitTree,
    getOrganizationId,
} from "@/lib/organization/orgunit";

function flattenTree(
    nodes: any[],
    prefix = ""
): { id: string; label: string }[] {
    let result: { id: string; label: string }[] = [];

    for (const node of nodes) {
        result.push({
            id: node.id,
            label: `${prefix}${node.name} (${node.unit_type})`,
        });

        if (node.children && node.children.length > 0) {
            const children = flattenTree(node.children, prefix + "— ");
            result = result.concat(children);
        }
    }

    return result;
}

export default function OrgUnitPage() {
    const [orgId, setOrgId] = useState<string | null>(null);
    const [flatUnits, setFlatUnits] = useState<{ id: string; label: string }[]>(
        []
    );
    const [name, setName] = useState("");
    const [unitType, setUnitType] = useState("");
    const [parentId, setParentId] = useState("root");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const init = async () => {
            try {
                const id = await getOrganizationId();
                if (!id) {
                    alert("Tashkilot topilmadi");
                    return;
                }
                setOrgId(id);
                const tree = await getOrgUnitTree(id);
                const flat = flattenTree(tree);
                setFlatUnits(flat);
            } catch (e) {
                console.error("Init error:", e);
            }
        };
        init();
    }, []);

    const handleSubmit = async () => {
        if (!orgId || !unitType || !name.trim()) {
            alert("Barcha maydonlarni to‘ldiring");
            return;
        }

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("organization_id", orgId);
            formData.append("name", name);
            formData.append("unit_type", unitType);
            if (parentId !== "root") formData.append("parent_id", parentId);

            await createOrgUnit(formData);
            alert("✅ Bo‘linma yaratildi!");
            setName("");
            setUnitType("");
            setParentId("root");
        } catch (err: any) {
            console.error(err);
            alert("❌ Xatolik: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-xl mx-auto p-6 space-y-6">
            <h2 className="text-xl font-bold">Yangi bo‘linma yaratish</h2>

            <div className="space-y-4">
                <div>
                    <Label>Bo‘linma nomi</Label>
                    <Input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Masalan: Rektor"
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
                    <Select
                        value={parentId}
                        onValueChange={(val) => setParentId(val)}
                    >
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

                <Button onClick={handleSubmit} disabled={loading}>
                    {loading ? "Yaratilmoqda..." : "Bo‘linmani yaratish"}
                </Button>
            </div>
        </div>
    );
}
