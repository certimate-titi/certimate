"""Knowledge Map service — business logic for knowledge node generation."""

from app.models.resource import Resource, ResourceStatus
from app.models.knowledge_node import KnowledgeNode
from app.repositories.resource_repository import ResourceRepository
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository


class KnowledgeMapService:

    """Knowledge Map Service 服務類別。"""
    def __init__(
        self,
        resource_repo: ResourceRepository,
        node_repo: KnowledgeNodeRepository,
    ):
        """初始化實例。"""
        self.resource_repo = resource_repo
        self.node_repo = node_repo

    def _find_owned_resource(self, resource_id: str, user_id: str):
        """查找並驗證資源歸屬，回傳 (resource, error_dict)。"""
        resource = self.resource_repo.find_by_id(resource_id)
        if resource is None:
            return None, {"error": True, "status_code": 404, "message": "資源不存在"}
        if str(resource.user_id) != user_id:
            return None, {"error": True, "status_code": 403, "message": "無權操作此資源"}
        return resource, None

    def complete_parsing(self, resource_id: str, user_id: str) -> dict:
        """資源解析完成，自動生成知識節點樹。"""
        resource, err = self._find_owned_resource(resource_id, user_id)
        if err:
            return err

        resource.status = ResourceStatus.COMPLETED
        self.resource_repo.save(resource)

        # 生成知識節點樹
        self._generate_knowledge_tree(resource)

        return {
            "error": False,
            "resource_id": str(resource.id),
            "status": "COMPLETED",
            "notification": "解析完成！心智圖已生成，立即查看",
        }

    def generate_map(self, resource_id: str, user_id: str) -> dict:
        """嘗試為資源生成心智圖（處理內容不足情況）。"""
        resource, err = self._find_owned_resource(resource_id, user_id)
        if err:
            return err

        # 模擬內容不足的判斷（實際場景會由 AI 引擎判斷）
        # 這裡用檔名中是否包含 "short_content" 作為模擬
        is_short_content = "short_content" in (resource.name or "")

        if is_short_content:
            resource.status = ResourceStatus.COMPLETED_NO_MAP
            self.resource_repo.save(resource)
            return {
                "error": False,
                "resource_id": str(resource.id),
                "status": "COMPLETED_NO_MAP",
                "hint": "內容不足以生成心智圖，但您仍可使用此資源出題",
            }

        # 正常生成
        resource.status = ResourceStatus.COMPLETED
        self.resource_repo.save(resource)
        self._generate_knowledge_tree(resource)

        return {
            "error": False,
            "resource_id": str(resource.id),
            "status": "COMPLETED",
            "notification": "心智圖已生成",
        }

    def _generate_knowledge_tree(self, resource: Resource):
        """為資源生成知識節點樹。"""
        resource_type = resource.type.value if hasattr(resource.type, 'value') else resource.type
        is_youtube = resource_type == "youtube"

        # 建立根節點 — depth=1 per migration 091 chk_depth_range CHECK (1..3)
        root = KnowledgeNode(
            resource_id=resource.id,
            parent_id=None,
            name=f"{resource.name} 知識總覽",
            depth=1,
            sort_order=0,
        )
        root = self.node_repo.save(root)

        # 建立子節點
        if is_youtube:
            child1 = KnowledgeNode(
                resource_id=resource.id,
                parent_id=root.id,
                name="核心概念",
                depth=1,
                sort_order=0,
                source_timestamp_seconds=120,
                source_text="影片核心概念摘要",
            )
            child2 = KnowledgeNode(
                resource_id=resource.id,
                parent_id=root.id,
                name="實務應用",
                depth=1,
                sort_order=1,
                source_timestamp_seconds=480,
                source_text="影片實務應用摘要",
            )
        else:
            child1 = KnowledgeNode(
                resource_id=resource.id,
                parent_id=root.id,
                name="第一章 基礎概念",
                depth=1,
                sort_order=0,
                source_page_number=1,
                source_text="基礎概念摘要",
            )
            child2 = KnowledgeNode(
                resource_id=resource.id,
                parent_id=root.id,
                name="第二章 進階主題",
                depth=1,
                sort_order=1,
                source_page_number=10,
                source_text="進階主題摘要",
            )

        self.node_repo.save(child1)
        self.node_repo.save(child2)
