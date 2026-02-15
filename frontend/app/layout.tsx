import "./globals.css";
import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
    title: "OTM tizimi ishlab chiqish",
    description: "Universitet boshqaruv tizimi — Superadmin paneli",
};

export default function RootLayout({
                                       children,
                                   }: {
    children: React.ReactNode;
}) {
    return (
        <html lang="uz">
        <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
        <Toaster position="top-right" reverseOrder={false} />
        </body>
        </html>
    );
}
