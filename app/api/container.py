"""Composition root for HTTP handlers.

HTTP modules depend on this factory, not on concrete SQLAlchemy classes directly.
"""
from sqlalchemy.orm import Session

from app.application.auth import AuthService
from app.application.doctors import DoctorService
from app.infrastructure.doctors_repository import SqlAlchemyDoctorRepository
from app.application.organizations import OrganizationService
from app.infrastructure.organizations_repository import SqlAlchemyOrganizationRepository
from app.application.patients import PatientService
from app.infrastructure.patients_repository import SqlAlchemyPatientRepository


def use_cases(session: Session) -> tuple[AuthService, OrganizationService, DoctorService, PatientService]:
    organizations = SqlAlchemyOrganizationRepository(session)
    doctors = SqlAlchemyDoctorRepository(session)
    patients = SqlAlchemyPatientRepository(session)
    return (
        AuthService(organizations, doctors),
        OrganizationService(organizations),
        DoctorService(organizations, doctors),
        PatientService(patients, doctors),
    )
