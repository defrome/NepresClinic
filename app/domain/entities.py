from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Organization:
    id: int
    name: str
    created_at: datetime


@dataclass(frozen=True)
class Doctor:
    id: int
    organization_id: int
    username: str
    full_name: str
    email: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class Patient:
    id: int
    organization_id: int
    doctor_id: int
    full_name: str
    birth_date: date | None
    contact: str | None
    notes: str | None
    created_at: datetime
