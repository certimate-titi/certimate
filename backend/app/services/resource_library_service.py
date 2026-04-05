"""資源庫管理 Service。"""

import uuid

from sqlalchemy.orm import Session

from app.models.resource import Resource, ResourceStatus


class ResourceLibraryService:
    def __init__(self, db: Session):
        self.db = db

    def list_resources(self, user_id: str, keyword: str | None = None):
        """列出使用者的資源。"""
        user_uuid = uuid.UUID(user_id)

        query = self.db.query(Resource).filter_by(user_id=user_uuid)

        if keyword:
            query = query.filter(Resource.name.ilike(f"%{keyword}%"))

        resources = query.order_by(Resource.created_at.desc()).all()

        items = []
        for r in resources:
            items.append({
                "resource_id": str(r.id),
                "name": r.name,
                "type": r.type.value if hasattr(r.type, 'value') else str(r.type),
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
            })

        return {"resources": items}

    def delete_resource(self, user_id: str, resource_id: str):
        """刪除資源。"""
        user_uuid = uuid.UUID(user_id)
        res_uuid = uuid.UUID(resource_id)

        resource = self.db.query(Resource).filter_by(id=res_uuid).first()
        if not resource:
            return {"error": True, "status_code": 404, "message": "資源不存在"}

        if resource.user_id != user_uuid:
            return {"error": True, "status_code": 403, "message": "無存取此資源的權限"}

        self.db.delete(resource)
        self.db.commit()
        return {"message": "資源已刪除"}

    def reparse_resource(self, user_id: str, resource_id: str):
        """重新解析資源。"""
        user_uuid = uuid.UUID(user_id)
        res_uuid = uuid.UUID(resource_id)

        resource = self.db.query(Resource).filter_by(id=res_uuid).first()
        if not resource:
            return {"error": True, "status_code": 404, "message": "資源不存在"}

        if resource.user_id != user_uuid:
            return {"error": True, "status_code": 403, "message": "無存取此資源的權限"}

        if resource.status in (ResourceStatus.PENDING, ResourceStatus.PROCESSING):
            return {"error": True, "status_code": 409, "message": "資源正在處理中，請稍後再試"}

        resource.status = ResourceStatus.PENDING
        self.db.commit()
        return {"message": "已重新觸發解析"}
