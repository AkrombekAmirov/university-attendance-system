// app/staff/monthly/page.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from 'next/navigation';
import dayjs from "dayjs";
import { motion, AnimatePresence } from "framer-motion";
import { fetchUnitMonthlyDetailed } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ArrowLeft, CalendarDays, TrendingUp, Users, AlertCircle, CheckCircle2 } from 'lucide-react';

const weekdaysUz = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"];
const monthNamesUz = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"];

export default function MonthlyAttendancePage() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const unitId = searchParams.get("unit_id");
    const unitName = searchParams.get("unit_name") ?? "Bo'lim";

    const today = dayjs();
    const [year, setYear] = useState(today.year());
    const [month, setMonth] = useState(today.month() + 1);
    const [rows, setRows] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const daysInMonth = dayjs(`${year}-${String(month).padStart(2, "0")}-01`).daysInMonth();
    const dayNumbers = Array.from({ length: daysInMonth }, (_, i) => i + 1);

    useEffect(() => {
        if (!unitId) return;
        (async () => {
            setLoading(true);
            const data = await fetchUnitMonthlyDetailed(unitId, year, month);
            setRows(data || []);
            setLoading(false);
        })();
    }, [unitId, year, month]);

    // Calculate daily attendance percentage
    const dailyPercent = useMemo(() => {
        return dayNumbers.map((d) => {
            const date = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
            const total = rows.length;
            let came = 0;
            rows.forEach((u) => {
                const rec = u.days?.find((x: any) => x.date === date);
                if (rec && !rec.is_absent) came++;
            });
            if (total === 0) return 0;
            return Math.round((came / total) * 100);
        });
    }, [rows, dayNumbers]);

    // Premium color system
    function getCellColor(rec: any, jsDay: number, columnIndex: number) {
        const isEvenColumn = columnIndex % 2 === 0;

        // Weekend - muted rose
        if (jsDay === 0) {
            return {
                bg: "bg-gradient-to-br from-rose-100/60 to-pink-100/60",
                border: "border-rose-200/50",
                text: "text-rose-700"
            };
        }

        // Absent - deep red gradient
        if (!rec || rec.is_absent) {
            return {
                bg: "bg-gradient-to-br from-red-400 to-rose-500",
                border: "border-red-600/50",
                text: "text-white font-semibold",
                hover: "hover:from-red-500 hover:to-rose-600"
            };
        }

        // Late - amber gradient
        const late = rec.first_entry && dayjs(rec.first_entry).isAfter(dayjs(rec.date + " 10:00"));
        if (late) {
            return {
                bg: "bg-gradient-to-br from-amber-300 to-yellow-400",
                border: "border-amber-500/50",
                text: "text-amber-900 font-bold",
                hover: "hover:from-amber-400 hover:to-yellow-500"
            };
        }

        // Present - emerald gradient with shimmer
        return {
            bg: isEvenColumn
                ? "bg-gradient-to-br from-emerald-300 to-teal-400"
                : "bg-gradient-to-br from-cyan-300 to-emerald-400",
            border: "border-emerald-500/50",
            text: "text-emerald-900 font-bold",
            hover: isEvenColumn
                ? "hover:from-emerald-400 hover:to-teal-500"
                : "hover:from-cyan-400 hover:to-emerald-500"
        };
    }

    function formatTime(rec: any) {
        if (!rec?.first_entry) return "—";
        const t = dayjs(rec.first_entry).format("HH:mm");
        const late = rec.first_entry && dayjs(rec.first_entry).isAfter(dayjs(rec.date + " 10:00"));
        return <span className={late ? "text-rose-800 font-bold" : "text-emerald-800 font-bold"}>{t}</span>;
    }

    function getDailyStatusColor(percent: number) {
        if (percent >= 85) return "from-emerald-500 to-teal-500";
        if (percent >= 70) return "from-cyan-500 to-blue-500";
        if (percent >= 50) return "from-amber-500 to-yellow-500";
        return "from-red-500 to-rose-500";
    }

    function openDay(date: string) {
        router.push(`/staff/users/daily?unit_id=${unitId}&date=${date}`);
    }

    const avgAttendance = rows.length > 0
        ? Math.round(rows.reduce((sum, u) => sum + ((u.total_present_days / (u.total_present_days + u.total_absent_days)) * 100 || 0), 0) / rows.length)
        : 0;

    const totalPresent = rows.reduce((sum, u) => sum + u.total_present_days, 0);
    const totalAbsent = rows.reduce((sum, u) => sum + u.total_absent_days, 0);

    if (loading) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900/50 to-slate-900 flex items-center justify-center"
            >
                <div className="text-center space-y-4">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400">
                        <div className="w-12 h-12 border-4 border-slate-900 border-t-emerald-300 rounded-full animate-spin"></div>
                    </div>
                    <p className="text-emerald-200 font-bold text-lg">Oylik davomat ma'lumotlari yuklanmoqda...</p>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900/40 to-slate-900 px-3 md:px-6 py-8"
        >
            <div className="max-w-full space-y-6">
                {/* PREMIUM HEADER */}
                <motion.div
                    initial={{ y: -30, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ duration: 0.6 }}
                    className="bg-gradient-to-r from-slate-800/80 via-emerald-800/60 to-slate-800/80 backdrop-blur-xl border border-emerald-400/30 rounded-2xl p-6 shadow-2xl"
                >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                            <motion.button
                                whileTap={{ scale: 0.95 }}
                                onClick={() => router.push("/staff/users")}
                                className="p-3 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl hover:from-emerald-600 hover:to-cyan-600 transition-all shadow-lg"
                            >
                                <ArrowLeft size={20} className="text-white" />
                            </motion.button>

                            <div>
                                <h1 className="text-3xl md:text-4xl font-black bg-gradient-to-r from-emerald-200 via-cyan-200 to-emerald-200 bg-clip-text text-transparent">
                                    Oylik Davomat
                                </h1>
                                <p className="text-emerald-300 font-semibold mt-1 flex items-center gap-2">
                                    <CalendarDays size={18} />
                                    {unitName}
                                </p>
                            </div>
                        </div>

                        {/* DATE SELECTORS */}
                        <div className="flex gap-3 flex-wrap">
                            <select
                                value={year}
                                onChange={(e) => setYear(Number(e.target.value))}
                                className="bg-gradient-to-br from-slate-700 to-slate-800 border border-emerald-400/50 rounded-xl px-4 py-2 text-emerald-200 font-semibold shadow-lg focus:outline-none focus:ring-2 focus:ring-emerald-400 transition-all"
                            >
                                {[year - 1, year, year + 1].map((y) => (
                                    <option key={y} value={y} className="bg-slate-900">
                                        {y}
                                    </option>
                                ))}
                            </select>

                            <select
                                value={month}
                                onChange={(e) => setMonth(Number(e.target.value))}
                                className="bg-gradient-to-br from-slate-700 to-slate-800 border border-emerald-400/50 rounded-xl px-4 py-2 text-emerald-200 font-semibold shadow-lg focus:outline-none focus:ring-2 focus:ring-emerald-400 transition-all"
                            >
                                {monthNamesUz.map((m, i) => (
                                    <option key={i + 1} value={i + 1} className="bg-slate-900">
                                        {m}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </motion.div>

                {/* PREMIUM STATS CARDS */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4"
                >
                    {/* Total Staff */}
                    <div className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 border border-blue-400/40 rounded-xl p-4 backdrop-blur-md hover:border-blue-300/60 transition-all">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-blue-200 text-xs font-medium">Jami Xodimlar</p>
                                <p className="text-2xl font-bold text-blue-100 mt-1">{rows.length}</p>
                            </div>
                            <div className="p-2 bg-blue-400/20 rounded-lg">
                                <Users size={20} className="text-blue-300" />
                            </div>
                        </div>
                    </div>

                    {/* Average Attendance */}
                    <div className="bg-gradient-to-br from-emerald-500/20 to-teal-600/20 border border-emerald-400/40 rounded-xl p-4 backdrop-blur-md hover:border-emerald-300/60 transition-all">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-emerald-200 text-xs font-medium">O'rtacha Davomat</p>
                                <p className="text-2xl font-bold text-emerald-100 mt-1">{avgAttendance}%</p>
                            </div>
                            <div className="p-2 bg-emerald-400/20 rounded-lg">
                                <TrendingUp size={20} className="text-emerald-300" />
                            </div>
                        </div>
                    </div>

                    {/* Total Present */}
                    <div className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 border border-green-400/40 rounded-xl p-4 backdrop-blur-md hover:border-green-300/60 transition-all">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-green-200 text-xs font-medium">Kelganlar</p>
                                <p className="text-2xl font-bold text-green-100 mt-1">{totalPresent}</p>
                            </div>
                            <div className="p-2 bg-green-400/20 rounded-lg">
                                <CheckCircle2 size={20} className="text-green-300" />
                            </div>
                        </div>
                    </div>

                    {/* Total Absent */}
                    <div className="bg-gradient-to-br from-red-500/20 to-rose-600/20 border border-red-400/40 rounded-xl p-4 backdrop-blur-md hover:border-red-300/60 transition-all">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-red-200 text-xs font-medium">Kelmaganlar</p>
                                <p className="text-2xl font-bold text-red-100 mt-1">{totalAbsent}</p>
                            </div>
                            <div className="p-2 bg-red-400/20 rounded-lg">
                                <AlertCircle size={20} className="text-red-300" />
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* MAIN TABLE */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-emerald-400/30 rounded-2xl backdrop-blur-xl overflow-hidden shadow-2xl"
                >
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            {/* HEADER */}
                            <thead>
                            {/* Date Header */}
                            <tr className="bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-b border-emerald-400/30">
                                <th className="sticky left-0 z-20 bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-3 text-left font-bold text-white shadow-lg">
                                    F.I.Sh
                                </th>
                                <th className="px-3 py-3 text-left font-bold text-emerald-200">Lavozim</th>

                                {dayNumbers.map((d, idx) => {
                                    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                                    const jsDay = dayjs(dateStr).day();
                                    const isWeekend = jsDay === 0;
                                    const isEvenCol = idx % 2 === 0;

                                    let headerBg = "bg-gradient-to-br from-emerald-500/40 to-teal-500/40";
                                    if (isWeekend) headerBg = "bg-gradient-to-br from-rose-500/40 to-pink-500/40";
                                    else if (!isEvenCol) headerBg = "bg-gradient-to-br from-cyan-500/40 to-blue-500/40";

                                    return (
                                        <th
                                            key={d}
                                            onClick={() => !isWeekend && openDay(dateStr)}
                                            className={`px-2 py-2 font-bold text-xs border-r border-emerald-400/20 cursor-pointer hover:brightness-110 transition-all ${headerBg}`}
                                        >
                                            <div className="text-slate-100">{d}</div>
                                            <div className="text-emerald-300 text-xs mt-0.5">{weekdaysUz[jsDay]}</div>
                                        </th>
                                    );
                                })}

                                <th className="px-3 py-3 font-bold text-amber-300 bg-gradient-to-br from-amber-600/40 to-yellow-600/40 border-l border-emerald-400/20">
                                    Jami
                                </th>
                                <th className="px-3 py-3 font-bold text-emerald-300 bg-gradient-to-br from-emerald-600/40 to-teal-600/40">
                                    %
                                </th>
                            </tr>
                            </thead>

                            {/* BODY */}
                            <tbody>
                            <AnimatePresence>
                                {rows.map((u, idx) => {
                                    const tot = u.total_present_days + u.total_absent_days;
                                    const percent = tot ? Math.round((u.total_present_days / tot) * 100) : 0;
                                    const rowBg = idx % 2 === 0 ? "bg-slate-800/30" : "bg-slate-700/30";

                                    return (
                                        <motion.tr
                                            key={u.user_id}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ duration: 0.3, delay: idx * 0.02 }}
                                            className={`${rowBg} border-b border-emerald-400/20 hover:bg-emerald-500/20 transition-all`}
                                        >
                                            {/* Name Column */}
                                            <td className="sticky left-0 z-10 px-4 py-3 font-bold text-emerald-100 bg-gradient-to-r from-slate-800/90 to-slate-900/80 backdrop-blur-sm shadow-sm">
                                                <span className="text-slate-400 mr-2">#{idx + 1}</span>{u.full_name}
                                            </td>

                                            {/* Position Column */}
                                            <td className="px-3 py-3 text-slate-300 font-medium">{u.position ?? "—"}</td>

                                            {/* Daily Cells */}
                                            {dayNumbers.map((d, colIdx) => {
                                                const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                                                const jsDay = dayjs(dateStr).day();
                                                const rec = u.days?.find((x: any) => x.date === dateStr);
                                                const colors = getCellColor(rec, jsDay, colIdx);

                                                return (
                                                    <motion.td
                                                        key={d}
                                                        whileHover={{ scale: 1.08, y: -2 }}
                                                        onClick={() => jsDay !== 0 && openDay(dateStr)}
                                                        className={`px-2 py-2 text-center font-bold border-r border-emerald-400/10 transition-all cursor-pointer text-xs md:text-sm bg-gradient-to-br ${colors.bg} border ${colors.border} ${colors.hover} ${colors.text}`}
                                                    >
                                                        {jsDay === 0 ? "" : formatTime(rec)}
                                                    </motion.td>
                                                );
                                            })}

                                            {/* Total Present */}
                                            <td className="px-3 py-3 text-center font-bold text-amber-200 bg-gradient-to-br from-amber-600/40 to-yellow-600/40 border-l border-emerald-400/20">
                                                {u.total_present_days}
                                            </td>

                                            {/* Percentage */}
                                            <td className="px-3 py-3 text-center">
                                                <div className={`inline-flex items-center justify-center px-3 py-1.5 rounded-lg font-bold text-white bg-gradient-to-r ${getDailyStatusColor(percent)} shadow-lg`}>
                                                    {percent}%
                                                </div>
                                            </td>
                                        </motion.tr>
                                    );
                                })}
                            </AnimatePresence>

                            {/* DAILY STATS ROW */}
                            <tr className="bg-gradient-to-r from-amber-600/50 via-yellow-600/50 to-amber-600/50 border-t-4 border-amber-400 font-bold">
                                <td colSpan={2} className="px-4 py-4 text-white bg-gradient-to-r from-slate-800 to-slate-900 backdrop-blur-sm sticky left-0 z-10">
                                    📊 Kunlik Davomat
                                </td>

                                {dailyPercent.map((p, i) => {
                                    const statusColor = getDailyStatusColor(p);
                                    return (
                                        <motion.td
                                            key={i}
                                            whileHover={{ scale: 1.05 }}
                                            className={`px-2 py-3 text-center border-r border-amber-400/30 bg-gradient-to-br ${statusColor}`}
                                        >
                                            <div className="flex flex-col items-center text-white">
                                                <span className="text-sm font-bold">{p}%</span>
                                                <div className="w-full h-1 mt-1.5 bg-white/20 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${p}%` }}
                                                        transition={{ duration: 0.8, ease: "easeOut" }}
                                                        className="h-full bg-white"
                                                    ></motion.div>
                                                </div>
                                            </div>
                                        </motion.td>
                                    );
                                })}

                                <td className="px-3 py-4 border-l border-amber-400/30 bg-gradient-to-r from-slate-800 to-slate-900"></td>
                                <td className="px-3 py-4 bg-gradient-to-r from-slate-800 to-slate-900"></td>
                            </tr>
                            </tbody>
                        </table>
                    </div>

                    {/* LEGEND */}
                    <div className="px-6 py-4 bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-t border-emerald-400/30 flex flex-wrap gap-6">
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-gradient-to-br from-emerald-400 to-teal-500"></div>
                            <span className="text-sm text-emerald-200 font-medium">Vaqtida Kelgan</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-gradient-to-br from-amber-400 to-yellow-500"></div>
                            <span className="text-sm text-amber-200 font-medium">Kech Kelgan (10:00+)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-gradient-to-br from-red-400 to-rose-500"></div>
                            <span className="text-sm text-red-200 font-medium">Kelmagan</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-gradient-to-br from-rose-300 to-pink-400"></div>
                            <span className="text-sm text-rose-200 font-medium">Dam Kunlari</span>
                        </div>
                    </div>
                </motion.div>
            </div>
        </motion.div>
    );
}