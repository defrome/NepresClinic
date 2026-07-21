from datetime import date

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.modules.patients_repository import SqlAlchemyPatientRepository
from app.modules.treatments_repository import TreatmentRepository


class TreatmentService:
    def __init__(self, repository: TreatmentRepository, patients: SqlAlchemyPatientRepository): self.repository, self.patients = repository, patients
    def _doctor_scope(self, actor, organization_id):
        if not actor.is_admin and actor.organization_id != organization_id: raise ForbiddenError("Нет доступа к данным другой организации")
    def create_template(self, actor, data: dict): return self.repository.create_template(actor.organization_id, actor.id, data)
    def templates(self, actor): return self.repository.templates(actor.organization_id)
    def template_detail(self, actor, template_id: int):
        template = self.repository.template(template_id)
        if not template: raise NotFoundError("Шаблон не найден")
        self._doctor_scope(actor, template.organization_id); return self._template_view(template)
    def _template_view(self, template):
        return {"id": template.id, "title": template.title, "description": template.description, "default_duration_days": template.default_duration_days, "days": [{"id": day.id, "day_number": day.day_number, "title": day.title, "blocks": [self._block_view(block) for block in self.repository.template_blocks(day.id)]} for day in self.repository.template_days(template.id)]}
    def assign_plan(self, actor, data: dict):
        patient = self.patients.get(data["patient_id"])
        if not patient: raise NotFoundError("Пациент не найден")
        self._doctor_scope(actor, patient.organization_id)
        template_id = data.get("template_id"); template = self.repository.template(template_id) if template_id else None
        if template: self._doctor_scope(actor, template.organization_id)
        days_input = data.pop("days", []); duration = data.get("duration_days") or (template.default_duration_days if template else None) or len(days_input) or 1
        data["duration_days"] = duration; data["organization_id"] = patient.organization_id; data["doctor_id"] = actor.id; data["title"] = data.get("title") or (template.title if template else "Индивидуальный план")
        plan = self.repository.create_plan(organization_id=patient.organization_id, doctor_id=actor.id, data=data)
        prepared = {item["day_number"]: item for item in days_input}
        if template:
            for source_day in self.repository.template_days(template.id):
                prepared.setdefault(source_day.day_number, {"day_number": source_day.day_number, "title": source_day.title, "blocks": [self._block_input(block) for block in self.repository.template_blocks(source_day.id)], "medications": []})
        for number in range(1, duration + 1):
            day = prepared.get(number, {"day_number": number, "title": None, "blocks": [], "medications": []})
            self.repository.clone_day(plan.id, number, day.get("title"), day.get("blocks", []), day.get("medications", []))
        return self.plan_detail(actor, plan.id)
    def _block_input(self, block): return {"block_type": block.block_type, "title": block.title, "content": block.content, "resource_url": block.resource_url, "question": block.question, "is_required": block.is_required}
    def _block_view(self, block): return {"id": block.id, "block_type": block.block_type, "title": block.title, "content": block.content, "resource_url": block.resource_url, "question": block.question, "is_required": block.is_required}
    def plans(self, actor):
        return [self._plan_summary(plan) for plan in self.repository.plans(actor.organization_id)]
    def _plan_summary(self, plan):
        days = self.repository.plan_days(plan.id)
        total = sum(len(self.repository.plan_blocks(day.id)) + len(self.repository.medications(day.id)) for day in days)
        activities = self.repository.activities(plan.patient_id, plan.id)
        return {"id": plan.id, "patient_id": plan.patient_id, "title": plan.title, "duration_days": plan.duration_days, "starts_on": plan.starts_on, "status": plan.status, "completed_count": len(activities), "total_count": total, "last_activity_at": max((item.completed_at for item in activities), default=None)}
    def plan_detail(self, actor, plan_id: int):
        plan = self.repository.plan(plan_id)
        if not plan: raise NotFoundError("План лечения не найден")
        self._doctor_scope(actor, plan.organization_id)
        return {"id": plan.id, "patient_id": plan.patient_id, "title": plan.title, "duration_days": plan.duration_days, "starts_on": plan.starts_on, "status": plan.status, "days": [{"id": day.id, "day_number": day.day_number, "title": day.title, "blocks": [self._block_view(block) for block in self.repository.plan_blocks(day.id)], "medications": [{"id": med.id, "medication_name": med.medication_name, "dosage": med.dosage, "scheduled_time": med.scheduled_time.isoformat() if med.scheduled_time else None, "question": med.question, "is_required": med.is_required} for med in self.repository.medications(day.id)]} for day in self.repository.plan_days(plan.id)]}
    def update_plan(self, actor, plan_id: int, data: dict):
        plan = self.repository.plan(plan_id)
        if not plan: raise NotFoundError("План лечения не найден")
        self._doctor_scope(actor, plan.organization_id); self.repository.update_plan(plan_id, data); return self.plan_detail(actor, plan_id)
    def add_block(self, actor, plan_id: int, day_number: int, data: dict):
        plan = self.repository.plan(plan_id)
        if not plan: raise NotFoundError("План лечения не найден")
        self._doctor_scope(actor, plan.organization_id); day = self.repository.plan_day(plan_id, day_number)
        if not day: raise NotFoundError("День лечения не найден")
        self.repository.add_block(day.id, data); return self.plan_detail(actor, plan_id)
    def add_medication(self, actor, plan_id: int, day_number: int, data: dict):
        plan = self.repository.plan(plan_id)
        if not plan: raise NotFoundError("План лечения не найден")
        self._doctor_scope(actor, plan.organization_id); day = self.repository.plan_day(plan_id, day_number)
        if not day: raise NotFoundError("День лечения не найден")
        self.repository.add_medication(day.id, data); return self.plan_detail(actor, plan_id)
    def patient_today(self, token: str):
        patient = self.repository.patient_by_token(token)
        if not patient: raise NotFoundError("Ссылка пациента недействительна")
        plan = self.repository.active_plan(patient.id)
        if not plan: raise NotFoundError("Активный план лечения не найден")
        day_number = max(1, min(plan.duration_days or 1, (date.today() - plan.starts_on).days + 1)); day = next((item for item in self.repository.plan_days(plan.id) if item.day_number == day_number), None)
        if not day: raise NotFoundError("День лечения не найден")
        activities = {(item.target_type, item.target_id) for item in self.repository.activities(patient.id, plan.id)}; blocks = [self._block_view(block) | {"completed": ("block", block.id) in activities} for block in self.repository.plan_blocks(day.id)]; meds = [{"id": med.id, "medication_name": med.medication_name, "dosage": med.dosage, "scheduled_time": med.scheduled_time.isoformat() if med.scheduled_time else None, "question": med.question, "completed": ("medication", med.id) in activities} for med in self.repository.medications(day.id)]
        return {"patient_name": f"{patient.first_name} {patient.last_name}", "plan_id": plan.id, "plan_title": plan.title, "day_number": day_number, "duration_days": plan.duration_days, "completed_count": sum(item["completed"] for item in blocks) + sum(item["completed"] for item in meds), "total_count": len(blocks) + len(meds), "blocks": blocks, "medications": meds}
    def complete_patient_item(self, token: str, target_type: str, target_id: int, answer: str | None):
        patient = self.repository.patient_by_token(token)
        if not patient: raise NotFoundError("Ссылка пациента недействительна")
        plan = self.repository.active_plan(patient.id)
        if not plan: raise NotFoundError("Активный план лечения не найден")
        self.repository.complete(patient.id, plan.id, target_type, target_id, answer)
