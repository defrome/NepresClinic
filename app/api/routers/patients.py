from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.container import use_cases
from app.api.dependencies import current_doctor
from app.api.schemas import PatientCreate, PatientOut, PatientUpdate
from app.domain.entities import Doctor
from app.infrastructure.database import get_session

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[3].list(actor)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[3].create(actor, **data.model_dump())


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[3].get(actor, patient_id)


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, data: PatientUpdate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return use_cases(session)[3].update(actor, patient_id, **data.model_dump())


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    use_cases(session)[3].delete(actor, patient_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
