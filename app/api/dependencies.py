from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.security import decode_token
from app.domain.entities import Doctor
from app.infrastructure.database import get_session
from app.infrastructure.doctors_repository import SqlAlchemyDoctorRepository
from app.settings import settings

bearer = HTTPBearer()


def current_doctor(credentials: HTTPAuthorizationCredentials = Depends(bearer), session: Session = Depends(get_session)) -> Doctor:
    subject = decode_token(credentials.credentials, settings.jwt_secret)
    doctor = SqlAlchemyDoctorRepository(session).get(int(subject)) if subject and subject.isdigit() else None
    if not doctor or not doctor.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return doctor


def require_admin(doctor: Doctor = Depends(current_doctor)) -> Doctor:
    if not doctor.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора")
    return doctor
