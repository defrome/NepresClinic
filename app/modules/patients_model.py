"""Patient persistence model owned by the patient context."""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class PatientModel(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    birth_date: Mapped[date] = mapped_column(Date)
    sex: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    emergency_contact: Mapped[str] = mapped_column(String(255))
    data_processing_consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    diagnosis: Mapped[str] = mapped_column(Text)
    diagnosis_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    treatment_start_date: Mapped[date] = mapped_column(Date)
    doctor_notes: Mapped[str] = mapped_column(Text)
    contraindications: Mapped[str | None] = mapped_column(Text, nullable=True)
    comorbidities: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    magic_link_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

__all__ = ["PatientModel"]
