"""AI 出題 API — 生成、品質閘門、條款同意、匯入。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.core.permissions import require_ai_budget_available
from app.services.ai_question_service import AiQuestionService
from app.services.retirement_service import RetirementService

router = APIRouter()


def _handle_result(result: dict):
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


class GenerateRequest(BaseModel):
    subject_id: Optional[str] = None
    count: int = 5


@router.post("/ai-questions/generate")
def generate(
    body: GenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    _gate: None = Depends(require_ai_budget_available),
):
    """generate。

    此 endpoint 對應 `generate` 操作。

    Args:
        body: 參數。
        _gate: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AiQuestionService(db)
    result = service.generate(
        user_id=user_id,
        subject_id=body.subject_id,
        count=body.count,
    )
    return _handle_result(result)


class ConsentRequest(BaseModel):
    agreed: bool


@router.post("/ai-questions/consent")
def consent(
    body: ConsentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """consent。

    此 endpoint 對應 `consent` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AiQuestionService(db)
    result = service.consent(user_id=user_id, agreed=body.agreed)
    return _handle_result(result)


class QualityCheckRequest(BaseModel):
    questions: list[dict] = []


@router.post("/ai-questions/quality-check")
def quality_check(
    body: QualityCheckRequest,
    db: Session = Depends(get_db),
):
    """quality check。

    此 endpoint 對應 `quality_check` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AiQuestionService(db)
    result = service.quality_check(body.questions)
    return _handle_result(result)


class RestoreRequest(BaseModel):
    subject_id: str


@router.post("/ai-questions/restore")
def restore(
    body: RestoreRequest,
    db: Session = Depends(get_db),
):
    """restore。

    此 endpoint 對應 `restore` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = RetirementService(db)
    result = service.restore(body.subject_id)
    return _handle_result(result)


class CheckReportsRequest(BaseModel):
    question_id: str


@router.post("/ai-questions/check-reports")
def check_reports(
    body: CheckReportsRequest,
    db: Session = Depends(get_db),
):
    """check reports。

    此 endpoint 對應 `check_reports` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = RetirementService(db)
    result = service.check_reports(body.question_id)
    return _handle_result(result)


class ImportRequest(BaseModel):
    subject_id: Optional[str] = None
    source_type: str = "historical"


@router.post("/questions/import")
def import_questions(
    body: ImportRequest,
    db: Session = Depends(get_db),
):
    """import questions。

    此 endpoint 對應 `import_questions` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AiQuestionService(db)
    result = service.import_questions(
        subject_id=body.subject_id,
        source_type=body.source_type,
    )
    return _handle_result(result)
