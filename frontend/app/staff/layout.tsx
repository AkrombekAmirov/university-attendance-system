// app/staff/layout.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { fetchMe } from "@/lib/me";

export default function StaffLayout({ children }: { children: React.ReactNode }) {
    const [loading, setLoading] = useState(true);
    const [authorized, setAuthorized] = useState(false);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        async function check() {
            try {
                const me = await fetchMe();
                if (!me) throw new Error("No session");
                if (me.is_superadmin) {
                    router.replace("/admin_manage/users");
                    return;
                }
                setAuthorized(true);
            } catch {
                router.replace(`/auth/login?next=${pathname}`);
            } finally {
                setLoading(false);
            }
        }
        check();
    }, []);

    if (loading) return <div className="p-6">Loading...</div>;
    if (!authorized) return null;

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="p-4 bg-white shadow">Staff Portal</header>
            <main className="p-4">{children}</main>
        </div>
    );
}
