"""Doctor repository adapter owned by this context."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import Doctor
from app.modules.doctors_model import DoctorModel


def to_entity(item: DoctorModel) -> Doctor:
    return Doctor(item.id, item.organization_id, item.username, item.full_name, item.email, item.is_admin, item.is_active, item.created_at)


class SqlAlchemyDoctorRepository:
    def __init__(self, session: Session): self.session = session
    def create(self, organization_id: int, username: str, password_hash: str, full_name: str, email: str | None, is_admin: bool = False) -> Doctor:
        item = DoctorModel(organization_id=organization_id, username=username, password_hash=password_hash, full_name=full_name, email=email, is_admin=is_admin)
        self.session.add(item); self.session.commit(); self.session.refresh(item); return to_entity(item)
    def get(self, doctor_id: int) -> Doctor | None:
        item = self.session.get(DoctorModel, doctor_id); return to_entity(item) if item else None
    def get_by_username(self, username: str) -> tuple[Doctor, str] | None:
        item = self.session.scalar(select(DoctorModel).where(DoctorModel.username == username)); return (to_entity(item), item.password_hash) if item else None
    def list_all(self) -> list[Doctor]: return [to_entity(x) for x in self.session.scalars(select(DoctorModel).order_by(DoctorModel.id)).all()]
    def list_for_organization(self, organization_id: int) -> list[Doctor]: return [to_entity(x) for x in self.session.scalars(select(DoctorModel).where(DoctorModel.organization_id == organization_id).order_by(DoctorModel.id)).all()]
    def update(self, doctor_id: int, full_name: str | None, email: str | None, is_active: bool | None) -> Doctor | None:
        item = self.session.get(DoctorModel, doctor_id)
        if not item: return None
        if full_name is not None: item.full_name = full_name
        if email is not None: item.email = email
        if is_active is not None: item.is_active = is_active
        self.session.commit(); self.session.refresh(item); return to_entity(item)
    def delete(self, doctor_id: int) -> bool:
        item = self.session.get(DoctorModel, doctor_id)
        if not item: return False
        self.session.delete(item); self.session.commit(); return True

__all__ = ["SqlAlchemyDoctorRepository"]
