"""Exam API — 測驗設定、生成、作答。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.exam_service import ExamService
from app.services.mock_exam_service import MockExamService
from app.services.exam_result_service import ExamResultService
from app.services.ai_generation_service import AiGenerationService

router = APIRouter(prefix="/exams")


class ExamConfigRequest(BaseModel):
    node_ids: list[str] | None = None
    document_ids: list[str] | None = None
    question_count: int
    difficulty: int | None = None
    difficulty_distribution: dict | None = None
    question_types: list[str] | None = None


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.post("/config")
def submit_exam_config(
    body: ExamConfigRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    node_ids = body.node_ids or []

    # If document_ids provided but no node_ids, resolve nodes from documents
    if not node_ids and body.document_ids:
        from app.models.knowledge_node import KnowledgeNode
        from app.models.resource import Resource
        import uuid as _uuid
        resource_ids = [_uuid.UUID(did) for did in body.document_ids]
        nodes = db.query(KnowledgeNode).filter(
            KnowledgeNode.resource_id.in_(resource_ids)
        ).all()
        node_ids = [str(n.id) for n in nodes]

    if not node_ids:
        raise HTTPException(status_code=400, detail={"message": "請至少選擇一個知識範圍"})

    # Build difficulty distribution from difficulty level if provided
    diff_dist = body.difficulty_distribution
    if not diff_dist and body.difficulty:
        diff_map = {
            1: {"easy": 60, "medium": 30, "hard": 10},
            2: {"easy": 30, "medium": 50, "hard": 20},
            3: {"easy": 10, "medium": 30, "hard": 60},
        }
        diff_dist = diff_map.get(body.difficulty, {"easy": 30, "medium": 50, "hard": 20})

    service = ExamService(db)
    result = service.submit_config(
        node_ids=node_ids,
        question_count=body.question_count,
        user_id=user_id,
        difficulty_distribution=diff_dist,
    )
    return _handle_result(result)


class SaveAnswerRequest(BaseModel):
    question_id: str
    selected_answer: str | None = None
    marked_for_review: bool | None = None


@router.post("/{exam_id}/start")
def start_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = MockExamService(db)
    result = service.start_exam(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.post("/{exam_id}/answers")
def save_answer(
    exam_id: str,
    body: SaveAnswerRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = MockExamService(db)
    result = service.save_answer(
        exam_id=exam_id,
        user_id=user_id,
        question_id=body.question_id,
        selected_answer=body.selected_answer,
        marked_for_review=body.marked_for_review,
    )
    return _handle_result(result)


@router.post("/{exam_id}/submit")
def submit_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = MockExamService(db)
    result = service.submit_exam(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.get("/{exam_id}/resume")
def resume_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = MockExamService(db)
    result = service.resume_exam(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.get("/{exam_id}/result")
def get_exam_result(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ExamResultService(db)
    result = service.get_result(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.get("/{exam_id}/result/nodes")
def get_exam_node_analysis(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ExamResultService(db)
    result = service.get_node_analysis(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


class GenerateExamRequest(BaseModel):
    fail_stage: Optional[int] = None
    always_fail: bool = False
    max_retries: int = 3


@router.post("/{exam_id}/generate")
def generate_exam(
    exam_id: str,
    body: Optional[GenerateExamRequest] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI 生成考卷，回傳進度事件（四階段 AI Prompt 流程）。"""
    service = AiGenerationService(db)

    if body and (body.fail_stage or body.always_fail):
        result = service.generate_with_retry(
            exam_id=exam_id,
            user_id=user_id,
            fail_stage=body.fail_stage,
            max_retries=body.max_retries,
            always_fail=body.always_fail,
        )
        # For retry failure, return the result directly with appropriate status
        if result.get("retries_exhausted"):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content=result)
        return _handle_result(result)
    else:
        result = service.generate(exam_id=exam_id, user_id=user_id)

    return _handle_result(result)


class UpdatePromptTemplateRequest(BaseModel):
    content: str


@router.put("/prompt-templates/{stage_id}")
def update_prompt_template(
    stage_id: int,
    body: UpdatePromptTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新 Prompt 模板（僅限管理員）。"""
    from app.models.user import User
    user = db.query(User).filter_by(id=user_id).first()
    admin_email = user.email if user else "unknown"

    service = AiGenerationService(db)
    result = service.update_prompt_template(
        stage_id=stage_id,
        new_content=body.content,
        admin_email=admin_email,
        user_id=user_id,
    )
    return _handle_result(result)


@router.get("/prompt-templates/{stage_id}/history")
def get_prompt_template_history(
    stage_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """查看 Prompt 模板的歷史版本。"""
    service = AiGenerationService(db)
    result = service.get_template_history(stage_id=stage_id, user_id=user_id)
    return _handle_result(result)
