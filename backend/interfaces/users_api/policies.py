from typing import Optional, Dict

_ROLE_REDIRECTS: Dict[str, str] = {
    "RECTOR": "/admin/rektor/dashboard",
    "PRORECTOR": "/admin/prorektor/dashboard",
    "DIRECTOR": "/admin/management/dashboard",
    "BOSHQARMA_BOSHLIGI": "/admin/management/dashboard",
    "CENTER_HEAD": "/admin/center/dashboard",
    "MARKAZ_BOSHLIGI": "/admin/center/dashboard",
    "DEAN": "/admin/dekan/dashboard",
    "CHAIR_HEAD": "/admin/kafedra/dashboard",
    "KAFEDRA_MUDIRI": "/admin/kafedra/dashboard",
    "TEACHER": "/teacher/dashboard",
    "SENIOR_SPECIALIST": "/employee/home",
    "WORKER": "/employee/home",
}

def decide_redirect(
    *,
    is_superadmin: bool,
    meta: Optional[dict],
) -> str:
    """
    Server-authoritative redirect logic.
    Priority:
    1. Superadmin
    2. HR (meta.role)
    3. Default staff
    """

    # 1️⃣ Superadmin
    if is_superadmin:
        return "/admin_manage/users"

    # 2️⃣ HR (kadrlar)
    if meta and meta.get("role") == "HR_MANAGER":
        return "/hr"

    # 3️⃣ Default (staff)
    return "/staff/users"
