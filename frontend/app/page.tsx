'use client';

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { setAccessToken, setRefreshToken } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import {
    User, Lock, LogIn, Eye, EyeOff, Check, UserCircle2, Trash2, ChevronRight
} from "lucide-react";

type LoginForm = {
    username: string;
    password: string;
    rememberMe: boolean;
};

type SavedUser = {
    username: string;
    password: string;
    lastLogin: string;
    avatar?: string;
};

// 🛡️ DYNAMIC COOKIE SETTER (Barcha muammolarni hal qiluvchi funksiya)
function setBulletproofCookie(name: string, value: string, days: number = 1) {
    const maxAge = days * 24 * 60 * 60;
    // Sayt HTTPS da ishlayotganini tekshiramiz
    const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';

    // Agar HTTPS bo'lsa Secure qo'shamiz, bo'lmasa yo'q. Bu HTTP da ham ishlashini kafolatlaydi!
    const secureFlag = isHttps ? 'Secure;' : '';

    document.cookie = `${name}=${value}; path=/; max-age=${maxAge}; SameSite=Lax; ${secureFlag}`;
}

export default function LoginPage() {
    const { register, handleSubmit, setValue } = useForm<LoginForm>();
    const router = useRouter();

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [savedUsers, setSavedUsers] = useState<SavedUser[]>([]);
    const [showSavedUsers, setShowSavedUsers] = useState(false);
    const [selectedUser, setSelectedUser] = useState<SavedUser | null>(null);

    useEffect(() => {
        const saved = localStorage.getItem("saved_users");
        if (saved) {
            try {
                const users = JSON.parse(saved);
                setSavedUsers(users);
                setShowSavedUsers(users.length > 0);
            } catch {
                setSavedUsers([]);
            }
        }
    }, []);

    useEffect(() => {
        if (selectedUser) {
            setValue("username", selectedUser.username);
            setValue("password", selectedUser.password);
            setValue("rememberMe", true);
        }
    }, [selectedUser, setValue]);

    const onSubmit = async (data: LoginForm) => {
        setLoading(true);
        setError("");

        try {
            const res = await api.post(
                "/users/auth/login",
                new URLSearchParams({
                    username: data.username,
                    password: data.password,
                })
            );

            const { access_token, refresh_token, redirect_path, ...user } = res.data;

            // 1. Tizim xotiralariga yozish
            setAccessToken(access_token);
            setRefreshToken(refresh_token);
            localStorage.setItem("user", JSON.stringify(user));

            // 2. 🛡️ ENG ASOSIY QADAM: Middleware o'qiy olishi uchun majburiy Cookie yozish
            setBulletproofCookie("access_token", access_token, 1);
            setBulletproofCookie("refresh_token", refresh_token, 7);

            if (data.rememberMe) {
                saveUserCredentials(data.username, data.password);
            }

            // 3. Next.js router orqali yo'naltirish (Sahifani qotirmaslik uchun)
            // window.location.href o'rniga router.push ishlatsak, tizim tezroq ishlaydi
            window.location.href = redirect_path || "/staff";

        } catch {
            setError("Login yoki parol xato!");
        } finally {
            setLoading(false);
        }
    };

    const saveUserCredentials = (username: string, password: string) => {
        const newUser: SavedUser = {
            username,
            password,
            lastLogin: new Date().toISOString(),
        };

        const existingIndex = savedUsers.findIndex(u => u.username === username);
        let updatedUsers: SavedUser[];

        if (existingIndex !== -1) {
            updatedUsers = [...savedUsers];
            updatedUsers[existingIndex] = newUser;
        } else {
            updatedUsers = [...savedUsers, newUser];
        }

        updatedUsers.sort((a, b) => new Date(b.lastLogin).getTime() - new Date(a.lastLogin).getTime());
        setSavedUsers(updatedUsers);
        localStorage.setItem("saved_users", JSON.stringify(updatedUsers));
    };

    const deleteSavedUser = (username: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const updated = savedUsers.filter(u => u.username !== username);
        setSavedUsers(updated);
        localStorage.setItem("saved_users", JSON.stringify(updated));

        if (selectedUser?.username === username) {
            setSelectedUser(null);
            setValue("username", "");
            setValue("password", "");
        }

        if (updated.length === 0) setShowSavedUsers(false);
    };

    const quickLogin = async (user: SavedUser) => {
        setLoading(true);
        setError("");

        try {
            const res = await api.post(
                "/users/auth/login",
                new URLSearchParams({
                    username: user.username,
                    password: user.password,
                })
            );

            const { access_token, refresh_token, redirect_path, ...userData } = res.data;

            // Xotiraga yozish
            setAccessToken(access_token);
            setRefreshToken(refresh_token);
            localStorage.setItem("user", JSON.stringify(userData));

            // 🛡️ Middleware uchun majburiy Cookie yozish
            setBulletproofCookie("access_token", access_token, 1);
            setBulletproofCookie("refresh_token", refresh_token, 7);

            saveUserCredentials(user.username, user.password);

            window.location.href = redirect_path || "/staff";

        } catch {
            setError("Avtomatik kirish xato! Iltimos qayta urinib ko'ring.");
        } finally {
            setLoading(false);
        }
    };

    const getUserInitials = (username: string) => username.slice(0, 2).toUpperCase();

    const formatLastLogin = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins} daqiqa oldin`;
        if (diffHours < 24) return `${diffHours} soat oldin`;
        if (diffDays === 1) return "Kecha";
        if (diffDays < 7) return `${diffDays} kun oldin`;
        return date.toLocaleDateString('uz-UZ');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">

                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200 }} className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl shadow-lg mb-4">
                        <UserCircle2 className="w-10 h-10 text-white" />
                    </motion.div>
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">Xush kelibsiz!</h1>
                    <p className="text-gray-600">Davom etish uchun tizimga kiring</p>
                </div>

                <AnimatePresence mode="wait">
                    {showSavedUsers && savedUsers.length > 0 ? (
                        /* Saved Users List */
                        <motion.div key="saved-users" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="bg-white rounded-2xl shadow-xl p-6 space-y-4">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-semibold text-gray-800">Saqlangan hisoblar</h2>
                                <button onClick={() => setShowSavedUsers(false)} className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">Boshqa hisob</button>
                            </div>

                            <div className="space-y-3">
                                {savedUsers.map((user, index) => (
                                    <motion.button key={user.username} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.1 }} onClick={() => quickLogin(user)} disabled={loading} className="w-full group relative">
                                        <div className="flex items-center gap-4 p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border-2 border-gray-200 hover:border-indigo-300 hover:shadow-md transition-all duration-200">
                                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg group-hover:scale-110 transition-transform">
                                                {getUserInitials(user.username)}
                                            </div>
                                            <div className="flex-1 text-left">
                                                <p className="font-semibold text-gray-800 text-lg">{user.username}</p>
                                                <p className="text-sm text-gray-500">{formatLastLogin(user.lastLogin)}</p>
                                            </div>
                                            <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
                                            <button onClick={(e) => deleteSavedUser(user.username, e)} className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/80 hover:bg-red-50 border border-gray-200 hover:border-red-300 opacity-0 group-hover:opacity-100 transition-all">
                                                <Trash2 className="w-4 h-4 text-red-500" />
                                            </button>
                                        </div>
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>
                    ) : (
                        /* Login Form */
                        <motion.div key="login-form" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="bg-white rounded-2xl shadow-xl p-8">
                            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                                {/* Username */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Foydalanuvchi nomi</label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input {...register("username")} placeholder="Ismingizni kiriting" className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 outline-none transition-all placeholder:text-gray-400" />
                                    </div>
                                </div>

                                {/* Password */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Parol</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input {...register("password")} type={showPassword ? "text" : "password"} placeholder="Parolingizni kiriting" className="w-full pl-11 pr-12 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 outline-none transition-all placeholder:text-gray-400" />
                                        <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                        </button>
                                    </div>
                                </div>

                                {/* Remember Me */}
                                <div className="flex items-center justify-between">
                                    <label className="flex items-center gap-3 cursor-pointer group">
                                        <div className="relative">
                                            <input type="checkbox" {...register("rememberMe")} className="sr-only peer" />
                                            <div className="w-5 h-5 border-2 border-gray-300 rounded peer-checked:bg-indigo-600 peer-checked:border-indigo-600 transition-all"></div>
                                            <Check className="absolute top-0.5 left-0.5 w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity" />
                                        </div>
                                        <span className="text-sm text-gray-600 group-hover:text-gray-800">Parolni saqlash</span>
                                    </label>
                                    {savedUsers.length > 0 && (
                                        <button type="button" onClick={() => setShowSavedUsers(true)} className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                                            Saqlangan hisoblar
                                        </button>
                                    )}
                                </div>

                                {/* Errors */}
                                <AnimatePresence>
                                    {error && (
                                        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl text-sm text-center">
                                            {error}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* Submit */}
                                <button type="submit" disabled={loading} className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 focus:ring-4 focus:ring-indigo-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2">
                                    {loading ? (
                                        <>
                                            <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                                            <span>Yuklanmoqda...</span>
                                        </>
                                    ) : (
                                        <>
                                            <LogIn className="w-5 h-5" />
                                            <span>Kirish</span>
                                        </>
                                    )}
                                </button>
                            </form>
                        </motion.div>
                    )}
                </AnimatePresence>

                <p className="text-center text-sm text-gray-500 mt-6">© 2026 Nazorat tizimi. Barcha huquqlar himoyalangan.</p>
            </motion.div>
        </div>
    );
}