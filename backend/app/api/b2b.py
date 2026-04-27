"""B2B API — 機構管理後台。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.b2b_service import B2BService
from app.models.user import User

router = APIRouter(prefix="/b2b")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ========== Admin Dashboard (ULTRA only) ==========

@router.get("/admin-dashboard")
def get_admin_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get admin dashboard。

    此 endpoint 對應 `get_admin_dashboard` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    if plan != "ULTRA":
        has_used_trial = bool(user.has_used_trial) if hasattr(user, 'has_used_trial') else False
        raise HTTPException(
            status_code=403,
            detail={
                "message": "此功能僅限 ULTRA 方案用戶使用",
                "upgrade_guidance": {
                    "required_plan": "ULTRA_1599",
                    "feature_name": "教育管理後台",
                    "trial_available": not has_used_trial,
                },
            },
        )

    service = B2BService(db)
    return {"message": "教育管理後台", "admin": True}


# ========== Dashboard ==========

@router.get("/dashboard")
def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get dashboard。

    此 endpoint 對應 `get_dashboard` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_dashboard(user_id=user_id)
    return _handle_result(result)


# ========== DPA ==========

class DPASignRequest(BaseModel):
    signer_name: str


@router.post("/dpa/sign")
def sign_dpa(
    body: DPASignRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """sign dpa。

    此 endpoint 對應 `sign_dpa` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.sign_dpa(user_id=user_id, signer_name=body.signer_name)
    return _handle_result(result)


@router.get("/dpa")
def get_dpa(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get dpa。

    此 endpoint 對應 `get_dpa` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_dpa(user_id=user_id)
    return _handle_result(result)


@router.get("/institutions/{inst_id}/dpa")
def get_institution_dpa(
    inst_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get institution dpa。

    此 endpoint 對應 `get_institution_dpa` 操作。

    Args:
        inst_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_institution_dpa(user_id=user_id, institution_id=inst_id)
    return _handle_result(result)


# ========== Student Import ==========

@router.post("/students/import")
async def import_students(
    file: UploadFile = File(...),
    consent_checked: bool = Query(True),
    confirm_surcharge: bool = Query(False),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """import students。

    此 endpoint 對應 `import_students` 操作。

    Args:
        file: 參數。
        consent_checked: 參數。
        confirm_surcharge: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail={"message": "請上傳 .csv 格式的檔案"})

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail={"message": "檔案編碼錯誤，請使用 UTF-8 編碼"})

    service = B2BService(db)
    result = service.import_students(
        user_id=user_id,
        csv_content=csv_text,
        consent_checked=consent_checked,
        confirm_surcharge=confirm_surcharge,
    )
    return _handle_result(result)


# ========== Student Management ==========

@router.delete("/students/{student_id}")
def remove_student(
    student_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """remove student。

    此 endpoint 對應 `remove_student` 操作。

    Args:
        student_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.remove_student(user_id=user_id, student_id=student_id)
    return _handle_result(result)


class BatchRemoveRequest(BaseModel):
    emails: list[str]


@router.post("/students/batch-remove")
def batch_remove_students(
    body: BatchRemoveRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """batch remove students。

    此 endpoint 對應 `batch_remove_students` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.batch_remove_students(user_id=user_id, emails=body.emails)
    return _handle_result(result)


@router.get("/students/{student_id}/report")
def get_student_report(
    student_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get student report。

    此 endpoint 對應 `get_student_report` 操作。

    Args:
        student_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_student_report(user_id=user_id, student_id=student_id)
    return _handle_result(result)


@router.get("/students/{student_id}/competency")
def get_student_competency(
    student_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get student competency。

    此 endpoint 對應 `get_student_competency` 操作。

    Args:
        student_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_student_competency(user_id=user_id, student_id=student_id)
    return _handle_result(result)


@router.post("/students/{student_id}/ai-suggestions")
def request_ai_suggestions(
    student_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """request ai suggestions。

    此 endpoint 對應 `request_ai_suggestions` 操作。

    Args:
        student_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_ai_suggestions(user_id=user_id, student_id=student_id)
    return _handle_result(result)


# ========== Institution Student Management ==========

@router.get("/institutions/{inst_id}/students")
def get_institution_students(
    inst_id: str,
    search: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get institution students。

    此 endpoint 對應 `get_institution_students` 操作。

    Args:
        inst_id: 參數。
        search: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_institution_students(user_id=user_id, institution_id=inst_id, search=search)
    return _handle_result(result)


@router.get("/students/{student_id}/review-schedule")
def get_student_review_schedule(
    student_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get student review schedule。

    此 endpoint 對應 `get_student_review_schedule` 操作。

    Args:
        student_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_student_review_schedule(user_id=user_id, student_id=student_id)
    return _handle_result(result)


@router.get("/groups/{group_id}/weakness-analysis")
def get_group_weakness_analysis(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get group weakness analysis。

    此 endpoint 對應 `get_group_weakness_analysis` 操作。

    Args:
        group_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_class_weakness_analysis(user_id=user_id, group_id=group_id)
    return _handle_result(result)


@router.delete("/institutions/{inst_id}/students/{email}")
def remove_student_by_email(
    inst_id: str,
    email: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """remove student by email。

    此 endpoint 對應 `remove_student_by_email` 操作。

    Args:
        inst_id: 參數。
        email: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.remove_student_by_email(user_id=user_id, institution_id=inst_id, email=email)
    return _handle_result(result)


class CancelSubscriptionRequest(BaseModel):
    expired: bool = False


@router.post("/institutions/{inst_id}/cancel-subscription")
def cancel_institution_subscription(
    inst_id: str,
    body: CancelSubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """cancel institution subscription。

    此 endpoint 對應 `cancel_institution_subscription` 操作。

    Args:
        inst_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.cancel_institution_subscription(
        user_id=user_id, institution_id=inst_id, expired=body.expired,
    )
    return _handle_result(result)


# ========== Institution Analytics ==========

@router.get("/institutions/{inst_id}/error-ranking")
def get_error_ranking(
    inst_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get error ranking。

    此 endpoint 對應 `get_error_ranking` 操作。

    Args:
        inst_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_error_ranking(user_id=user_id, institution_id=inst_id)
    return _handle_result(result)


@router.get("/institutions/{inst_id}/health-kpi")
def get_health_kpi(
    inst_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get health kpi。

    此 endpoint 對應 `get_health_kpi` 操作。

    Args:
        inst_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_health_kpi(user_id=user_id, institution_id=inst_id)
    return _handle_result(result)


@router.get("/institutions/{inst_id}/early-warnings")
def get_early_warnings(
    inst_id: str,
    score_overrides: str = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get early warnings。

    此 endpoint 對應 `get_early_warnings` 操作。

    Args:
        inst_id: 參數。
        score_overrides: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    import json as _json
    overrides = _json.loads(score_overrides) if score_overrides else None
    service = B2BService(db)
    result = service.get_early_warnings(user_id=user_id, institution_id=inst_id, score_overrides=overrides)
    return _handle_result(result)


@router.put("/institutions/{inst_id}/warning-rules")
def update_warning_rules(
    inst_id: str,
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """update warning rules。

    此 endpoint 對應 `update_warning_rules` 操作。

    Args:
        inst_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.update_warning_rules(
        user_id=user_id,
        institution_id=inst_id,
        min_avg_score=body.get("min_avg_score"),
        max_decline_trend=body.get("max_decline_trend"),
        max_inactive_days=body.get("max_inactive_days"),
    )
    return _handle_result(result)


# ========== Group Management ==========

@router.delete("/groups/{group_id}")
def delete_group(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """delete group。

    此 endpoint 對應 `delete_group` 操作。

    Args:
        group_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.delete_group(user_id=user_id, group_id=group_id)
    return _handle_result(result)


@router.get("/groups/{group_id}/students")
def get_group_students(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get group students。

    此 endpoint 對應 `get_group_students` 操作。

    Args:
        group_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_group_students(user_id=user_id, group_id=group_id)
    return _handle_result(result)


@router.post("/groups/{group_id}/assign-exam")
def assign_exam_to_group(
    group_id: str,
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """assign exam to group。

    此 endpoint 對應 `assign_exam_to_group` 操作。

    Args:
        group_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.assign_exam(
        user_id=user_id,
        group_id=group_id,
        exam_id=body.get("exam_id"),
        deadline=body.get("deadline"),
        exam_name=body.get("exam_name"),
    )
    return _handle_result(result)


@router.get("/groups/{group_id}/heatmap")
def get_group_heatmap(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get group heatmap。

    此 endpoint 對應 `get_group_heatmap` 操作。

    Args:
        group_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_group_heatmap(user_id=user_id, group_id=group_id)
    return _handle_result(result)


# ========== Class Weakness ==========

@router.get("/class/{group_id}/weakness")
def get_class_weakness(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get class weakness。

    此 endpoint 對應 `get_class_weakness` 操作。

    Args:
        group_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_class_weakness(user_id=user_id, group_id=group_id)
    return _handle_result(result)


# ========== Remediation Exam ==========

class RemediationRequest(BaseModel):
    question_count: int = 20


@router.post("/exam/remediation/{group_id}")
def generate_remediation_exam(
    group_id: str,
    body: RemediationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """generate remediation exam。

    此 endpoint 對應 `generate_remediation_exam` 操作。

    Args:
        group_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.generate_remediation_exam(
        user_id=user_id,
        group_id=group_id,
        question_count=body.question_count,
    )
    return _handle_result(result)


# ========== Student Remediation Exam ==========

class CompetencyWeight(BaseModel):
    label: str
    weight: int


class StudentRemediationRequest(BaseModel):
    question_count: int = 20
    competency_weights: list[CompetencyWeight]


@router.post("/students/{student_id}/remediation-exam")
def create_student_remediation_exam(
    student_id: str,
    body: StudentRemediationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """create student remediation exam。

    此 endpoint 對應 `create_student_remediation_exam` 操作。

    Args:
        student_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.create_student_remediation_exam(
        user_id=user_id,
        student_id=student_id,
        question_count=body.question_count,
        competency_weights=[w.model_dump() for w in body.competency_weights],
    )
    return _handle_result(result)


@router.get("/students/{student_id}/remediation-defaults")
def get_student_remediation_defaults(
    student_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get student remediation defaults。

    此 endpoint 對應 `get_student_remediation_defaults` 操作。

    Args:
        student_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = B2BService(db)
    result = service.get_student_remediation_defaults(
        user_id=user_id,
        student_id=student_id,
    )
    return _handle_result(result)
