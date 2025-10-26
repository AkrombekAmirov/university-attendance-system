// app/admin_manage/layout.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { fetchMe } from "@/lib/me";
import { Button } from "@/components/ui/button";

export default function AdminManageLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [checking, setChecking] = useState(true);
    const [isSuperadmin, setIsSuperadmin] = useState(false);

    useEffect(() => {
        (async () => {
            const me = await fetchMe();
            if (!me) {
                router.replace("/auth/login");
                return;
            }

            if (!me.is_superadmin) {
                router.replace(me.redirect_path || "/");
                return;
            }

            setIsSuperadmin(true);
            setChecking(false);
        })();
    }, []);

    const links = [
        { href: "/admin_manage/users", label: "👤 Foydalanuvchilar" },
        // { href: "/admin_manage/roles", label: "📄 Rollar" },
        // { href: "/admin_manage/organization", label: "🏢 Tashkilotlar" }, // ✅ YANGI QATOR
        {href: "/admin_manage/orgunit", label: "🏢 Tashkilot bo'limlari"},
        {href: "/admin_manage/positions", label: "💼 Tashkilot lavozimlari"},
        {href: "/admin_manage/assignments", label: "Lavozimga biriktirish"},
        // {href: "/admin_manage/reporting-links", label: "Rahbar-Bo'ysunuvchi Aloqasini Yaratish"},
    ];

    if (checking) return <div className="p-10">Yuklanmoqda...</div>;
    if (!isSuperadmin) return null;

    return (
        <div className="min-h-screen bg-slate-50">
            <nav className="border-b bg-white px-6 py-3 flex gap-4 shadow-sm">
                {links.map((link) => (
                    <Link key={link.href} href={link.href}>
                        <Button variant={pathname === link.href ? "default" : "outline"}>{link.label}</Button>
                    </Link>
                ))}
            </nav>
            <main className="px-6 py-8">{children}</main>
        </div>
    );
}
