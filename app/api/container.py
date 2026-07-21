"""Composition root for HTTP handlers.

HTTP modules depend on this factory, not on concrete SQLAlchemy classes directly.
"""
from sqlalchemy.orm import Session

from app.modules.auth_service import AuthService
from app.modules.doctors_service import DoctorService
from app.modules.doctors_repository import SqlAlchemyDoctorRepository
from app.modules.organizations_service import OrganizationService
from app.modules.organizations_repository import SqlAlchemyOrganizationRepository
from app.modules.patients_service import PatientService
from app.modules.patients_repository import SqlAlchemyPatientRepository


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
