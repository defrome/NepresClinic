from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.container import use_cases
from app.api.dependencies import current_doctor
from app.api.schemas import DoctorCreate, DoctorOut, DoctorUpdate
from app.domain.entities import Doctor
from app.infrastructure.database import get_session

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorOut])
def list_doctors(actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[2].list(actor)


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(data: DoctorCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[2].create(actor, **data.model_dump())


@router.patch("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, data: DoctorUpdate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[2].update(actor, doctor_id, **data.model_dump())


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    use_cases(session)[2].delete(actor, doctor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
