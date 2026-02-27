// frontend/lib/security/auth.ts
import { NextResponse, type NextRequest } from 'next/server';

const PROTECTED_PATHS = ['/staff', '/admin_manage', '/hr'];
const AUTH_PATH = '/auth/login';

export function checkAuth(request: NextRequest): NextResponse | null {
    const pathname = request.nextUrl.pathname;
    const token = request.cookies.get("access_token")?.value;

    const isProtected = PROTECTED_PATHS.some((p) => pathname.startsWith(p));
    const isAuthPage = pathname.startsWith(AUTH_PATH);

    // 1. Himoyalangan sahifaga tokensiz kirsa -> Loginga qaytarish
    if (isProtected && !token) {
        return NextResponse.redirect(new URL(AUTH_PATH, request.url));
    }

    // 2. Tizimga kirgan (tokeni bor) foydalanuvchi Login sahifasiga kelib qolsa -> Ichkariga kiritish (Loop ni buzish)
    if (isAuthPage && token) {
        return NextResponse.redirect(new URL('/staff', request.url));
    }

    return null;
}