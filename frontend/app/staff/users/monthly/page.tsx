"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import dayjs from "dayjs";
import { motion } from "framer-motion";
import { fetchUnitMonthlyDetailed } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ArrowLeft, CalendarDays } from "lucide-react";

const weekdaysUz = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"];

export default function MonthlyAttendancePage() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const unitId = searchParams.get("unit_id");
    const unitName = searchParams.get("unit_name") ?? "Bo‘lim";

    const today = dayjs();
    const [year, setYear] = useState(today.year());
    const [month, setMonth] = useState(today.month() + 1);

    const [rows, setRows] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const daysInMonth = dayjs(`${year}-${String(month).padStart(2, "0")}-01`).daysInMonth();
    const dayNumbers = Array.from({ length: daysInMonth }, (_, i) => i + 1);

    /* ===================================
        FETCH MONTHLY DATA
    ==================================== */
    useEffect(() => {
        if (!unitId) return;
        (async () => {
            setLoading(true);
            const data = await fetchUnitMonthlyDetailed(unitId, year, month);
            setRows(data);
            setLoading(false);
        })();
    }, [unitId, year, month]);

    /* ===================================
        DAILY PERCENT
    ==================================== */
    const dailyPercent = useMemo(() => {
        return dayNumbers.map((d) => {
            const date = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
            const total = rows.length;

            let came = 0;
            rows.forEach((u) => {
                const rec = u.days.find((x: any) => x.date === date);
                if (rec && !rec.is_absent) came++;
            });

            if (total === 0) return 0;
            return Math.round((came / total) * 100);
        });
    }, [rows, dayNumbers]);

    /* ===================================
        CELL COLOR LOGIC — Kechikkanlar QIZIL!
    ==================================== */
    function getCellClasses(rec: any, jsDay: number, columnIndex: number) {
        let base = "border border-emerald-100 text-center text-xs md:text-sm font-medium px-1.5 py-2 transition-all duration-150";

        // Yakshanba — och qizil fon
        if (jsDay === 0) {
            return `${base} bg-rose-100 text-rose-800`;
        }

        // Ustun rangini belgilash: juft-toq
        const isEvenColumn = columnIndex % 2 === 0;
        const columnBg = isEvenColumn ? "bg-emerald-50" : "bg-emerald-100";

        // ❌ KELMAGAN — TO'Q QIZIL
        if (!rec || rec.is_absent) {
            return `${base} ${columnBg} bg-rose-300 text-rose-900 hover:bg-rose-400 cursor-pointer`;
        }

        // ⏰ KECHIKKAN — OCH QIZIL (soat 10:00 dan keyin)
        const late = rec.first_entry && dayjs(rec.first_entry).isAfter(dayjs(rec.date + " 10:00"));
        if (late) {
            return `${base} ${columnBg} bg-rose-200 text-rose-800 hover:bg-rose-300 cursor-pointer`;
        }

        // ✅ VAQTIDA KELGAN — YASHIL
        return `${base} ${columnBg} bg-emerald-200/70 text-emerald-800 hover:bg-emerald-300 cursor-pointer`;
    }

    /* ===================================
        FORMAT TIME — Kechikkanlar matni ham qizil
    ==================================== */
    function fmt(rec: any) {
        if (!rec?.first_entry) return "—";
        const t = dayjs(rec.first_entry).format("HH:mm");
        const late = rec.first_entry && dayjs(rec.first_entry).isAfter(dayjs(rec.date + " 10:00"));
        return (
            <span className={late ? "text-rose-800 font-bold" : "text-emerald-800 font-semibold"}>
        {t}
      </span>
        );
    }

    /* ===================================
        JUMP TO DAILY PAGE
    ==================================== */
    function openDay(date: string) {
        router.push(`/staff/users/daily?unit_id=${unitId}&date=${date}`);
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="min-h-screen p-4 space-y-8"
        >
            {/* HEADER */}
            <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.4 }}
                className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/80 backdrop-blur-xl p-5 rounded-2xl shadow-lg border border-emerald-200"
            >
                <div className="flex items-center gap-3">
                    <Button
                        variant="outline"
                        onClick={() => router.push("/staff/users")}
                        className="gap-2 border-emerald-300 text-emerald-800 hover:bg-emerald-100 rounded-xl"
                    >
                        <ArrowLeft size={18} /> Orqaga
                    </Button>

                    <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2 text-emerald-900">
                        <CalendarDays className="text-teal-600" />
                        {unitName} — Oylik davomat
                    </h1>
                </div>

                <div className="flex gap-3 flex-wrap">
                    <select
                        value={year}
                        onChange={(e) => setYear(Number(e.target.value))}
                        className="border border-emerald-200 rounded-xl px-4 py-2 bg-white/80 backdrop-blur text-emerald-800 font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
                    >
                        {[year - 1, year, year + 1].map((y) => (
                            <option key={y} value={y}>
                                {y}
                            </option>
                        ))}
                    </select>

                    <select
                        value={month}
                        onChange={(e) => setMonth(Number(e.target.value))}
                        className="border border-emerald-200 rounded-xl px-4 py-2 bg-white/80 backdrop-blur text-emerald-800 font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-300"
                    >
                        {Array.from({ length: 12 }, (_, i) => (
                            <option key={i + 1} value={i + 1}>
                                {i + 1}-oy
                            </option>
                        ))}
                    </select>
                </div>
            </motion.div>

            {/* TABLE */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="overflow-auto rounded-2xl shadow-xl border border-emerald-200 bg-white/70 backdrop-blur-xl"
            >
                <table className="w-full min-w-max border-collapse text-sm">
                    <thead>
                    {/* SANALAR USTUNI */}
                    <tr className="bg-emerald-50 text-emerald-900">
                        <th className="sticky left-0 z-10 border border-emerald-200 p-3 text-left font-bold bg-emerald-50/90 backdrop-blur">№ / F.I.Sh</th>
                        <th className="border border-emerald-200 p-3 text-left font-bold bg-emerald-50/90 backdrop-blur">Lavozim</th>

                        {dayNumbers.map((d, idx) => {
                            const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                            const jsDay = dayjs(dateStr).day();
                            const isEven = idx % 2 === 0;
                            const bgClass = jsDay === 0
                                ? "bg-rose-200 text-rose-800"
                                : isEven
                                    ? "bg-emerald-200 text-emerald-900"
                                    : "bg-emerald-300 text-emerald-900";

                            return (
                                <th
                                    key={d}
                                    className={`border border-emerald-200 px-2 py-2 font-bold cursor-pointer hover:bg-emerald-100 transition-colors ${bgClass}`}
                                    onClick={() => openDay(dateStr)}
                                >
                                    {d}
                                </th>
                            );
                        })}

                        <th className="border border-emerald-200 px-3 py-2 font-bold bg-amber-100 text-amber-900">Jami</th>
                        <th className="border border-emerald-200 px-3 py-2 font-bold bg-emerald-200 text-emerald-900">%</th>
                    </tr>

                    {/* HAFTA KUNLARI */}
                    <tr className="bg-slate-100 text-center text-xs font-semibold text-slate-700">
                        <th className="border border-emerald-200"></th>
                        <th className="border border-emerald-200"></th>
                        {dayNumbers.map((d, idx) => {
                            const date = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                            const js = dayjs(date).day();
                            const isEven = idx % 2 === 0;
                            const bgClass = js === 0
                                ? "bg-rose-100"
                                : isEven
                                    ? "bg-emerald-100"
                                    : "bg-emerald-200";

                            return (
                                <th key={"wd" + d} className={`border border-emerald-200 py-1.5 ${bgClass}`}>
                    <span className={js === 0 ? "text-rose-700 font-bold" : "text-emerald-800"}>
                      {weekdaysUz[js]}
                    </span>
                                </th>
                            );
                        })}
                        <th className="border border-emerald-200 bg-amber-50"></th>
                        <th className="border border-emerald-200 bg-emerald-100"></th>
                    </tr>
                    </thead>

                    <tbody>
                    {rows.map((u, idx) => {
                        const tot = u.total_present_days + u.total_absent_days;
                        const percent = tot ? Math.round((u.total_present_days / tot) * 100) : 0;
                        const isEvenRow = idx % 2 === 0;
                        const rowBg = isEvenRow ? "bg-sky-50" : "bg-sky-100";

                        return (
                            <tr key={u.user_id} className={`${rowBg} hover:bg-emerald-50/50 transition-colors`}>
                                {/* Sticky F.I.Sh */}
                                <td className="sticky left-0 z-10 border border-emerald-200 p-2.5 bg-white font-medium text-emerald-900 shadow-sm">
                                    {idx + 1}. {u.full_name}
                                </td>
                                <td className="border border-emerald-200 p-2.5 text-slate-700">{u.position ?? "-"}</td>

                                {dayNumbers.map((d, colIdx) => {
                                    const date = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                                    const js = dayjs(date).day();
                                    const rec = u.days.find((x: any) => x.date === date);

                                    return (
                                        <td
                                            key={d}
                                            onClick={() => js !== 0 && openDay(date)}
                                            className={getCellClasses(rec, js, colIdx)}
                                        >
                                            {js === 0 ? "" : fmt(rec)}
                                        </td>
                                    );
                                })}

                                {/* Jami va % */}
                                <td className="border border-emerald-200 text-center font-bold bg-amber-100 text-amber-800">
                                    {u.total_present_days}
                                </td>
                                <td className="border border-emerald-200 text-center font-bold bg-emerald-200 text-emerald-800">
                                    {percent}%
                                </td>
                            </tr>
                        );
                    })}

                    {/* ======== KUNLIK FOIZ QATORI — AJRALIB TURADI ======== */}
                    <tr className="bg-gradient-to-r from-amber-50 via-yellow-50 to-amber-50 border-t-4 border-amber-300">
                        <td colSpan={2} className="border border-emerald-200 p-2.5 font-bold text-amber-900 bg-white/80 backdrop-blur">
                            Kunlik davomat (%)
                        </td>
                        {dailyPercent.map((p, i) => {
                            const bgClass = p < 40
                                ? "bg-rose-200 text-rose-800"
                                : p < 70
                                    ? "bg-amber-200 text-amber-800"
                                    : "bg-emerald-200 text-emerald-800";

                            return (
                                <td
                                    key={i}
                                    className={`border border-emerald-200 py-2 font-bold ${bgClass}`}
                                >
                                    <div className="flex flex-col items-center">
                                        <span>{p}%</span>
                                        <div className="w-full h-1.5 mt-1 bg-white/60 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${
                                                    p < 40 ? "bg-rose-500" : p < 70 ? "bg-amber-500" : "bg-emerald-500"
                                                }`}
                                                style={{ width: `${p}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </td>
                            );
                        })}
                        <td className="border border-emerald-200 bg-white"></td>
                        <td className="border border-emerald-200 bg-white"></td>
                    </tr>
                    </tbody>
                </table>
            </motion.div>
        </motion.div>
    );
}