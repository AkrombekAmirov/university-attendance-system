from __future__ import annotations
from fastapi import APIRouter, Depends, Query

from backend.core.DatabaseService.base import get_db, DatabaseService
from backend.core.security import get_current_user
from backend.domain.user.models import User

from .controller import HRController
from datetime import date
from uuid import UUID

router = APIRouter(
    prefix="/hr",
    tags=["HR"]
)


# -------------------------------------------------
# Controller factory
# -------------------------------------------------
def get_ctrl(
        db: DatabaseService = Depends(get_db),
) -> HRController:
    return HRController(db=db)


# -------------------------------------------------
# HR endpoints
# -------------------------------------------------
@router.get("/units")
async def hr_units_list(
        current: User = Depends(get_current_user),
        ctrl: HRController = Depends(get_ctrl),
):
    """
    HR chap panel uchun bo‘limlar:
    - ATM
    - Bino komendantlari
    - va hokazo
    """
    return await ctrl.get_hr_units(current)


# =====================================================
# HR → KUNLIK DAVOMAT (REUSE)
# =====================================================
@router.get("/daily/page")
async def hr_unit_daily_attendance(
        unit_id: UUID = Query(...),
        day: date = Query(default_factory=date.today),
        current: User = Depends(get_current_user),
        ctrl: HRController = Depends(get_ctrl),
):
    """
    HR uchun kunlik keldi-ketdi.
    TurniketService dagi tayyor logika ishlatiladi.
    """
    return await ctrl.hr_unit_daily_attendance(
        current=current,
        unit_id=unit_id,
        day=day
    )


@router.get("/units/summary")
async def hr_units_daily_summary(
        day: date = Query(...),
        current: User = Depends(get_current_user),
        ctrl: HRController = Depends(get_ctrl),
):
    """
    HR uchun barcha bo‘limlar bo‘yicha kunlik statistika
    """
    return await ctrl.units_daily_summary(current, day)
