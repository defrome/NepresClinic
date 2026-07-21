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
    magic_link_token: str
    created_at: datetime


BlockType = Literal["text", "video", "pdf", "exercise", "question", "checklist", "photo", "link"]


class BlockCreate(BaseModel):
    block_type: BlockType
    title: str = Field(min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=10000)
    resource_url: str | None = Field(default=None, max_length=2000)
    question: str | None = Field(default=None, max_length=5000)
    is_required: bool = True


class TemplateDayCreate(BaseModel):
    day_number: int = Field(ge=1, le=365)
    title: str | None = Field(default=None, max_length=160)
    blocks: list[BlockCreate] = Field(default_factory=list)


class TreatmentTemplateCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    default_duration_days: int | None = Field(default=None, ge=1, le=365)
    days: list[TemplateDayCreate] = Field(default_factory=list)


class MedicationCreate(BaseModel):
    medication_name: str = Field(min_length=1, max_length=200)
    dosage: str | None = Field(default=None, max_length=160)
    scheduled_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    question: str | None = Field(default=None, max_length=5000)
    is_required: bool = True


class PlanDayCreate(TemplateDayCreate):
    medications: list[MedicationCreate] = Field(default_factory=list)


class TreatmentPlanCreate(BaseModel):
    patient_id: int
    template_id: int | None = None
    title: str | None = Field(default=None, max_length=160)
    duration_days: int | None = Field(default=None, ge=1, le=365)
    starts_on: date
    days: list[PlanDayCreate] = Field(default_factory=list)


class TreatmentPlanUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    status: Literal["active", "paused", "completed"] | None = None


class ActivityCreate(BaseModel):
    answer: str | None = Field(default=None, max_length=10000)


class PatientAccessOut(BaseModel):
    patient_name: str
    plan_id: int
    plan_title: str
    day_number: int
    duration_days: int | None
    completed_count: int
    total_count: int
    blocks: list[dict]
    medications: list[dict]
