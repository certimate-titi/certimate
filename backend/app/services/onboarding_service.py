"""首次登入引導 Service。"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User, LearningPreference
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney, SelfAssessedLevel


LEVEL_MAP = {
    "beginner": SelfAssessedLevel.BEGINNER,
    "intermediate": SelfAssessedLevel.INTERMEDIATE,
    "advanced": SelfAssessedLevel.ADVANCED,
    "初學": SelfAssessedLevel.BEGINNER,
    "有基礎": SelfAssessedLevel.INTERMEDIATE,
    "進階": SelfAssessedLevel.ADVANCED,
}

PREF_MAP = {
    "drill": LearningPreference.DRILL,
    "concept": LearningPreference.CONCEPT,
    "mixed": LearningPreference.MIXED,
    "觀念理解優先": LearningPreference.CONCEPT,
    "大量刷題優先": LearningPreference.DRILL,
    "混合": LearningPreference.MIXED,
    "custom": LearningPreference.MIXED,
}

EDUCATION_OPTIONS = [
    "國中", "高中 / 高職", "專科", "大學", "碩士", "博士", "其他"
]


class OnboardingService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_default_category(self) -> SubjectCategory:
        cat = self.db.query(SubjectCategory).first()
        if not cat:
            cat = SubjectCategory(name="default")
            self.db.add(cat)
            self.db.flush()
        return cat

    def _create_journey(self, user_uuid: uuid.UUID, subj_data: dict) -> LearningJourney:
        subj_name = subj_data["subject_name"]
        subject = self.db.query(Subject).filter_by(name=subj_name).first()
        if not subject:
            cat = self._get_or_create_default_category()
            subject = Subject(name=subj_name, category_id=cat.id)
            self.db.add(subject)
            self.db.flush()

        exam_date_str = subj_data.get("exam_date")
        exam_date = date.fromisoformat(exam_date_str) if exam_date_str else None
        level = LEVEL_MAP.get(subj_data.get("self_assessed_level", "beginner"), SelfAssessedLevel.BEGINNER)

        journey = LearningJourney(
            user_id=user_uuid,
            subject_id=subject.id,
            exam_date=exam_date,
            self_assessed_level=level,
        )
        self.db.add(journey)
        return journey

    def get_status(self, user_id: str):
        """查看 Onboarding 狀態。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        return {"onboarding_completed": user.onboarding_completed}

    def get_step(self, user_id: str, step: int):
        """取得 Onboarding 步驟資訊。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        if step == 1:
            default_name = user.email.split("@")[0] if user.email else ""
            return {
                "step": 1,
                "show_welcome_animation": True,
                "can_skip": True,
                "fields": [
                    {"label": "顯示名稱", "type": "text", "required": False, "default": default_name},
                    {"label": "年齡", "type": "number", "required": False, "default": None},
                    {"label": "最高學歷", "type": "select", "required": False, "default": None},
                    {"label": "職業 / 領域", "type": "text", "required": False, "default": None},
                ],
                "age_range": {"min": 15, "max": 70},
                "education_options": EDUCATION_OPTIONS,
                "hint_text": "填寫個人資訊有助於 AI 教練提供更適合您的學習建議",
            }

        return {"error": True, "status_code": 400, "message": "無效的步驟"}

    def next_step(self, user_id: str, data: dict):
        """嘗試進入下一步。"""
        step = data.get("step", 0)
        subjects = data.get("subjects", [])

        if step == 2 and not subjects:
            return {"error": True, "status_code": 400, "message": "請至少選擇一個備考科目"}

        return {"message": "OK", "next_step": step + 1}

    def browse_subjects(self, user_id: str, category: str | None = None):
        """瀏覽科目分類。"""
        # Build a category name lookup
        all_cats = {c.id: c.name for c in self.db.query(SubjectCategory).all()}

        query = self.db.query(Subject)
        if category:
            cat = self.db.query(SubjectCategory).filter_by(name=category).first()
            if cat:
                query = query.filter_by(category_id=cat.id)
            else:
                return {"subjects": []}

        subjects = query.all()
        return {
            "subjects": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "category": all_cats.get(s.category_id, "其他"),
                    "description": s.description or "",
                    "isPopular": s.is_popular or False,
                }
                for s in subjects
            ]
        }

    def search_subjects(self, user_id: str, query: str):
        """搜尋科目。"""
        all_cats = {c.id: c.name for c in self.db.query(SubjectCategory).all()}
        subjects = self.db.query(Subject).filter(
            Subject.name.ilike(f"%{query}%")
        ).all()
        return {
            "subjects": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "category": all_cats.get(s.category_id, "其他"),
                    "description": s.description or "",
                    "isPopular": s.is_popular or False,
                }
                for s in subjects
            ]
        }

    def select_subjects(self, user_id: str, subjects_data: list[dict]):
        """選擇備考科目（Onboarding Step 2）。"""
        selected = []
        for s in subjects_data:
            subj = self.db.query(Subject).filter_by(name=s["subject_name"]).first()
            if subj:
                selected.append({
                    "id": str(subj.id),
                    "name": subj.name,
                    "exam_date": s.get("exam_date"),
                    "self_assessed_level": s.get("self_assessed_level"),
                    "removable": True,
                })
        return {"selected_subjects": selected}

    def remove_selected_subject(self, user_id: str, subject_id: str):
        """移除已選擇的科目（Onboarding 中）。"""
        subj_uuid = uuid.UUID(subject_id)
        subj = self.db.query(Subject).filter_by(id=subj_uuid).first()
        if not subj:
            return {"error": True, "status_code": 404, "message": "找不到該科目"}

        # Return all subjects except the removed one
        all_subjects = self.db.query(Subject).filter(Subject.id != subj_uuid).all()
        remaining = [
            {"id": str(s.id), "name": s.name, "removable": True}
            for s in all_subjects
        ]
        return {"message": f"已移除 {subj.name}", "selected_subjects": remaining}

    def set_preferences(self, user_id: str, data: dict):
        """設定學習偏好。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        minutes = data.get("daily_study_minutes", 30)
        pref = data.get("learning_preference", "mixed")

        user.daily_study_minutes = minutes
        user.learning_preference = PREF_MAP.get(pref, LearningPreference.MIXED)
        self.db.commit()

        return {"daily_study_minutes": minutes, "learning_preference": pref}

    def get_summary(self, user_id: str):
        """取得 Onboarding 設定摘要。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        journeys = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, is_archived=False
        ).all()

        subjects = []
        for j in journeys:
            subj = self.db.query(Subject).filter_by(id=j.subject_id).first()
            subjects.append({
                "id": str(subj.id) if subj else str(j.subject_id),
                "name": subj.name if subj else "Unknown",
                "exam_date": j.exam_date.isoformat() if j.exam_date else None,
                "self_assessed_level": j.self_assessed_level,
            })

        return {
            "display_name": user.display_name,
            "daily_study_minutes": user.daily_study_minutes,
            "learning_preference": user.learning_preference,
            "subjects": subjects,
            "show_start_button": True,
        }

    def complete(self, user_id: str, data: dict):
        """完成 Onboarding。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        subjects = data.get("subjects", [])

        # If no subjects provided, check if user already has journeys (from Step 2)
        if not subjects:
            existing = self.db.query(LearningJourney).filter_by(
                user_id=user_uuid, is_archived=False
            ).count()
            if existing == 0:
                return {"error": True, "status_code": 400, "message": "請至少選擇一個備考科目"}

        # Update user profile
        if data.get("display_name"):
            user.display_name = data["display_name"]
        user.daily_study_minutes = data.get("daily_study_minutes", 30)
        pref = data.get("learning_preference", "mixed")
        user.learning_preference = PREF_MAP.get(pref, LearningPreference.MIXED)

        for subj_data in subjects:
            self._create_journey(user_uuid, subj_data)

        user.onboarding_completed = True
        self.db.commit()
        return {"message": "Onboarding 完成", "redirect": "/dashboard"}

    def add_subject(self, user_id: str, data: dict):
        """新增備考科目。"""
        user_uuid = uuid.UUID(user_id)
        self._create_journey(user_uuid, data)
        self.db.commit()
        return {"message": f"已新增備考科目 {data['subject_name']}"}

    def get_available_subjects(self, user_id: str):
        """取得可選科目列表。"""
        categories = self.db.query(SubjectCategory).all()
        result = []
        for cat in categories:
            subjects = self.db.query(Subject).filter_by(category_id=cat.id).all()
            result.append({
                "category": cat.name,
                "subjects": [{"id": str(s.id), "name": s.name} for s in subjects],
            })
        return {"categories": result, "subjects": [
            {"id": str(s.id), "name": s.name}
            for s in self.db.query(Subject).all()
        ]}

    def remove_subject(self, user_id: str, subject_id: str):
        """移除備考科目（返回確認提示）。"""
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        journey = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subj_uuid, is_archived=False
        ).first()

        if not journey:
            return {"error": True, "status_code": 404, "message": "找不到該學習歷程"}

        return {
            "confirm_message": "移除後該科目的學習紀錄將被封存，確定要移除嗎？",
            "subject_id": subject_id,
        }

    def _archive_journey(self, user_id: str, subject_id: str, *, active_only: bool = True):
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        filters = {"user_id": user_uuid, "subject_id": subj_uuid}
        if active_only:
            filters["is_archived"] = False

        journey = self.db.query(LearningJourney).filter_by(**filters).first()
        if not journey:
            return {"error": True, "status_code": 404, "message": "找不到該學習歷程"}

        journey.is_archived = True
        self.db.commit()
        return {"message": "科目已封存"}

    def confirm_remove_subject(self, user_id: str, subject_id: str):
        """確認移除備考科目（封存學習歷程）。"""
        return self._archive_journey(user_id, subject_id, active_only=True)

    def archive_subject(self, user_id: str, subject_id: str):
        """封存備考科目。"""
        return self._archive_journey(user_id, subject_id, active_only=False)
