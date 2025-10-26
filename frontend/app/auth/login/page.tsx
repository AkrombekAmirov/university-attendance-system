"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { setAccessToken, setRefreshToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setErr("");
        setLoading(true);
        try {
            const res = await api.post("/users/auth/login", new URLSearchParams({ username, password }));
            const { access_token, refresh_token, redirect_path } = res.data || {};
            if (!access_token || !refresh_token) throw new Error("Invalid response");
            setAccessToken(access_token);
            setRefreshToken(refresh_token);
            window.location.href = redirect_path || "/";
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
                    <form onSubmit={handleLogin} className="space-y-4">
                        <Input placeholder="Login" value={username} onChange={(e) => setUsername(e.target.value)} />
                        <Input type="password" placeholder="Parol" value={password} onChange={(e) => setPassword(e.target.value)} />
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
