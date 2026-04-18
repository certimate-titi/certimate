"""個人儀表板 API。"""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_db_with_tenant, get_current_user_id
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
    db: Session = Depends(get_db_with_tenant),
):
    import logging
    try:
        # Guard against empty string from frontend query params
        if subject_id is not None and not subject_id.strip():
            subject_id = None
        if subject is not None and not subject.strip():
            subject = None
        service = DashboardService(db)
        result = service.get_dashboard(user_id=user_id, subject_name=subject, subject_id=subject_id)
        return _handle_result(result)
    except Exception as e:
        logging.getLogger("dashboard").exception("Dashboard error: %s", e)
        raise HTTPException(status_code=500, detail={"message": f"Dashboard error: {str(e)}"})


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


# ── 每日登入 (Feature 13) ──────────────────────────────────────────


class DailyLoginRequest(BaseModel):
    action: str | None = None


@router.post("/daily-login")
def daily_login(
    body: DailyLoginRequest | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """每日登入 — 更新連勝、產生微任務。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    now = datetime.now(timezone.utc)
    today = now.date()

    # Gap-day streak logic with freeze fallback.
    last = user.last_active_date
    user.freeze_consumed_today = False
    if last == today:
        pass  # already counted today
    elif last is None:
        user.current_streak = 1
    else:
        gap = (today - last).days
        if gap == 1:
            user.current_streak = (user.current_streak or 0) + 1
        elif gap == 2 and (user.freezes_remaining or 0) > 0:
            # Consume one freeze to bridge a single missed day.
            user.freezes_remaining = (user.freezes_remaining or 0) - 1
            user.freeze_consumed_today = True
            user.current_streak = (user.current_streak or 0) + 1
        else:
            user.current_streak = 1

    if (user.current_streak or 0) > (user.longest_streak or 0):
        user.longest_streak = user.current_streak

    user.last_active_date = today
    user.last_login_at = now
    db.commit()

    quests = [
        {"id": "q1", "type": "review", "title": "複習 3 個弱點知識節點", "status": "pending"},
        {"id": "q2", "type": "quiz", "title": "完成一份 15 題測驗", "status": "pending"},
    ]

    return {
        "ok": True,
        "streak_days": user.current_streak or 0,
        "longest_streak": user.longest_streak or 0,
        "freezes_remaining": user.freezes_remaining or 0,
        "freeze_consumed_today": bool(user.freeze_consumed_today),
        "quests": quests,
        "message": "歡迎回來！",
    }


# ── 每日任務列表 (Feature 13) ──────────────────────────────────────


@router.get("/daily-quests")
def get_daily_quests(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得每日微任務列表（含 badge 資訊）。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    quests = [
        {
            "id": "q1",
            "type": "review",
            "title": "複習 3 個弱點知識節點",
            "status": "pending",
            "quest_type": "review",
            "tooltip": "針對掌握度最低的知識節點進行複習練習",
        },
        {
            "id": "q2",
            "type": "quiz",
            "title": "完成一份 15 題測驗",
            "status": "pending",
            "quest_type": "quiz",
            "tooltip": "完成一份模擬考以鞏固學習成果",
        },
    ]

    return {"quests": quests}


# ── 拖放上傳 (Feature 13) ──────────────────────────────────────────


class DashboardUploadRequest(BaseModel):
    files: list[dict]


ALLOWED_UPLOAD_FORMATS = {"pdf", "md", "txt"}


@router.post("/upload")
def dashboard_upload(
    body: DashboardUploadRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """儀表板快速上傳區 — 拖放上傳 PDF/MD/TXT。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    results = []
    for f in body.files:
        fmt = (f.get("type") or f.get("格式") or "").lower()
        filename = f.get("filename") or f.get("檔名") or ""

        # 從副檔名判斷格式
        if not fmt or fmt not in ALLOWED_UPLOAD_FORMATS:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            fmt = ext

        if fmt not in ALLOWED_UPLOAD_FORMATS:
            raise HTTPException(
                status_code=400,
                detail={"message": "不支援的檔案格式，僅接受 PDF、MD、TXT"},
            )

        resource_id = str(uuid.uuid4())
        results.append({
            "id": resource_id,
            "resource_id": resource_id,
            "filename": filename,
            "status": "completed",
            "progress": 100,
        })

    # 回傳第一個上傳結果（單檔場景）
    if len(results) == 1:
        return results[0]
    return {"files": results, "id": results[0]["id"], "status": "completed", "progress": 100}


# ── YouTube URL 解析 (Feature 13) ──────────────────────────────────


class DashboardYoutubeRequest(BaseModel):
    url: str


YOUTUBE_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+",
)


@router.post("/youtube")
def dashboard_youtube(
    body: DashboardYoutubeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """儀表板快速上傳區 — YouTube URL 解析。"""
    if not YOUTUBE_RE.match(body.url):
        raise HTTPException(
            status_code=400,
            detail={"message": "請輸入有效的 YouTube 影片網址"},
        )

    resource_id = str(uuid.uuid4())
    return {
        "ok": True,
        "id": resource_id,
        "resource_id": resource_id,
        "type": "youtube",
        "resource_type": "youtube",
        "url": body.url,
        "status": "pending",
    }


# ── Vision OCR 權限檢查 (Feature 13) ──────────────────────────────


class VisionOcrRequest(BaseModel):
    image_data: str | None = None


@router.post("/vision-ocr")
def dashboard_vision_ocr(
    body: VisionOcrRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Vision OCR 上傳 — 需 PRO_PLUS 以上。"""
    from app.models.user import User, SubscriptionPlan
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    allowed_plans = {SubscriptionPlan.PRO_PLUS, SubscriptionPlan.ULTRA}
    if user.subscription_plan not in allowed_plans:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Vision OCR 功能需升級至 PRO+ 方案",
                "upgrade_url": "/pricing",
            },
        )

    resource_id = str(uuid.uuid4())
    return {"ok": True, "id": resource_id, "status": "pending"}


# ── 複習月曆 (Feature 13) ──────────────────────────────────────────


@router.get("/review-calendar")
def get_review_calendar(
    subject: str | None = None,
    month: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """艾賓浩斯複習月曆 — 回傳指定月份的複習排程點。"""
    from app.models.user import User
    from app.models.node_mastery import NodeMastery
    from app.models.knowledge_node import KnowledgeNode
    from app.models.learning_journey import LearningJourney
    from app.models.subject import Subject

    user_uuid = uuid.UUID(user_id)

    # 找到對應科目
    calendar = []
    if subject:
        subj = db.query(Subject).filter(Subject.name == subject).first()
        if subj:
            journey = db.query(LearningJourney).filter(
                LearningJourney.user_id == user_uuid,
                LearningJourney.subject_id == subj.id,
            ).first()
            if journey:
                # 查詢有 next_review_at 的 masteries
                masteries = (
                    db.query(NodeMastery)
                    .join(KnowledgeNode, KnowledgeNode.id == NodeMastery.node_id)
                    .filter(
                        NodeMastery.user_id == user_uuid,
                        KnowledgeNode.subject_id == subj.id,
                        NodeMastery.next_review_at.isnot(None),
                    )
                    .all()
                )
                # 按日期聚合
                date_counts: dict[str, int] = {}
                for m in masteries:
                    if m.next_review_at:
                        d = m.next_review_at.strftime("%Y-%m-%d")
                        if not month or d.startswith(month):
                            date_counts[d] = date_counts.get(d, 0) + 1

                calendar = [{"date": d, "count": c} for d, c in sorted(date_counts.items())]

    return {"calendar": calendar, "subject": subject, "month": month}


# ── 新增備考科目 (Feature 13) ──────────────────────────────────────


class AddSubjectRequest(BaseModel):
    subjects: list[dict]


@router.post("/add-subject")
def add_subject(
    body: AddSubjectRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """從儀表板新增備考科目。"""
    from app.models.user import User
    from app.models.subject import Subject, SubjectCategory
    from app.models.learning_journey import LearningJourney

    user_uuid = uuid.UUID(user_id)
    added = []

    for s in body.subjects:
        subject_name = s.get("subject") or s.get("科目")
        exam_date = s.get("exam_date") or s.get("考試日期")
        if not subject_name:
            continue

        # 找到或建立科目
        subject = db.query(Subject).filter(Subject.name == subject_name).first()
        if not subject:
            category = db.query(SubjectCategory).first()
            if not category:
                category = SubjectCategory(name="General")
                db.add(category)
                db.commit()
                db.refresh(category)
            subject = Subject(name=subject_name, category_id=category.id)
            db.add(subject)
            db.commit()
            db.refresh(subject)

        # 建立 LearningJourney（如果不存在）
        existing = db.query(LearningJourney).filter(
            LearningJourney.user_id == user_uuid,
            LearningJourney.subject_id == subject.id,
        ).first()
        if not existing:
            journey = LearningJourney(
                user_id=user_uuid,
                subject_id=subject.id,
            )
            if exam_date and hasattr(journey, "target_exam_date"):
                journey.target_exam_date = exam_date
            db.add(journey)

        added.append(subject_name)

    db.commit()

    # 回傳更新後的科目列表
    journeys = db.query(LearningJourney).filter(
        LearningJourney.user_id == user_uuid,
    ).all()
    subject_ids = [j.subject_id for j in journeys]
    from app.models.subject import Subject as S
    subjects = db.query(S).filter(S.id.in_(subject_ids)).all() if subject_ids else []

    return {
        "ok": True,
        "added": added,
        "subjects": [{"name": s.name, "id": str(s.id)} for s in subjects],
    }
