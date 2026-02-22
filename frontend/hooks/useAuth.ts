import { useEffect, useState } from "react";

export function useAuth() {
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        setToken(localStorage.getItem("access_token"));
    }, []);

    return { token, isAuthenticated: !!token };
}
