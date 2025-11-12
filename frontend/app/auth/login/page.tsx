"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { setAccessToken, setRefreshToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
    const params = useSearchParams();
    const next = params.get("next");

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    const login = async (e: any) => {
        e.preventDefault();
        setErr("");
        setLoading(true);

        try {
            const res = await api.post(
                "/users/auth/login",
                new URLSearchParams({ username, password })
            );

            const { access_token, refresh_token, redirect_path } = res.data;
            setAccessToken(access_token);
            setRefreshToken(refresh_token);

            window.location.href = next || redirect_path || "/staff";
        } catch (e: any) {
            setErr(e?.response?.data?.detail || "Login xatosi");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
            <Card className="w-[380px] shadow-xl">
                <CardHeader>
                    <CardTitle className="text-center text-2xl">🔐 Tizimga kirish</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={login} className="space-y-4">
                        <Input value={username} onChange={e=>setUsername(e.target.value)} placeholder="Login" />
                        <Input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Parol" />
                        {err && <p className="text-red-500 text-sm">{err}</p>}
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? "Kutilmoqda..." : "Kirish"}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
