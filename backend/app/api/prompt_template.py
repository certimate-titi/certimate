"""Prompt Template API — Feature 30 (super_admin only)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.prompt_template_service import PromptTemplateService

# Admin routes (super_admin only)
router = APIRouter(prefix="/admin/prompt-templates")

# Internal routes (for AI services)
internal_router = APIRouter(prefix="/internal/prompt-templates")


def _handle(result: dict):
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


# ── Template List & Detail ────────────────────────────────────────────────────

@router.get("")
def list_templates(
    category: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """list templates。

    此 endpoint 對應 `list_templates` 操作。

    Args:
        category: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(service.list_templates(actor_id=user_id, category=category))


@router.get("/ab-tests")
def list_ab_tests(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """list ab tests。

    此 endpoint 對應 `list_ab_tests` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    from app.repositories.prompt_template_repository import PromptTemplateRepository
    from app.models.user import User, UserRole

    u = db.query(User).filter(User.id == user_id).first()
    if not u or u.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "權限不足"})

    repo = PromptTemplateRepository(db)
    tests = repo.find_all_ab_tests()
    return {"ab_tests": [_ab_to_dict(t) for t in tests], "total": len(tests)}


@router.get("/{template_id}")
def get_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get template。

    此 endpoint 對應 `get_template` 操作。

    Args:
        template_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(service.get_template(actor_id=user_id, template_id=template_id))


# ── Create ────────────────────────────────────────────────────────────────────

class CreateTemplateRequest(BaseModel):
    template_id: str
    name: str
    display_name: str
    category: str
    model: str
    max_tokens: int
    max_tokens_by_plan: Optional[dict] = None
    temperature: Optional[float] = 0.5
    system_prompt: str
    user_prompt: str
    variables: Optional[list] = []
    feature_refs: Optional[list] = []
    change_note: Optional[str] = None


@router.post("")
def create_template(
    req: CreateTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """create template。

    此 endpoint 對應 `create_template` 操作。

    Args:
        req: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(service.create_template(actor_id=user_id, data=req.model_dump()))


# ── Update ────────────────────────────────────────────────────────────────────

class UpdateTemplateRequest(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    max_tokens_by_plan: Optional[dict] = None
    temperature: Optional[float] = None
    display_name: Optional[str] = None
    variables: Optional[list] = None
    feature_refs: Optional[list] = None
    change_note: Optional[str] = None


@router.patch("/{template_id}")
def update_template(
    template_id: str,
    req: UpdateTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """update template。

    此 endpoint 對應 `update_template` 操作。

    Args:
        template_id: 參數。
        req: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    return _handle(
        service.update_template(actor_id=user_id, template_id=template_id, data=data)
    )


# ── Deactivate ────────────────────────────────────────────────────────────────

@router.delete("/{template_id}")
def deactivate_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """deactivate template。

    此 endpoint 對應 `deactivate_template` 操作。

    Args:
        template_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(
        service.deactivate_template(actor_id=user_id, template_id=template_id)
    )


# ── Version History ───────────────────────────────────────────────────────────

@router.get("/{template_id}/versions")
def list_versions(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """list versions。

    此 endpoint 對應 `list_versions` 操作。

    Args:
        template_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(service.list_versions(actor_id=user_id, template_id=template_id))


class RollbackRequest(BaseModel):
    version: int


@router.post("/{template_id}/rollback")
def rollback_template(
    template_id: str,
    req: RollbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """rollback template。

    此 endpoint 對應 `rollback_template` 操作。

    Args:
        template_id: 參數。
        req: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(
        service.rollback_template(
            actor_id=user_id,
            template_id=template_id,
            target_version=req.version,
        )
    )


# ── A/B Test ──────────────────────────────────────────────────────────────────

class CreateAbTestRequest(BaseModel):
    name: str
    variant_b_system_prompt: str
    variant_b_user_prompt: str
    variant_b_temperature: Optional[float] = None
    traffic_split: Optional[int] = 50
    metric_name: Optional[str] = None


@router.post("/{template_id}/ab-tests")
def create_ab_test(
    template_id: str,
    req: CreateAbTestRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """create ab test。

    此 endpoint 對應 `create_ab_test` 操作。

    Args:
        template_id: 參數。
        req: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(
        service.create_ab_test(
            actor_id=user_id,
            template_id=template_id,
            data=req.model_dump(),
        )
    )


class CompleteAbTestRequest(BaseModel):
    action: str  # "complete" or "cancel"
    winner: Optional[str] = None  # "A" or "B", required when action="complete"


@router.patch("/ab-tests/{test_id}")
def update_ab_test(
    test_id: str,
    req: CompleteAbTestRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """update ab test。

    此 endpoint 對應 `update_ab_test` 操作。

    Args:
        test_id: 參數。
        req: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    if req.action == "cancel":
        return _handle(service.cancel_ab_test(actor_id=user_id, test_id=test_id))
    elif req.action == "complete":
        if not req.winner:
            raise HTTPException(
                status_code=422, detail={"message": "winner 必須為 A 或 B"}
            )
        return _handle(
            service.complete_ab_test(
                actor_id=user_id, test_id=test_id, winner=req.winner
            )
        )
    else:
        raise HTTPException(status_code=422, detail={"message": "action 無效"})


# ── Internal API (for AI services) ───────────────────────────────────────────

@internal_router.get("/{name}")
def get_prompt_for_ai(
    name: str,
    user_id_hash: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """get prompt for ai。

    此 endpoint 對應 `get_prompt_for_ai` 操作。

    Args:
        name: 參數。
        user_id_hash: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = PromptTemplateService(db)
    return _handle(
        service.get_prompt_for_ai(name=name, user_id_hash=user_id_hash)
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ab_to_dict(ab) -> dict:
    return {
        "id": str(ab.id),
        "template_id": str(ab.template_id),
        "name": ab.name,
        "variant_a_version": ab.variant_a_version,
        "traffic_split": ab.traffic_split,
        "status": ab.status,
        "winner": ab.winner,
        "metric_name": ab.metric_name,
        "started_at": ab.started_at.isoformat() if ab.started_at else None,
        "ended_at": ab.ended_at.isoformat() if ab.ended_at else None,
    }
