"""Orphan Scaffold Fill API — AI 補洞鷹架 endpoints.

路由前綴：/api/v1（掛載於 main router）

Endpoints:
  GET  /scaffolds/orphan-fill/{node_id}            — 取得/觸發 orphan scaffold
  POST /scaffolds/orphan-fill/{node_id}/regenerate — 重新生成（admin only）
  POST /scaffolds/{scaffold_id}/report-inaccurate  — 回報不準確
  GET  /admin/orphan-scaffolds/review-queue        — 審核佇列（admin only）

設計規範：docs/design/orphan-mitigation-design.md 區塊 A
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db, get_current_user_with_tenant
from app.models.resource_scaffold import ResourceScaffold
from app.models.scaffold_node_link import ScaffoldNodeLink
from app.services.orphan_scaffold_fill_service import OrphanScaffoldFillService

log = logging.getLogger(__name__)

router = APIRouter()


# ── Pydantic Schemas ───────────────────────────────────────────────


class ReportInaccurateRequest(BaseModel):
    """回報 AI 補洞鷹架不準確的請求體."""

    model_config = ConfigDict(from_attributes=True)

    reason_code: str
    note: str | None = None

    @field_validator("reason_code")
    @classmethod
    def validate_reason_code(cls, v: str) -> str:
        """驗證 reason_code 在允許值集合中."""
        from app.models.scaffold_review_queue import VALID_REASON_CODES
        if v not in VALID_REASON_CODES:
            raise ValueError(
                f"reason_code 必須是以下之一：{sorted(VALID_REASON_CODES)}"
            )
        return v

    @field_validator("note")
    @classmethod
    def validate_note_length(cls, v: str | None) -> str | None:
        """note 限 100 字."""
        if v and len(v) > 100:
            raise ValueError("note 超過 100 字上限")
        return v


# ── 共用 helper ────────────────────────────────────────────────────


def _handle_result(result: dict) -> dict:
    """統一處理 service 回傳結果，錯誤時 raise HTTPException."""
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(
            status_code=status_code,
            detail={"message": result["message"]},
        )
    return result


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("/scaffolds/orphan-fill/{node_id}")
def get_orphan_scaffold(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得指定節點的 AI 補洞鷹架.

    流程：
    1. 若已有 cache（trust_level = AI_INFERRED 或 PENDING_REVIEW）→ 直接回傳 200
    2. 否則觸發生成（同步），完成後回傳 200
    3. fail-safe 阻止（佐證不足 / 信心低 / URL 幻覺）→ 回傳 422 + fail_safe=True

    Returns:
        200: 鷹架內容（is_cached=True 表示來自 cache）
        400: node_id 格式無效
        422: fail-safe 阻止生成
        503: LLM 服務暫時無法使用
    """
    import json as _json
    import uuid as _uuid

    try:
        nid = _uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"message": "無效的 node_id 格式"})

    # 先查 cache
    cached = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == nid,
            ResourceScaffold.is_orphan_fill.is_(True),
            ResourceScaffold.trust_level.in_(["AI_INFERRED", "PENDING_REVIEW"]),
        )
        .first()
    )

    if cached:
        try:
            content_parsed = _json.loads(cached.content)
        except Exception:
            content_parsed = {"raw": cached.content}

        return {
            "scaffold_id": str(cached.id),
            "node_id": node_id,
            "trust_level": cached.trust_level,
            "confidence_score": cached.confidence_score,
            "content": content_parsed,
            "template_code": cached.template_code,
            "is_cached": True,
        }

    # 觸發生成
    service = OrphanScaffoldFillService(db)
    result = service.generate_scaffold(node_id=node_id, user_id=user_id)

    if result.get("error"):
        status_code = result.get("status_code", 422)
        raise HTTPException(
            status_code=status_code,
            detail={
                "message": result["message"],
                "fail_safe": True,
            },
        )

    scaffold_id = result.get("scaffold_id")
    confidence = result.get("confidence_score")

    # 取生成的鷹架內容
    if scaffold_id:
        try:
            sid = _uuid.UUID(scaffold_id)
            new_scaffold = db.query(ResourceScaffold).filter(
                ResourceScaffold.id == sid
            ).first()
            if new_scaffold:
                try:
                    content_parsed = _json.loads(new_scaffold.content)
                except Exception:
                    content_parsed = {"raw": new_scaffold.content}
                return {
                    "scaffold_id": scaffold_id,
                    "node_id": node_id,
                    "trust_level": "AI_INFERRED",
                    "confidence_score": confidence,
                    "content": content_parsed,
                    "template_code": "K-ORPHAN-01",
                    "is_cached": False,
                    "evidence_count": result.get("evidence_count"),
                }
        except Exception as e:
            log.warning("讀取新生成鷹架失敗: %s", e)

    return result


@router.post("/scaffolds/orphan-fill/{node_id}/regenerate")
def regenerate_orphan_scaffold(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """重新生成 orphan scaffold（admin only）.

    先刪除既有 AI_INFERRED 鷹架，再重新生成。

    Returns:
        200: 重新生成成功
        403: 非 admin 用戶
        422: fail-safe 阻止
    """
    from app.models.user import User

    # admin 權限檢查
    try:
        import uuid as _uuid
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail={"message": "無效的用戶 ID"})

    user = db.query(User).filter(User.id == uid).first()
    if not user or user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail={"message": "需要管理員權限"})

    # 刪除既有 orphan scaffold
    try:
        nid = _uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"message": "無效的 node_id"})

    existing = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == nid,
            ResourceScaffold.is_orphan_fill.is_(True),
        )
        .all()
    )
    for s in existing:
        db.delete(s)
    db.commit()

    # 重新生成
    service = OrphanScaffoldFillService(db)
    result = service.generate_scaffold(node_id=node_id, user_id=user_id)
    return _handle_result(result)


@router.post("/scaffolds/{scaffold_id}/report-inaccurate")
def report_inaccurate(
    scaffold_id: str,
    body: ReportInaccurateRequest,
    ctx=Depends(get_current_user_with_tenant),
    db: Session = Depends(get_db),
):
    """學生標記 AI 補洞鷹架不準確.

    - 送出後：對此學生隱藏（前端自行處理），寫入 scaffold_review_queue
    - 若同一鷹架收到 ≥ 3 份不同用戶回報 → trust_level → PENDING_REVIEW（全部隱藏）

    Request body:
        reason_code: definition_wrong / example_wrong / answer_wrong / unrelated / other
        note: 選填說明（≤ 100 字）

    Returns:
        200: 回報成功
        404: 鷹架不存在
        409: 已回報過
        422: reason_code 不合法
    """
    service = OrphanScaffoldFillService(db)
    result = service.report_inaccurate(
        scaffold_id=scaffold_id,
        user_id=ctx.user_id,
        reason_code=body.reason_code,
        note=body.note,
        tenant_id=ctx.tenant_id,
    )
    return _handle_result(result)


@router.get("/admin/orphan-scaffolds/review-queue")
def get_review_queue(
    min_reports: int = 3,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出需人工審核的 AI 補洞鷹架佇列（admin only）.

    篩選條件：同一鷹架不同用戶回報數 ≥ min_reports（預設 3）

    Returns:
        200: {"items": [...], "total": n}
        403: 非 admin 用戶
    """
    from app.models.user import User

    try:
        import uuid as _uuid
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail={"message": "無效的用戶 ID"})

    user = db.query(User).filter(User.id == uid).first()
    if not user or user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail={"message": "需要管理員權限"})

    service = OrphanScaffoldFillService(db)
    result = service.get_review_queue(min_reports=min_reports)
    return _handle_result(result)
