from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=254)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)


class OrganizationOut(ORMModel):
    id: int
    name: str
    created_at: datetime


class DoctorCreate(BaseModel):
    organization_id: int | None = None
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=254)


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=254)
    is_active: bool | None = None


class DoctorOut(ORMModel):
    id: int
    organization_id: int
    username: str
    full_name: str
    email: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime


class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    birth_date: date
    sex: Literal["male", "female", "other", "not_specified"]
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    height_cm: int | None = Field(default=None, ge=20, le=300)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    emergency_contact: str = Field(min_length=2, max_length=255)
    consent_to_data_processing: bool
    diagnosis: str = Field(min_length=2, max_length=5000)
    diagnosis_date: date | None = None
    treatment_start_date: date
    doctor_notes: str = Field(min_length=2, max_length=10000)
    contraindications: str | None = Field(default=None, max_length=5000)
    comorbidities: str | None = Field(default=None, max_length=5000)
    allergies: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def require_delivery_contact(self) -> "PatientCreate":
        if not self.phone and not self.email:
            raise ValueError("Укажите телефон или email для Magic Link")
        return self


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    birth_date: date | None = None
    sex: Literal["male", "female", "other", "not_specified"] | None = None
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    height_cm: int | None = Field(default=None, ge=20, le=300)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    emergency_contact: str | None = Field(default=None, max_length=255)
    diagnosis: str | None = Field(default=None, min_length=2, max_length=5000)
    diagnosis_date: date | None = None
    treatment_start_date: date | None = None
    doctor_notes: str | None = Field(default=None, min_length=2, max_length=10000)
    contraindications: str | None = Field(default=None, max_length=5000)
    comorbidities: str | None = Field(default=None, max_length=5000)
    allergies: str | None = Field(default=None, max_length=5000)


class PatientOut(ORMModel):
    id: int
    organization_id: int
    doctor_id: int
    first_name: str
    last_name: str
    full_name: str
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
