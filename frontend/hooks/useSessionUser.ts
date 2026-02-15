// src/hooks/useSessionUser.ts
import { useEffect, useState } from "react";

type SessionUser = {
    id: string;
    name: string;
    email: string;
    is_superadmin: boolean;
    redirect_path: string;
};

export function useSessionUser() {
    const [user, setUser] = useState<SessionUser | null>(null);

    useEffect(() => {
        const stored = localStorage.getItem("user");
        if (stored) {
            setUser(JSON.parse(stored));
        }
    }, []);

    return { user, isLoading: !user };
}
