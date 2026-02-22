"use client";
import Link from "next/link";

export default function StaffHome() {
    return (
        <div>
            <h1 className="text-xl font-bold mb-4">👤 Staff Dashboard</h1>
            <Link className="text-blue-600 underline" href="/staff/users">
                My Subordinates
            </Link>
        </div>
    );
}
