"""Wrong Answer API — 錯題複習與 AI 教練。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.wrong_answer_service import WrongAnswerService

router = APIRouter(prefix="/wrong-answers")


class CoachChatRequest(BaseModel):
    message: str


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("")
def list_wrong_answers(
    subject_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = WrongAnswerService(db)
    result = service.list_by_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)


@router.get("/questions/{question_id}/coach")
def get_coach_info_no_exam(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得 AI 教練資訊（前端不帶 exam_id 的路由）。"""
    service = WrongAnswerService(db)
    result = service.get_coach_info(
        exam_id=None, user_id=user_id, question_id=question_id
    )
    return _handle_result(result)


@router.post("/questions/{question_id}/coach")
def ai_coach_chat_no_exam(
    question_id: str,
    body: CoachChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI 教練聊天（前端不帶 exam_id 的路由）。"""
    service = WrongAnswerService(db)
    result = service.ai_coach_chat(
        exam_id=None, user_id=user_id,
        question_id=question_id, message=body.message
    )
    return _handle_result(result)


@router.get("/{exam_id}")
def get_wrong_answers_by_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = WrongAnswerService(db)
    result = service.get_wrong_answers_by_exam(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.get("/{exam_id}/questions/{question_id}/analysis")
def get_question_analysis(
    exam_id: str,
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = WrongAnswerService(db)
    result = service.get_analysis(
        exam_id=exam_id, user_id=user_id, question_id=question_id
    )
    return _handle_result(result)


@router.get("/{exam_id}/questions/{question_id}/coach")
def get_coach_info(
    exam_id: str,
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = WrongAnswerService(db)
    result = service.get_coach_info(
        exam_id=exam_id, user_id=user_id, question_id=question_id
    )
    return _handle_result(result)


@router.post("/{exam_id}/questions/{question_id}/coach")
def ai_coach_chat(
    exam_id: str,
    question_id: str,
    body: CoachChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = WrongAnswerService(db)
    result = service.ai_coach_chat(
        exam_id=exam_id, user_id=user_id,
        question_id=question_id, message=body.message
    )
    return _handle_result(result)
