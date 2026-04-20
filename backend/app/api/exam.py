"""Exam API — 測驗設定、生成、作答。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_db, get_db_with_tenant, get_current_user_id
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
    exam_mode: str | None = None  # "hybrid" (default) | "historical_only"
    custom_bloom_ratio: dict | None = None


class SelectResourceRequest(BaseModel):
    resource_id: str


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
        custom_bloom_ratio=body.custom_bloom_ratio,
        question_types=body.question_types,
        exam_mode=body.exam_mode,
    )
    return _handle_result(result)


@router.post("/select-resource")
def select_resource(
    body: SelectResourceRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    result = service.select_resource(user_id=user_id, resource_id=body.resource_id)
    return _handle_result(result)


class SaveAnswerRequest(BaseModel):
    question_id: str
    selected_answer: str | None = None
    user_choice: str | None = None  # frontend sends this
    marked_for_review: bool | None = None
    confidence: str | None = None


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
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    service = MockExamService(db)
    result = service.save_answer(
        exam_id=exam_id,
        user_id=user_id,
        question_id=body.question_id,
        selected_answer=body.selected_answer or body.user_choice,
        marked_for_review=body.marked_for_review,
        confidence=body.confidence,
    )
    return _handle_result(result)


@router.post("/{exam_id}/submit")
def submit_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """考試交卷 — 回傳 202 Accepted，非同步結算 SM-2。"""
    import logging
    from fastapi.responses import JSONResponse
    from app.models.answer import Answer
    from app.models.question import Question
    import uuid as uuid_mod

    try:
        service = MockExamService(db)
        result = service.submit_exam(exam_id=exam_id, user_id=user_id)

        if result.get("error"):
            return _handle_result(result)

        # 收集答案用於 SM-2 結算
        answers_for_settlement = []
        answers = db.query(Answer).filter(
            Answer.exam_id == uuid_mod.UUID(exam_id),
            Answer.user_id == uuid_mod.UUID(user_id),
        ).all()

        for a in answers:
            q = db.query(Question).filter(Question.id == a.question_id).first()
            if q and q.node_id:
                answers_for_settlement.append({
                    "question_id": str(a.question_id),
                    "node_id": str(q.node_id),
                    "is_correct": bool(a.is_correct),
                })

        # 非同步結算（Celery），失敗則同步 fallback
        settlement_mode = "none"
        if answers_for_settlement:
            try:
                from app.tasks.exam_settlement import settle_exam
                task = settle_exam.delay(exam_id, user_id, answers_for_settlement)
                settlement_mode = "async"
                result["task_id"] = task.id
            except Exception:
                try:
                    from app.tasks.exam_settlement import _settle_exam_sync
                    _settle_exam_sync(exam_id, user_id, answers_for_settlement)
                    settlement_mode = "sync_fallback"
                except Exception as se:
                    logging.getLogger("exam").warning("Settlement failed: %s", se)
                    settlement_mode = "settlement_failed"

        result["settlement"] = settlement_mode

        # Daily quest hook — count exam submission
        try:
            from app.services.daily_quest_service import DailyQuestService
            DailyQuestService(db).record_exam_completed(user_id, exam_id)
            db.commit()
        except Exception:
            pass

        # 非同步時回傳 202，同步時回傳 200
        status_code = 202 if settlement_mode == "async" else 200
        return JSONResponse(status_code=status_code, content=result)
    except Exception as e:
        logging.getLogger("exam").exception("Submit exam error: %s", e)
        raise HTTPException(status_code=500, detail={"message": f"Submit error: {str(e)}"})


@router.get("/{exam_id}/settlement-status")
def get_settlement_status(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """輪詢考試結算狀態（前端每 2 秒呼叫直到 settled）。"""
    from app.models.exam import Exam, ExamStatus
    import uuid as uuid_mod

    exam = db.query(Exam).filter(
        Exam.id == uuid_mod.UUID(exam_id),
        Exam.user_id == uuid_mod.UUID(user_id),
    ).first()

    if not exam:
        raise HTTPException(status_code=404, detail={"message": "考試不存在"})

    # 計算結算結果
    settled = exam.status == ExamStatus.SUBMITTED and exam.submitted_at is not None

    if settled:
        # 計算成長資料供結算動畫使用
        from app.models.node_mastery import NodeMastery
        masteries = db.query(NodeMastery).filter(
            NodeMastery.user_id == exam.user_id,
        ).all()

        mastered = sum(1 for m in masteries if m.status == "MASTERED")
        critical = sum(1 for m in masteries if m.status == "CRITICAL")
        total = len(masteries)
        avg_mastery = sum(float(m.base_mastery or 0) for m in masteries) / max(1, total)

        return {
            "settled": True,
            "exam_id": exam_id,
            "score": exam.score,
            "correct_count": exam.correct_count,
            "settlement_data": {
                "upgradedTopics": mastered,
                "blindSpots": critical,
                "previousProgress": round(avg_mastery * 0.9, 2),  # 近似值
                "newProgress": round(avg_mastery, 2),
            },
        }

    return {"settled": False, "exam_id": exam_id, "message": "結算中..."}


@router.get("/{exam_id}/resume")
def resume_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    import logging
    try:
        service = MockExamService(db)
        result = service.resume_exam(exam_id=exam_id, user_id=user_id)
        return _handle_result(result)
    except Exception as e:
        logging.getLogger("exam").exception("Resume exam error: %s", e)
        raise HTTPException(status_code=500, detail={"message": f"Resume error: {str(e)}"})


@router.get("/{exam_id}/result")
def get_exam_result(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    service = ExamResultService(db)
    result = service.get_result(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.get("/{exam_id}/result/nodes")
def get_exam_node_analysis(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
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


# ── 信心度校準 (Feature 20) ──────────────────────────────────────────

@router.get("/{exam_id}/confidence-analysis")
def get_confidence_analysis(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """信心度四象限分析。"""
    from app.models.answer import Answer
    import uuid as uuid_mod

    try:
        exam_uuid = uuid_mod.UUID(exam_id)
    except ValueError:
        return {"error": True, "status_code": 400, "message": "無效的測驗 ID"}

    answers = (
        db.query(Answer)
        .filter(Answer.exam_id == exam_uuid, Answer.user_id == uuid_mod.UUID(user_id))
        .all()
    )

    quadrants = {
        "confident_correct": [],
        "confident_incorrect": [],
        "guessing_correct": [],
        "guessing_incorrect": [],
        "somewhat_correct": [],
        "somewhat_incorrect": [],
    }

    for a in answers:
        conf = a.confidence or "somewhat"
        correct = "correct" if a.is_correct else "incorrect"
        key = f"{conf}_{correct}"
        if key in quadrants:
            quadrants[key].append({
                "question_id": str(a.question_id),
                "selected_answer": a.selected_answer,
                "confidence": conf,
                "is_correct": a.is_correct,
            })

    quadrant_summary = {}
    for key, items in quadrants.items():
        label_map = {
            "confident_correct": "真正掌握",
            "confident_incorrect": "危險盲點",
            "guessing_correct": "幸運猜對",
            "guessing_incorrect": "預期中的弱點",
            "somewhat_correct": "有點把握答對",
            "somewhat_incorrect": "有點把握答錯",
        }
        quadrant_summary[key] = {
            "count": len(items),
            "label": label_map.get(key, key),
            "questions": items,
            "alert": "red" if key == "confident_incorrect" else
                     "yellow" if key == "guessing_correct" else "green",
            "priority": "high" if key == "confident_incorrect" else
                        "medium" if key in ("guessing_correct", "guessing_incorrect") else "normal",
        }

    total = len(answers)
    calibration_rate = (
        len(quadrants["confident_correct"]) / max(1, len(quadrants["confident_correct"]) + len(quadrants["confident_incorrect"]))
    ) if answers else 0

    return {
        "exam_id": exam_id,
        "total_answers": total,
        "quadrants": quadrant_summary,
        "calibration_rate": round(calibration_rate, 2),
        "ai_coach_messages": {
            "confident_incorrect": "您對這題很有把握但答錯了，這是最需要釐清的認知盲點",
            "guessing_correct": "這些題目雖然答對，但您不太確定，建議加強相關知識點",
        },
    }


@router.get("/{exam_id}/question-grid")
def get_question_grid(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """題號導覽網格（含信心度顏色）。"""
    from app.models.answer import Answer
    from app.models.question import Question
    import uuid as uuid_mod

    try:
        exam_uuid = uuid_mod.UUID(exam_id)
    except ValueError:
        return {"error": True, "status_code": 400, "message": "無效的測驗 ID"}

    questions = db.query(Question).filter(Question.exam_id == exam_uuid).order_by(Question.question_number).all()
    answers = {
        str(a.question_id): a
        for a in db.query(Answer).filter(
            Answer.exam_id == exam_uuid, Answer.user_id == uuid_mod.UUID(user_id)
        ).all()
    }

    color_map = {"confident": "green", "somewhat": "blue", "guessing": "orange"}
    grid = []
    for q in questions:
        a = answers.get(str(q.id))
        grid.append({
            "question_id": str(q.id),
            "question_number": q.question_number,
            "answered": a is not None,
            "confidence": a.confidence if a else None,
            "color": color_map.get(a.confidence, "gray") if a else "gray",
            "marked_for_review": a.marked_for_review if a else False,
        })

    return {"exam_id": exam_id, "grid": grid}


# ── Draft Checkpoint (P2.3) ──────────────────────────────────────────

@router.patch("/{exam_id}/draft")
def save_draft(
    exam_id: str,
    body: dict,
    user_id: str = Depends(get_current_user_id),
):
    """考試草稿存檔（Redis only，不觸發 state machine）。

    前端每 30 秒呼叫一次，存入 Redis（TTL 24 小時）。
    """
    import json
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)
        key = f"exam_draft:{exam_id}:{user_id}"
        r.setex(key, 86400, json.dumps(body, ensure_ascii=False))  # 24 hr TTL
        return {"ok": True, "message": "draft saved"}
    except Exception:
        # Redis 不可用 → 靜默失敗（草稿存檔非關鍵）
        return {"ok": True, "message": "draft skipped (redis unavailable)"}


@router.get("/{exam_id}/draft")
def get_draft(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """恢復考試草稿。"""
    import json
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)
        key = f"exam_draft:{exam_id}:{user_id}"
        data = r.get(key)
        if data:
            return {"ok": True, "draft": json.loads(data)}
        return {"ok": False, "message": "no draft found"}
    except Exception:
        return {"ok": False, "message": "redis unavailable"}
