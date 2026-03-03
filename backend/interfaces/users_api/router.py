from __future__ import annotations
from fastapi import APIRouter, Depends, Request, Response, Form
from typing import List
from uuid import UUID


from backend.core.DatabaseService.base import get_db, DatabaseService
from backend.core.security import get_current_user
from backend.domain.user.models import User

from .controller import UserAuthController
from .schemas import LoginIn, RegisterIn, TokenResponse, MeOut, UserCreateIn, UserOut, UserFullOut, UserUpdateIn

router = APIRouter(prefix="/users", tags=["Users & Auth"])


# ----------------------------
# Controller factory
# ----------------------------
def get_ctrl(
        request: Request,
        response: Response,
        db: DatabaseService = Depends(get_db),
) -> UserAuthController:
    return UserAuthController(db=db, request=request, response=response)


# ----------------------------
# Auth endpoints
# ----------------------------

@router.post("/auth/login", response_model=TokenResponse)
async def login_endpoint(
        ctrl: UserAuthController = Depends(get_ctrl),
        username: str = Form(...),
        password: str = Form(...),
):
    return await ctrl.login(LoginIn(username=username, password=password))


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_endpoint(
        ctrl: UserAuthController = Depends(get_ctrl),
        refresh_token: str = Form(None), # Endi ixtiyoriy, chunki cookie dan olinishi mumkin
):
    # Agar form data bo'lmasa, bo'sh string kelishi mumkin, controller ichida cookie tekshiriladi
    return await ctrl.refresh(refresh_token or "")


@router.post("/auth/logout_all")
async def logout_all_endpoint(
        ctrl: UserAuthController = Depends(get_ctrl),
        current: User = Depends(get_current_user),
):
    return await ctrl.logout_all(current)


@router.get("/auth/me", response_model=MeOut)
async def me_endpoint(
        ctrl: UserAuthController = Depends(get_ctrl),
        current: User = Depends(get_current_user),
):
    return await ctrl.me(current)


@router.post("/auth/register", response_model=MeOut)
async def register_endpoint(
        ctrl: UserAuthController = Depends(get_ctrl),
        current: User = Depends(get_current_user),
        payload: RegisterIn = Depends(),
):
    return await ctrl.register(payload, current)


# ----------------------------
# User creation and listing
# ----------------------------

@router.post("/create_simple", response_model=UserOut)
async def create_user_simple_endpoint(
    ctrl: UserAuthController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
    payload: UserCreateIn = Depends(UserCreateIn.as_form),
):
    return await ctrl.create_user_simple(payload, current)


@router.get("/get_users", response_model=List[UserOut])
async def get_users(
    ctrl: UserAuthController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
):
    return await ctrl.get_users(current)

@router.get("/list_full", response_model=List[UserFullOut])
async def list_full_for_users(
        current: User = Depends(get_current_user),
        c: UserAuthController = Depends(get_ctrl)
):
    return await c.list_full_for_users(current)

@router.put("/update_basic/{user_id}", response_model=UserOut)
async def update_user_basic_endpoint(
    user_id: UUID,
    payload: UserUpdateIn = Depends(UserUpdateIn.as_form),
    ctrl: UserAuthController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
):
    return await ctrl.update_user_basic(user_id, payload, current)
