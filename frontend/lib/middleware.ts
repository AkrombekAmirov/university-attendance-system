// middleware.ts
import {NextRequest, NextResponse} from "next/server";

export function middleware(request: NextRequest) {
    const token = request.cookies.get("access_token")?.value;
    const pathname = request.nextUrl.pathname;

    const protectedPaths = ["/staff", "/admin_manage", "/hr"];
    const authPath = "/auth/login";

    const isProtected = protectedPaths.some((p) =>
        pathname.startsWith(p)
    );

    if (isProtected && !token) {
        return NextResponse.redirect(new URL(authPath, request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/staff/:path*", "/admin_manage/:path*", "/hr/:path*"],
};
