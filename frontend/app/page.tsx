"use client";

import { useEffect } from "react";
import { fetchMe } from "@/lib/me";

export default function Home() {
    useEffect(() => {
        (async () => {
            const me = await fetchMe();
            if (me?.redirect_path) {
                window.location.replace(me.redirect_path);
            } else {
                window.location.replace("/auth/login");
            }
        })();
    }, []);
    return null;
}
