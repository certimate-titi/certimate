"""個人儀表板 API。"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("")
def get_dashboard(
    subject: str | None = None,
    subject_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    result = service.get_dashboard(user_id=user_id, subject_name=subject, subject_id=subject_id)
    return _handle_result(result)


@router.get("/profile")
def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    result = service.get_profile(user_id=user_id)
    return _handle_result(result)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    age: int | None = None
    education: str | None = None
    career: str | None = None
    daily_study_minutes: int | None = None
    learning_style: str | None = None
    current_password: str | None = None
    new_password: str | None = None


@router.patch("/profile")
def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    result = service.update_profile(user_id=user_id, data=body.model_dump(exclude_none=True))
    return _handle_result(result)


@router.post("/quests/{quest_id}/complete")
def complete_quest(
    quest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """完成每日任務。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    return {"message": "任務已完成", "quest_id": quest_id}


@router.post("/profile/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """上傳使用者頭像。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    # Store avatar URL (in production, upload to cloud storage)
    user.avatar_url = f"/avatars/{user_id}/{file.filename}"
    db.commit()
    return {"message": "頭像已更新", "avatar_url": user.avatar_url}


@router.get("/usage")
def get_usage(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得使用量統計。"""
    from app.models.user import User
    from app.models.resource import Resource
    from app.models.exam import Exam
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    upload_count = db.query(Resource).filter_by(user_id=user_uuid).count()
    exam_count = db.query(Exam).filter_by(user_id=user_uuid).count()

    return {
        "plan": user.subscription_plan or "FREE",
        "uploads": {"used": upload_count, "limit": 5},
        "exams": {"used": exam_count, "limit": 10},
        "ai_queries": {"used": 0, "limit": 50},
        "vision_pages": {"used": 0, "limit": 0},
    }


@router.get("/achievements")
def get_achievements(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得成就資料。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    return {
        "streak": {"current": 0, "best": 0, "freeze_credits": 0},
        "achievements": [],
        "milestones": [],
    }


@router.get("/export")
def export_data(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """匯出使用者資料。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    export = {
        "exported_at": datetime.utcnow().isoformat(),
        "user": {
            "email": user.email,
            "display_name": user.display_name,
            "created_at": str(user.created_at) if user.created_at else None,
        },
    }
    content = json.dumps(export, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=certimate_export_{user_id}.json"},
    )


# ── 信心度校準 (Feature 20) ──────────────────────────────────────────

@router.get("/confidence-calibration")
def get_confidence_calibration(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """儀表板信心校準區塊 — 近 5 場測驗的校準率趨勢。"""
    import uuid as uuid_mod
    from app.models.answer import Answer
    from app.models.exam import Exam, ExamStatus

    user_uuid = uuid_mod.UUID(user_id)

    # 取最近 5 場已完成且有信心度標記的測驗
    recent_exams = (
        db.query(Exam)
        .filter(Exam.user_id == user_uuid, Exam.status == ExamStatus.SUBMITTED)
        .order_by(Exam.submitted_at.desc())
        .limit(5)
        .all()
    )

    trend = []
    for exam in recent_exams:
        answers = db.query(Answer).filter(
            Answer.exam_id == exam.id, Answer.user_id == user_uuid
        ).all()

        confident_answers = [a for a in answers if a.confidence == "confident"]
        if confident_answers:
            correct = sum(1 for a in confident_answers if a.is_correct)
            rate = correct / len(confident_answers)
        else:
            rate = 0

        trend.append({
            "exam_id": str(exam.id),
            "submitted_at": exam.submitted_at.isoformat() if exam.submitted_at else None,
            "calibration_rate": round(rate, 2),
        })

    overall_rate = sum(t["calibration_rate"] for t in trend) / max(1, len(trend))
    status = "校準良好" if overall_rate >= 0.8 else "需要改善" if overall_rate >= 0.5 else "偏差較大"

    return {
        "calibration_rate": round(overall_rate, 2),
        "status": status,
        "trend": trend,
        "exam_count": len(trend),
    }
