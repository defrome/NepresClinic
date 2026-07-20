from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import current_doctor, require_admin
from app.api.schemas import (DoctorCreate, DoctorOut, DoctorUpdate, LoginRequest, OrganizationCreate, OrganizationOut, PatientCreate, PatientOut, PatientUpdate, RegisterRequest, TokenResponse)
from app.application.security import create_token
from app.application.services import AuthService, DoctorService, OrganizationService, PatientService
from app.domain.entities import Doctor
from app.infrastructure.database import get_session
from app.infrastructure.repositories import SqlAlchemyDoctorRepository, SqlAlchemyOrganizationRepository, SqlAlchemyPatientRepository
from app.settings import settings

router = APIRouter(prefix="/api/v1")


def services(session: Session):
    organizations = SqlAlchemyOrganizationRepository(session)
    doctors = SqlAlchemyDoctorRepository(session)
    patients = SqlAlchemyPatientRepository(session)
    return AuthService(organizations, doctors), OrganizationService(organizations), DoctorService(organizations, doctors), PatientService(patients, doctors)


@router.post("/auth/register", response_model=DoctorOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    return services(session)[0].register(**data.model_dump())


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(data: LoginRequest, session: Session = Depends(get_session)):
    doctor = services(session)[0].authenticate(data.username, data.password)
    return TokenResponse(access_token=create_token(str(doctor.id), settings.jwt_secret, settings.jwt_expire_minutes))


@router.get("/auth/me", response_model=DoctorOut, tags=["auth"])
def me(doctor: Doctor = Depends(current_doctor)):
    return doctor


@router.get("/organizations", response_model=list[OrganizationOut], tags=["organizations"])
def list_organizations(_: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return services(session)[1].list()


@router.post("/organizations", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED, tags=["organizations"])
def create_organization(data: OrganizationCreate, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return services(session)[1].create(data.name)


@router.get("/organizations/{organization_id}", response_model=OrganizationOut, tags=["organizations"])
def get_organization(organization_id: int, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return services(session)[1].get(organization_id)


@router.patch("/organizations/{organization_id}", response_model=OrganizationOut, tags=["organizations"])
def update_organization(organization_id: int, data: OrganizationCreate, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return services(session)[1].update(organization_id, data.name)


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["organizations"])
def delete_organization(organization_id: int, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    services(session)[1].delete(organization_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/doctors", response_model=list[DoctorOut], tags=["doctors"])
def list_doctors(actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[2].list(actor)


@router.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED, tags=["doctors"])
def create_doctor(data: DoctorCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[2].create(actor, **data.model_dump())


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut, tags=["doctors"])
def update_doctor(doctor_id: int, data: DoctorUpdate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[2].update(actor, doctor_id, **data.model_dump())


@router.delete("/doctors/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["doctors"])
def delete_doctor(doctor_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    services(session)[2].delete(actor, doctor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients", response_model=list[PatientOut], tags=["patients"])
def list_patients(actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[3].list(actor)


@router.post("/patients", response_model=PatientOut, status_code=status.HTTP_201_CREATED, tags=["patients"])
def create_patient(data: PatientCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[3].create(actor, **data.model_dump())


@router.get("/patients/{patient_id}", response_model=PatientOut, tags=["patients"])
def get_patient(patient_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[3].get(actor, patient_id)


@router.patch("/patients/{patient_id}", response_model=PatientOut, tags=["patients"])
def update_patient(patient_id: int, data: PatientUpdate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return services(session)[3].update(actor, patient_id, **data.model_dump())


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["patients"])
def delete_patient(patient_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    services(session)[3].delete(actor, patient_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
