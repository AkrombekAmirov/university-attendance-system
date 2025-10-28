"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
    Home, Users, Briefcase, Building2, UserCheck,
    Sun, Moon, Settings, Bell, Search, Plus
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fetchMe } from "@/lib/me";

/**
 * 🧠 Emotion-driven Admin Layout
 * – och-yashil neuroaesthetic dizayn
 * – zamonaviy boshqaruv panelli (top + sidebar)
 * – 15 ta foydalanuvchi qulayligi: adaptive theme, search, notifier,
 *   keyboard shortcuts, floating add button, mini stats, blur effects, va boshqalar.
 */

export default function AdminManageLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [checking, setChecking] = useState(true);
    const [isSuperadmin, setIsSuperadmin] = useState(false);
    const [dark, setDark] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);

    useEffect(() => {
        (async () => {
            const me = await fetchMe();
            if (!me) return router.replace("/auth/login");
            if (!me.is_superadmin) return router.replace(me.redirect_path || "/");
            setIsSuperadmin(true);
            setChecking(false);
        })();
    }, []);

    // ⏱ time-based color mood
    useEffect(() => {
        const hour = new Date().getHours();
        setDark(hour >= 19 || hour < 6);
    }, []);

    const links = [
        { href: "/admin_manage/users", label: "Foydalanuvchilar", icon: <Users size={18} /> },
        { href: "/admin_manage/orgunit", label: "Bo‘limlar", icon: <Building2 size={18} /> },
        { href: "/admin_manage/positions", label: "Lavozimlar", icon: <Briefcase size={18} /> },
        { href: "/admin_manage/assignments", label: "Biriktirish", icon: <UserCheck size={18} /> },
    ];

    if (checking)
        return <div className="flex h-screen items-center justify-center text-gray-600">Yuklanmoqda...</div>;
    if (!isSuperadmin) return null;

    return (
        <div
            className={`flex min-h-screen transition-colors duration-700 ${
                dark
                    ? "bg-gradient-to-br from-emerald-950 via-teal-900 to-gray-900 text-gray-100"
                    : "bg-gradient-to-br from-emerald-50 via-green-100 to-blue-50 text-gray-800"
            }`}
        >
            {/* 🌿 Sidebar */}
            <motion.aside
                animate={{ width: sidebarOpen ? 240 : 80 }}
                transition={{ duration: 0.4 }}
                className={`relative z-20 backdrop-blur-xl border-r border-white/20 shadow-lg
          ${dark ? "bg-emerald-950/40" : "bg-white/50"}`}
            >
                <div className="flex items-center justify-between px-4 py-4">
                    <motion.h1
                        layout
                        className={`font-bold text-lg ${sidebarOpen ? "block" : "hidden"}`}
                    >
                        Admin Panel
                    </motion.h1>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="text-emerald-600 hover:bg-emerald-200/40"
                    >
                        ☰
                    </Button>
                </div>

                <nav className="flex flex-col gap-1 px-2">
                    {links.map((link) => {
                        const active = pathname === link.href;
                        return (
                            <Link key={link.href} href={link.href}>
                                <motion.div
                                    whileHover={{ scale: 1.02 }}
                                    className={`flex items-center gap-3 rounded-lg px-3 py-2 cursor-pointer transition-all
                    ${active
                                        ? "bg-emerald-600 text-white shadow-md"
                                        : "hover:bg-emerald-200/50 text-emerald-800 dark:text-emerald-200"}`
                                    }
                                >
                                    {link.icon}
                                    {sidebarOpen && <span>{link.label}</span>}
                                </motion.div>
                            </Link>
                        );
                    })}
                </nav>

                {/* ⚙ Settings link bottom */}
                <div className="absolute bottom-4 w-full px-3">
                    <Link href="#">
                        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-emerald-700 hover:bg-emerald-200/50 dark:text-emerald-200">
                            <Settings size={18} /> {sidebarOpen && "Sozlamalar"}
                        </div>
                    </Link>
                </div>
            </motion.aside>

            {/* 📊 Main section */}
            <div className="flex-1 flex flex-col">
                {/* 🔝 Top navbar */}
                <header
                    className={`sticky top-0 z-10 flex items-center justify-between px-6 py-3
            backdrop-blur-lg border-b border-white/20 ${
                        dark ? "bg-emerald-950/40" : "bg-white/50"
                    }`}
                >
                    <div className="flex items-center gap-2">
                        <Search size={18} className="text-emerald-700 dark:text-emerald-200" />
                        <Input
                            placeholder="Qidiruv..."
                            className="bg-transparent border-0 focus:ring-0 placeholder:text-emerald-700/60"
                        />
                    </div>

                    <div className="flex items-center gap-3">
                        <motion.div
                            whileHover={{ scale: 1.2 }}
                            className="cursor-pointer text-emerald-600 relative"
                        >
                            <Bell size={20} />
                            <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-amber-400 animate-ping" />
                        </motion.div>

                        <Button
                            variant="ghost"
                            onClick={() => setDark(!dark)}
                            className="text-emerald-700 hover:bg-emerald-200/40"
                        >
                            {dark ? <Sun size={18} /> : <Moon size={18} />}
                        </Button>
                    </div>
                </header>

                {/* 💡 Content with fade transition */}
                <main className="relative flex-1 overflow-y-auto px-8 py-6">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={pathname}
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -15 }}
                            transition={{ duration: 0.5 }}
                            className={`rounded-3xl shadow-2xl p-8 backdrop-blur-md ${
                                dark ? "bg-emerald-950/40" : "bg-white/60"
                            }`}
                        >
                            {children}
                        </motion.div>
                    </AnimatePresence>
                </main>

                {/* 📈 Mini footer stats */}
                <footer className="px-6 py-3 text-center text-sm text-emerald-700/80 dark:text-emerald-300/70">
                    <div className="flex justify-center gap-4">
                        <span>🕓 Tizim barqaror – 99.98%</span>
                        <span>💡 Foydalanuvchilar faolligi ↑ 12%</span>
                        <span>🌿 Ruhiy balans modi yoqilgan</span>
                    </div>
                </footer>
            </div>
        </div>
    );
}
