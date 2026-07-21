from datetime import datetime, timezone
import secrets

from app.application.ports import DoctorRepository, OrganizationRepository, PatientRepository
from app.application.security import hash_password, verify_password
from app.domain.entities import Doctor, Organization, Patient
from app.domain.exceptions import ConflictError, ForbiddenError, NotFoundError


class AuthService:
    def __init__(self, organizations: OrganizationRepository, doctors: DoctorRepository):
        self.organizations, self.doctors = organizations, doctors

    def register(self, organization_name: str, username: str, password: str, full_name: str, email: str | None) -> Doctor:
        if self.doctors.get_by_username(username):
            raise ConflictError("Логин уже занят")
        organization = self.organizations.create(organization_name)
        return self.doctors.create(organization.id, username, hash_password(password), full_name, email)

    def authenticate(self, username: str, password: str) -> Doctor:
        result = self.doctors.get_by_username(username)
        if not result or not verify_password(password, result[1]) or not result[0].is_active:
            raise ForbiddenError("Неверный логин или пароль")
        return result[0]


class OrganizationService:
    def __init__(self, repository: OrganizationRepository): self.repository = repository
    def get(self, organization_id: int) -> Organization:
        item = self.repository.get(organization_id)
        if not item: raise NotFoundError("Организация не найдена")
        return item
    def list(self) -> list[Organization]: return self.repository.list()
    def create(self, name: str) -> Organization: return self.repository.create(name)
    def update(self, organization_id: int, name: str) -> Organization:
        item = self.repository.update(organization_id, name)
        if not item: raise NotFoundError("Организация не найдена")
        return item
    def delete(self, organization_id: int) -> None:
        if not self.repository.delete(organization_id): raise NotFoundError("Организация не найдена")


class DoctorService:
    def __init__(self, organizations: OrganizationRepository, doctors: DoctorRepository): self.organizations, self.doctors = organizations, doctors
    def list(self, actor: Doctor) -> list[Doctor]:
        return self.doctors.list_all() if actor.is_admin else self.doctors.list_for_organization(actor.organization_id)
    def create(self, actor: Doctor, username: str, password: str, full_name: str, email: str | None, organization_id: int | None = None) -> Doctor:
        if self.doctors.get_by_username(username): raise ConflictError("Логин уже занят")
        target_organization_id = organization_id if actor.is_admin else actor.organization_id
        if target_organization_id is None: raise ConflictError("Для врача нужно указать организацию")
        if not self.organizations.get(target_organization_id): raise NotFoundError("Организация не найдена")
        return self.doctors.create(target_organization_id, username, hash_password(password), full_name, email)
    def update(self, actor: Doctor, doctor_id: int, **fields: object) -> Doctor:
        self._own(actor, doctor_id)
        item = self.doctors.update(doctor_id, **fields)
        if not item: raise NotFoundError("Врач не найден")
        return item
    def delete(self, actor: Doctor, doctor_id: int) -> None:
        self._own(actor, doctor_id)
        if actor.id == doctor_id: raise ConflictError("Нельзя удалить собственный профиль")
        if not self.doctors.delete(doctor_id): raise NotFoundError("Врач не найден")
    def _own(self, actor: Doctor, doctor_id: int) -> None:
        item = self.doctors.get(doctor_id)
        if not item: raise NotFoundError("Врач не найден")
        if item.organization_id != actor.organization_id and not actor.is_admin: raise ForbiddenError("Нет доступа к врачу другой организации")


class PatientService:
    def __init__(self, patients: PatientRepository, doctors: DoctorRepository): self.patients, self.doctors = patients, doctors
    def list(self, actor: Doctor) -> list[Patient]:
        return self.patients.list_all() if actor.is_admin else self.patients.list_for_organization(actor.organization_id)
    def get(self, actor: Doctor, patient_id: int) -> Patient: return self._own(actor, patient_id)
    def create(self, actor: Doctor, consent_to_data_processing: bool, **fields: object) -> Patient:
        if actor.is_admin:
            raise ForbiddenError("Пациента создаёт только лечащий врач")
        if not consent_to_data_processing:
            raise ConflictError("Нужно получить согласие на обработку персональных данных")
        return self.patients.create(actor.organization_id, actor.id, data_processing_consent_at=datetime.now(timezone.utc), magic_link_token=secrets.token_urlsafe(32), **fields)
    def update(self, actor: Doctor, patient_id: int, **fields: object) -> Patient:
        self._own(actor, patient_id)
        item = self.patients.update(patient_id, **fields)
        if not item: raise NotFoundError("Пациент не найден")
        return item
    def delete(self, actor: Doctor, patient_id: int) -> None:
        self._own(actor, patient_id)
        if not self.patients.delete(patient_id): raise NotFoundError("Пациент не найден")
    def _own(self, actor: Doctor, patient_id: int) -> Patient:
        item = self.patients.get(patient_id)
        if not item: raise NotFoundError("Пациент не найден")
        if item.organization_id != actor.organization_id and not actor.is_admin: raise ForbiddenError("Нет доступа к пациенту другой организации")
        return item
