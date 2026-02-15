"use client";

import {useEffect, useState} from "react";
import {useRouter} from "next/navigation";
import dayjs from "dayjs";
import {motion, AnimatePresence} from "framer-motion";

import {fetchHrUnits, fetchHrUnitDaily} from "@/lib/api";
import {Card, CardHeader, CardTitle} from "@/components/ui/card";
import {Button} from "@/components/ui/button";

import {
    ArrowLeft,
    Users,
    Clock,
    Calendar,
    Building2
} from "lucide-react";

/* ================= TYPES ================= */

type HrUnit = {
    id: string;
    name: string;
};

type DailyRow = {
    user_id: string;
    full_name: string;
    position: string;
    first_entry?: string | null;
    last_exit?: string | null;
    first_device?: string | null;
    last_device?: string | null;
};

/* ================= PAGE ================= */

export default function HrDailyPage() {
    const router = useRouter();

    const [units, setUnits] = useState<HrUnit[]>([]);
    const [selectedUnit, setSelectedUnit] = useState<HrUnit | null>(null);

    const [daily, setDaily] = useState<DailyRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingDaily, setLoadingDaily] = useState(false);

    const [selectedDate, setSelectedDate] = useState(
        dayjs().format("YYYY-MM-DD")
    );

    /* ================= INITIAL LOAD ================= */
    useEffect(() => {
        (async () => {
            const data = await fetchHrUnits();
            setUnits(data);
            setLoading(false);
        })();
    }, []);

    /* ================= LOAD DAILY ================= */
    async function loadDaily(unit: HrUnit, dateStr: string) {
        setSelectedUnit(unit);
        setLoadingDaily(true);
        const data = await fetchHrUnitDaily(unit.id, dateStr);
        setDaily(data);
        setLoadingDaily(false);
    }

    function goBack() {
        setSelectedUnit(null);
        setDaily([]);
    }

    function statusColor(item: DailyRow) {
        if (!item.first_entry)
            return "bg-red-100 text-red-700 border-red-200";
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
    }

    function safeExit(
        first?: string | null,
        last?: string | null,
        minMinutes = 60
    ) {
        if (!first || !last) return null;
        const diff = dayjs(last).diff(dayjs(first), "minute");
        if (diff < minMinutes) return null;
        return dayjs(last).format("HH:mm");
    }

    if (loading) {
        return (
            <div className="text-center py-10 text-gray-500 animate-pulse">
                Yuklanmoqda...
            </div>
        );
    }

    /* ================= RENDER ================= */

    return (
        <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            className="
                min-h-screen p-4 space-y-6
                bg-gradient-to-br from-indigo-50 via-white to-blue-50
            "
        >

            {/* HEADER */}
            <div className="
                sticky top-0 z-20
                flex items-center gap-4
                bg-white/70 backdrop-blur
                p-4 rounded-xl shadow border
            ">
                {selectedUnit && (
                    <Button
                        variant="ghost"
                        onClick={goBack}
                        className="gap-2"
                    >
                        <ArrowLeft size={18}/> Orqaga
                    </Button>
                )}

                <h2 className="
                    text-2xl font-bold
                    bg-gradient-to-r from-indigo-600 to-blue-600
                    bg-clip-text text-transparent
                    flex gap-2 items-center
                ">
                    <Building2/> HR — Kunlik davomat
                </h2>
            </div>

            <AnimatePresence mode="wait">

                {/* ================= UNIT LIST ================= */}
                {!selectedUnit && (
                    <motion.div
                        key="units"
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: -20}}
                        className="grid gap-5 grid-cols-1 md:grid-cols-2"
                    >
                        {units.map((u) => (
                            <motion.div
                                key={u.id}
                                whileHover={{scale: 1.02}}
                            >
                                <Card
                                    onClick={() =>
                                        loadDaily(u, selectedDate)
                                    }
                                    className="
                                        cursor-pointer
                                        bg-white/70 backdrop-blur
                                        border rounded-2xl shadow
                                        hover:bg-indigo-50
                                    "
                                >
                                    <CardHeader>
                                        <CardTitle className="text-lg">
                                            {u.name}
                                        </CardTitle>
                                    </CardHeader>
                                </Card>
                            </motion.div>
                        ))}
                    </motion.div>
                )}

                {/* ================= DAILY TABLE ================= */}
                {selectedUnit && (
                    <motion.div
                        key="daily"
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: -20}}
                        className="space-y-5"
                    >

                        {/* DATE PICKER */}
                        <div className="
                            flex justify-between items-center
                            bg-white/60 p-4 rounded-xl shadow border
                        ">
                            <h3 className="text-xl font-semibold flex gap-2">
                                <Users className="text-indigo-600"/>
                                {selectedUnit.name}
                            </h3>

                            <div className="flex gap-3 items-center">
                                <Calendar className="text-indigo-600"/>
                                <input
                                    type="date"
                                    value={selectedDate}
                                    onChange={(e) => {
                                        const d = e.target.value;
                                        setSelectedDate(d);
                                        loadDaily(selectedUnit, d);
                                    }}
                                    className="
                                        px-3 py-2 rounded-lg border
                                        bg-white/70 shadow
                                    "
                                />
                            </div>
                        </div>

                        {/* TABLE */}
                        <div className="
                            overflow-hidden rounded-2xl
                            bg-white/70 backdrop-blur
                            shadow border
                        ">
                            <table className="w-full text-sm">
                                <thead className="bg-indigo-100 text-slate-700">
                                <tr>
                                    <th className="p-3 text-left">F.I.Sh</th>
                                    <th className="p-3 text-left">Lavozim</th>
                                    <th className="p-3 text-center">Kirish</th>
                                    <th className="p-3 text-center">Kirish turniketi</th>
                                    <th className="p-3 text-center">Chiqish</th>
                                    <th className="p-3 text-center">Chiqish turniketi</th>
                                </tr>
                                </thead>

                                <tbody>
                                {loadingDaily && (
                                    <tr>
                                        <td colSpan={6}
                                            className="text-center p-6 text-gray-500">
                                            Yuklanmoqda...
                                        </td>
                                    </tr>
                                )}

                                {!loadingDaily && daily.map((item, idx) => (
                                    <tr
                                        key={item.user_id}
                                        className={idx % 2 === 0
                                            ? "bg-white/80"
                                            : "bg-indigo-50/40"}
                                    >
                                        <td className="p-3">{item.full_name}</td>
                                        <td className="p-3">{item.position}</td>

                                        <td className={`p-3 text-center font-semibold ${statusColor(item)}`}>
                                            {item.first_entry
                                                ? dayjs(item.first_entry).format("HH:mm")
                                                : "KELMADI"}
                                        </td>

                                        <td className="p-3 text-center">
                                            {item.first_device || "-"}
                                        </td>

                                        <td className="p-3 text-center">
                                            {safeExit(item.first_entry, item.last_exit) ?? "-"}
                                        </td>

                                        <td className="p-3 text-center">
                                            {safeExit(item.first_entry, item.last_exit)
                                                ? item.last_device || "-"
                                                : "-"}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>

                    </motion.div>
                )}

            </AnimatePresence>
        </motion.div>
    );
}
