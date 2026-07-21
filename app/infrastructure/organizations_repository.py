"""Organization repository adapter owned by this context."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import Organization
from app.infrastructure.organizations_model import OrganizationModel


def to_entity(item: OrganizationModel) -> Organization:
    return Organization(item.id, item.name, item.created_at)


class SqlAlchemyOrganizationRepository:
    def __init__(self, session: Session): self.session = session
    def create(self, name: str) -> Organization:
        item = OrganizationModel(name=name); self.session.add(item); self.session.commit(); self.session.refresh(item); return to_entity(item)
    def get(self, organization_id: int) -> Organization | None:
        item = self.session.get(OrganizationModel, organization_id); return to_entity(item) if item else None
    def list(self) -> list[Organization]: return [to_entity(x) for x in self.session.scalars(select(OrganizationModel).order_by(OrganizationModel.id)).all()]
    def update(self, organization_id: int, name: str) -> Organization | None:
        item = self.session.get(OrganizationModel, organization_id)
        if not item: return None
        item.name = name; self.session.commit(); self.session.refresh(item); return to_entity(item)
    def delete(self, organization_id: int) -> bool:
        item = self.session.get(OrganizationModel, organization_id)
        if not item: return False
        self.session.delete(item); self.session.commit(); return True

__all__ = ["SqlAlchemyOrganizationRepository"]
