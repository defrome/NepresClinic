"""Patient repository adapter owned by this context."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import Patient
from app.modules.patients_model import PatientModel


def to_entity(item: PatientModel) -> Patient:
    return Patient(item.id, item.organization_id, item.doctor_id, item.first_name, item.last_name, item.birth_date, item.sex, item.phone, item.email, item.height_cm, item.weight_kg, item.emergency_contact, item.data_processing_consent_at, item.diagnosis, item.diagnosis_date, item.treatment_start_date, item.doctor_notes, item.contraindications, item.comorbidities, item.allergies, item.magic_link_token, item.created_at)


class SqlAlchemyPatientRepository:
    def __init__(self, session: Session): self.session = session
    def create(self, organization_id: int, doctor_id: int, **fields: object) -> Patient:
        item = PatientModel(organization_id=organization_id, doctor_id=doctor_id, **fields); self.session.add(item); self.session.commit(); self.session.refresh(item); return to_entity(item)
    def get(self, patient_id: int) -> Patient | None:
        item = self.session.get(PatientModel, patient_id); return to_entity(item) if item else None
    def list_all(self) -> list[Patient]: return [to_entity(x) for x in self.session.scalars(select(PatientModel).order_by(PatientModel.id)).all()]
    def list_for_organization(self, organization_id: int) -> list[Patient]: return [to_entity(x) for x in self.session.scalars(select(PatientModel).where(PatientModel.organization_id == organization_id).order_by(PatientModel.id)).all()]
    def update(self, patient_id: int, **fields: object) -> Patient | None:
        item = self.session.get(PatientModel, patient_id)
        if not item: return None
        for key, value in fields.items():
            if value is not None: setattr(item, key, value)
        self.session.commit(); self.session.refresh(item); return to_entity(item)
    def delete(self, patient_id: int) -> bool:
        item = self.session.get(PatientModel, patient_id)
        if not item: return False
        self.session.delete(item); self.session.commit(); return True

__all__ = ["SqlAlchemyPatientRepository"]
