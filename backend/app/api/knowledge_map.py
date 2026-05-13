"""Knowledge Map API — 知識心智圖導航與 AI 教練。"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_db_with_tenant, get_current_user_id
from app.services.knowledge_nav_service import KnowledgeNavService


def _sync_scaffold_tags(db: Session, scaffold_id: UUID, user_id: UUID, user_response: str) -> None:
    """從 scaffold user_response 解析 hashtag 並增量同步 scaffold_tags。

    增量策略：
    1. 計算 new_tags set（normalized）
    2. 刪除不再出現的 tags（old - new）
    3. 新增新出現的 tags（new - old）
    """
    from app.models.scaffold_tag import ScaffoldTag
    from app.utils.markdown_hashtags import extract_hashtags

    new_pairs = extract_hashtags(user_response)
    new_normalized: set[str] = {n for n, _ in new_pairs}

    # 取得現有 tags
    existing = (
        db.query(ScaffoldTag)
        .filter(
            ScaffoldTag.scaffold_id == scaffold_id,
            ScaffoldTag.user_id == user_id,
        )
        .all()
    )
    old_normalized: set[str] = {t.tag_normalized for t in existing}

    # 刪除消失的 tags
    to_delete = old_normalized - new_normalized
    if to_delete:
        db.query(ScaffoldTag).filter(
            ScaffoldTag.scaffold_id == scaffold_id,
            ScaffoldTag.user_id == user_id,
            ScaffoldTag.tag_normalized.in_(to_delete),
        ).delete(synchronize_session=False)

    # 新增出現的 tags
    to_add = new_normalized - old_normalized
    for normalized, display in new_pairs:
        if normalized in to_add:
            db.add(
                ScaffoldTag(
                    scaffold_id=scaffold_id,
                    user_id=user_id,
                    tag_normalized=normalized,
                    tag_display=display,
                )
            )

router = APIRouter(prefix="/knowledge-map")


class CoachMessageRequest(BaseModel):
    node_id: str | None = None
    message: str


class SubmitAnswersRequest(BaseModel):
    correct_count: int
    total_count: int


def _handle_result(result: dict):
    """統一處理 service 回傳結果。"""
    if result.get("error"):
        status_code = result.get("status_code", 400)
        resp = {"message": result["message"]}
        for key in ("upgrade", "paywall", "upgrade_prompt", "target_plan"):
            if key in result:
                resp[key] = result[key]
        raise HTTPException(status_code=status_code, detail=resp)
    return result


@router.get("/subjects/{subject_id}/nodes")
def get_nodes_by_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """get nodes by subject。

    此 endpoint 對應 `get_nodes_by_subject` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.get_nodes_by_subject(subject_id, user_id)
    return _handle_result(result)


@router.get("/nodes/{node_id}")
def get_node_detail(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """get node detail。

    此 endpoint 對應 `get_node_detail` 操作。

    Args:
        node_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.get_node_detail(node_id, user_id)
    return _handle_result(result)


@router.get("/nodes/{node_id}/scaffolds")
def get_node_scaffolds(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """取得節點對應的學習鷹架（TASK-02）。"""
    service = KnowledgeNavService(db)
    result = service.get_node_scaffolds(node_id, user_id)
    return _handle_result(result)


@router.get("/subjects/{subject_id}/scaffolds")
def get_subject_scaffolds(
    subject_id: str,
    user_response_only: bool = True,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """取得科目層級的學習鷹架（跨 resource 合併）。

    - user_response_only=true（預設）：只回有 user_response 的筆記，供 /notes 頁使用。
    - 回傳 {items: [...], total} shape。
    """
    service = KnowledgeNavService(db)
    result = service.get_subject_scaffolds(
        subject_id=subject_id,
        user_id=user_id,
        user_response_only=user_response_only,
        limit=limit,
        offset=offset,
    )
    return _handle_result(result)


@router.get("/resources/{resource_id}/scaffolds")
def get_resource_scaffolds(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """取得資源層級的學習鷹架清單（Spec 11 §「解析內容」入口）。

    用於從 /account/resource-library 點擊「解析內容」進入知識地圖時，
    顯示該資源所有 scaffolds（不限定到單一節點）。
    """
    service = KnowledgeNavService(db)
    result = service.get_resource_scaffolds(resource_id, user_id)
    return _handle_result(result)


@router.get("/nodes/{node_id}/source")
def get_node_source(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """get node source。

    此 endpoint 對應 `get_node_source` 操作。

    Args:
        node_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.get_node_source(node_id, user_id)
    return _handle_result(result)


@router.get("/resources/{resource_id}/summary")
def get_resource_summary(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """Return synthesized summary for a resource — used by frontend 原文
    fallback when resource_chunks is empty (system-created 考古題題庫).

    Walks the knowledge_nodes subtree rooted at any node with matching
    resource_id, concatenating source_text fields into a readable document.
    """
    import uuid as _u
    from sqlalchemy import text as _sql
    try:
        rid = _u.UUID(resource_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"message": "invalid resource_id"})

    rows = db.execute(
        _sql(
            """
            SELECT id::text, name, depth, parent_id::text, source_text
            FROM knowledge_nodes
            WHERE resource_id = :rid
            ORDER BY depth, sort_order
            """
        ),
        {"rid": rid},
    ).fetchall()
    if not rows:
        return {"title": "", "content": "", "node_count": 0}

    root = rows[0]
    parts = [str(root[4] or root[1])]
    for r in rows[1:]:
        parts.append(f"\n\n## {r[1]}\n\n{r[4] or ''}")
    return {
        "title": root[1],
        "content": "\n".join(parts),
        "node_count": len(rows),
    }


@router.get("/layout")
def get_layout(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """get layout。

    此 endpoint 對應 `get_layout` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.get_layout(user_id)
    return _handle_result(result)


@router.post("/coach/message")
def send_coach_message(
    body: CoachMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """send coach message。

    此 endpoint 對應 `send_coach_message` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.send_coach_message(body.node_id, body.message, user_id)
    return _handle_result(result)


@router.post("/ai-coach/chat")
def ai_coach_chat(
    body: CoachMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """ai coach chat。

    此 endpoint 對應 `ai_coach_chat` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.send_coach_message(body.node_id, body.message, user_id)
    return _handle_result(result)


class NodeChatRequest(BaseModel):
    message: str


@router.post("/nodes/{node_id}/chat")
def node_chat(
    node_id: str,
    body: NodeChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """節點聊天（前端 knowledge page 使用）。"""
    service = KnowledgeNavService(db)
    result = service.send_coach_message(node_id, body.message, user_id)
    return _handle_result(result)


@router.post("/nodes/{node_id}/submit-answers")
def submit_answers(
    node_id: str,
    body: SubmitAnswersRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: resource_chunks + answers
):
    """submit answers。

    此 endpoint 對應 `submit_answers` 操作。

    Args:
        node_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = KnowledgeNavService(db)
    result = service.submit_answers(node_id, user_id, body.correct_count, body.total_count)
    return _handle_result(result)


# ---------------------------------------------------------------------------
# PATCH /knowledge-map/scaffolds/{scaffold_id} — 更新 user_response（Feature 50）
# ---------------------------------------------------------------------------

@router.post("/scaffolds/reset-responses")
def reset_scaffold_user_responses(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """將當前 user 擁有的所有 resource 的 scaffold.user_response 全部 NULL 化。

    - 只清該 user 自己 resource 的 scaffolds（resource.user_id == user）
    - 不刪 scaffold row（鷹架本身是系統資產）
    - 無資料時回 {cleared: 0}，不報錯
    - 需登入（JWT）
    """
    from sqlalchemy import update
    from app.models.resource import Resource
    from app.models.resource_scaffold import ResourceScaffold

    uid = UUID(user_id)

    # 取得該 user 所有 resource id
    resource_ids = [
        r.id
        for r in db.query(Resource.id).filter(Resource.user_id == uid).all()
    ]

    if not resource_ids:
        return {"cleared": 0}

    # 只清有 user_response 的 scaffolds（有效範圍：user 擁有的 resources）
    result = db.execute(
        update(ResourceScaffold)
        .where(
            ResourceScaffold.resource_id.in_(resource_ids),
            ResourceScaffold.user_response.isnot(None),
        )
        .values(user_response=None, responded_at=None)
    )
    db.commit()

    return {"cleared": result.rowcount}


class ScaffoldUserResponseUpdate(BaseModel):
    """PATCH scaffold user_response request body。"""

    user_response: str = Field(..., min_length=1, max_length=10000)


@router.patch("/scaffolds/{scaffold_id}")
def patch_scaffold_user_response(
    scaffold_id: UUID,
    body: ScaffoldUserResponseUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """更新 scaffold 的 user_response（使用者練習作答）。

    - 不存在 → 404
    - 不屬於自己的 resource → 403
    - user_response 不可為空（Pydantic min_length=1）
    """
    from app.models.resource import Resource
    from app.models.resource_scaffold import ResourceScaffold

    scaffold = db.get(ResourceScaffold, scaffold_id)
    if not scaffold:
        raise HTTPException(status_code=404, detail="scaffold 不存在")

    resource = db.get(Resource, scaffold.resource_id)
    if not resource or resource.user_id != UUID(user_id):
        raise HTTPException(status_code=403, detail="無權限修改此 scaffold")

    scaffold.user_response = body.user_response.strip()
    scaffold.responded_at = datetime.now(timezone.utc)
    db.flush()  # 確保 scaffold.id 可用

    # 解析 user_response 中的 hashtag 並同步 scaffold_tags
    _sync_scaffold_tags(db, scaffold_id, UUID(user_id), scaffold.user_response)

    db.commit()
    db.refresh(scaffold)
    return {"status": "ok", "scaffold_id": str(scaffold_id)}
