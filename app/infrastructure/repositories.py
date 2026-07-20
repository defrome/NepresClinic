from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import Doctor, Organization, Patient
from app.infrastructure.models import DoctorModel, OrganizationModel, PatientModel


def organization_entity(item: OrganizationModel) -> Organization:
    return Organization(item.id, item.name, item.created_at)


def doctor_entity(item: DoctorModel) -> Doctor:
    return Doctor(item.id, item.organization_id, item.username, item.full_name, item.email, item.is_admin, item.is_active, item.created_at)


def patient_entity(item: PatientModel) -> Patient:
    return Patient(item.id, item.organization_id, item.doctor_id, item.first_name, item.last_name, item.birth_date, item.sex, item.phone, item.email, item.height_cm, item.weight_kg, item.emergency_contact, item.data_processing_consent_at, item.diagnosis, item.diagnosis_date, item.treatment_start_date, item.doctor_notes, item.contraindications, item.comorbidities, item.allergies, item.created_at)


class SqlAlchemyOrganizationRepository:
    def __init__(self, session: Session): self.session = session
    def create(self, name: str) -> Organization:
        item = OrganizationModel(name=name); self.session.add(item); self.session.commit(); self.session.refresh(item); return organization_entity(item)
    def get(self, organization_id: int) -> Organization | None:
        item = self.session.get(OrganizationModel, organization_id); return organization_entity(item) if item else None
    def list(self) -> list[Organization]: return [organization_entity(x) for x in self.session.scalars(select(OrganizationModel).order_by(OrganizationModel.id)).all()]
    def update(self, organization_id: int, name: str) -> Organization | None:
        item = self.session.get(OrganizationModel, organization_id)
        if not item: return None
        item.name = name; self.session.commit(); self.session.refresh(item); return organization_entity(item)
    def delete(self, organization_id: int) -> bool:
        item = self.session.get(OrganizationModel, organization_id)
        if not item: return False
        self.session.delete(item); self.session.commit(); return True


class SqlAlchemyDoctorRepository:
    def __init__(self, session: Session): self.session = session
    def create(self, organization_id: int, username: str, password_hash: str, full_name: str, email: str | None, is_admin: bool = False) -> Doctor:
        item = DoctorModel(organization_id=organization_id, username=username, password_hash=password_hash, full_name=full_name, email=email, is_admin=is_admin)
        self.session.add(item); self.session.commit(); self.session.refresh(item); return doctor_entity(item)
    def get(self, doctor_id: int) -> Doctor | None:
        item = self.session.get(DoctorModel, doctor_id); return doctor_entity(item) if item else None
    def get_by_username(self, username: str) -> tuple[Doctor, str] | None:
        item = self.session.scalar(select(DoctorModel).where(DoctorModel.username == username))
        return (doctor_entity(item), item.password_hash) if item else None
    def list_all(self) -> list[Doctor]:
        return [doctor_entity(x) for x in self.session.scalars(select(DoctorModel).order_by(DoctorModel.id)).all()]
    def list_for_organization(self, organization_id: int) -> list[Doctor]:
        return [doctor_entity(x) for x in self.session.scalars(select(DoctorModel).where(DoctorModel.organization_id == organization_id).order_by(DoctorModel.id)).all()]
    def update(self, doctor_id: int, full_name: str | None, email: str | None, is_active: bool | None) -> Doctor | None:
        item = self.session.get(DoctorModel, doctor_id)
        if not item: return None
        if full_name is not None: item.full_name = full_name
        if email is not None: item.email = email
        if is_active is not None: item.is_active = is_active
        self.session.commit(); self.session.refresh(item); return doctor_entity(item)
    def delete(self, doctor_id: int) -> bool:
        item = self.session.get(DoctorModel, doctor_id)
        if not item: return False
        self.session.delete(item); self.session.commit(); return True


class SqlAlchemyPatientRepository:
    def __init__(self, session: Session): self.session = session
    def create(self, organization_id: int, doctor_id: int, **fields: object) -> Patient:
        item = PatientModel(organization_id=organization_id, doctor_id=doctor_id, **fields)
        self.session.add(item); self.session.commit(); self.session.refresh(item); return patient_entity(item)
    def get(self, patient_id: int) -> Patient | None:
        item = self.session.get(PatientModel, patient_id); return patient_entity(item) if item else None
    def list_all(self) -> list[Patient]:
        return [patient_entity(x) for x in self.session.scalars(select(PatientModel).order_by(PatientModel.id)).all()]
    def list_for_organization(self, organization_id: int) -> list[Patient]:
        return [patient_entity(x) for x in self.session.scalars(select(PatientModel).where(PatientModel.organization_id == organization_id).order_by(PatientModel.id)).all()]
    def update(self, patient_id: int, **fields: object) -> Patient | None:
        item = self.session.get(PatientModel, patient_id)
        if not item: return None
        for key, value in fields.items():
            if value is not None: setattr(item, key, value)
        self.session.commit(); self.session.refresh(item); return patient_entity(item)
    def delete(self, patient_id: int) -> bool:
        item = self.session.get(PatientModel, patient_id)
        if not item: return False
        self.session.delete(item); self.session.commit(); return True
