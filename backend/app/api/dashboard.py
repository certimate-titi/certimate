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
    """get dashboard。

    此 endpoint 對應 `get_dashboard` 操作。

    Args:
        subject: 參數。
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """get profile。

    此 endpoint 對應 `get_profile` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = DashboardService(db)
    result = service.get_profile(user_id=user_id)
    return _handle_result(result)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    age: int | None = None
    education: str | None = None
    career: str | None = None
    occupation: str | None = None
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
    """update profile。

    此 endpoint 對應 `update_profile` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = DashboardService(db)
    result = service.update_profile(user_id=user_id, data=body.model_dump(exclude_none=True))
    return _handle_result(result)


@router.post("/quests/{quest_id}/complete")
def complete_quest(
    quest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """手動完成每日任務（通常由自動 hook 驅動，此為相容保留）。"""
    from app.models.user import User
    from app.services.daily_quest_service import DailyQuestService
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    result = DailyQuestService(db).mark_complete_by_id(user_id, quest_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"message": "任務不存在"})
    db.commit()
    return {"message": "任務已完成", "quest_id": quest_id, **result}


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

    from app.services.daily_quest_service import DailyQuestService
    quests = DailyQuestService(db).list_today(user_id)
    db.commit()

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
    """取得每日微任務列表（真實進度）。"""
    from app.models.user import User
    from app.services.daily_quest_service import DailyQuestService
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    quests = DailyQuestService(db).list_today(user_id)
    db.commit()
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


# ── Sprint 5 P4 T42：/today 學習首頁 endpoint ────────────────────────────────


class TodayResume(BaseModel):
    """上次中斷的章節（給「今日 3 件事」的「繼續讀」卡片用）。"""

    resource_id: str
    resource_name: str
    subject_id: str | None
    chapter_anchor: str | None  # 待 Sprint 6 接 reading_progress 表


class TodayItem(BaseModel):
    """今日學習任務（建議行動）。"""

    kind: str  # "resume" | "review" | "sprint_exam"
    title: str
    description: str
    minutes: int
    target_count: int | None = None
    href: str


class TodayResponse(BaseModel):
    """`/dashboard/today` 回應。"""

    greeting: str  # 早安/午安/晚安
    streak_days: int
    days_to_exam: int | None
    review_count: int  # 答錯題待複習數
    scaffold_due_count: int  # P5 (Sprint 6 T47)：SM-2 鷹架到期數
    resume: TodayResume | None
    items: list[TodayItem]


@router.get("/today", response_model=TodayResponse)
def get_today(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
) -> TodayResponse:
    """今日學習首頁資料聚合。

    給前端 /today 路由使用，回傳今日 3 件事 + Hero 資訊。

    Args:
        user_id: 從 JWT 取得
        db: tenant-scoped session

    Returns:
        TodayResponse — 含 resume / streak / 距考天數 / 3 件事
    """
    import logging
    from datetime import datetime
    from sqlalchemy import select, desc, and_, exists
    from app.models.resource import Resource
    from app.models.learning_journey import LearningJourney
    from app.models.answer import Answer
    from app.models.question import Question

    user_uuid = uuid.UUID(user_id)

    # Greeting by hour（伺服器時區）
    h = datetime.now().hour
    greeting = (
        "夜深了" if h < 6 else
        "早安" if h < 12 else
        "午安" if h < 18 else
        "晚安"
    )

    # Resume：最近上傳 / 最近被讀的 resource（簡化：用最近 created）
    resume = None
    try:
        recent = db.execute(
            select(Resource)
            .where(Resource.user_id == user_uuid)
            .where(Resource.status == "COMPLETED")
            .order_by(desc(Resource.created_at))
            .limit(1)
        ).scalar_one_or_none()
        if recent:
            resume = TodayResume(
                resource_id=str(recent.id),
                resource_name=recent.name or '上次的資源',
                subject_id=str(recent.subject_id) if recent.subject_id else None,
                chapter_anchor=None,  # P5 接 reading_progress 表
            )
    except Exception as e:
        logging.getLogger("dashboard.today").warning("resume lookup failed: %s", e)

    # 距考天數：取最早的 LearningJourney.target_exam_date
    days_to_exam: int | None = None
    try:
        journeys = db.execute(
            select(LearningJourney)
            .where(LearningJourney.user_id == user_uuid)
        ).scalars().all()
        future_dates = [
            j.target_exam_date
            for j in journeys
            if getattr(j, "target_exam_date", None) is not None
        ]
        if future_dates:
            today = datetime.now().date()
            min_date = min(d for d in future_dates if d >= today) if any(d >= today for d in future_dates) else None
            if min_date:
                days_to_exam = (min_date - today).days
    except Exception as e:
        logging.getLogger("dashboard.today").warning("exam date lookup failed: %s", e)

    # Streak: 用 dashboard_service 既有計算（best-effort）
    streak_days = 0
    try:
        from app.services.dashboard_service import DashboardService
        svc = DashboardService(db)
        result = svc.get_dashboard(user_id=user_id, subject_name=None, subject_id=None)
        streak_days = int(result.get("streak_days", 0) or 0)
    except Exception:
        streak_days = 0

    # Review count: 待複習錯題（answers.is_correct=false 且 retired_at IS NULL 的 question 數）
    review_count = 0
    try:
        review_count = db.execute(
            select(Answer.question_id)
            .distinct()
            .where(Answer.user_id == user_uuid)
            .where(Answer.is_correct.is_(False))
            .where(
                exists().where(
                    and_(
                        Question.id == Answer.question_id,
                        Question.retired_at.is_(None),
                    )
                )
            )
        ).rowcount or 0
        # rowcount may be -1 for SELECT in some drivers; do a count fallback
        if review_count <= 0:
            from sqlalchemy import func as _func
            review_count = db.execute(
                select(_func.count(Answer.question_id.distinct()))
                .where(Answer.user_id == user_uuid)
                .where(Answer.is_correct.is_(False))
            ).scalar() or 0
    except Exception as e:
        logging.getLogger("dashboard.today").warning("review count failed: %s", e)
        review_count = 0

    # P5 (Sprint 6 T47)：SM-2 scaffold due reviews
    scaffold_due_count = 0
    try:
        from app.services.sm2_service import list_due_reviews
        due = list_due_reviews(db, user_id=user_uuid, limit=100)
        scaffold_due_count = len(due)
    except Exception as e:
        logging.getLogger("dashboard.today").warning("sm2 due lookup failed: %s", e)

    # 組「今日 3 件事」items
    items: list[TodayItem] = []
    if resume:
        items.append(TodayItem(
            kind="resume",
            title=f"繼續讀「{resume.resource_name[:40]}」",
            description="點擊接續上次中斷處",
            minutes=20,
            href=f"/library/read/reading?docId={resume.resource_id}" + (
                f"&subjectId={resume.subject_id}" if resume.subject_id else ""
            ),
        ))
    # 整合：scaffold_due 與 review_count 取較大者作主訊息
    total_review = review_count + scaffold_due_count
    if total_review > 0:
        if scaffold_due_count > 0 and review_count > 0:
            review_title = f"複習 {scaffold_due_count} 個重點 + {review_count} 題錯題"
        elif scaffold_due_count > 0:
            review_title = f"複習 {scaffold_due_count} 個鷹架重點"
        else:
            review_title = f"複習 {review_count} 題錯題"
        items.append(TodayItem(
            kind="review",
            title=review_title,
            description="遺忘曲線提醒（SM-2 演算法），現在複習效果最好",
            minutes=10 + scaffold_due_count // 5,  # 多 5 個鷹架 +1 分鐘
            target_count=total_review,
            href="/knowledge/wrong-answers" if review_count > 0 else "/today/reviews",
        ))
    items.append(TodayItem(
        kind="sprint_exam",
        title=(
            f"距考試 {days_to_exam} 天，建議今日 Sprint 模擬"
            if days_to_exam is not None and days_to_exam <= 14
            else "Sprint 模擬測驗"
        ),
        description="testing effect — 練習比再讀有效",
        minutes=30,
        href="/exam/setup",
    ))

    return TodayResponse(
        greeting=greeting,
        streak_days=streak_days,
        days_to_exam=days_to_exam,
        review_count=review_count,
        scaffold_due_count=scaffold_due_count,
        resume=resume,
        items=items,
    )
