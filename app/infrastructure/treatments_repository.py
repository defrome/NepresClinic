from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.treatments_models import (MedicationDoseModel, PatientActivityModel, PlanBlockModel, PlanDayModel, TemplateBlockModel, TemplateDayModel, TreatmentPlanModel, TreatmentTemplateModel)


class TreatmentRepository:
    def __init__(self, session: Session): self.session = session
    def template(self, template_id: int): return self.session.get(TreatmentTemplateModel, template_id)
    def templates(self, organization_id: int): return self.session.scalars(select(TreatmentTemplateModel).where(TreatmentTemplateModel.organization_id == organization_id).order_by(TreatmentTemplateModel.id.desc())).all()
    def create_template(self, organization_id: int, doctor_id: int, data: dict):
        days = data.pop("days", []); item = TreatmentTemplateModel(organization_id=organization_id, doctor_id=doctor_id, **data); self.session.add(item); self.session.flush()
        for day_data in days:
            blocks = day_data.pop("blocks", []); day = TemplateDayModel(template_id=item.id, **day_data); self.session.add(day); self.session.flush()
            for position, block in enumerate(blocks, 1): self.session.add(TemplateBlockModel(template_day_id=day.id, position=position, **block))
        self.session.commit(); self.session.refresh(item); return item
    def template_days(self, template_id: int): return self.session.scalars(select(TemplateDayModel).where(TemplateDayModel.template_id == template_id).order_by(TemplateDayModel.day_number)).all()
    def template_blocks(self, day_id: int): return self.session.scalars(select(TemplateBlockModel).where(TemplateBlockModel.template_day_id == day_id).order_by(TemplateBlockModel.position)).all()
    def create_plan(self, organization_id: int, doctor_id: int, data: dict):
        item = TreatmentPlanModel(**data); self.session.add(item); self.session.commit(); self.session.refresh(item); return item
    def plans(self, organization_id: int): return self.session.scalars(select(TreatmentPlanModel).where(TreatmentPlanModel.organization_id == organization_id).order_by(TreatmentPlanModel.id.desc())).all()
    def plan(self, plan_id: int): return self.session.get(TreatmentPlanModel, plan_id)
    def plan_days(self, plan_id: int): return self.session.scalars(select(PlanDayModel).where(PlanDayModel.plan_id == plan_id).order_by(PlanDayModel.day_number)).all()
    def plan_day(self, plan_id: int, day_number: int): return self.session.scalar(select(PlanDayModel).where(PlanDayModel.plan_id == plan_id, PlanDayModel.day_number == day_number))
    def ensure_plan_day(self, plan: TreatmentPlanModel, day_number: int):
        existing = {day.day_number for day in self.plan_days(plan.id)}
        for number in range(1, day_number + 1):
            if number not in existing:
                self.session.add(PlanDayModel(plan_id=plan.id, day_number=number, title=None))
        if not plan.duration_days or day_number > plan.duration_days:
            plan.duration_days = day_number
        self.session.commit()
        return self.plan_day(plan.id, day_number)
    def plan_blocks(self, day_id: int): return self.session.scalars(select(PlanBlockModel).where(PlanBlockModel.plan_day_id == day_id).order_by(PlanBlockModel.position)).all()
    def medications(self, day_id: int): return self.session.scalars(select(MedicationDoseModel).where(MedicationDoseModel.plan_day_id == day_id).order_by(MedicationDoseModel.position)).all()
    def clone_day(self, plan_id: int, day_number: int, title: str | None, blocks: list[dict], medications: list[dict]):
        day = PlanDayModel(plan_id=plan_id, day_number=day_number, title=title); self.session.add(day); self.session.flush()
        for position, block in enumerate(blocks, 1): self.session.add(PlanBlockModel(plan_day_id=day.id, position=position, **block))
        for position, medication in enumerate(medications, 1):
            scheduled = medication.pop("scheduled_time", None)
            self.session.add(MedicationDoseModel(plan_day_id=day.id, position=position, scheduled_time=time.fromisoformat(scheduled) if scheduled else None, **medication))
        self.session.commit(); return day
    def add_block(self, day_id: int, data: dict):
        position = len(self.plan_blocks(day_id)) + 1; item = PlanBlockModel(plan_day_id=day_id, position=position, **data); self.session.add(item); self.session.commit(); self.session.refresh(item); return item
    def add_medication(self, day_id: int, data: dict):
        position = len(self.medications(day_id)) + 1; scheduled = data.pop("scheduled_time", None); item = MedicationDoseModel(plan_day_id=day_id, position=position, scheduled_time=time.fromisoformat(scheduled) if scheduled else None, **data); self.session.add(item); self.session.commit(); self.session.refresh(item); return item
    def update_plan(self, plan_id: int, data: dict):
        item = self.plan(plan_id)
        if not item: return None
        for key, value in data.items():
            if value is not None: setattr(item, key, value)
        self.session.commit(); self.session.refresh(item); return item
    def patient_by_token(self, token: str):
        from app.infrastructure.patients_model import PatientModel
        return self.session.scalar(select(PatientModel).where(PatientModel.magic_link_token == token))
    def active_plan(self, patient_id: int): return self.session.scalar(select(TreatmentPlanModel).where(TreatmentPlanModel.patient_id == patient_id, TreatmentPlanModel.status == "active").order_by(TreatmentPlanModel.id.desc()))
    def activities(self, patient_id: int, plan_id: int): return self.session.scalars(select(PatientActivityModel).where(PatientActivityModel.patient_id == patient_id, PatientActivityModel.plan_id == plan_id)).all()
    def complete(self, patient_id: int, plan_id: int, target_type: str, target_id: int, answer: str | None):
        current = self.session.scalar(select(PatientActivityModel).where(PatientActivityModel.patient_id == patient_id, PatientActivityModel.plan_id == plan_id, PatientActivityModel.target_type == target_type, PatientActivityModel.target_id == target_id))
        if current: current.answer = answer
        else: self.session.add(PatientActivityModel(patient_id=patient_id, plan_id=plan_id, target_type=target_type, target_id=target_id, answer=answer))
        self.session.commit()
    def uncomplete(self, patient_id: int, plan_id: int, target_type: str, target_id: int):
        item = self.session.scalar(select(PatientActivityModel).where(PatientActivityModel.patient_id == patient_id, PatientActivityModel.plan_id == plan_id, PatientActivityModel.target_type == target_type, PatientActivityModel.target_id == target_id))
        if item:
            self.session.delete(item)
            self.session.commit()
