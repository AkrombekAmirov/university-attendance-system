from fastapi import APIRouter, Depends, Request, Query
from uuid import UUID
from backend.core.DatabaseService.base import get_db, DatabaseService
from backend.core.security import get_current_user
from backend.domain.user.models import User
from .controller import OrganizationController
from .schemas import (
    OrganizationCreateIn, OrganizationOut,
    OrgUnitCreateIn, OrgUnitOut,
    PositionCreateIn, PositionOut,
    AssignmentCreateIn, AssignmentOut,
    ReportingLinkCreateIn, ReportingLinkOut,
    PositionClosureCreateIn, PositionClosureOut
)
from typing import Annotated

router = APIRouter(prefix="/organization", tags=["Organization Management"])


# -------------------------------
# Dependency provider
# -------------------------------
def get_ctrl(request: Request, db: DatabaseService = Depends(get_db)) -> OrganizationController:
    return OrganizationController(db=db, request=request)


# ==========================================================
# ORGANIZATION ENDPOINTS
# ==========================================================
@router.post("/create", response_model=OrganizationOut, status_code=201)
async def create_organization(
    payload: OrganizationCreateIn = Depends(OrganizationCreateIn.as_form),
    ctrl: OrganizationController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
):
    return await ctrl.create_organization(payload, current)


@router.get("/list", response_model=list[OrganizationOut])
async def list_organizations(ctrl: OrganizationController = Depends(get_ctrl)):
    return await ctrl.list_organizations()


@router.get("/search", response_model=list[OrganizationOut])
async def search_organizations(
    keyword: str = Query(...),
    ctrl: OrganizationController = Depends(get_ctrl),
    current: User = Depends(get_current_user)
):
    return await ctrl.search_organizations(keyword)


# ==========================================================
# ORG UNIT ENDPOINTS
# ==========================================================
@router.post("/units/create", response_model=OrgUnitOut, status_code=201)
async def create_org_unit(
    payload: OrgUnitCreateIn = Depends(OrgUnitCreateIn.as_form),
    ctrl: OrganizationController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
):
    return await ctrl.create_org_unit(payload, current)


@router.get("/units/tree/{organization_id}", response_model=dict)
async def get_org_tree(
    organization_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current: User = Depends(get_current_user)
):
    return await ctrl.get_org_tree(organization_id)


# ==========================================================
# POSITION ENDPOINTS
# ==========================================================
@router.post("/positions/create")
async def create_position(
    payload: Annotated[PositionCreateIn, Depends(PositionCreateIn.as_form)],
    ctrl: OrganizationController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
):
    return await ctrl.create_position(payload, current)


@router.get("/positions/list", response_model=list[PositionOut])
async def get_positions_list(
    current_user: User = Depends(get_current_user),
    ctrl: OrganizationController = Depends(get_ctrl),
):
    return await ctrl.get_position_list(current_user)


# ==========================================================
# ASSIGNMENT ENDPOINTS
# ==========================================================
@router.post("/assignments/create", response_model=AssignmentOut, status_code=201)
async def create_assignment(
    payload: AssignmentCreateIn = Depends(AssignmentCreateIn.as_form),
    ctrl: OrganizationController = Depends(get_ctrl),
    current: User = Depends(get_current_user),
):
    return await ctrl.create_assignment(payload, current)


@router.get("/assignments/list", response_model=list[AssignmentOut])
async def list_assignments(ctrl: OrganizationController = Depends(get_ctrl)):
    return await ctrl.list_assignments()


# ==========================================================
# REPORTING LINK ENDPOINTS
# ==========================================================
@router.post("/reporting/create", response_model=ReportingLinkOut, status_code=201)
async def create_reporting_link(
    payload: ReportingLinkCreateIn = Depends(ReportingLinkCreateIn.as_form),
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.create_reporting_link(payload, current_user)


@router.get("/by-parent/{parent_position_id}", response_model=list[ReportingLinkOut])
async def get_links_by_parent(
    parent_position_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.get_reporting_links_by_parent(parent_position_id, current_user)


@router.get("/by-child/{child_position_id}", response_model=list[ReportingLinkOut])
async def get_links_by_child(
    child_position_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.get_reporting_links_by_child(child_position_id, current_user)


@router.get("/manager/{child_position_id}", response_model=ReportingLinkOut)
async def get_direct_manager(
    child_position_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.get_direct_manager(child_position_id, current_user)


# ==========================================================
# POSITION CLOSURE ENDPOINTS
# ==========================================================
@router.post("/create", response_model=PositionClosureOut, status_code=201)
async def create_position_closure(
    payload: PositionClosureCreateIn = Depends(PositionClosureCreateIn.as_form),
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.create_position_closure(payload, current_user)


@router.post("/bulk-create", response_model=list[PositionClosureOut], status_code=201)
async def bulk_create_position_closures(
    payloads: list[PositionClosureCreateIn],
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.bulk_create_position_closures(payloads, current_user)


@router.get("/by-parent/{parent_id}", response_model=list[PositionClosureOut])
async def get_closures_by_parent(
    parent_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.get_closures_by_parent(parent_id)


@router.get("/by-child/{child_id}", response_model=list[PositionClosureOut])
async def get_closures_by_child(
    child_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.get_closures_by_child(child_id)


@router.get("/direct-manager/{child_id}", response_model=PositionClosureOut)
async def get_direct_manager_closure(
    child_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.get_direct_manager_closure(child_id)


@router.get("/check-exists", response_model=bool)
async def check_if_closure_exists(
    parent_id: UUID = Query(...),
    child_id: UUID = Query(...),
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.check_if_closure_exists(parent_id, child_id)


@router.delete("/delete-by-position/{position_id}", response_model=int)
async def delete_position_closures_by_position(
    position_id: UUID,
    ctrl: OrganizationController = Depends(get_ctrl),
    current_user: User = Depends(get_current_user),
):
    return await ctrl.delete_position_closures_by_position(position_id)
