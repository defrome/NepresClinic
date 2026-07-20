"""Composition root for HTTP handlers.

HTTP modules depend on this factory, not on concrete SQLAlchemy classes directly.
"""
from sqlalchemy.orm import Session

from app.modules.auth.application.service import AuthService
from app.modules.doctors.application.service import DoctorService
from app.modules.doctors.infrastructure.repository import SqlAlchemyDoctorRepository
from app.modules.organizations.application.service import OrganizationService
from app.modules.organizations.infrastructure.repository import SqlAlchemyOrganizationRepository
from app.modules.patients.application.service import PatientService
from app.modules.patients.infrastructure.repository import SqlAlchemyPatientRepository


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
