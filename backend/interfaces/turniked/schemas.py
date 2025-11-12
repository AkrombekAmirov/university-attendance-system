from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List


class TurniketLoginIn(BaseModel):
    username: str
    password: str


class TurniketTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    redirect_path: str
    expires_in: int


class MeTurniketOut(BaseModel):
    id: UUID
    username: str
    full_name: Optional[str]
    position: Optional[str]
    org_unit_id: Optional[UUID]


class StaffOut(BaseModel):
    id: UUID
    full_name: str
    position: Optional[str]


class OrgNode(BaseModel):
    position_id: UUID
    position: str
    users: List[StaffOut]
    children: List["OrgNode"] = []


class OrgTreeOut(BaseModel):
    root: OrgNode


class StaffNode(BaseModel):
    id: UUID
    full_name: str
    position: Optional[str] = None


class PositionNode(BaseModel):
    id: UUID
    title: str
    staff: List[StaffNode]
    children: List["PositionNode"] = []


class OrgUnitNode(BaseModel):
    id: UUID
    name: str
    unit_type: str
    positions: List[PositionNode]
    children: List["OrgUnitNode"] = []


class OrgTreeResponse(BaseModel):
    id: UUID
    full_name: str
    position: Optional[str] = None
    units: List[OrgUnitNode]
OrgUnitNode.model_rebuild()
PositionNode.model_rebuild()


class DailyRowOut(BaseModel):
    user_id: UUID
    full_name: str
    position: Optional[str] = None
    event_date: str
    first_entry: Optional[str] = None
    last_exit: Optional[str] = None
    worked_minutes: int
    was_late: bool
    left_early: bool
    entries_count: int

class MonthlyRowOut(BaseModel):
    user_id: UUID
    full_name: str
    position: Optional[str] = None
    year: int
    month: int
    present_days: int
    late_days: int
    early_leave_days: int
    absent_days: int
    total_worked_minutes: int
    total_expected_minutes: int
    attendance_rate: float
    punctuality_score: float
