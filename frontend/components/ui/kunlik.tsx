// app/staff/users/page.tsx
"use client";

import { useEffect, useState } from "react";
import { fetchMyTree, fetchUnitDaily } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Users, FolderTree, Clock, Calendar, ChevronRight, CheckCircle2, AlertCircle, TrendingUp } from 'lucide-react';
import dayjs from "dayjs";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from 'next/navigation';

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

    // <CHANGE> Enhanced status styling with gradient colors
    function getStatusStyles(item: any) {
        if (!item.first_entry) {
            return {
                badge: "bg-gradient-to-br from-red-400 to-rose-500 text-white border border-red-600/50",
                icon: <AlertCircle size={16} className="text-white" />,
                text: "Kelmadi",
                label: "—"
            };
        }
        return {
            badge: "bg-gradient-to-br from-emerald-400 to-teal-500 text-white border border-emerald-600/50",
            icon: <CheckCircle2 size={16} className="text-white" />,
            text: dayjs(item.first_entry).format("HH:mm"),
            label: dayjs(item.first_entry).format("HH:mm")
        };
    }

    // <CHANGE> Calculate daily statistics
    function getDailyStats() {
        const total = daily.length;
        let present = 0;
        daily.forEach(item => {
            if (item.first_entry) present++;
        });
        return {
            total,
            present,
            absent: total - present,
            percentage: total > 0 ? Math.round((present / total) * 100) : 0
        };
    }

    if (loading)
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900/50 to-slate-900 flex items-center justify-center"
            >
                <div className="text-center space-y-4">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400">
                        <div className="w-8 h-8 border-3 border-slate-900 border-t-emerald-300 rounded-full animate-spin"></div>
                    </div>
                    <p className="text-emerald-300 font-semibold">Ma'lumotlar yuklanmoqda...</p>
                </div>
            </motion.div>
        );

    const root = tree.units?.[0];
    const firstLevel = root?.children || [];
    const stats = getDailyStats();

    /* ====================== PAGE =========================== */

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900/40 to-slate-900 px-4 md:px-8 py-8 space-y-6"
        >

            {/* HEADER */}
            <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="sticky top-0 z-20 bg-gradient-to-r from-slate-900/95 via-emerald-900/95 to-slate-900/95 backdrop-blur-xl border border-emerald-500/20 rounded-2xl shadow-2xl p-6"
            >
                <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-4 flex-1">
                        {step !== "root" && !isBottomUnit && (
                            <motion.div whileTap={{ scale: 0.95 }}>
                                <Button
                                    onClick={reset}
                                    className="gap-2 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-semibold shadow-lg"
                                >
                                    <ArrowLeft size={18} />
                                    Orqaga
                                </Button>
                            </motion.div>
                        )}

                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-gradient-to-br from-emerald-400 to-cyan-400 rounded-lg">
                                <FolderTree size={20} className="text-slate-900" />
                            </div>
                            <div>
                                <h1 className="text-2xl md:text-3xl font-black bg-gradient-to-r from-emerald-200 via-cyan-200 to-emerald-200 bg-clip-text text-transparent">
                                    Kunlik Davomat
                                </h1>
                                <p className="text-emerald-300 font-medium text-sm">
                                    {step === "root"
                                        ? "Tuzilmani tanlang"
                                        : step === "unit"
                                            ? `${selectedNode?.name} — Bo'limlar`
                                            : `${selectedNode?.name} — Davomat`}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* ===================== ROOT ===================== */}
            <AnimatePresence mode="wait">
                {step === "root" && (
                    <motion.div
                        key="root"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.4 }}
                        className="grid gap-5 grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                    >
                        {firstLevel.map((n: any, idx: number) => (
                            <motion.div
                                key={n.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.4, delay: idx * 0.1 }}
                                whileHover={{ y: -4 }}
                            >
                                <Card
                                    onClick={() => openNode(n)}
                                    className="cursor-pointer bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-emerald-500/20 backdrop-blur-md rounded-2xl hover:border-emerald-400/50 transition-all hover:shadow-xl group"
                                >
                                    <CardHeader className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <div className="p-3 bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 group-hover:from-emerald-500/40 group-hover:to-cyan-500/40 rounded-xl transition-colors">
                                                <FolderTree size={24} className="text-emerald-400" />
                                            </div>
                                            <ChevronRight size={20} className="text-emerald-300/50 group-hover:text-emerald-300 transition-colors" />
                                        </div>
                                        <CardTitle className="text-emerald-100 group-hover:text-white transition-colors">
                                            {n.name}
                                        </CardTitle>
                                        <p className="text-xs text-emerald-300/70 font-medium">
                                            {n.children?.length || 0} bo'lim
                                        </p>
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
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.4 }}
                        className="space-y-6"
                    >
                        <div className="bg-gradient-to-r from-slate-800/80 to-slate-900/80 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6">
                            <h2 className="text-2xl font-bold bg-gradient-to-r from-emerald-200 to-cyan-200 bg-clip-text text-transparent mb-2">
                                {selectedNode.name}
                            </h2>
                            <p className="text-emerald-300/70 font-medium">
                                {selectedNode.children?.length || 0} bo'limlar mavjud
                            </p>
                        </div>

                        <div className="grid gap-5 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                            {selectedNode.children?.map((c: any, idx: number) => (
                                <motion.div
                                    key={c.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.4, delay: idx * 0.1 }}
                                    whileHover={{ y: -4 }}
                                >
                                    <Card
                                        onClick={() => openNode(c)}
                                        className="cursor-pointer bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-cyan-500/20 backdrop-blur-md rounded-2xl hover:border-cyan-400/50 transition-all hover:shadow-xl group"
                                    >
                                        <CardHeader className="space-y-3">
                                            <div className="flex items-center justify-between">
                                                <div className="p-3 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 group-hover:from-cyan-500/40 group-hover:to-blue-500/40 rounded-xl transition-colors">
                                                    <Users size={24} className="text-cyan-400" />
                                                </div>
                                                <ChevronRight size={20} className="text-cyan-300/50 group-hover:text-cyan-300 transition-colors" />
                                            </div>
                                            <CardTitle className="text-emerald-100 group-hover:text-white transition-colors">
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
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.4 }}
                        className="space-y-6"
                    >

                        {/* <CHANGE> Premium stats cards section */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.1 }}
                                className="bg-gradient-to-br from-emerald-500/20 to-teal-600/20 border border-emerald-400/40 rounded-xl p-4 backdrop-blur-md hover:border-emerald-300/60 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-emerald-200 text-xs font-medium">Jami Xodimlar</p>
                                        <p className="text-2xl font-bold text-emerald-100 mt-1">{stats.total}</p>
                                    </div>
                                    <div className="p-2 bg-emerald-400/20 rounded-lg">
                                        <Users size={20} className="text-emerald-300" />
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.2 }}
                                className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 border border-green-400/40 rounded-xl p-4 backdrop-blur-md hover:border-green-300/60 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-green-200 text-xs font-medium">Kelganlar</p>
                                        <p className="text-2xl font-bold text-green-100 mt-1">{stats.present}</p>
                                    </div>
                                    <div className="p-2 bg-green-400/20 rounded-lg">
                                        <CheckCircle2 size={20} className="text-green-300" />
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.3 }}
                                className="bg-gradient-to-br from-red-500/20 to-rose-600/20 border border-red-400/40 rounded-xl p-4 backdrop-blur-md hover:border-red-300/60 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-red-200 text-xs font-medium">Kelmaganlar</p>
                                        <p className="text-2xl font-bold text-red-100 mt-1">{stats.absent}</p>
                                    </div>
                                    <div className="p-2 bg-red-400/20 rounded-lg">
                                        <AlertCircle size={20} className="text-red-300" />
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.4 }}
                                className="bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-400/40 rounded-xl p-4 backdrop-blur-md hover:border-cyan-300/60 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-cyan-200 text-xs font-medium">Davomat %</p>
                                        <p className="text-2xl font-bold text-cyan-100 mt-1">{stats.percentage}%</p>
                                    </div>
                                    <div className="p-2 bg-cyan-400/20 rounded-lg">
                                        <TrendingUp size={20} className="text-cyan-300" />
                                    </div>
                                </div>
                            </motion.div>
                        </div>

                        {/* <CHANGE> Premium controls section */}
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="bg-gradient-to-r from-slate-800/80 to-slate-900/80 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 flex flex-col lg:flex-row justify-between lg:items-center gap-4"
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-cyan-500/20 rounded-lg">
                                    <Users size={20} className="text-cyan-400" />
                                </div>
                                <div>
                                    <h2 className="font-semibold text-white">
                                        {selectedNode.name}
                                    </h2>
                                    <p className="text-xs text-emerald-300 font-medium">Kunlik davomat jadvali</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-3 bg-emerald-500/20 px-4 py-2 rounded-xl border border-emerald-400/30">
                                <Calendar size={18} className="text-emerald-400" />
                                <input
                                    type="date"
                                    value={selectedDate}
                                    onChange={(e) => {
                                        const newDate = e.target.value;
                                        setSelectedDate(newDate);
                                        loadDaily(selectedNode.id, newDate);
                                    }}
                                    className="bg-transparent border-0 outline-none font-medium text-white text-sm focus:ring-0"
                                />
                            </div>

                            <motion.div whileTap={{ scale: 0.95 }}>
                                <Button
                                    onClick={() =>
                                        router.push(
                                            `/staff/users/monthly?unit_id=${selectedNode.id}`
                                        )
                                    }
                                    className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-semibold shadow-lg w-full lg:w-auto"
                                >
                                    📊 Oylik Ko'rish
                                </Button>
                            </motion.div>
                        </motion.div>

                        {/* <CHANGE> Premium table section with enhanced styling */}
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.15 }}
                            className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-emerald-500/20 rounded-2xl backdrop-blur-xl overflow-hidden shadow-2xl"
                        >
                            {loadingDaily ? (
                                <div className="flex items-center justify-center py-16">
                                    <div className="text-center space-y-3">
                                        <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-emerald-100">
                                            <div className="w-6 h-6 border-2 border-emerald-200 border-t-emerald-500 rounded-full animate-spin"></div>
                                        </div>
                                        <p className="text-emerald-300 text-sm font-medium">Davomat ma'lumotlari yuklanmoqda...</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gradient-to-r from-emerald-600/40 to-cyan-600/40 border-b border-emerald-500/30">
                                        <tr>
                                            <th className="px-4 md:px-6 py-4 text-left font-bold text-emerald-200">F.I.Sh</th>
                                            <th className="px-4 md:px-6 py-4 text-left font-bold text-emerald-200">Lavozim</th>
                                            <th className="px-3 md:px-4 py-4 text-center font-bold text-emerald-200">
                                                <div className="flex items-center justify-center gap-1">
                                                    <Clock size={14} />
                                                    Kirish
                                                </div>
                                            </th>
                                            <th className="px-3 md:px-4 py-4 text-center font-bold text-emerald-200">Turniket</th>
                                            <th className="px-3 md:px-4 py-4 text-center font-bold text-emerald-200">
                                                <div className="flex items-center justify-center gap-1">
                                                    <Clock size={14} />
                                                    Chiqish
                                                </div>
                                            </th>
                                            <th className="px-3 md:px-4 py-4 text-center font-bold text-emerald-200">Turniket</th>
                                        </tr>
                                        </thead>

                                        <tbody>
                                        {daily.map((item, idx) => {
                                            const status = getStatusStyles(item);
                                            return (
                                                <motion.tr
                                                    key={item.user_id}
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    transition={{ duration: 0.3, delay: idx * 0.02 }}
                                                    className={`border-b border-emerald-500/20 hover:bg-emerald-500/10 transition-all ${
                                                        idx % 2 === 0
                                                            ? "bg-slate-800/40"
                                                            : "bg-slate-700/40"
                                                    }`}
                                                >
                                                    <td className="px-4 md:px-6 py-4 font-bold text-emerald-100">
                                                        {item.full_name}
                                                    </td>
                                                    <td className="px-4 md:px-6 py-4 text-emerald-300/80">
                                                        {item.position}
                                                    </td>

                                                    <td className="px-3 md:px-4 py-4 text-center">
                                                        <motion.div
                                                            whileHover={{ scale: 1.05 }}
                                                            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg font-bold text-sm ${status.badge}`}
                                                        >
                                                            {status.icon}
                                                            <span>{status.label}</span>
                                                        </motion.div>
                                                    </td>

                                                    <td className="px-3 md:px-4 py-4 text-center text-cyan-300 font-medium">
                                                        {item.first_device || "—"}
                                                    </td>

                                                    <td className="px-3 md:px-4 py-4 text-center text-emerald-300/80">
                                                        {item.last_exit
                                                            ? dayjs(item.last_exit).format("HH:mm")
                                                            : "—"}
                                                    </td>

                                                    <td className="px-3 md:px-4 py-4 text-center text-cyan-300 font-medium">
                                                        {item.last_device || "—"}
                                                    </td>
                                                </motion.tr>
                                            );
                                        })}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {!loadingDaily && daily.length === 0 && (
                                <div className="text-center py-16">
                                    <AlertCircle size={32} className="text-emerald-300/50 mx-auto mb-3" />
                                    <p className="text-emerald-300 font-medium">Bu sanada hech qanday davomat ma'lumoti yo'q</p>
                                </div>
                            )}
                        </motion.div>

                    </motion.div>
                )}
            </AnimatePresence>

        </motion.div>
    );
}