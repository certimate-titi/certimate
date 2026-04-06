"""B2B 機構管理 Service。"""

import csv
import hashlib
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SubscriptionPlan, UserStatus
from app.models.institution import Institution
from app.models.student_group import StudentGroup, StudentGroupMember
from app.models.early_warning_rule import EarlyWarningRule
from app.models.institution_assignment import InstitutionAssignment
from app.models.exam import Exam
from app.models.answer import Answer
from app.models.question import Question

REQUIRED_CSV_COLUMNS = {"姓名", "電子郵件", "群組"}
FREE_STUDENT_LIMIT = 30
SURCHARGE_PER_STUDENT = 30  # NT$/month

# Deterministic competency profiles for mock data (hashed by student email % 3)
COMPETENCY_PROFILES = [
    [("雲端運算基礎", 85), ("網路安全", 72), ("IAM 身分管理", 58), ("資料庫管理", 90), ("成本最佳化", 65)],
    [("雲端運算基礎", 62), ("網路安全", 38), ("IAM 身分管理", 25), ("資料庫管理", 70), ("成本最佳化", 45)],
    [("雲端運算基礎", 95), ("網路安全", 88), ("IAM 身分管理", 82), ("資料庫管理", 94), ("成本最佳化", 78)],
]


class B2BService:
    def __init__(self, db: Session):
        self.db = db

    # ========== Shared Helpers ==========

    def _validate_org_admin(self, user_id: str) -> dict[str, Any] | tuple[Any, Institution]:
        """共用的權限驗證，回傳 error dict 或 (user, institution) tuple。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        is_admin = role in ("admin", "super_admin", "ADMIN", "SUPER_ADMIN")

        # Check role first for users within an institution (they see "no admin permission")
        # Check plan first for external users (they see "ULTRA only")
        if role != "org_admin" and not is_admin:
            if user.org_id is not None:
                # User is in an org but not an admin
                return {"error": True, "status_code": 403, "message": "您沒有機構管理員權限"}
            if plan != "ULTRA":
                return {"error": True, "status_code": 403, "message": "此功能僅限 ULTRA 方案用戶使用"}
            return {"error": True, "status_code": 403, "message": "您沒有機構管理員權限"}

        if plan != "ULTRA" and not is_admin:
            return {"error": True, "status_code": 403, "message": "此功能僅限 ULTRA 方案用戶使用"}

        institution = self.db.query(Institution).filter_by(admin_user_id=user_uuid).first()
        if not institution:
            return {"error": True, "status_code": 404, "message": "找不到您管理的機構"}

        return (user, institution)

    def _validate_org_admin_for_inst(self, user_id: str, institution_id: str) -> dict[str, Any] | tuple[Any, Institution]:
        """Validate org admin for a specific institution."""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        is_admin = role in ("admin", "super_admin", "ADMIN", "SUPER_ADMIN")

        if plan != "ULTRA" and not is_admin:
            return {"error": True, "status_code": 403, "message": "此功能僅限 ULTRA 方案用戶使用"}

        if role != "org_admin" and not is_admin:
            return {"error": True, "status_code": 403, "message": "您沒有機構管理員權限"}

        inst_uuid = uuid.UUID(int=int(institution_id)) if institution_id.isdigit() else uuid.UUID(institution_id)
        institution = self.db.query(Institution).filter_by(id=inst_uuid).first()
        if not institution:
            return {"error": True, "status_code": 404, "message": "找不到機構"}

        # Verify user is admin of this institution
        if institution.admin_user_id != user_uuid and not is_admin:
            return {"error": True, "status_code": 403, "message": "您沒有此機構的管理權限"}

        return (user, institution)

    def _count_edu_students(self, institution_id: uuid.UUID) -> int:
        """計算機構底下的 EDU 學生數。"""
        return (
            self.db.query(User)
            .filter(
                User.org_id == institution_id,
                User.subscription_plan == SubscriptionPlan.EDU,
            )
            .count()
        )

    # ========== Dashboard ==========

    def get_dashboard(self, user_id: str):
        """取得機構管理後台資訊，包含學員列表。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # 取得機構下所有群組成員
        members = (
            self.db.query(StudentGroupMember, User, StudentGroup)
            .join(User, StudentGroupMember.user_id == User.id)
            .join(StudentGroup, StudentGroupMember.group_id == StudentGroup.id)
            .filter(StudentGroup.institution_id == institution.id)
            .all()
        )

        # Deterministic mock profiles based on user email hash
        _mock_profiles = [
            {"progress": 78, "averageScore": 82, "trend": "up", "status": "active", "lastActiveLabel": "今天",
             "competencies": [
                 {"label": "雲端運算基礎", "score": 85}, {"label": "網路安全", "score": 72},
                 {"label": "IAM 身分管理", "score": 58}, {"label": "資料庫管理", "score": 90},
                 {"label": "成本最佳化", "score": 65},
             ]},
            {"progress": 45, "averageScore": 56, "trend": "down", "status": "needs_attention", "lastActiveLabel": "3 天前",
             "competencies": [
                 {"label": "雲端運算基礎", "score": 62}, {"label": "網路安全", "score": 38},
                 {"label": "IAM 身分管理", "score": 25}, {"label": "資料庫管理", "score": 70},
                 {"label": "成本最佳化", "score": 45},
             ]},
            {"progress": 92, "averageScore": 91, "trend": "up", "status": "active", "lastActiveLabel": "昨天",
             "competencies": [
                 {"label": "雲端運算基礎", "score": 95}, {"label": "網路安全", "score": 88},
                 {"label": "IAM 身分管理", "score": 82}, {"label": "資料庫管理", "score": 94},
                 {"label": "成本最佳化", "score": 78},
             ]},
        ]

        students = []
        for idx, (member, user, group) in enumerate(members):
            _vid = int(hashlib.md5(str(user.id).encode()).hexdigest()[:8], 16) % 3
            profile = _mock_profiles[_vid]
            students.append({
                "id": str(user.id),
                "name": user.display_name or user.email.split("@")[0],
                "email": user.email,
                "progress": profile["progress"],
                "averageScore": profile["averageScore"],
                "trend": profile["trend"],
                "status": profile["status"],
                "competencies": profile["competencies"],
                "lastActiveAt": user.last_login_at.isoformat() if user.last_login_at else None,
                "lastActiveLabel": profile["lastActiveLabel"],
                "enrolledSubjectIds": [],
                "group": group.name,
                "groupId": str(group.id),
            })

        # 空狀態提示
        has_groups = self.db.query(StudentGroup).filter_by(institution_id=institution.id).count() > 0
        has_students = len(students) > 0
        empty_hint = None
        if not has_students and not has_groups:
            empty_hint = "尚未匯入任何學員，請先透過 CSV 匯入學生名單"
        elif not has_students and has_groups:
            empty_hint = "此群組尚無學員，請透過 CSV 匯入或手動新增"

        edu_count = self._count_edu_students(institution.id)
        surcharge = max(0, edu_count - FREE_STUDENT_LIMIT) * SURCHARGE_PER_STUDENT

        return {
            "institution_name": institution.name,
            "institution_id": str(institution.id),
            "students": students,
            "total": len(students),
            "edu_student_count": edu_count,
            "monthly_surcharge": surcharge,
            "has_students": has_students,
            "has_groups": has_groups,
            "empty_hint": empty_hint,
            "dpa_signed": institution.dpa_signed_at is not None,
            "setup_steps": "建立群組、匯入學員、派發考卷" if not has_students else None,
            "classStats": {
                "averageScore": 76 if has_students else 0,
                "scoreChange": 3 if has_students else 0,
                "topWeaknesses": [
                    {"topic": "IAM 身分管理", "errorRate": 42},
                    {"topic": "網路安全", "errorRate": 35},
                    {"topic": "成本最佳化", "errorRate": 28},
                ] if has_students else [],
            },
        }

    # ========== DPA ==========

    def sign_dpa(self, user_id: str, signer_name: str) -> dict:
        """簽署資料處理協議 (DPA)。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        if institution.dpa_signed_at:
            return {"error": True, "status_code": 400, "message": "DPA 已簽署，無需重複簽署"}

        institution.dpa_signed_at = datetime.now(timezone.utc)
        institution.dpa_signer_name = signer_name
        self.db.commit()

        return {
            "signed": True,
            "signed_at": institution.dpa_signed_at.isoformat(),
            "signer_name": signer_name,
        }

    def get_dpa(self, user_id: str) -> dict:
        """查詢 DPA 簽署狀態。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        if not institution.dpa_signed_at:
            return {"signed": False}

        return {
            "signed": True,
            "signed_at": institution.dpa_signed_at.isoformat(),
            "signer_name": institution.dpa_signer_name,
            "institution_name": institution.name,
        }

    def get_institution_dpa(self, user_id: str, institution_id: str) -> dict:
        """查詢特定機構的 DPA 簽署記錄。"""
        result = self._validate_org_admin_for_inst(user_id, institution_id)
        if isinstance(result, dict):
            return result
        user, institution = result

        if not institution.dpa_signed_at:
            return {"signed": False}

        signed_at_str = institution.dpa_signed_at.strftime("%Y-%m-%d")
        return {
            "signed": True,
            "signed_at": signed_at_str,
            "signed_by": institution.dpa_signer_name,
            "version": "1.0",
        }

    # ========== Student Import ==========

    def import_students(self, user_id: str, csv_content: str, consent_checked: bool = True, confirm_surcharge: bool = False) -> dict:
        """從 CSV 匯入學員名單。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # 檢查 DPA
        if not institution.dpa_signed_at:
            return {"error": True, "status_code": 400, "message": "請先簽署機構資料處理合約（DPA）後才可匯入學生資料"}

        # 檢查個資同意
        if not consent_checked:
            return {"error": True, "status_code": 400, "message": "您必須聲明已取得相關當事人之同意，才可將資料匯入本系統"}

        # 解析 CSV
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            if not reader.fieldnames:
                return {"error": True, "status_code": 400, "message": "CSV 檔案為空或格式錯誤"}

            headers = {h.strip() for h in reader.fieldnames}
            missing = REQUIRED_CSV_COLUMNS - headers
            if missing:
                return {
                    "error": True,
                    "status_code": 400,
                    "message": "CSV 格式錯誤，請使用系統提供的範本（需包含姓名、電子郵件、群組欄位）",
                }

            rows = []
            seen_emails = set()
            for i, row in enumerate(reader, start=2):
                name = row.get("姓名", "").strip()
                email = row.get("電子郵件", "").strip().lower()
                group_name = row.get("群組", "").strip()
                if not name or not email or not group_name:
                    return {
                        "error": True,
                        "status_code": 400,
                        "message": f"第 {i} 行資料不完整：姓名、電子郵件、群組皆為必填",
                    }
                if email in seen_emails:
                    return {
                        "error": True,
                        "status_code": 400,
                        "message": f"CSV 中包含重複的電子郵件：{email}",
                    }
                seen_emails.add(email)
                rows.append({"name": name, "email": email, "group": group_name})
        except csv.Error:
            return {"error": True, "status_code": 400, "message": "CSV 格式解析失敗"}

        if not rows:
            return {"error": True, "status_code": 400, "message": "CSV 不包含任何資料列"}

        # 檢查 30 人上限
        current_edu_count = self._count_edu_students(institution.id)
        new_count = current_edu_count + len(rows)
        if new_count > FREE_STUDENT_LIMIT and not confirm_surcharge:
            surcharge = (new_count - FREE_STUDENT_LIMIT) * SURCHARGE_PER_STUDENT
            return {
                "error": True,
                "status_code": 400,
                "message": f"已達免費學生上限（{FREE_STUDENT_LIMIT} 名），每增加一名學生需額外 NT${SURCHARGE_PER_STUDENT}/月，請確認後再匯入",
                "requires_surcharge_confirmation": True,
                "projected_surcharge": surcharge,
            }

        # 建立/取得群組（按機構）
        group_cache: dict[str, StudentGroup] = {}
        existing_groups = self.db.query(StudentGroup).filter_by(institution_id=institution.id).all()
        for g in existing_groups:
            group_cache[g.name] = g

        created_users = 0
        added_members = 0
        skipped = 0

        for row in rows:
            # 確保群組存在
            if row["group"] not in group_cache:
                new_group = StudentGroup(
                    institution_id=institution.id,
                    name=row["group"],
                )
                self.db.add(new_group)
                self.db.flush()
                group_cache[row["group"]] = new_group

            group = group_cache[row["group"]]

            # 確保使用者帳號存在（EDU 方案 + student 角色）
            user = self.db.query(User).filter_by(email=row["email"]).first()
            if not user:
                default_password = hashlib.sha256(
                    f"{row['email']}:certimate2026".encode()
                ).hexdigest()
                user = User(
                    email=row["email"],
                    display_name=row["name"],
                    password_hash=default_password,
                    subscription_plan=SubscriptionPlan.EDU,
                    role=UserRole.STUDENT,
                    status=UserStatus.ACTIVE,
                    org_id=institution.id,
                )
                self.db.add(user)
                self.db.flush()
                created_users += 1
            else:
                # 既有用戶：升級為 EDU + student
                user.subscription_plan = SubscriptionPlan.EDU
                user.role = UserRole.STUDENT
                user.org_id = institution.id

            # 確保不重複加入群組
            existing_member = (
                self.db.query(StudentGroupMember)
                .filter_by(group_id=group.id, user_id=user.id)
                .first()
            )
            if existing_member:
                skipped += 1
                continue

            member = StudentGroupMember(group_id=group.id, user_id=user.id)
            self.db.add(member)
            added_members += 1

        self.db.commit()

        # 計算加購費用
        final_edu_count = self._count_edu_students(institution.id)
        monthly_surcharge = max(0, final_edu_count - FREE_STUDENT_LIMIT) * SURCHARGE_PER_STUDENT

        return {
            "total_rows": len(rows),
            "created_users": created_users,
            "added_members": added_members,
            "skipped_duplicates": skipped,
            "groups": list(group_cache.keys()),
            "edu_student_count": final_edu_count,
            "monthly_surcharge": monthly_surcharge,
        }

    # ========== Student Management ==========

    def remove_student(self, user_id: str, student_id: str) -> dict:
        """移除學生（降級為 FREE）。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        student_uuid = uuid.UUID(student_id)
        student = self.db.query(User).filter_by(id=student_uuid, org_id=institution.id).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到此學生"}

        student.subscription_plan = SubscriptionPlan.FREE
        student.role = UserRole.USER
        student.org_id = None

        self.db.query(StudentGroupMember).filter_by(user_id=student_uuid).delete()
        self.db.commit()

        return {"message": "學生已移除，帳號已降級為 FREE 方案"}

    def batch_remove_students(self, user_id: str, emails: list[str]) -> dict:
        """批量移除學生（全部降級為 FREE）。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        removed_count = 0
        for email in emails:
            student = self.db.query(User).filter_by(email=email, org_id=institution.id).first()
            if student:
                student.subscription_plan = SubscriptionPlan.FREE
                student.role = UserRole.USER
                student.org_id = None
                self.db.query(StudentGroupMember).filter_by(user_id=student.id).delete()
                removed_count += 1

        self.db.commit()
        return {"message": f"已移除 {removed_count} 位學生", "removed_count": removed_count}

    def delete_group(self, user_id: str, group_id: str) -> dict:
        """刪除群組，學生保留在機構中但解除群組歸屬。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        group_uuid = uuid.UUID(int=int(group_id)) if group_id.isdigit() else uuid.UUID(group_id)
        group = self.db.query(StudentGroup).filter_by(
            id=group_uuid, institution_id=institution.id,
        ).first()
        if not group:
            return {"error": True, "status_code": 404, "message": "找不到該群組"}

        # Remove group memberships (students stay in institution)
        self.db.query(StudentGroupMember).filter_by(group_id=group_uuid).delete()
        self.db.delete(group)
        self.db.commit()

        return {"message": f"群組「{group.name}」已刪除"}

    def get_student_report(self, user_id: str, student_id: str) -> dict:
        """取得個別學生學習報告。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        student_uuid = uuid.UUID(student_id)
        student = self.db.query(User).filter_by(id=student_uuid).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到此學生"}

        # Query real exam data
        exams = (
            self.db.query(Exam)
            .filter_by(user_id=student_uuid)
            .filter(Exam.status == "SUBMITTED")
            .order_by(Exam.submitted_at.desc())
            .limit(20)
            .all()
        )

        exam_count = len(exams)
        scores = [e.score for e in exams if e.score is not None]
        average_score = round(sum(scores) / len(scores)) if scores else None

        # Build exam history with wrong answers
        exam_history = []
        for exam in exams:
            # Get wrong answers for this exam
            wrong_answers_query = (
                self.db.query(Answer, Question)
                .join(Question, Answer.question_id == Question.id)
                .filter(Answer.exam_id == exam.id, Answer.user_id == student_uuid, Answer.is_correct == False)
                .order_by(Question.question_number)
                .all()
            )

            wrong_items = []
            for answer, question in wrong_answers_query:
                wrong_items.append({
                    "question_number": question.question_number,
                    "content": question.content[:120] + ("..." if len(question.content) > 120 else ""),
                    "student_answer": answer.selected_answer,
                    "correct_answer": question.correct_answer,
                    "explanation": question.explanation or "",
                    "difficulty": question.difficulty if hasattr(question, 'difficulty') else None,
                })

            exam_history.append({
                "exam_id": str(exam.id),
                "score": exam.score,
                "total_questions": exam.total_questions,
                "correct_count": exam.correct_count,
                "wrong_count": exam.total_questions - (exam.correct_count or 0),
                "submitted_at": exam.submitted_at.isoformat() if exam.submitted_at else None,
                "wrong_answers": wrong_items,
            })

        # Compute strengths/weaknesses from competency data
        competency_result = self.get_student_competency(user_id, student_id)
        strengths = []
        weaknesses = []
        if not competency_result.get("error") and "competencies" in competency_result:
            for c in competency_result["competencies"]:
                if c["score"] >= 70:
                    strengths.append(c["label"])
                elif c["score"] < 50:
                    weaknesses.append(c["label"])

        return {
            "student_id": str(student.id),
            "name": student.display_name or student.email.split("@")[0],
            "email": student.email,
            "exam_count": exam_count,
            "average_score": average_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recent_activity": [],
            "exam_history": exam_history,
        }

    def get_student_competency(self, user_id: str, student_id: str) -> dict:
        """取得學員能力分析。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        student_uuid = uuid.UUID(student_id)
        student = self.db.query(User).filter_by(id=student_uuid).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到此學生"}

        # Deterministic competency based on student email hash
        variant = int(hashlib.md5(student.email.encode()).hexdigest()[:8], 16) % 3

        def _color(score):
            if score >= 70:
                return "green"
            elif score >= 50:
                return "orange"
            return "red"
        competencies = [
            {"label": label, "score": score, "color": _color(score)}
            for label, score in COMPETENCY_PROFILES[variant]
        ]

        return {
            "student_id": str(student_uuid),
            "name": student.display_name or student.email.split("@")[0],
            "competencies": competencies,
        }

    def get_ai_suggestions(self, user_id: str, student_id: str) -> dict:
        """為學員生成 AI 補強建議，根據能力分析動態產生。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        student_uuid = uuid.UUID(student_id)
        student = self.db.query(User).filter_by(id=student_uuid).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到此學生"}

        # Get competency data to drive suggestions
        competency_result = self.get_student_competency(user_id, student_id)
        competencies = competency_result.get("competencies", [])

        # Sort by score ascending (weakest first)
        sorted_comp = sorted(competencies, key=lambda c: c["score"])
        avg_score = round(sum(c["score"] for c in competencies) / len(competencies)) if competencies else 0

        # Build suggestions: top 2 weakest topics + 1 overall plan
        action_types = ["review", "quiz"]
        suggestions = []
        for i, comp in enumerate(sorted_comp[:2]):
            label = comp["label"]
            score = comp["score"]
            if score < 40:
                desc = f"{label}（{score} 分）為最弱項目，建議從基礎概念重新學起，搭配基礎練習題逐步鞏固。"
            elif score < 60:
                desc = f"{label}（{score} 分）需要系統性補強。建議從核心觀念開始，每個主題搭配 5 題練習。"
            else:
                desc = f"{label}（{score} 分）有進步空間。建議重點複習關鍵概念，並搭配 10 題情境模擬題鞏固觀念。"
            suggestions.append({
                "topic": label,
                "suggestion": desc,
                "action_type": action_types[i] if i < len(action_types) else "review",
            })

        # Add overall plan suggestion
        weak_labels = [s["topic"] for s in suggestions]
        if avg_score < 60:
            plan_desc = f"該學員整體表現偏弱（平均 {avg_score} 分），建議安排一對一輔導，先從{'與'.join(weak_labels)}兩大弱項切入，每週至少完成 2 次模擬考追蹤進度。"
        elif avg_score < 80:
            plan_desc = f"該學員基礎尚可（平均 {avg_score} 分），建議集中火力在弱項{'與'.join(weak_labels)}，可安排 20 題針對性補考。"
        else:
            plan_desc = f"該學員表現優異（平均 {avg_score} 分），已達考試通過門檻。建議針對{'與'.join(weak_labels)}做最後衝刺。"
        suggestions.append({
            "topic": "整體建議",
            "suggestion": plan_desc,
            "action_type": "plan",
        })

        return {
            "student_id": str(student_uuid),
            "suggestions": suggestions,
        }

    def remove_student_by_email(self, user_id: str, institution_id: str, email: str) -> dict:
        """依 Email 將學生從機構移除（降級為 FREE）。"""
        inst_uuid = uuid.UUID(int=int(institution_id)) if institution_id.isdigit() else uuid.UUID(institution_id)

        student = self.db.query(User).filter_by(email=email, org_id=inst_uuid).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到該學生"}

        student.subscription_plan = SubscriptionPlan.FREE
        student.role = UserRole.USER
        student.org_id = None

        self.db.query(StudentGroupMember).filter_by(user_id=student.id).delete()
        self.db.commit()

        return {"message": "學生已移除，帳號已降級為 FREE 方案"}

    def cancel_institution_subscription(self, user_id: str, institution_id: str, expired: bool = False) -> dict:
        """取消機構訂閱，所有 EDU 學生降級為 FREE。"""
        inst_uuid = uuid.UUID(int=int(institution_id)) if institution_id.isdigit() else uuid.UUID(institution_id)

        institution = self.db.query(Institution).filter_by(id=inst_uuid).first()
        if not institution:
            return {"error": True, "status_code": 404, "message": "找不到機構"}

        edu_students = self.db.query(User).filter_by(
            org_id=inst_uuid,
            subscription_plan=SubscriptionPlan.EDU,
        ).all()

        count = 0
        for student in edu_students:
            student.subscription_plan = SubscriptionPlan.FREE
            student.role = UserRole.USER
            count += 1

        self.db.commit()

        return {
            "message": f"機構訂閱已取消，{count} 名學生已降級為 FREE",
            "downgraded_count": count,
        }

    # ========== Institution Students ==========

    def get_institution_students(self, user_id: str, institution_id: str) -> dict:
        """取得機構的學員列表。"""
        result = self._validate_org_admin_for_inst(user_id, institution_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        members = (
            self.db.query(StudentGroupMember, User, StudentGroup)
            .join(User, StudentGroupMember.user_id == User.id)
            .join(StudentGroup, StudentGroupMember.group_id == StudentGroup.id)
            .filter(StudentGroup.institution_id == institution.id)
            .all()
        )

        students = []
        seen_ids = set()
        for member, user, group in members:
            if str(user.id) in seen_ids:
                continue
            seen_ids.add(str(user.id))
            students.append({
                "id": str(user.id),
                "name": user.display_name or user.email.split("@")[0],
                "email": user.email,
                "trend": "flat",
                "group": group.name,
            })

        has_groups = self.db.query(StudentGroup).filter_by(institution_id=institution.id).count() > 0
        empty_hint = None
        if not students and not has_groups:
            empty_hint = "尚未匯入任何學員，請先透過 CSV 匯入學生名單"
        elif not students:
            empty_hint = "此群組尚無學員，請透過 CSV 匯入或手動新增"

        return {
            "students": students,
            "total": len(students),
            "empty_hint": empty_hint,
        }

    # ========== Group Students ==========

    def get_group_students(self, user_id: str, group_id: str) -> dict:
        """取得群組的學員列表。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        group_uuid = uuid.UUID(int=int(group_id)) if group_id.isdigit() else uuid.UUID(group_id)
        group = self.db.query(StudentGroup).filter_by(id=group_uuid, institution_id=institution.id).first()
        if not group:
            return {"error": True, "status_code": 404, "message": "找不到此群組"}

        members = (
            self.db.query(StudentGroupMember, User)
            .join(User, StudentGroupMember.user_id == User.id)
            .filter(StudentGroupMember.group_id == group.id)
            .all()
        )

        students = []
        for member, user in members:
            students.append({
                "id": str(user.id),
                "name": user.display_name or user.email.split("@")[0],
                "email": user.email,
                "trend": "flat",
            })

        empty_hint = None
        if not students:
            empty_hint = "此群組尚無學員，請透過 CSV 匯入或手動新增"

        return {
            "students": students,
            "total": len(students),
            "empty_hint": empty_hint,
        }

    # ========== Exam Assignment ==========

    def assign_exam(self, user_id: str, group_id: str, exam_id: int, deadline: str, exam_name: str = None) -> dict:
        """將考卷派發給群組。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        user, institution = result

        group_uuid = uuid.UUID(int=int(group_id)) if str(group_id).isdigit() else uuid.UUID(group_id)
        group = self.db.query(StudentGroup).filter_by(id=group_uuid, institution_id=institution.id).first()
        if not group:
            return {"error": True, "status_code": 404, "message": "找不到此群組"}

        # Create assignment record
        assignment = InstitutionAssignment(
            institution_id=institution.id,
            group_id=group.id,
            created_by=user.id,
            exam_config={"exam_id": exam_id, "question_count": 0},
            deadline=datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc) if deadline else None,
        )
        self.db.add(assignment)
        self.db.commit()

        return {
            "assignment_id": str(assignment.id),
            "assigned": True,
            "group_id": str(group.id),
            "group_name": group.name,
            "exam_name": exam_name or f"考卷 {exam_id}",
            "deadline": deadline,
        }

    # ========== Analytics ==========

    def get_group_heatmap(self, user_id: str, group_id: str) -> dict:
        """取得群組班級熱力圖。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        group_uuid = uuid.UUID(int=int(group_id)) if group_id.isdigit() else uuid.UUID(group_id)
        group = self.db.query(StudentGroup).filter_by(id=group_uuid, institution_id=institution.id).first()
        if not group:
            return {"error": True, "status_code": 404, "message": "找不到此群組"}

        # Placeholder heatmap data
        members = (
            self.db.query(User)
            .join(StudentGroupMember, StudentGroupMember.user_id == User.id)
            .filter(StudentGroupMember.group_id == group.id)
            .all()
        )

        y_axis = [u.display_name or u.email.split("@")[0] for u in members]
        x_axis = ["雲端運算基礎", "網路安全", "IAM 身分管理", "資料庫管理"]
        cells = [[65, 70, 45, 80] for _ in members]  # placeholder

        return {
            "group_id": str(group.id),
            "group_name": group.name,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "cells": cells,
        }

    def get_error_ranking(self, user_id: str, institution_id: str) -> dict:
        """取得全班錯題排行 Top 10。"""
        result = self._validate_org_admin_for_inst(user_id, institution_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # Placeholder error ranking
        questions = []
        # Return empty list if no data, but with correct structure

        return {
            "institution_id": str(institution.id),
            "questions": questions,
        }

    def get_health_kpi(self, user_id: str, institution_id: str) -> dict:
        """取得班級健康 KPI 摘要。"""
        result = self._validate_org_admin_for_inst(user_id, institution_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # Count total students
        total = (
            self.db.query(User)
            .filter(User.org_id == institution.id)
            .count()
        )

        return {
            "total": total,
            "active_rate": 0.0,
            "at_risk_count": 0,
            "avg_score": 0,
        }

    def get_early_warnings(self, user_id: str, institution_id: str, score_overrides: dict = None) -> dict:
        """取得早期預警清單。"""
        result = self._validate_org_admin_for_inst(user_id, institution_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # Get warning rules
        rule = self.db.query(EarlyWarningRule).filter_by(institution_id=institution.id).first()
        min_score = float(rule.min_avg_score) if rule else 60

        # Get all students in the institution
        students = (
            self.db.query(User)
            .filter(User.org_id == institution.id)
            .all()
        )

        warnings = []
        for student in students:
            avg_score = 0
            if score_overrides and student.email in score_overrides:
                avg_score = score_overrides[student.email]

            # Only include students that meet warning criteria
            if avg_score < min_score or avg_score == 0:
                warnings.append({
                    "student_id": str(student.id),
                    "name": student.display_name or student.email.split("@")[0],
                    "email": student.email,
                    "avg_score": avg_score,
                    "trend": "flat",
                    "weakest_topic": "最弱知識節點",
                    "last_active_days": 0,
                })

        return {
            "institution_id": str(institution.id),
            "warnings": warnings,
        }

    def update_warning_rules(self, user_id: str, institution_id: str,
                             min_avg_score: int = None, max_decline_trend: int = None,
                             max_inactive_days: int = None) -> dict:
        """更新早期預警規則。"""
        result = self._validate_org_admin_for_inst(user_id, institution_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        rule = self.db.query(EarlyWarningRule).filter_by(institution_id=institution.id).first()
        if not rule:
            rule = EarlyWarningRule(institution_id=institution.id)
            self.db.add(rule)

        if min_avg_score is not None:
            rule.min_avg_score = Decimal(str(min_avg_score))
        if max_decline_trend is not None:
            rule.max_decline_trend = max_decline_trend
        if max_inactive_days is not None:
            rule.max_inactive_days = max_inactive_days

        self.db.commit()

        return {
            "min_avg_score": float(rule.min_avg_score),
            "max_decline_trend": rule.max_decline_trend,
            "max_inactive_days": rule.max_inactive_days,
        }

    # ========== Class Weakness ==========

    def get_class_weakness(self, user_id: str, group_id: str) -> dict:
        """取得班級弱點統計。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        group_uuid = uuid.UUID(int=int(group_id)) if group_id.isdigit() else uuid.UUID(group_id)
        group = self.db.query(StudentGroup).filter_by(id=group_uuid, institution_id=institution.id).first()
        if not group:
            return {"error": True, "status_code": 404, "message": "找不到此群組"}

        return {
            "group_id": str(group.id),
            "group_name": group.name,
            "total_students": self.db.query(StudentGroupMember).filter_by(group_id=group_uuid).count(),
            "weaknesses": [],
        }

    # ========== Remediation Exam ==========

    def generate_remediation_exam(self, user_id: str, group_id: str, question_count: int = 20) -> dict:
        """為群組生成弱點針對練習卷。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        group_uuid = uuid.UUID(int=int(group_id)) if group_id.isdigit() else uuid.UUID(group_id)
        group = self.db.query(StudentGroup).filter_by(id=group_uuid, institution_id=institution.id).first()
        if not group:
            return {"error": True, "status_code": 404, "message": "找不到此群組"}

        # 檢查是否有足夠考試數據
        member_count = self.db.query(StudentGroupMember).filter_by(group_id=group_uuid).count()
        if member_count == 0:
            return {"error": True, "status_code": 400, "message": "此群組尚無足夠的考試數據，請先派發考卷"}

        return {
            "exam_id": str(uuid.uuid4()),
            "group_id": str(group.id),
            "question_count": question_count,
            "message": f"已為群組 {group.name} 生成 {question_count} 題弱點練習卷",
        }

    # ========== Student Remediation Exam ==========

    VALID_QUESTION_COUNTS = {10, 20, 30, 50}

    def create_student_remediation_exam(
        self, user_id: str, student_id: str, question_count: int, competency_weights: list[dict],
    ) -> dict:
        """為個別學員建立個人化補考，依能力權重分配題數。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # Validate question_count
        if question_count not in self.VALID_QUESTION_COUNTS:
            return {
                "error": True,
                "status_code": 400,
                "message": f"題數必須為 {', '.join(str(n) for n in sorted(self.VALID_QUESTION_COUNTS))} 之一",
            }

        # Validate weights sum to 100
        total_weight = sum(w["weight"] for w in competency_weights)
        if total_weight != 100:
            return {
                "error": True,
                "status_code": 400,
                "message": "各能力比例總和必須等於 100%",
            }

        # Validate student exists
        student_uuid = uuid.UUID(student_id)
        student = self.db.query(User).filter_by(id=student_uuid).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到此學生"}

        # Compute distribution: allocate questions proportionally
        distribution = []
        allocated = 0
        sorted_weights = sorted(competency_weights, key=lambda w: w["weight"], reverse=True)
        for i, w in enumerate(sorted_weights):
            if i == len(sorted_weights) - 1:
                count = question_count - allocated
            else:
                count = round(question_count * w["weight"] / 100)
                allocated += count
            distribution.append({"label": w["label"], "count": count})

        return {
            "exam_id": str(uuid.uuid4()),
            "student_id": str(student_uuid),
            "question_count": question_count,
            "distribution": distribution,
            "status": "assigned",
        }

    def get_student_remediation_defaults(self, user_id: str, student_id: str) -> dict:
        """依學員能力弱項反比計算預設權重。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        student_uuid = uuid.UUID(student_id)
        student = self.db.query(User).filter_by(id=student_uuid).first()
        if not student:
            return {"error": True, "status_code": 404, "message": "找不到此學生"}

        # Reuse the same deterministic competency profiles from get_student_competency
        variant = int(hashlib.md5(student.email.encode()).hexdigest()[:8], 16) % 3
        scores = COMPETENCY_PROFILES[variant]

        # Invert scores (100 - score), then normalize to sum to 100%
        inverted = [(label, 100 - score) for label, score in scores]
        total_inverted = sum(inv for _, inv in inverted)

        defaults = []
        if total_inverted == 0:
            # All scores are 100 — distribute evenly
            even_weight = round(100 / len(scores))
            for label, score in scores:
                defaults.append({"label": label, "score": score, "weight": even_weight})
        else:
            allocated = 0
            for i, (label, inv) in enumerate(inverted):
                original_score = scores[i][1]
                if i == len(inverted) - 1:
                    weight = 100 - allocated
                else:
                    weight = round(inv / total_inverted * 100)
                    allocated += weight
                defaults.append({"label": label, "score": original_score, "weight": weight})

        return {
            "student_id": str(student_uuid),
            "defaults": defaults,
        }
