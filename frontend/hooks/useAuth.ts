// frontend/hooks/useAuth.ts
"use client"; // Next.js da hooklar uchun shart

import { useEffect, useState } from "react";
import { getAccessToken } from "@/lib/auth"; // auth.ts dan chaqiramiz (yo'lni o'zingizga moslang)

export function useAuth() {
    const [token, setToken] = useState<string | null>(null);
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        setToken(getAccessToken());
    }, []);

    // Hydration mismatch oldini olish uchun mount bo'lmaguncha isAuthenticated: false
    return { 
        token, 
        isAuthenticated: isMounted ? !!token : false,
        isReady: isMounted 
    };
}