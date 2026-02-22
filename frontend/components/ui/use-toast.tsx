"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Toast = {
    id: number;
    title: string;
    description?: string;
};

const ToastContext = createContext<any>(null);

export const ToastProvider = ({ children }: { children: ReactNode }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = (title: string, description?: string) => {
        const id = Date.now();
        setToasts((prev) => [...prev, { id, title, description }]);
        setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
    };

    return (
        <ToastContext.Provider value={{ addToast }}>
            {children}
            <div className="fixed top-4 right-4 space-y-2 z-[9999]">
                <AnimatePresence>
                    {toasts.map((toast) => (
                        <motion.div
                            key={toast.id}
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.3 }}
                            className="backdrop-blur-lg bg-white/70 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-100 rounded-xl p-4 shadow-lg"
                        >
                            <p className="font-semibold">{toast.title}</p>
                            {toast.description && <p className="text-sm opacity-80">{toast.description}</p>}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
};

export const useToast = () => useContext(ToastContext);
