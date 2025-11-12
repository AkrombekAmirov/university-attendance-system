from fastapi import APIRouter, Depends, Request, Query
from backend.core.DatabaseService import get_db, DatabaseService
from backend.core.security import get_current_user
from backend.domain.user.models import User
from .controller import TurniketController
from .schemas import (
    StaffOut, OrgTreeResponse, DailyRowOut, MonthlyRowOut
)
from uuid import UUID
from datetime import date

router = APIRouter(prefix="/turniked", tags=["Turniket Staff"])


def ctrl(req: Request, db: DatabaseService = Depends(get_db)):
    return TurniketController(db=db, request=req)


# Auth
# @router.post("/auth/login", response_model=TurniketTokenResponse)
# async def login(
#     c: TurniketController = Depends(ctrl),
#     username: str = Form(...),
#     password: str = Form(...)
# ):
#     return await c.login(TurniketLoginIn(username=username, password=password))
#
# @router.get("/auth/me", response_model=MeTurniketOut)
# async def me(
#     c: TurniketController = Depends(ctrl),
#     current: User = Depends(get_current_user)
# ):
#     return await c.me(current)

# Org visibility
@router.get("/org/my-staff", response_model=list[StaffOut])
async def my_staff(
        unit_id: UUID | None = None,
        current: User = Depends(get_current_user),
        c: TurniketController = Depends(ctrl)
):
    return await c.my_staff(current, unit_id)


@router.get("/org/my-tree", response_model=OrgTreeResponse)
async def my_tree(
        c: TurniketController = Depends(ctrl),
        current: User = Depends(get_current_user)
):
    return await c.org_tree(current)


# Attendance
@router.get("/attendance/unit/daily", response_model=list[DailyRowOut])
async def unit_daily_attendance(
        unit_id: UUID = Query(...),
        day: date = Query(default_factory=date.today),
        current: User = Depends(get_current_user),
        c: TurniketController = Depends(ctrl)
):
    return await c.unit_daily_attendance(current, unit_id, day)


@router.get("/attendance/unit/monthly", response_model=list[MonthlyRowOut])
async def unit_monthly_attendance(
        unit_id: UUID = Query(...),
        year: int = Query(..., ge=2000, le=2100),
        month: int = Query(..., ge=1, le=12),
        current: User = Depends(get_current_user),
        c: TurniketController = Depends(ctrl)
):
    return await c.unit_monthly_attendance(current, unit_id, year, month)
