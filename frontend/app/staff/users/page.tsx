"use client";

import {useEffect, useState} from "react";
import {fetchMyTree, fetchUnitDaily} from "@/lib/api";
import {Card, CardHeader, CardTitle} from "@/components/ui/card";
import {Button} from "@/components/ui/button";

import {
    ArrowLeft,
    Users,
    FolderTree,
    Clock,
    Calendar
} from "lucide-react";

import dayjs from "dayjs";
import {motion, AnimatePresence} from "framer-motion";
import {useRouter} from "next/navigation";

type Step = "root" | "unit" | "staff";

export default function StaffUsersPage() {
    const router = useRouter();

    const [tree, setTree] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [step, setStep] = useState<Step>("root");

    const [selectedNode, setSelectedNode] = useState<any | null>(null);
    const [daily, setDaily] = useState<any[]>([]);
    const [loadingDaily, setLoadingDaily] = useState(false);

    const [selectedDate, setSelectedDate] = useState(dayjs().format("YYYY-MM-DD"));
    const [isBottomUnit, setIsBottomUnit] = useState(false);
    const [nodeStack, setNodeStack] = useState<any[]>([]);


    /* ===================== INITIAL LOAD ===================== */
    useEffect(() => {
        (async () => {
            const data = await fetchMyTree();
            setTree(data);

            const rootUnit = data.units?.[0];
            const hasChildUnits = rootUnit?.children?.length > 0;

            if (!hasChildUnits && rootUnit) {
                setIsBottomUnit(true);
                setSelectedNode(rootUnit);
                loadDaily(rootUnit.id, selectedDate);
                setStep("staff");
            } else {
                setIsBottomUnit(false);
            }

            setLoading(false);
        })();
    }, []);

    /* ===================== LOAD DAILY ===================== */
    async function loadDaily(unitId: string, dateStr: string) {
        setLoadingDaily(true);
        const data = await fetchUnitDaily(unitId, dateStr);
        setDaily(data);
        setLoadingDaily(false);
    }

    function openNode(node: any) {
        if (selectedNode) {
            setNodeStack((prev) => [...prev, selectedNode]);
        }

        setSelectedNode(node);

        if (node.children?.length > 0) {
            setStep("unit");
        } else {
            setStep("staff");
            loadDaily(node.id, selectedDate);
        }
    }


    function reset() {
        setStep("root");
        setSelectedNode(null);
        setDaily([]);
    }

    function goBack() {
        setDaily([]);

        setNodeStack((prev) => {
            if (prev.length === 0) {
                // Root darajaga qaytdik
                setSelectedNode(null);
                setStep("root");
                return [];
            }

            const newStack = [...prev];
            const parent = newStack.pop();

            setSelectedNode(parent);

            if (parent.children?.length > 0) {
                setStep("unit");
            } else {
                setStep("staff");
                loadDaily(parent.id, selectedDate);
            }

            return newStack;
        });
    }


    function getSafeExitTime(
        firstEntry?: string | null,
        lastExit?: string | null,
        minMinutes = 60
    ): string | null {
        if (!firstEntry || !lastExit) return null;

        const entry = dayjs(firstEntry);
        const exit = dayjs(lastExit);

        // Agar vaqt noto‘g‘ri bo‘lsa
        if (!entry.isValid() || !exit.isValid()) return null;

        const diffMinutes = exit.diff(entry, "minute");

        // 60 minutdan kam bo‘lsa – chiqishni YASHIRAMIZ
        if (diffMinutes < minMinutes) return null;

        return exit.format("HH:mm");
    }


    function statusColor(item: any) {
        if (!item.first_entry) return "bg-red-100 text-red-700 border-red-200";
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
    }

    if (loading)
        return (
            <motion.div
                initial={{opacity: 0}}
                animate={{opacity: 1}}
                className="text-center text-gray-500 py-10 animate-pulse"
            >
                Yuklanmoqda...
            </motion.div>
        );

    const root = tree.units?.[0];
    const firstLevel = root?.children || [];

    /* ====================== PAGE =========================== */

    return (
        <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            transition={{duration: 0.6, ease: "easeOut"}}
            className="
                space-y-6 p-4
                bg-gradient-to-br from-indigo-50 via-white to-blue-50
                min-h-screen
                backdrop-blur-xl
            "
        >

            {/* HEADER */}
            <motion.div
                initial={{y: -20, opacity: 0}}
                animate={{y: 0, opacity: 1}}
                transition={{duration: 0.5}}
                className="
                    sticky top-0 z-20
                    flex items-center justify-between
                    p-4 rounded-xl shadow
                    bg-white/60 backdrop-blur-xl border border-white/40
                "
            >
                <div className="flex items-center gap-3">
                    {step !== "root" && !isBottomUnit && (
                        <motion.div whileTap={{scale: 0.95}}>
                            <Button
                                onClick={goBack}
                                variant="ghost"
                                className="
                                    gap-2 rounded-xl
                                    hover:bg-indigo-100 hover:text-indigo-900
                                "
                            >
                                <ArrowLeft size={18}/>
                                Orqaga
                            </Button>
                        </motion.div>
                    )}

                    <h2
                        className="
                            text-2xl font-bold bg-gradient-to-r
                            from-indigo-600 to-blue-600
                            bg-clip-text text-transparent
                            flex gap-2
                        "
                    >
                        <FolderTree/> Xodimlar tuzilmasi
                    </h2>
                </div>
            </motion.div>

            {/* ===================== ROOT ===================== */}
            <AnimatePresence mode="wait">
                {step === "root" && (
                    <motion.div
                        key="root"
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: -20}}
                        transition={{duration: 0.4}}
                        className="grid gap-5 grid-cols-1 md:grid-cols-2"
                    >
                        {firstLevel.map((n: any) => (
                            <motion.div
                                key={n.id}
                                whileHover={{scale: 1.02, y: -4}}
                                transition={{type: "spring", stiffness: 120}}
                            >
                                <Card
                                    onClick={() => openNode(n)}
                                    className="
                                        cursor-pointer
                                        bg-white/70 backdrop-blur-md
                                        border border-white/40
                                        rounded-2xl shadow
                                        transition-all
                                    "
                                >
                                    <CardHeader>
                                        <CardTitle className="text-lg font-semibold">
                                            {n.name}
                                        </CardTitle>
                                    </CardHeader>
                                </Card>
                            </motion.div>
                        ))}
                    </motion.div>
                )}

                {/* ===================== UNIT ===================== */}
                {step === "unit" && selectedNode && (
                    <motion.div
                        key="unit"
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: -20}}
                        transition={{duration: 0.4}}
                        className="space-y-3"
                    >
                        <h3 className="text-xl font-semibold text-slate-700">
                            {selectedNode.name} →
                            <span className="text-indigo-600"> Bo‘limlar</span>
                        </h3>

                        <div className="grid gap-5 grid-cols-1 md:grid-cols-2">
                            {selectedNode.children?.map((c: any) => (
                                <motion.div
                                    key={c.id}
                                    whileHover={{scale: 1.02, y: -4}}
                                    transition={{type: "spring", stiffness: 120}}
                                >
                                    <Card
                                        onClick={() => openNode(c)}
                                        className="
                                            cursor-pointer bg-white/70
                                            border border-white/40 backdrop-blur-md
                                            rounded-2xl p-2 shadow-sm
                                            hover:bg-emerald-50/70
                                            transition-all
                                        "
                                    >
                                        <CardHeader>
                                            <CardTitle className="text-lg text-slate-800">
                                                {c.name}
                                            </CardTitle>
                                        </CardHeader>
                                    </Card>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* ===================== STAFF ===================== */}
                {step === "staff" && selectedNode && (
                    <motion.div
                        key="staff"
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: -20}}
                        transition={{duration: 0.4}}
                        className="space-y-6"
                    >

                        {/* Title + Calendar + MONTHLY BUTTON */}
                        <motion.div
                            initial={{opacity: 0, y: 10}}
                            animate={{opacity: 1, y: 0}}
                            transition={{duration: 0.5}}
                            className="
                                flex flex-col md:flex-row justify-between items-start md:items-center
                                gap-4 bg-white/60 p-4 rounded-xl shadow border border-white/40 backdrop-blur
                            "
                        >
                            <h3 className="text-xl font-semibold text-slate-800 flex gap-2">
                                <Users className="text-indigo-600"/>
                                {selectedNode.name} —
                                <span className="text-indigo-700">Davomat</span>
                            </h3>

                            <div className="flex items-center gap-3">
                                {/* Oylik ko‘rish tugmasi */}
                                <Button
                                    onClick={() =>
                                        router.push(
                                            `/staff/users/monthly?unit_id=${selectedNode.id}`
                                        )
                                    }
                                    className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg shadow"
                                >
                                    🗓 Oylik ko‘rish
                                </Button>

                                {/* Date input */}
                                <div className="flex items-center gap-3 text-slate-700">
                                    <Calendar size={22} className="text-indigo-600"/>
                                    <input
                                        type="date"
                                        value={selectedDate}
                                        onChange={(e) => {
                                            const newDate = e.target.value;
                                            setSelectedDate(newDate);
                                            loadDaily(selectedNode.id, newDate);
                                        }}
                                        className="
                                            px-3 py-2 rounded-lg border
                                            shadow-sm bg-white/70
                                            focus:ring-2 focus:ring-indigo-400
                                            transition
                                        "
                                    />
                                </div>
                            </div>
                        </motion.div>

                        {/* TABLE */}
                        <motion.div
                            initial={{opacity: 0, y: 10}}
                            animate={{opacity: 1, y: 0}}
                            transition={{duration: 0.5, delay: 0.15}}
                            className="
                                overflow-hidden rounded-2xl shadow-xl
                                bg-white/70 backdrop-blur border border-white/40
                            "
                        >
                            <table className="w-full text-sm">
                                <thead
                                    className="
                                        bg-gradient-to-r from-indigo-100 to-blue-100
                                        border-b text-slate-700
                                    "
                                >
                                <tr>
                                    <th className="p-3 text-center w-12">№</th>
                                    <th className="p-3 text-left">F.I.Sh</th>
                                    <th className="p-3 text-left">Lavozim</th>
                                    <th className="p-3 text-center">
                                        <Clock size={14}/> Kirish
                                    </th>
                                    <th className="p-3 text-center">Kirish turniketi</th>
                                    <th className="p-3 text-center">
                                        <Clock size={14}/> Chiqish
                                    </th>
                                    <th className="p-3 text-center">Chiqish turniketi</th>
                                </tr>
                                </thead>

                                <tbody>
                                {daily.map((item, idx) => (
                                    <motion.tr
                                        key={item.user_id}
                                        initial={{opacity: 0}}
                                        animate={{opacity: 1}}
                                        transition={{duration: 0.3, delay: idx * 0.03}}
                                        className={`
                                                border-b 
                                                ${
                                            idx % 2 === 0
                                                ? "bg-white/80"
                                                : "bg-indigo-50/40"
                                        }
                                                transition hover:bg-indigo-100/60
                                            `}
                                    >
                                        <td className="p-3 text-center font-semibold text-gray-600">
                                            {idx + 1}
                                        </td>

                                        <td className="p-3">
                                            {item.full_name}
                                        </td>

                                        <td className="p-3">{item.position}</td>

                                        <td
                                            className={`
                                                    p-3 text-center font-semibold border 
                                                    rounded-lg ${statusColor(item)}
                                                `}
                                        >
                                            {item.first_entry
                                                ? dayjs(item.first_entry).format("HH:mm")
                                                : "KELMADI"}
                                        </td>

                                        <td className="p-3 text-center text-indigo-700 font-medium">
                                            {item.first_device || "-"}
                                        </td>

                                        <td className="p-3 text-center font-medium">
                                            {getSafeExitTime(item.first_entry, item.last_exit) ?? "-"}
                                        </td>


                                        <td className="p-3 text-center text-indigo-700 font-medium">
                                            {getSafeExitTime(item.first_entry, item.last_exit)
                                                ? item.last_device || "-"
                                                : "-"}
                                        </td>
                                    </motion.tr>
                                ))}
                                </tbody>
                            </table>
                        </motion.div>

                    </motion.div>
                )}
            </AnimatePresence>

        </motion.div>
    );
}
