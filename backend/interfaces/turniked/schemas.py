from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date

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
    first_device: Optional[str] = None
    last_device: Optional[str] = None
    worked_minutes: int
    was_late: bool
    left_early: bool
    entries_count: int

class MonthlyDayRowOut(BaseModel):
    date: date
    weekday: int
    weekday_name: str
    first_entry: Optional[datetime]
    last_exit: Optional[datetime]
    worked_minutes: int
    was_late: bool
    left_early: bool
    is_absent: bool


class MonthlyRowOut(BaseModel):
    user_id: UUID
    full_name: str
    position: Optional[str]
    year: int
    month: int

    total_present_days: int
    total_absent_days: int
    total_worked_minutes: int
    total_expected_minutes: int

    days: List[MonthlyDayRowOut]
