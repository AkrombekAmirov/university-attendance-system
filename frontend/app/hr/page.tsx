"use client";
import {useEffect, useState} from "react";
import {useRouter} from "next/navigation";
import dayjs from "dayjs";
import {motion, AnimatePresence} from "framer-motion";
import {fetchHrUnitsSummary} from "@/lib/api";
import {fetchHrUnits, fetchHrUnitDaily} from "@/lib/api";
import {Card, CardHeader, CardTitle} from "@/components/ui/card";
import {Button} from "@/components/ui/button";
import {
    ArrowLeft,
    Users,
    Clock,
    Calendar,
    Building2,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Filter,
    Search,
    Loader,
    ChevronDown,
    BarChart3,
    ListFilter,
    Sparkles,
    Target,
    Award,
    Zap,
    TrendingDown,
    Coffee
} from "lucide-react";
/* ================= TYPES ================= */
// type HrUnit = {
//     id: string;
//     name: string;
//     employeeCount?: number;
//     department?: string;
//     attendanceRate?: number;
//     presentCount?: number;
//     absentCount?: number;
//     lateCount?: number;
// };
type DailyRow = {
    user_id: string;
    full_name: string;
    position: string;
    first_entry?: string | null;
    last_exit?: string | null;
    first_device?: string | null;
    last_device?: string | null;
};
type HrUnit = {
    id: string;
    name: string;
    employeeCount?: number;
    attendanceRate?: number;
    presentCount?: number;
    absentCount?: number;
    lateCount?: number;
};
/* ================= LOADING TIPS ================= */
const loadingTips = [
    {icon: "🎯", text: "90% va undan yuqori davomat - a'lo ko'rsatkich!"},
    {icon: "📊", text: "Statistika real vaqtda yangilanmoqda..."},
    {icon: "⚡", text: "Eng past foizli bo'limlar birinchi ko'rsatiladi"},
    {icon: "🔍", text: "Qidiruv orqali bo'limni tez topishingiz mumkin"},
    {icon: "🎨", text: "Har bir rang davomat darajasini bildiradi"},
    {icon: "👥", text: "Kelgan va kelmagan xodimlar alohida ko'rsatiladi"},
    {icon: "📈", text: "Progress bar davomat foizini vizual ko'rsatadi"},
    {icon: "🏆", text: "Yaxshi bo'limlarni filtr orqali ajratishingiz mumkin"},
    {icon: "⏰", text: "Har qanday sana uchun ma'lumot olishingiz mumkin"},
    {icon: "💡", text: "Kartochkani bosish orqali batafsil ma'lumot oling"},
    {icon: "🎯", text: "70% dan past - e'tibor talab qiladi"},
    {icon: "✨", text: "Ma'lumotlar xavfsiz yuklanmoqda..."},
    {icon: "🚀", text: "Tizim barcha bo'limlarni tekshiryapti..."},
    {icon: "📱", text: "Responsive dizayn - istalgan qurilmada qulay"},
    {icon: "🎪", text: "Bo'limlar avtomatik tartiblangan"},
];

/* ================= CREATIVE LOADING COMPONENT ================= */
function CreativeLoadingScreen() {
    const [currentTip, setCurrentTip] = useState(0);
    const [progress, setProgress] = useState(0);
    const [funFact, setFunFact] = useState(0);
    const funFacts = [
        "Ma'lumotlar yuklanmoqda... ☕",
        "Bo'limlar tahlil qilinmoqda... 📊",
        "Davomat foizlari hisoblanmoqda... 🧮",
        "Statistika tayyorlanmoqda... 📈",
        "Ranglar sozlanmoqda... 🎨",
    ];
    useEffect(() => {
// Tip rotation
        const tipInterval = setInterval(() => {
            setCurrentTip((prev) => (prev + 1) % loadingTips.length);
        }, 3000);
// Progress animation
        const progressInterval = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 95) return 95; // Max at 95 until real data loads
                return prev + Math.random() * 10;
            });
        }, 500);
// Fun fact rotation
        const factInterval = setInterval(() => {
            setFunFact((prev) => (prev + 1) % funFacts.length);
        }, 2500);
        return () => {
            clearInterval(tipInterval);
            clearInterval(progressInterval);
            clearInterval(factInterval);
        };
    }, []);
    return (
        <div
            className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-4">
            <motion.div
                initial={{opacity: 0, scale: 0.9}}
                animate={{opacity: 1, scale: 1}}
                className="max-w-2xl w-full"
            >
                {/* Main Loading Card */}
                <div
                    className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/50 overflow-hidden">
                    {/* Header with Animation */}
                    <div
                        className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-8 text-center relative overflow-hidden">
                        {/* Animated background circles */}
                        <motion.div
                            className="absolute inset-0 opacity-20"
                            animate={{
                                backgroundPosition: ["0% 0%", "100% 100%"],
                            }}
                            transition={{
                                duration: 20,
                                repeat: Infinity,
                                repeatType: "reverse",
                            }}
                            style={{
                                backgroundImage: "radial-gradient(circle, white 2px, transparent 2px)",
                                backgroundSize: "50px 50px",
                            }}
                        />
                        <motion.div
                            animate={{rotate: 360}}
                            transition={{duration: 3, repeat: Infinity, ease: "linear"}}
                            className="inline-block mb-4"
                        >
                            <Sparkles className="w-16 h-16 text-white"/>
                        </motion.div>
                        <h2 className="text-3xl font-bold text-white mb-2">
                            Ma'lumotlar yuklanmoqda
                        </h2>
                        <p className="text-white/90 text-lg">
                            {funFacts[funFact]}
                        </p>
                    </div>
                    {/* Content */}
                    <div className="p-8 space-y-6">
                        {/* Animated Progress Bar */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600 font-medium">Yuklanmoqda...</span>
                                <span className="text-indigo-600 font-bold">{Math.round(progress)}%</span>
                            </div>
                            <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden shadow-inner">
                                <motion.div
                                    className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full"
                                    initial={{width: "0%"}}
                                    animate={{width: `${progress}%`}}
                                    transition={{duration: 0.5, ease: "easeOut"}}
                                />
                                {/* Shimmer effect */}
                                <motion.div
                                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                                    animate={{x: ["-100%", "200%"]}}
                                    transition={{duration: 2, repeat: Infinity, ease: "linear"}}
                                />
                            </div>
                        </div>
                        {/* Stats Grid Animation */}
                        <div className="grid grid-cols-3 gap-4">
                            {[
                                {icon: Building2, label: "Bo'limlar", color: "indigo"},
                                {icon: Users, label: "Xodimlar", color: "purple"},
                                {icon: BarChart3, label: "Statistika", color: "pink"},
                            ].map((item, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{opacity: 0, y: 20}}
                                    animate={{opacity: 1, y: 0}}
                                    transition={{delay: idx * 0.2}}
                                    className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-4 text-center"
                                >
                                    <motion.div
                                        animate={{scale: [1, 1.1, 1]}}
                                        transition={{duration: 2, repeat: Infinity}}
                                        className={`inline-flex p-3 rounded-xl bg-${item.color}-100 mb-2`}
                                    >
                                        <item.icon className={`w-6 h-6 text-${item.color}-600`}/>
                                    </motion.div>
                                    <p className="text-xs font-medium text-gray-600">{item.label}</p>
                                </motion.div>
                            ))}
                        </div>
                        {/* Rotating Tips */}
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentTip}
                                initial={{opacity: 0, y: 10}}
                                animate={{opacity: 1, y: 0}}
                                exit={{opacity: 0, y: -10}}
                                transition={{duration: 0.5}}
                                className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-6 border border-indigo-100"
                            >
                                <div className="flex items-start gap-4">
                                    <span className="text-4xl">{loadingTips[currentTip].icon}</span>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
                                            <Zap className="w-4 h-4 text-yellow-500"/>
                                            Foydali maslahat
                                        </h3>
                                        <p className="text-gray-700">
                                            {loadingTips[currentTip].text}
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        </AnimatePresence>
                        {/* Animated Loading Indicators */}
                        <div className="flex items-center justify-center gap-3">
                            {[0, 1, 2, 3, 4].map((i) => (
                                <motion.div
                                    key={i}
                                    className="w-3 h-3 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                                    animate={{
                                        scale: [1, 1.5, 1],
                                        opacity: [0.5, 1, 0.5],
                                    }}
                                    transition={{
                                        duration: 1.5,
                                        repeat: Infinity,
                                        delay: i * 0.2,
                                    }}
                                />
                            ))}
                        </div>
                        {/* Bottom Info */}
                        <div className="text-center text-sm text-gray-500 pt-4 border-t border-gray-100">
                            <motion.p
                                animate={{opacity: [0.5, 1, 0.5]}}
                                transition={{duration: 2, repeat: Infinity}}
                            >
                                Iltimos kuting, ma'lumotlar tayyorlanmoqda...
                            </motion.p>
                        </div>
                    </div>
                </div>
                {/* Extra floating elements */}
                <div className="mt-6 flex items-center justify-center gap-4">
                    {[Award, Target, TrendingUp].map((Icon, idx) => (
                        <motion.div
                            key={idx}
                            animate={{
                                y: [0, -10, 0],
                                rotate: [0, 5, -5, 0],
                            }}
                            transition={{
                                duration: 3,
                                repeat: Infinity,
                                delay: idx * 0.4,
                            }}
                            className="p-3 bg-white/50 backdrop-blur rounded-xl shadow-lg border border-white/50"
                        >
                            <Icon className="w-6 h-6 text-indigo-600"/>
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        </div>
    );
}

/* ================= MINI LOADING (for stats update) ================= */
function MiniLoadingOverlay() {
    return (
        <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            exit={{opacity: 0}}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center"
        >
            <motion.div
                initial={{scale: 0.8, opacity: 0}}
                animate={{scale: 1, opacity: 1}}
                className="bg-white rounded-2xl shadow-2xl p-8 max-w-md mx-4"
            >
                <div className="text-center space-y-4">
                    <motion.div
                        animate={{rotate: 360}}
                        transition={{duration: 2, repeat: Infinity, ease: "linear"}}
                    >
                        <Loader className="w-12 h-12 text-indigo-600 mx-auto"/>
                    </motion.div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">
                            Yangilanmoqda
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                            Statistika qayta hisoblanmoqda...
                        </p>
                    </div>
                    <div className="flex justify-center gap-2">
                        {[0, 1, 2].map((i) => (
                            <motion.div
                                key={i}
                                className="w-2 h-2 rounded-full bg-indigo-600"
                                animate={{
                                    scale: [1, 1.3, 1],
                                    opacity: [0.5, 1, 0.5],
                                }}
                                transition={{
                                    duration: 1,
                                    repeat: Infinity,
                                    delay: i * 0.2,
                                }}
                            />
                        ))}
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

/* ================= PAGE ================= */
export default function HrDailyPage() {
    const router = useRouter();
    const [units, setUnits] = useState<HrUnit[]>([]);
    const [filteredUnits, setFilteredUnits] = useState<HrUnit[]>([]);
    const [selectedUnit, setSelectedUnit] = useState<HrUnit | null>(null);
    const [daily, setDaily] = useState<DailyRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingDaily, setLoadingDaily] = useState(false);
    const [loadingUnitsData, setLoadingUnitsData] = useState(false);
    const [selectedDate, setSelectedDate] = useState(
        dayjs().format("YYYY-MM-DD")
    );
// Filtrlash holatlari
    const [searchQuery, setSearchQuery] = useState("");
    const [filterType, setFilterType] = useState<"all" | "problem" | "good">("all");
    const [sortBy, setSortBy] = useState<"name" | "rate" | "absent">("rate");
    /* ================= INITIAL LOAD ================= */
    useEffect(() => {
        (async () => {
            try {
                setLoading(true);
                const summary = await fetchHrUnitsSummary(selectedDate);
// backend → frontend moslash
                const mapped: HrUnit[] = summary.map((u: any) => ({
                    id: u.unit_id,
                    name: u.name,
                    employeeCount: u.employeeCount,
                    presentCount: u.presentCount,
                    absentCount: u.absentCount,
                    lateCount: u.lateCount,
                    attendanceRate: u.attendanceRate,
                }));
                setUnits(mapped);
                setFilteredUnits(mapped);
            } catch (err) {
                console.error("❌ HR summary load error:", err);
            } finally {
                setLoading(false);
            }
        })();
    }, [selectedDate]);
    /* ================= FILTER AND SORT ================= */
    useEffect(() => {
        let result = [...units];
// Qidiruv
        if (searchQuery.trim()) {
            result = result.filter(unit =>
                unit.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                unit.department?.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }
// Filtrlash
        if (filterType === "problem") {
            result = result.filter(unit => (unit.attendanceRate || 0) < 80);
        } else if (filterType === "good") {
            result = result.filter(unit => (unit.attendanceRate || 0) >= 80);
        }
// Sortirovka
        result.sort((a, b) => {
            if (sortBy === "rate") {
                return (b.attendanceRate || 0) - (a.attendanceRate || 0);
            } else if (sortBy === "absent") {
                return (b.absentCount || 0) - (a.absentCount || 0);
            } else {
                return a.name.localeCompare(b.name);
            }
        });
        setFilteredUnits(result);
    }, [units, searchQuery, filterType, sortBy]);

    /* ================= LOAD DAILY ================= */
    async function loadDaily(unit: HrUnit, dateStr: string) {
        setSelectedUnit(unit);
        setLoadingDaily(true);
        try {
            const data = await fetchHrUnitDaily(unit.id, dateStr);
            setDaily(data);
        } catch (error) {
            console.error("Error loading daily ", error);
        } finally {
            setLoadingDaily(false);
        }
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

// Bo'lim uchun rang tanlash (YUMSHOQ RANGLAR)
    function getUnitColor(rate: number) {
        if (rate >= 90) return "from-blue-50 to-blue-100 border-blue-200 hover:border-blue-300";
        if (rate >= 80) return "from-indigo-50 to-indigo-100 border-indigo-200 hover:border-indigo-300";
        if (rate >= 70) return "from-purple-50 to-purple-100 border-purple-200 hover:border-purple-300";
        return "from-pink-50 to-pink-100 border-pink-200 hover:border-pink-300";
    }

// Foiz uchun progress rangi
    function getProgressColor(rate: number) {
        if (rate >= 90) return "bg-gradient-to-r from-blue-500 to-blue-600";
        if (rate >= 80) return "bg-gradient-to-r from-indigo-500 to-indigo-600";
        if (rate >= 70) return "bg-gradient-to-r from-purple-500 to-purple-600";
        return "bg-gradient-to-r from-pink-500 to-pink-600";
    }

// SHOW CREATIVE LOADING SCREEN
    if (loading || loadingUnitsData) {
        return <CreativeLoadingScreen/>;
    }
    /* ================= RENDER ================= */
    return (
        <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            className="
min-h-screen p-3 md:p-4 space-y-4
bg-gradient-to-br from-gray-50 via-white to-gray-100
"
        >
            {/* HEADER */}
            <div className="
sticky top-3 z-20
flex items-center gap-3
bg-white/95 backdrop-blur-sm
p-4 rounded-xl shadow-md border border-gray-200
">
                {selectedUnit && (
                    <Button
                        variant="ghost"
                        onClick={goBack}
                        className="gap-2 px-3 py-2 hover:bg-gray-100"
                    >
                        <ArrowLeft size={18}/> Orqaga
                    </Button>
                )}
                <h2 className="
text-xl md:text-2xl font-bold
bg-gradient-to-r from-indigo-700 to-purple-600
bg-clip-text text-transparent
flex gap-2.5 items-center
">
                    <Building2 className="w-6 h-6"/> HR — Kunlik Davomat
                </h2>
                {!selectedUnit && (
                    <div className="ml-auto flex items-center gap-2 text-sm text-gray-600">
                        <span className="font-medium">{filteredUnits.length}</span>
                        <span>ta bo'lim</span>
                    </div>
                )}
            </div>
            <AnimatePresence mode="wait">
                {/* ================= UNIT LIST ================= */}
                {!selectedUnit && (
                    <motion.div
                        key="units"
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: -20}}
                        className="space-y-4"
                    >
                        {/* STATS SUMMARY - IXCHAM */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <div
                                className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs text-gray-500 font-medium">Jami bo'limlar</p>
                                        <p className="text-xl font-bold text-gray-800 mt-1">{units.length}</p>
                                    </div>
                                    <div className="p-2.5 bg-indigo-50 rounded-lg">
                                        <Building2 className="w-5 h-5 text-indigo-600"/>
                                    </div>
                                </div>
                            </div>
                            <div
                                className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs text-gray-500 font-medium">Yaxshi (≥80%)</p>
                                        <p className="text-xl font-bold text-indigo-700 mt-1">
                                            {units.filter(u => (u.attendanceRate || 0) >= 80).length}
                                        </p>
                                    </div>
                                    <div className="p-2.5 bg-blue-50 rounded-lg">
                                        <CheckCircle className="w-5 h-5 text-blue-600"/>
                                    </div>
                                </div>
                            </div>
                            <div
                                className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs text-gray-500 font-medium">E'tibor (70-79%)</p>
                                        <p className="text-xl font-bold text-purple-700 mt-1">
                                            {units.filter(u => (u.attendanceRate || 0) >= 70 && (u.attendanceRate || 0) < 80).length}
                                        </p>
                                    </div>
                                    <div className="p-2.5 bg-purple-50 rounded-lg">
                                        <Clock className="w-5 h-5 text-purple-600"/>
                                    </div>
                                </div>
                            </div>
                            <div
                                className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs text-gray-500 font-medium">Muammo (70%)</p>
                                        <p className="text-xl font-bold text-pink-700 mt-1">
                                            {units.filter(u => (u.attendanceRate || 0) < 70).length}
                                        </p>
                                    </div>
                                    <div className="p-2.5 bg-pink-50 rounded-lg">
                                        <AlertTriangle className="w-5 h-5 text-pink-600"/>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {/* FILTERS AND SEARCH - IXCHAM */}
                        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                                {/* SEARCH BAR */}
                                <div className="flex-1">
                                    <div className="relative">
                                        <Search
                                            className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                                        <input
                                            type="text"
                                            placeholder="🔍 Bo'lim nomi bo'yicha qidirish..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="
w-full pl-10 pr-4 py-2.5 rounded-lg
border border-gray-200 bg-gray-50
focus:ring-2 focus:ring-indigo-300 focus:border-indigo-300
outline-none transition-all text-sm
"
                                        />
                                    </div>
                                </div>
                                {/* FILTER BUTTONS */}
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant={filterType === "all" ? "default" : "outline"}
                                        onClick={() => setFilterType("all")}
                                        size="sm"
                                        className={`gap-1.5 ${
                                            filterType === "all"
                                                ? "bg-indigo-600 hover:bg-indigo-700"
                                                : "bg-white hover:bg-gray-100 border-gray-200"
                                        }`}
                                    >
                                        <ListFilter className="w-3.5 h-3.5"/>
                                        Barcha
                                    </Button>
                                    <Button
                                        variant={filterType === "problem" ? "destructive" : "outline"}
                                        onClick={() => setFilterType("problem")}
                                        size="sm"
                                        className={`gap-1.5 ${
                                            filterType === "problem"
                                                ? "bg-pink-600 hover:bg-pink-700"
                                                : "bg-white hover:bg-pink-50 border-pink-200 text-pink-600"
                                        }`}
                                    >
                                        <AlertTriangle className="w-3.5 h-3.5"/>
                                        Muammo
                                    </Button>
                                    <Button
                                        variant={filterType === "good" ? "default" : "outline"}
                                        onClick={() => setFilterType("good")}
                                        size="sm"
                                        className={`gap-1.5 ${
                                            filterType === "good"
                                                ? "bg-blue-600 hover:bg-blue-700"
                                                : "bg-white hover:bg-blue-50 border-blue-200 text-blue-600"
                                        }`}
                                    >
                                        <CheckCircle className="w-3.5 h-3.5"/>
                                        Yaxshi
                                    </Button>
                                    {/* SORT DROPDOWN */}
                                    <div className="relative">
                                        <select
                                            value={sortBy}
                                            onChange={(e) => setSortBy(e.target.value as any)}
                                            className="appearance-none px-3 py-2 rounded-lg border border-gray-200 bg-white focus:ring-2 focus:ring-indigo-300 outline-none cursor-pointer font-medium text-gray-700 text-sm">
                                            <option value="rate">Foiz 🔽</option>
                                            <option value="absent">Absent 🔽</option>
                                            <option value="name">Nomi 🔤</option>
                                        </select>
                                        <ChevronDown
                                            className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"/>
                                    </div>
                                    {/* DATE PICKER — SUMMARY UCHUN */}
                                    {!selectedUnit && (
                                        <div className="ml-auto flex items-center gap-2">
                                            {/*<Calendar className="w-4 h-4 text-indigo-600"/>*/}
                                            <input
                                                type="date"
                                                value={selectedDate}
                                                onChange={(e) => setSelectedDate(e.target.value)}
                                                className="px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm font-medium shadow-sm focus:ring-2 focus:ring-indigo-300 outline-none"/>
                                        </div>
                                    )}

                                </div>
                            </div>
                        </div>
                        {/* UNITS GRID - 6 COLUMNS FOR MAXIMUM VISIBILITY */}
                        <div
                            className="grid gap-3 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 auto-rows-fr">
                            {filteredUnits.length === 0 ? (
// Empty state
                                <div
                                    className="col-span-full bg-white rounded-xl border-2 border-dashed border-gray-200 p-8 text-center">
                                    <Search className="w-10 h-10 text-gray-300 mx-auto mb-3"/>
                                    <p className="text-base font-medium text-gray-600">
                                        Hech narsa topilmadi
                                    </p>
                                    <p className="text-gray-500 mt-1 text-sm">
                                        Qidiruv so'rovingizga mos bo'lim topilmadi
                                    </p>
                                </div>
                            ) : (
// IXCHAM UNIT CARDS - TO'LIQ NOM VA KATTAROQ RAQAMLAR BILAN
                                filteredUnits.map((u) => {
                                    const rate = u.attendanceRate || 0;
                                    const colorClass = getUnitColor(rate);
                                    const progressColor = getProgressColor(rate);
                                    return (
                                        <motion.div
                                            key={u.id}
                                            whileHover={{y: -2, scale: 1.01}}
                                            whileTap={{scale: 0.99}}
                                            transition={{type: "spring", stiffness: 140}}>
                                            <Card
                                                onClick={() => loadDaily(u, selectedDate)}
                                                className={`cursor-pointer rounded-lg bg-gradient-to-br ${colorClass} 
                                                border hover:border-indigo-300 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden h-full flex flex-col p-0`}>
                                                <CardHeader className="space-y-2 p-4">
                                                    {/* HEADER - TO'LIQ NOM BILAN */}
                                                    <div className="flex items-start justify-between gap-3">
                                                        <div className="flex items-start gap-2.5 flex-1 min-w-0">
                                                            {/*<div className="p-2 bg-white/70 rounded-lg">*/}
                                                            {/*    <Building2 className="w-5 h-5 text-gray-700"/>*/}
                                                            {/*</div>*/}
                                                            <div className="min-w-0">
                                                                <CardTitle
                                                                    className="text-base font-bold text-gray-800">
                                                                    {u.name}
                                                                </CardTitle>
                                                                {u.department && (
                                                                    <p className="text-xs text-gray-600 mt-0.5">
                                                                        {u.department}
                                                                    </p>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {/* FOIZ KURSATGICH - PASTDA */}
                                                    {/*<div className="flex items-center justify-end mt-2">*/}
                                                    {/*<span className={`*/}
                                                    {/*px-3 py-1.5 rounded-lg font-bold text-base whitespace-nowrap*/}
                                                    {/*${rate >= 90 ? 'bg-blue-100 text-blue-700' :*/}
                                                    {/*    rate >= 80 ? 'bg-indigo-100 text-indigo-700' :*/}
                                                    {/*        rate >= 70 ? 'bg-purple-100 text-purple-700' :*/}
                                                    {/*            'bg-pink-100 text-pink-700'}`}>*/}
                                                    {/*{rate}%*/}
                                                    {/*</span>*/}
                                                    {/*</div>*/}
                                                    {/* EMPLOYEE COUNT - KATTAROQ SHRIFT */}
                                                    <div
                                                        className="flex items-center justify-between pt-3 border-t border-white/70">
                                                        <div className="flex items-center gap-2">
                                                            <Users className="w-5 h-5 text-gray-600"/>
                                                            <span className="text-sm font-bold text-gray-700">
                                                        {u.employeeCount || 0} xodim
                                                        </span>
                                                        </div>
                                                        <span className={`
                                                    px-3 py-1.5 rounded-lg font-bold text-base whitespace-nowrap
                                                    ${rate >= 90 ? 'bg-blue-100 text-blue-700' :
                                                            rate >= 80 ? 'bg-indigo-100 text-indigo-700' :
                                                                rate >= 70 ? 'bg-purple-100 text-purple-700' :
                                                                    'bg-pink-100 text-pink-700'}`}>
                                                    {rate}%
                                                    </span>
                                                    </div>
                                                    {/* ATTENDANCE BAR - KATTAROQ MA'LUMOTLAR */}
                                                    <div className="space-y-2 pt-3 border-t border-white/70">
                                                        <div
                                                            className="h-2.5 w-full bg-white/70 rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
                                                                style={{width: `${rate}%`}}
                                                            ></div>
                                                        </div>
                                                        <div
                                                            className="flex items-center justify-between text-sm font-bold text-gray-700">
                                                            <span className="flex items-center gap-1.5">
                                                            <CheckCircle className="w-4 h-4 text-green-600"/>
                                                                {u.presentCount || 0} keldi
                                                            </span>
                                                            <span className="flex items-center gap-1.5">
                                                                <XCircle className="w-4 h-4 text-pink-600"/>
                                                                {u.absentCount || 0} kelmadi
                                                            </span>
                                                        </div>
                                                    </div>
                                                </CardHeader>
                                            </Card>
                                        </motion.div>
                                    );
                                })
                            )}
                        </div>
                        {/* PAGINATION INFO */}
                        {filteredUnits.length > 0 && (
                            <div className="text-center text-xs text-gray-500 py-2">
                                <p>
                                    {filteredUnits.length} ta bo'limdan {filteredUnits.length} tasi ko'rsatilmoqda
                                </p>
                            </div>
                        )}
                    </motion.div>
                )}
                {/* ================= DAILY TABLE - UNCHANGED ================= */}
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
                                    <th className="p-3 text-center w-12">№</th>
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
                                        <td colSpan={6} className="text-center p-6 text-gray-500">
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
                                        <td className="p-3 text-center font-semibold text-gray-600">
                                            {idx + 1}
                                        </td>

                                        <td className="p-3">
                                            {item.full_name}
                                        </td>
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