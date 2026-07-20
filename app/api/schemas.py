from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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
    organization_id: int | None = None
    doctor_id: int | None = None
    full_name: str = Field(min_length=2, max_length=160)
    birth_date: date | None = None
    contact: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=5000)


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    birth_date: date | None = None
    contact: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=5000)


class PatientOut(ORMModel):
    id: int
    organization_id: int
    doctor_id: int
    full_name: str
    birth_date: date | None
    contact: str | None
    notes: str | None
    created_at: datetime
