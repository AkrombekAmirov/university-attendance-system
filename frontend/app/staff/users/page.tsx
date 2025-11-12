"use client";

import { useEffect, useState } from "react";
import { fetchMyTree, fetchUnitDaily } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Users, FolderTree, Clock } from "lucide-react";
import dayjs from "dayjs";

type Step = "root" | "unit" | "staff";

export default function StaffUsersPage() {
    const [tree, setTree] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [step, setStep] = useState<Step>("root");

    const [selectedNode, setSelectedNode] = useState<any | null>(null);
    const [daily, setDaily] = useState<any[]>([]);
    const [loadingDaily, setLoadingDaily] = useState(false);

    useEffect(() => {
        (async () => {
            const data = await fetchMyTree();
            setTree(data);

            const rootUnit = data.units?.[0];
            const hasChildUnits = rootUnit?.children?.length > 0;

            if (!hasChildUnits) {
                setSelectedNode(rootUnit);
                loadDaily(rootUnit.id);
                setStep("staff");
            }

            setLoading(false);
        })();
    }, []);

    async function loadDaily(unitId: string) {
        setLoadingDaily(true);
        const today = dayjs().format("YYYY-MM-DD");
        const data = await fetchUnitDaily(unitId, today);
        setDaily(data);
        setLoadingDaily(false);
    }

    function openNode(node: any) {
        setSelectedNode(node);

        if (node.children?.length > 0) {
            setStep("unit");
        } else {
            setStep("staff");
            loadDaily(node.id);
        }
    }

    function reset() {
        setStep("root");
        setSelectedNode(null);
        setDaily([]);
    }

    if (loading) return <p className="text-gray-500">Yuklanmoqda...</p>;

    const root = tree.units?.[0];
    const firstLevel = root?.children || [];

    const statusColor = (item: any) => {
        if (!item.first_entry) return "bg-red-200 text-red-800";
        return "bg-green-200 text-green-800";
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-3">
                {step !== "root" && (
                    <Button onClick={reset} variant="ghost" className="gap-2">
                        <ArrowLeft size={18} /> Orqaga
                    </Button>
                )}
                <h2 className="text-xl font-bold flex gap-2"><FolderTree /> Xodimlar tuzilmasi</h2>
            </div>

            {/* STEP: ROOT */}
            {step === "root" && (
                <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
                    {firstLevel.map((n: any) => (
                        <Card key={n.id} onClick={() => openNode(n)} className="hover:bg-accent cursor-pointer transition">
                            <CardHeader><CardTitle>{n.name}</CardTitle></CardHeader>
                        </Card>
                    ))}
                </div>
            )}

            {/* STEP: UNIT */}
            {step === "unit" && selectedNode && (
                <>
                    <h3 className="font-semibold text-lg mb-2">{selectedNode.name} → Bo‘limlar</h3>
                    <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
                        {selectedNode.children?.map((c: any) => (
                            <Card key={c.id} onClick={() => openNode(c)} className="hover:bg-green-50 cursor-pointer">
                                <CardHeader><CardTitle>{c.name}</CardTitle></CardHeader>
                            </Card>
                        ))}
                    </div>
                </>
            )}

            {/* STEP: DAILY STAFF */}
            {step === "staff" && selectedNode && (
                <>
                    <h3 className="font-semibold text-lg mb-3 flex gap-2">
                        <Users /> {selectedNode.name} — Bugungi davomat
                    </h3>

                    {loadingDaily && <p className="text-gray-500">Davomat yuklanmoqda...</p>}

                    {!loadingDaily && (
                        <div className="rounded-lg overflow-hidden border">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-100 border-b">
                                <tr>
                                    <th className="p-2 text-left">F.I.Sh</th>
                                    <th className="p-2 text-left">Lavozim</th>
                                    <th className="p-2 text-center"><Clock size={14} /> Kirish</th>
                                    <th className="p-2 text-center"><Clock size={14} /> Chiqish</th>
                                </tr>
                                </thead>
                                <tbody>
                                {daily.map((item) => (
                                    <tr key={item.user_id} className="border-b">
                                        <td className="p-2">{item.full_name}</td>
                                        <td className="p-2">{item.position}</td>
                                        <td className={`p-2 text-center font-semibold ${statusColor(item)}`}>
                                            {item.first_entry ? dayjs(item.first_entry).format("HH:mm") : "KELMADI"}
                                        </td>
                                        <td className="p-2 text-center">
                                            {item.last_exit ? dayjs(item.last_exit).format("HH:mm") : "-"}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
