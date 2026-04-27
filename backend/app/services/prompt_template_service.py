"""Prompt Template Service — 模板管理業務邏輯 (Feature 30)."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AdminAuditLog
from app.models.prompt_template import (
    PromptTemplateV2,
    PromptTemplateVersion,
    PromptAbTest,
    AbTestStatus,
    PromptCategory,
)
from app.models.user import User, UserRole
from app.repositories.prompt_template_repository import PromptTemplateRepository


def _get_user(db: Session, user_id: str) -> Optional[User]:
    """取得 user。"""
    return db.query(User).filter(User.id == user_id).first()


def _require_super_admin(db: Session, user_id: str) -> Optional[dict]:
    """ require super admin。"""
    user = _get_user(db, user_id)
    if not user:
        return {"error": True, "status_code": 401, "message": "未授權"}
    if user.role != UserRole.SUPER_ADMIN:
        return {"error": True, "status_code": 403, "message": "權限不足"}
    return None


def _log_audit(
    db: Session,
    admin_id: str,
    action: str,
    details: Optional[dict] = None,
):
    """ log audit。"""
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type="prompt_template",
        details=details,
    )
    db.add(log)
    db.commit()


class PromptTemplateService:
    """Prompt 模板管理服務。"""

    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self.repo = PromptTemplateRepository(db)

    # ── List / Get ────────────────────────────────────────────────────────

    def list_templates(self, actor_id: str, category: Optional[str] = None) -> dict:
        """列出 templates。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        templates = self.repo.find_all(category=category)
        return {
            "templates": [self._to_summary(t) for t in templates],
            "total": len(templates),
        }

    def get_template(self, actor_id: str, template_id: str) -> dict:
        """取得 template。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        t = self.repo.find_by_template_id(template_id)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}

        return self._to_detail(t)

    # ── Create ────────────────────────────────────────────────────────────

    def create_template(self, actor_id: str, data: dict) -> dict:
        """建立 template。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        # 必要欄位驗證
        required = ["template_id", "name", "display_name", "category", "model",
                    "max_tokens", "system_prompt", "user_prompt"]
        for field in required:
            val = data.get(field)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                return {
                    "error": True, "status_code": 422,
                    "message": "必要參數未提供",
                }

        # 唯一性檢查
        if self.repo.exists_by_template_id(data["template_id"]):
            return {
                "error": True, "status_code": 409,
                "message": "template_id 已存在",
            }
        if self.repo.exists_by_name(data["name"]):
            return {
                "error": True, "status_code": 409,
                "message": "name 已存在",
            }

        user_uuid = uuid.UUID(actor_id)

        template = PromptTemplateV2(
            template_id=data["template_id"],
            name=data["name"],
            display_name=data["display_name"],
            category=data["category"],
            model=data["model"],
            max_tokens=int(data["max_tokens"]),
            max_tokens_by_plan=data.get("max_tokens_by_plan"),
            temperature=float(data.get("temperature", 0.5)),
            system_prompt=data["system_prompt"],
            user_prompt=data["user_prompt"],
            variables=data.get("variables", []),
            feature_refs=data.get("feature_refs", []),
            current_version=1,
            is_active=True,
            created_by=user_uuid,
        )
        saved = self.repo.save(template)

        # 建立版本 1
        self._create_version(
            saved,
            change_note=data.get("change_note", "Initial version"),
            actor_id=user_uuid,
        )

        _log_audit(
            self.db, actor_id,
            action="create_prompt_template",
            details={
                "action": "create_prompt_template",
                "details": f"{saved.template_id} {saved.name} ({saved.category.value if hasattr(saved.category, 'value') else saved.category})",
            },
        )

        return {"template_id": saved.template_id, "current_version": 1}

    # ── Update ────────────────────────────────────────────────────────────

    def update_template(self, actor_id: str, template_id: str, data: dict) -> dict:
        """更新 template。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        t = self.repo.find_by_template_id(template_id)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}

        old_version = t.current_version

        # 更新欄位
        updatable = ["system_prompt", "user_prompt", "model", "max_tokens",
                     "max_tokens_by_plan", "temperature", "display_name",
                     "variables", "feature_refs"]
        for field in updatable:
            if field in data and data[field] is not None:
                val = data[field]
                if field in ("max_tokens",):
                    val = int(val)
                elif field in ("temperature",):
                    val = float(val)
                setattr(t, field, val)

        t.current_version = old_version + 1
        t.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(t)

        # 新增版本歷史
        self._create_version(
            t,
            change_note=data.get("change_note"),
            actor_id=uuid.UUID(actor_id),
        )

        _log_audit(
            self.db, actor_id,
            action="update_prompt_template",
            details={
                "action": "update_prompt_template",
                "details": (
                    f"{t.template_id} {t.name}: "
                    f"v{old_version} → v{t.current_version}"
                ),
            },
        )

        return {"template_id": t.template_id, "current_version": t.current_version}

    # ── Deactivate ────────────────────────────────────────────────────────

    def deactivate_template(self, actor_id: str, template_id: str) -> dict:
        """deactivate template。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        t = self.repo.find_by_template_id(template_id)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}

        t.is_active = False
        self.db.commit()

        _log_audit(
            self.db, actor_id,
            action="deactivate_prompt_template",
            details={
                "action": "deactivate_prompt_template",
                "details": f"{t.template_id} {t.name}",
            },
        )

        return {"template_id": t.template_id, "is_active": False}

    # ── Version History ───────────────────────────────────────────────────

    def list_versions(self, actor_id: str, template_id: str) -> dict:
        """列出 versions。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        t = self.repo.find_by_template_id(template_id)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}

        versions = self.repo.find_versions(t.id)
        return {
            "template_id": template_id,
            "versions": [self._version_to_dict(v) for v in versions],
            "total": len(versions),
        }

    def rollback_template(
        self, actor_id: str, template_id: str, target_version: int
    ) -> dict:
        """回滾 template。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        t = self.repo.find_by_template_id(template_id)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}

        target_v = self.repo.find_version(t.id, target_version)
        if not target_v:
            return {
                "error": True, "status_code": 404,
                "message": f"版本 {target_version} 不存在",
            }

        old_version = t.current_version

        # 從目標版本複製內容至主表
        t.system_prompt = target_v.system_prompt
        t.user_prompt = target_v.user_prompt
        t.model = target_v.model
        t.max_tokens = target_v.max_tokens
        t.temperature = float(target_v.temperature)
        t.variables = target_v.variables
        t.current_version = old_version + 1
        t.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(t)

        # 建立新版本（回滾記錄）
        self._create_version(
            t,
            change_note=f"Rollback to v{target_version}",
            actor_id=uuid.UUID(actor_id),
        )

        _log_audit(
            self.db, actor_id,
            action="rollback_prompt_template",
            details={
                "action": "rollback_prompt_template",
                "details": (
                    f"{t.template_id} {t.name}: "
                    f"rollback to v{target_version} → v{t.current_version}"
                ),
            },
        )

        return {
            "template_id": t.template_id,
            "current_version": t.current_version,
            "rolled_back_to": target_version,
        }

    # ── A/B Test ──────────────────────────────────────────────────────────

    def create_ab_test(
        self, actor_id: str, template_id: str, data: dict
    ) -> dict:
        """建立 ab test。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        t = self.repo.find_by_template_id(template_id)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}

        # 唯一性：同一模板最多一個 running
        existing = self.repo.find_running_ab_test(t.id)
        if existing:
            return {
                "error": True, "status_code": 409,
                "message": "該模板已有進行中的 A/B 測試",
            }

        ab_test = PromptAbTest(
            template_id=t.id,
            name=data["name"],
            variant_a_version=t.current_version,
            variant_b_system_prompt=data["variant_b_system_prompt"],
            variant_b_user_prompt=data["variant_b_user_prompt"],
            variant_b_temperature=(
                float(data["variant_b_temperature"])
                if data.get("variant_b_temperature") is not None
                else None
            ),
            traffic_split=int(data.get("traffic_split", 50)),
            status=AbTestStatus.RUNNING,
            metric_name=data.get("metric_name"),
            created_by=uuid.UUID(actor_id),
        )
        saved = self.repo.save_ab_test(ab_test)

        _log_audit(
            self.db, actor_id,
            action="create_ab_test",
            details={
                "action": "create_ab_test",
                "details": (
                    f"{t.template_id} {t.name}: "
                    f"{data['name']} ({data.get('traffic_split', 50)}%)"
                ),
            },
        )

        return {
            "ab_test_id": str(saved.id),
            "variant_a_version": saved.variant_a_version,
            "status": saved.status,
        }

    def complete_ab_test(
        self, actor_id: str, test_id: str, winner: str
    ) -> dict:
        """complete ab test。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        ab = self.repo.find_ab_test_by_id(test_id)
        if not ab:
            ab = self.repo.find_ab_test_by_name(test_id)
        if not ab:
            return {"error": True, "status_code": 404, "message": "A/B 測試不存在"}

        if ab.status != AbTestStatus.RUNNING:
            return {
                "error": True, "status_code": 409,
                "message": "A/B 測試已結束",
            }

        ab.status = AbTestStatus.COMPLETED
        ab.winner = winner.upper()
        ab.ended_at = datetime.now(timezone.utc)
        self.db.commit()

        # 若勝者為 B，自動將 variant B 套用為新版本
        t = self.db.query(PromptTemplateV2).filter_by(id=ab.template_id).first()
        if winner.upper() == "B" and t:
            old_version = t.current_version
            t.system_prompt = ab.variant_b_system_prompt
            t.user_prompt = ab.variant_b_user_prompt
            if ab.variant_b_temperature is not None:
                t.temperature = float(ab.variant_b_temperature)
            t.current_version = old_version + 1
            t.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(t)
            self._create_version(
                t,
                change_note=f"A/B Test winner: B ({ab.name})",
                actor_id=uuid.UUID(actor_id),
            )

            _log_audit(
                self.db, actor_id,
                action="complete_ab_test",
                details={
                    "action": "complete_ab_test",
                    "details": (
                        f"{t.template_id} {t.name}: "
                        f"winner=B, applied as new version"
                    ),
                },
            )
        elif t:
            _log_audit(
                self.db, actor_id,
                action="complete_ab_test",
                details={
                    "action": "complete_ab_test",
                    "details": (
                        f"{t.template_id} {t.name}: winner=A, no change"
                    ),
                },
            )

        return {
            "ab_test_id": str(ab.id),
            "status": ab.status,
            "winner": ab.winner,
        }

    def cancel_ab_test(self, actor_id: str, test_id: str) -> dict:
        """cancel ab test。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        ab = self.repo.find_ab_test_by_id(test_id)
        if not ab:
            ab = self.repo.find_ab_test_by_name(test_id)
        if not ab:
            return {"error": True, "status_code": 404, "message": "A/B 測試不存在"}

        ab.status = AbTestStatus.CANCELLED
        ab.ended_at = datetime.now(timezone.utc)
        self.db.commit()

        return {"ab_test_id": str(ab.id), "status": ab.status}

    # ── Internal (AI Service) ─────────────────────────────────────────────

    def get_prompt_for_ai(self, name: str, user_id_hash: Optional[int] = None) -> dict:
        """AI 服務取得生效 prompt，含 A/B 分流邏輯。"""
        t = self.repo.find_by_name(name)
        if not t:
            return {"error": True, "status_code": 404, "message": "模板不存在"}
        if not t.is_active:
            return {"error": True, "status_code": 410, "message": "模板已停用"}

        # A/B 分流
        if user_id_hash is not None:
            ab = self.repo.find_running_ab_test(t.id)
            if ab and user_id_hash % 100 < ab.traffic_split:
                # variant B
                return {
                    "template_id": t.template_id,
                    "name": t.name,
                    "variant": "B",
                    "system_prompt": ab.variant_b_system_prompt,
                    "user_prompt": ab.variant_b_user_prompt,
                    "temperature": (
                        float(ab.variant_b_temperature)
                        if ab.variant_b_temperature is not None
                        else float(t.temperature)
                    ),
                    "model": t.model,
                    "max_tokens": t.max_tokens,
                }
            # variant A (or no A/B test)
            return {
                "template_id": t.template_id,
                "name": t.name,
                "variant": "A",
                "system_prompt": t.system_prompt,
                "user_prompt": t.user_prompt,
                "temperature": float(t.temperature),
                "model": t.model,
                "max_tokens": t.max_tokens,
            }

        return {
            "template_id": t.template_id,
            "name": t.name,
            "system_prompt": t.system_prompt,
            "user_prompt": t.user_prompt,
            "temperature": float(t.temperature),
            "model": t.model,
            "max_tokens": t.max_tokens,
            "variables": t.variables,
        }

    # ── Prompt Rendering ────────────────────────────────────────────────

    @staticmethod
    def render_prompt(template_str: str, variables: dict) -> str:
        """Replace {var_name} placeholders with actual values."""
        result = template_str
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    # ── Private Helpers ───────────────────────────────────────────────────

    def _create_version(
        self,
        template: PromptTemplateV2,
        change_note: Optional[str],
        actor_id: uuid.UUID,
    ) -> PromptTemplateVersion:
        """建立 version。"""
        v = PromptTemplateVersion(
            template_id=template.id,
            version=template.current_version,
            model=template.model,
            max_tokens=template.max_tokens,
            max_tokens_by_plan=template.max_tokens_by_plan,
            temperature=float(template.temperature),
            system_prompt=template.system_prompt,
            user_prompt=template.user_prompt,
            variables=template.variables or [],
            change_note=change_note,
            created_by=actor_id,
        )
        self.repo.save_version(v)
        return v

    @staticmethod
    def _to_summary(t: PromptTemplateV2) -> dict:
        """轉換為 summary。"""
        return {
            "template_id": t.template_id,
            "name": t.name,
            "display_name": t.display_name,
            "category": t.category,
            "model": t.model,
            "temperature": float(t.temperature),
            "current_version": t.current_version,
            "is_active": t.is_active,
        }

    @staticmethod
    def _to_detail(t: PromptTemplateV2) -> dict:
        """轉換為 detail。"""
        return {
            "template_id": t.template_id,
            "name": t.name,
            "display_name": t.display_name,
            "category": t.category,
            "model": t.model,
            "max_tokens": t.max_tokens,
            "max_tokens_by_plan": t.max_tokens_by_plan,
            "temperature": float(t.temperature),
            "system_prompt": t.system_prompt,
            "user_prompt": t.user_prompt,
            "variables": t.variables,
            "feature_refs": t.feature_refs,
            "current_version": t.current_version,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    @staticmethod
    def _version_to_dict(v: PromptTemplateVersion) -> dict:
        """ version to dict。"""
        return {
            "version": v.version,
            "model": v.model,
            "system_prompt": v.system_prompt,
            "user_prompt": v.user_prompt,
            "temperature": float(v.temperature),
            "change_note": v.change_note,
            "created_by": str(v.created_by) if v.created_by else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
