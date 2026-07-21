from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import current_doctor
from app.api.schemas import ActivityCreate, BlockCreate, MedicationCreate, TreatmentPlanCreate, TreatmentPlanUpdate, TreatmentTemplateCreate
from app.domain.entities import Doctor
from app.infrastructure.database import get_session
from app.modules.patients_repository import SqlAlchemyPatientRepository
from app.modules.treatments_repository import TreatmentRepository
from app.modules.treatments_service import TreatmentService

router = APIRouter(tags=["treatments"])


def service(session: Session) -> TreatmentService:
    return TreatmentService(TreatmentRepository(session), SqlAlchemyPatientRepository(session))


@router.get("/treatment-templates")
def list_templates(actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).templates(actor)


@router.post("/treatment-templates", status_code=status.HTTP_201_CREATED)
def create_template(data: TreatmentTemplateCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).create_template(actor, data.model_dump())


@router.get("/treatment-templates/{template_id}")
def get_template(template_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).template_detail(actor, template_id)


@router.get("/treatment-plans")
def list_plans(actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).plans(actor)


@router.post("/treatment-plans", status_code=status.HTTP_201_CREATED)
def assign_plan(data: TreatmentPlanCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).assign_plan(actor, data.model_dump())


@router.get("/treatment-plans/{plan_id}")
def get_plan(plan_id: int, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).plan_detail(actor, plan_id)


@router.patch("/treatment-plans/{plan_id}")
def update_plan(plan_id: int, data: TreatmentPlanUpdate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).update_plan(actor, plan_id, data.model_dump())


@router.post("/treatment-plans/{plan_id}/days/{day_number}/blocks")
def add_plan_block(plan_id: int, day_number: int, data: BlockCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).add_block(actor, plan_id, day_number, data.model_dump())


@router.post("/treatment-plans/{plan_id}/days/{day_number}/medications")
def add_plan_medication(plan_id: int, day_number: int, data: MedicationCreate, actor: Doctor = Depends(current_doctor), session: Session = Depends(get_session)):
    return service(session).add_medication(actor, plan_id, day_number, data.model_dump())


@router.get("/patient-access/{token}/today")
def patient_today(token: str, session: Session = Depends(get_session)):
    return service(session).patient_today(token)


@router.post("/patient-access/{token}/{target_type}/{target_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_item(token: str, target_type: str, target_id: int, data: ActivityCreate, session: Session = Depends(get_session)):
    if target_type not in {"block", "medication"}: return {"detail": "Недопустимый тип действия"}
    service(session).complete_patient_item(token, target_type, target_id, data.answer)
