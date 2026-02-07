"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
    Users,
    CalendarDays,
    LayoutDashboard,
    LogOut,
} from "lucide-react";

import { clearTokens } from "@/lib/auth";

type Props = {
    children: ReactNode;
};

export default function HrLayout({ children }: Props) {
    const router = useRouter();

    function logout() {
        clearTokens();
        localStorage.removeItem("user");
        router.push("/auth/login");
    }

    return (
        <div className="min-h-screen flex bg-slate-100">
            {/* ================= SIDEBAR ================= */}
            <aside
                className="
                    w-64 shrink-0
                    bg-white border-r
                    flex flex-col
                "
            >
                {/* Logo / Title */}
                <div className="px-6 py-5 border-b">
                    <h1 className="text-xl font-bold text-indigo-700">
                        HR Panel
                    </h1>
                    <p className="text-xs text-slate-500">
                        Kadrlar bo‘limi
                    </p>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1">
                    <NavItem
                        href="/hr"
                        icon={<LayoutDashboard size={18} />}
                        label="Bo‘limlar"
                    />
                    <NavItem
                        href="/hr/daily"
                        icon={<Users size={18} />}
                        label="Kunlik davomat"
                    />
                    <NavItem
                        href="/hr/monthly"
                        icon={<CalendarDays size={18} />}
                        label="Oylik davomat"
                    />
                </nav>

                {/* Footer */}
                <div className="border-t px-4 py-4">
                    <button
                        onClick={logout}
                        className="
                            w-full flex items-center gap-2
                            px-3 py-2 rounded-lg
                            text-sm font-medium
                            text-red-600 hover:bg-red-50
                            transition
                        "
                    >
                        <LogOut size={18} />
                        Chiqish
                    </button>
                </div>
            </aside>

            {/* ================= MAIN ================= */}
            <main className="flex-1 flex flex-col">
                {/* Header */}
                <header
                    className="
                        h-16 bg-white border-b
                        flex items-center justify-between
                        px-6
                    "
                >
                    <h2 className="text-lg font-semibold text-slate-800">
                        Kadrlar boshqaruvi
                    </h2>

                    <div className="text-sm text-slate-500">
                        Davomat tizimi
                    </div>
                </header>

                {/* Content */}
                <section className="flex-1 p-6 overflow-auto">
                    {children}
                </section>
            </main>
        </div>
    );
}

/* ================= NAV ITEM ================= */

function NavItem({
                     href,
                     icon,
                     label,
                 }: {
    href: string;
    icon: ReactNode;
    label: string;
}) {
    return (
        <Link
            href={href}
            className="
                flex items-center gap-3
                px-3 py-2 rounded-lg
                text-slate-700
                hover:bg-indigo-50 hover:text-indigo-700
                transition
                text-sm font-medium
            "
        >
            {icon}
            {label}
        </Link>
    );
}
