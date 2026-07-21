from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.container import use_cases
from app.api.dependencies import require_admin
from app.api.schemas import OrganizationCreate, OrganizationOut
from app.domain.entities import Doctor
from app.infrastructure.database import get_session

router = APIRouter(prefix="/organizations", tags=["Организации"])


@router.get("", response_model=list[OrganizationOut], summary="Список организаций")
def list_organizations(_: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return use_cases(session)[1].list()


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED, summary="Создать организацию")
def create_organization(data: OrganizationCreate, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return use_cases(session)[1].create(data.name)


@router.get("/{organization_id}", response_model=OrganizationOut, summary="Получить организацию")
def get_organization(organization_id: int, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return use_cases(session)[1].get(organization_id)


@router.patch("/{organization_id}", response_model=OrganizationOut, summary="Изменить организацию")
def update_organization(organization_id: int, data: OrganizationCreate, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    return use_cases(session)[1].update(organization_id, data.name)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить организацию")
def delete_organization(organization_id: int, _: Doctor = Depends(require_admin), session: Session = Depends(get_session)):
    use_cases(session)[1].delete(organization_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
