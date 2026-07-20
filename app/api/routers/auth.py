from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.container import use_cases
from app.api.dependencies import current_doctor
from app.api.schemas import DoctorOut, LoginRequest, RegisterRequest, TokenResponse
from app.application.security import create_token
from app.domain.entities import Doctor
from app.infrastructure.database import get_session
from app.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=DoctorOut, status_code=201)
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    return use_cases(session)[0].register(**data.model_dump())


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    doctor = use_cases(session)[0].authenticate(data.username, data.password)
    return TokenResponse(access_token=create_token(str(doctor.id), settings.jwt_secret, settings.jwt_expire_minutes))


@router.get("/me", response_model=DoctorOut)
def me(doctor: Doctor = Depends(current_doctor)):
    return doctor
