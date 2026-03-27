"""Resource Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.resource import Resource


class ResourceRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, resource: Resource) -> Resource:
        self.session.add(resource)
        self.session.commit()
        self.session.refresh(resource)
        return resource

    def find_by_id(self, resource_id) -> Optional[Resource]:
        return self.session.query(Resource).filter_by(id=resource_id).first()
