'use client';

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { setAccessToken, setRefreshToken } from "@/lib/auth";

type LoginForm = {
    username: string;
    password: string;
};

export default function LoginPage() {
    const { register, handleSubmit } = useForm<LoginForm>();
    const router = useRouter();
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const onSubmit = async (data: LoginForm) => {
        setLoading(true);
        setError("");
        try {
            const res = await api.post("/users/auth/login", new URLSearchParams(data));
            const { access_token, refresh_token, redirect_path, ...user } = res.data;

            setAccessToken(access_token);
            setRefreshToken(refresh_token);
            localStorage.setItem("user", JSON.stringify(user));

            window.location.href = redirect_path; // Dinamik redirect

        } catch (err: any) {
            setError("Login yoki parol xato!");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto mt-24 p-4 border shadow rounded-xl bg-white">
            <h1 className="text-2xl font-bold mb-4">Tizimga kirish</h1>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <input {...register("username")} placeholder="Foydalanuvchi nomi" className="w-full border p-2 rounded" />
                <input {...register("password")} type="password" placeholder="Parol" className="w-full border p-2 rounded" />
                {error && <p className="text-red-500">{error}</p>}
                <button disabled={loading} className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
                    {loading ? "Yuklanmoqda..." : "Kirish"}
                </button>
            </form>
        </div>
    );
}
