// app/staff/layout.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from 'next/navigation';
import { fetchMe } from "@/lib/me";
import { LogOut, Home } from 'lucide-react';
import { Button } from "@/components/ui/button";

export default function StaffLayout({ children }: { children: React.ReactNode }) {
    const [loading, setLoading] = useState(true);
    const [authorized, setAuthorized] = useState(false);
    const [userName, setUserName] = useState("");

    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        async function check() {
            try {
                const me = await fetchMe();
                if (!me) throw new Error();
                if (me.is_superadmin) {
                    router.replace("/admin_manage/users");
                    return;
                }
                setUserName(me.full_name || me.email || "Foydalanuvchi");
                setAuthorized(true);
            } catch {
                router.replace(`/?next=${encodeURIComponent(pathname)}`);
            } finally {
                setLoading(false);
            }
        }
        check();
    }, [pathname, router]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center">
                <div className="text-center space-y-3">
                    <div className="w-12 h-12 rounded-full border-4 border-emerald-300 border-t-emerald-600 animate-spin mx-auto"></div>
                    <p className="text-emerald-800 font-medium">Tizim yuklanmoqda...</p>
                </div>
            </div>
        );
    }

    if (!authorized) return null;

    return (
        <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50">

            {/* HEADER */}
            <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-emerald-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-emerald-100 rounded-xl">
                            <Home size={22} className="text-emerald-700" />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-emerald-900">Xodimlar Portali</h1>
                            <p className="text-xs text-emerald-700">{userName}</p>
                        </div>
                    </div>

                    <Button
                        className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all shadow-md hover:shadow-lg"
                        onClick={() => router.replace("/")}
                    >
                        <LogOut size={16} />
                        Chiqish
                    </Button>
                </div>
            </header>

            {/* MAIN CONTENT */}
            <main className="py-8 px-4 md:px-8">
                {children}
            </main>

            {/* FOOTER */}
            <footer className="mt-12 border-t border-emerald-200 bg-white/50 backdrop-blur">
                <div className="text-center py-5 text-sm text-emerald-700">
                    © 2025 Xodimlar Boshqarish Tizimi. Barcha huquqlar himoyalangan.
                </div>
            </footer>
        </div>
    );
}