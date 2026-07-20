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
    first_name: str
    last_name: str
    birth_date: date
    sex: str
    phone: str | None
    email: str | None
    height_cm: int | None
    weight_kg: float | None
    emergency_contact: str
    data_processing_consent_at: datetime
    diagnosis: str
    diagnosis_date: date | None
    treatment_start_date: date
    doctor_notes: str
    contraindications: str | None
    comorbidities: str | None
    allergies: str | None
    created_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
