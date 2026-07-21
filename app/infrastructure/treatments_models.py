from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class TreatmentTemplateModel(Base):
    __tablename__ = "treatment_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TemplateDayModel(Base):
    __tablename__ = "template_days"
    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("treatment_templates.id"), index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)


class TemplateBlockModel(Base):
    __tablename__ = "template_blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    template_day_id: Mapped[int] = mapped_column(ForeignKey("template_days.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    block_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class TreatmentPlanModel(Base):
    __tablename__ = "treatment_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("treatment_templates.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(160))
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    starts_on: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanDayModel(Base):
    __tablename__ = "plan_days"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("treatment_plans.id"), index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)


class PlanBlockModel(Base):
    __tablename__ = "plan_blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_day_id: Mapped[int] = mapped_column(ForeignKey("plan_days.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    block_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class MedicationDoseModel(Base):
    __tablename__ = "medication_doses"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_day_id: Mapped[int] = mapped_column(ForeignKey("plan_days.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    medication_name: Mapped[str] = mapped_column(String(200))
    dosage: Mapped[str | None] = mapped_column(String(160), nullable=True)
    scheduled_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class PatientActivityModel(Base):
    __tablename__ = "patient_activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("treatment_plans.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[int] = mapped_column(Integer)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
