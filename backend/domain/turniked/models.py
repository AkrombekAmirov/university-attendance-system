from sqlmodel import SQLModel, Field, Index
from datetime import datetime, date, time
from typing import Optional, Any, Dict
from uuid import UUID, uuid4
from sqlalchemy import JSON
from backend.domain.organization.models import OrgUnit
from backend.domain.user.models import User


class BaseModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    event_date: Optional[date] = Field(default_factory=lambda: datetime.utcnow().date(), index=True)
    event_time: Optional[time] = Field(default_factory=lambda: datetime.utcnow().time(), index=True)

    class Config:
        arbitrary_types_allowed = True

    timecontrol: Optional[str] = Field(
        default=None,
        description="Legacy time control field (e.g., 20251030|085532)"
    )

    extra_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column_kwargs={"nullable": True},
        sa_type=JSON,
        description="Extensible metadata for analytics/debugging"
    )

    source_system: Optional[str] = Field(
        default="device",
        description="Indicates where the data originated"
    )

    timezone: Optional[str] = Field(default="Asia/Tashkent", description="IANA timezone string")
    is_deleted: bool = Field(default=False, index=True)
    hash_code: Optional[str] = Field(default=None, index=True, description="Unique content hash/fingerprint")


class AttendanceEvent(BaseModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", index=True)
    device_id: UUID = Field(foreign_key="device.id", index=True)

    direction: str = Field(index=True, description="entry / exit")
    turniked_id: str = Field(index=True, description="turniked ID")


class DailyAttendance(BaseModel, table=True):
    __table_args__ = (
        Index("ix_user_org_unit_event_date_time_device", "user_id", "org_unit_id", "event_date", "event_time", "device_id"),
    )
    user_id: UUID = Field(foreign_key="user.id", index=True)
    org_unit_id: UUID = Field(foreign_key="org_unit.id", index=True)
    device_id: UUID = Field(foreign_key="device.id", index=True)
    first_entry: Optional[datetime] = Field(default=None)
    last_exit: Optional[datetime] = Field(default=None)
    first_device_id: Optional[UUID] = Field(default=None, foreign_key="device.id")
    last_device_id: Optional[UUID] = Field(default=None, foreign_key="device.id")

    worked_minutes: int = Field(default=0)
    expected_minutes: int = Field(default=480)
    missed_minutes: int = Field(default=0)

    is_absent: bool = Field(default=False)
    was_late: bool = Field(default=False)
    left_early: bool = Field(default=False)
    entries_count: int = Field(default=0)

    shift_start_time: Optional[time] = Field(default=None)
    shift_end_time: Optional[time] = Field(default=None)
    late_penalty_minutes: int = Field(default=0)
    early_leave_penalty: int = Field(default=0)
    justified_absence: bool = Field(default=False)
    alert_flag: bool = Field(default=False)


class MonthlyAttendanceSummary(BaseModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", index=True)
    org_unit_id: UUID = Field(foreign_key="org_unit.id", index=True)
    year: int = Field(index=True)
    month: int = Field(index=True)

    total_days: int = Field(default=0)
    present_days: int = Field(default=0)
    late_days: int = Field(default=0)
    early_leave_days: int = Field(default=0)
    absent_days: int = Field(default=0)
    justified_absent_days: int = Field(default=0)

    total_worked_minutes: int = Field(default=0)
    total_expected_minutes: int = Field(default=0)
    total_missed_minutes: int = Field(default=0)

    attendance_rate: float = Field(default=0.0)
    punctuality_score: float = Field(default=0.0)
    ai_discipline_score: float = Field(default=0.0, description="AI discipline (0–100)")

    needs_review: bool = Field(default=False)
    most_used_device_id: Optional[UUID] = Field(default=None, foreign_key="device.id")

class Device(BaseModel, table=True):
    name: str = Field(index=True, description="Qurilma nomi")
    location: str = Field(index=True, description="Joylashuv")
    type: str = Field(default="turnstile", description="turnstile / face_terminal / nfc / camera")
    is_active: bool = Field(default=True, description="Faolmi yoki yo‘q")

    zone: Optional[str] = Field(default=None, description="Bino zonasi")
    direction: Optional[str] = Field(default=None, description="entry / exit / both")

    last_serial_no: Optional[int] = Field(default=None, description="Oxirgi yuborilgan serial")
    last_event_time: Optional[datetime] = Field(default=None, description="Oxirgi event vaqti")

    ip_address: Optional[str] = Field(default=None, description="IP manzil")
    username: Optional[str] = Field(default=None, description="Login")
    password: Optional[str] = Field(default=None, description="Parol")

    sync_status: Optional[str] = Field(default="pending", description="pending / synced / error")
