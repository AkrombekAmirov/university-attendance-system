from __future__ import annotations
from typing import List, Dict

# RBAC → redirect siyosati (server authoritative)
_ROLE_REDIRECTS: Dict[str, str] = {
    # High-level admins
    "RECTOR": "/admin/rektor/dashboard",
    "PRORECTOR": "/admin/prorektor/dashboard",
    "DIRECTOR": "/admin/management/dashboard",
    "BOSHQARMA_BOSHLIGI": "/admin/management/dashboard",
    "CENTER_HEAD": "/admin/center/dashboard",
    "MARKAZ_BOSHLIGI": "/admin/center/dashboard",
    "DEAN": "/admin/dekan/dashboard",
    "CHAIR_HEAD": "/admin/kafedra/dashboard",
    "KAFEDRA_MUDIRI": "/admin/kafedra/dashboard",

    # Staff & employees
    "TEACHER": "/teacher/dashboard",
    "SENIOR_SPECIALIST": "/employee/home",
    "WORKER": "/employee/home",
}

_DEFAULT_REDIRECT = "/user/home"
_SUPERADMIN_REDIRECT = "/admin_manage"


def decide_redirect(roles: List[str], is_superadmin: bool) -> str:
    """
    Superadmin har doim admin bosh paneliga yo'naltiriladi.
    Aks holda, ro'l kodlari bo'yicha mos sahifa tanlanadi.
    """
    if is_superadmin:
        return _SUPERADMIN_REDIRECT

    for code in roles:
        if code in _ROLE_REDIRECTS:
            return _ROLE_REDIRECTS[code]

    # fallback
    return _DEFAULT_REDIRECT


def register_redirect(role_code: str, url: str) -> None:
    """Dinamically yangi ro‘l uchun yo‘naltirish qo‘shish."""
    _ROLE_REDIRECTS[role_code.upper()] = url
