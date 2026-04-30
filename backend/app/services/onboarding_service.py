"""首次登入引導 Service。"""

import uuid
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User, LearningPreference
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney, SelfAssessedLevel
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.resource_chunk import ResourceChunk
from app.models.question import Question
from app.models.exam import Exam
from app.models.answer import Answer

logger = logging.getLogger("certimate.onboarding")


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
    """Onboarding Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def _get_or_create_default_category(self) -> SubjectCategory:
        """取得 or create default category。"""
        cat = self.db.query(SubjectCategory).first()
        if not cat:
            cat = SubjectCategory(name="default")
            self.db.add(cat)
            self.db.flush()
        return cat

    SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    def _ensure_exam_bank_resource(self, subject: Subject, parent_subject: Subject | None = None) -> None:
        """若科目有考古題但尚無 Resource + KnowledgeNode，自動建立。

        Args:
            subject: 目標科目（Resource 將建在此科目下）
            parent_subject: 若子科目本身無考古題，可傳入父科目以查詢其考古題
        """
        if not subject.available_questions or subject.available_questions <= 0:
            return

        existing = self.db.query(Resource).filter_by(subject_id=subject.id).first()
        if existing:
            return

        # 決定查詢考古題的 subject_id（優先用父科目）
        exam_subject_id = parent_subject.id if parent_subject else subject.id

        # 建立系統級考古題 Resource
        resource = Resource(
            user_id=self.SYSTEM_USER_ID,
            subject_id=subject.id,
            name=f"{subject.name}考古題題庫",
            type=ResourceType.MARKDOWN,
            status=ResourceStatus.COMPLETED,
        )
        self.db.add(resource)
        self.db.flush()

        # 依 historical_source（年度/次數）分群統計
        from sqlalchemy import func as sa_func
        from app.models.exam import Exam

        source_counts = (
            self.db.query(Question.historical_source, sa_func.count(Question.id))
            .join(Exam, Question.exam_id == Exam.id)
            .filter(Exam.subject_id == exam_subject_id)
            .filter(Question.historical_source.isnot(None))
            .group_by(Question.historical_source)
            .order_by(Question.historical_source)
            .all()
        )

        # 也取得 Bloom 分佈供知識總覽摘要
        bloom_counts = (
            self.db.query(Question.bloom_category, sa_func.count(Question.id))
            .join(Exam, Question.exam_id == Exam.id)
            .filter(Exam.subject_id == exam_subject_id)
            .filter(Question.bloom_category.isnot(None))
            .group_by(Question.bloom_category)
            .all()
        )
        bloom_label = {
            "remember": "記憶", "understand": "理解", "apply": "應用",
            "analyze": "分析", "evaluate": "評鑑", "create": "創造",
        }

        # 組合根節點摘要
        total_q = subject.available_questions or 0
        source_count = len(source_counts)
        source_names = [self._format_source_name(s) for s, _ in source_counts] if source_counts else []
        bloom_summary = "、".join(
            f"{bloom_label.get(b, b)} {c} 題" for b, c in bloom_counts
        ) if bloom_counts else "尚無分類統計"

        root_summary = (
            f"📚 {subject.name}考古題題庫\n\n"
            f"總題數：{total_q} 題（涵蓋 {source_count} 份歷屆試卷）\n\n"
            f"📋 收錄試卷：\n"
        )
        for sn in source_names:
            root_summary += f"  • {sn}\n"
        root_summary += f"\n📊 Bloom 認知層次分佈：{bloom_summary}\n"
        root_summary += f"\n💡 建議先從「記憶」與「理解」層次開始練習，再逐步挑戰「應用」與「分析」題型。"

        # 建立根節點
        root = KnowledgeNode(
            resource_id=resource.id,
            name=f"{subject.name}考古題題庫 知識總覽",
            depth=0,
            sort_order=0,
            available_questions=0,
            source_text=root_summary,
            source_page_number=1,
        )
        self.db.add(root)
        self.db.flush()

        if source_counts:
            # 取得每份試卷的 bloom 分佈
            for i, (source, cnt) in enumerate(source_counts, 1):
                display_name = self._format_source_name(source)

                # 取該 source 的 bloom 細分
                per_source_bloom = (
                    self.db.query(Question.bloom_category, sa_func.count(Question.id))
                    .join(Exam, Question.exam_id == Exam.id)
                    .filter(Exam.subject_id == exam_subject_id)
                    .filter(Question.historical_source == source)
                    .filter(Question.bloom_category.isnot(None))
                    .group_by(Question.bloom_category)
                    .all()
                )
                bloom_detail = "、".join(
                    f"{bloom_label.get(b, b)} {c} 題" for b, c in per_source_bloom
                ) if per_source_bloom else ""

                child_summary = (
                    f"📝 {display_name}\n\n"
                    f"題數：{cnt} 題\n"
                    f"來源：{source}\n"
                )
                if bloom_detail:
                    child_summary += f"Bloom 分佈：{bloom_detail}\n"
                child_summary += f"\n🟢 所有題目均為歷屆真題（高信度）"

                node = KnowledgeNode(
                    resource_id=resource.id,
                    parent_id=root.id,
                    name=display_name,
                    depth=1,
                    sort_order=i,
                    available_questions=cnt,
                    source_text=child_summary,
                    source_page_number=i,
                )
                self.db.add(node)
        else:
            node = KnowledgeNode(
                resource_id=resource.id,
                parent_id=root.id,
                name=f"{subject.name}考古題",
                depth=1,
                sort_order=1,
                available_questions=subject.available_questions,
                source_text=f"📝 {subject.name}考古題\n\n題數：{subject.available_questions} 題\n🟢 所有題目均為歷屆真題（高信度）",
                source_page_number=1,
            )
            self.db.add(node)

        # 為 seed 資源建立 resource_chunks（供知識庫 accordion 展開顯示）
        self._create_seed_chunks(resource.id, exam_subject_id, resource.tenant_id)

        logger.info("Auto-created exam bank resource for subject %s (%d questions)",
                     subject.name, subject.available_questions)

    def _create_seed_chunks(self, resource_id: uuid.UUID, exam_subject_id: uuid.UUID, tenant_id: uuid.UUID | None = None) -> None:
        """從考古題 questions 建立 resource_chunks，按 historical_exam 分群。

        每個 chunk = 一份考卷（historical_exam），內容為格式化的考題列表。
        透過 subject.exam_subject_codes → historical_exams → questions 路徑查詢。
        """
        from app.models.historical_exam import HistoricalExam

        # 取得 subject 的 exam_subject_codes
        subject = self.db.query(Subject).filter(Subject.id == exam_subject_id).first()
        if not subject or not subject.exam_subject_codes:
            return

        # 解析 exam_subject_codes → (exam_code, subject_code) pairs
        # 格式: ["IPA114:114_ai_fundamentals_4th", "IPA114:114_ai_application_4th"]
        code_pairs = []
        for code_str in subject.exam_subject_codes:
            parts = code_str.split(":", 1)
            if len(parts) == 2:
                code_pairs.append((parts[0], parts[1]))

        if not code_pairs:
            return

        # 查找對應的 historical_exams
        from sqlalchemy import or_, and_
        conditions = [
            and_(HistoricalExam.exam_code == ec, HistoricalExam.subject_code == sc)
            for ec, sc in code_pairs
        ]
        hist_exams = (
            self.db.query(HistoricalExam)
            .filter(or_(*conditions))
            .order_by(HistoricalExam.subject_code)
            .all()
        )

        for i, he in enumerate(hist_exams):
            # 取得該份考卷的所有題目
            questions = (
                self.db.query(Question)
                .filter(Question.historical_exam_id == he.id)
                .order_by(Question.question_number)
                .all()
            )
            if not questions:
                continue

            # 用 exam_name + subject_name 產生可辨識的標題
            exam_title = he.exam_name or he.subject_code
            # 加入考科名稱區分（同一考試可能有多個考科）
            subject_label = he.subject_name or ""
            # 若 subject_name 與 exam_name 高度重複，改用 subject_code 解析
            if not subject_label or subject_label in (exam_title or ""):
                code_label = self._subject_code_to_label(he.subject_code)
                if code_label:
                    subject_label = code_label
            if subject_label:
                exam_title = f"{exam_title}｜{subject_label}"

            # 格式化考題內容
            lines = [f"📝 {exam_title}（共 {len(questions)} 題）\n"]
            for q in questions:
                lines.append(f"{q.question_number}. {q.content}")
                if q.option_a:
                    lines.append(f"   (A) {q.option_a}")
                if q.option_b:
                    lines.append(f"   (B) {q.option_b}")
                if q.option_c:
                    lines.append(f"   (C) {q.option_c}")
                if q.option_d:
                    lines.append(f"   (D) {q.option_d}")
                if q.correct_answer:
                    lines.append(f"   ✅ 答案：{q.correct_answer}")
                lines.append("")  # blank line between questions

            content = "\n".join(lines)

            chunk = ResourceChunk(
                resource_id=resource_id,
                tenant_id=tenant_id,
                chunk_index=i,
                content=content,
                token_count=len(content),
                source_page_start=i + 1,
                source_page_end=i + 1,
                metadata_json={
                    "section_title": f"{exam_title} — {len(questions)} 題",
                    "depth": 1,
                    "chunk_type": "exam_questions",
                    "historical_exam_id": str(he.id),
                    "subject_code": he.subject_code,
                    "question_count": len(questions),
                },
            )
            self.db.add(chunk)

    @staticmethod
    def _format_source_name(raw_source: str) -> str:
        """將 historical_source 轉為使用者友善的顯示名稱。

        Examples:
            '民國114年 ai application 4th' → '民國114年 第4回'
            '第01次 證券商業務員' → '第1次 證券商業務員'
            '民國109年 bda beginner sample subject1' → '民國109年 模擬卷1'
        """
        import re

        # 已經有中文描述的直接清理
        parts = raw_source.strip().split(" ", 1)
        prefix = parts[0]  # e.g., '民國114年' or '第01次'
        suffix = parts[1] if len(parts) > 1 else ""

        # Remove leading zeros from 第0N次
        prefix = re.sub(r'第0*(\d+)次', r'第\1次', prefix)

        # If suffix is Chinese already, return as-is
        if suffix and any('\u4e00' <= c <= '\u9fff' for c in suffix):
            return f"{prefix} {suffix}"

        # Parse English suffix patterns
        # 'bda beginner sample subject1' → '模擬卷1'
        m = re.search(r'sample\s*subject(\d+)', suffix, re.IGNORECASE)
        if m:
            return f"{prefix} 模擬卷{m.group(1)}"

        # 'bda beginner subject1' → '科目卷1'
        m = re.search(r'subject(\d+)', suffix, re.IGNORECASE)
        if m:
            return f"{prefix} 科目卷{m.group(1)}"

        # Skip noise words, translate meaningful keywords
        noise = {"ai", "is", "mid", "beginner", "advanced", "bda"}
        keyword_map = {
            "fundamentals": "基礎概論", "application": "應用",
            "tech": "技術", "management": "管理",
            "planning": "規劃", "ml": "機器學習",
            "bigdata": "大數據", "land": "土地", "law": "法規",
            "civil": "民事",
        }

        # 'ai application 4th' → extract Nth回 + translated keywords
        ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', suffix)
        ordinal_str = f"第{ordinal_match.group(1)}回 " if ordinal_match else ""

        translated = []
        for word in suffix.split():
            # Skip ordinal (already handled)
            if re.match(r'\d+(?:st|nd|rd|th)', word):
                continue
            low = word.lower()
            if low in noise:
                continue
            mapped = keyword_map.get(low)
            if mapped:
                translated.append(mapped)
            else:
                translated.append(word)

        label = ordinal_str + "".join(translated)
        if label.strip():
            return f"{prefix} {label.strip()}"

        return raw_source

    @staticmethod
    def _subject_code_to_label(subject_code: str) -> str:
        """從 historical_exam.subject_code 提取考科中文標籤。

        Examples:
            '114_ai_fundamentals_4th' → '基礎概論'
            '114_ai_application_4th'  → '應用'
            '0101'                    → ''（純數字編碼不翻譯）
        """
        keyword_map = {
            "fundamentals": "基礎概論", "application": "應用",
            "tech": "技術", "management": "管理",
            "planning": "規劃", "ml": "機器學習",
            "bigdata": "大數據", "land": "土地", "law": "法規",
            "civil": "民事", "security": "資安",
        }
        noise = {"ai", "is", "mid", "beginner", "advanced", "bda", "114", "113", "112"}

        parts = subject_code.replace("_", " ").split()
        labels = []
        for p in parts:
            low = p.lower()
            if low in noise or low.isdigit() or low.endswith(("st", "nd", "rd", "th")):
                continue
            mapped = keyword_map.get(low)
            if mapped:
                labels.append(mapped)
        return "".join(labels)

    def _create_journey(self, user_uuid: uuid.UUID, subj_data: dict) -> LearningJourney:
        """建立 journey。"""
        subj_name = subj_data["subject_name"]
        # PRD-033: 先找平台官方考科（scope=platform）或自己建的
        subject = self.db.query(Subject).filter(
            Subject.name == subj_name,
            ((Subject.scope == "platform") & (Subject.owner_user_id.is_(None)))
            | ((Subject.scope == "personal") & (Subject.owner_user_id == user_uuid)),
        ).first()
        if not subject:
            cat = self._get_or_create_default_category()
            # 自建考科：標記 owner + scope=personal，避免污染他人選單
            subject = Subject(
                name=subj_name,
                category_id=cat.id,
                owner_user_id=user_uuid,
                scope="personal",
            )
            self.db.add(subject)
            self.db.flush()

        # 自動建立考古題 Resource（若有考古題且尚未建立）
        self._ensure_exam_bank_resource(subject)

        exam_date_str = subj_data.get("exam_date")
        exam_date = date.fromisoformat(exam_date_str) if exam_date_str else None
        level = LEVEL_MAP.get(subj_data.get("self_assessed_level", "beginner"), SelfAssessedLevel.BEGINNER)

        # 防止重複建立（unique constraint: user_id + subject_id）
        existing = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subject.id
        ).first()
        if existing:
            if existing.is_archived:
                existing.is_archived = False
                existing.exam_date = exam_date
                existing.self_assessed_level = level
            return existing

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

        if step == 2:
            return {
                "step": 2,
                "title": "選擇備考科目",
                "can_skip": False,
            }

        if step == 3:
            return {
                "step": 3,
                "title": "學習偏好設定",
                "can_skip": False,
                "daily_study_minutes": user.daily_study_minutes or 30,
            }

        return {"error": True, "status_code": 400, "message": "無效的步驟"}

    def next_step(self, user_id: str, data: dict):
        """嘗試進入下一步。"""
        step = data.get("step", 0)
        subjects = data.get("subjects", [])

        if step == 2 and not subjects:
            return {"error": True, "status_code": 400, "message": "請至少選擇一個備考科目"}

        return {"message": "OK", "next_step": step + 1}

    def _get_parent_subject_ids(self) -> set:
        """取得傘狀父科目 ID（有子科目的）。"""
        parent_ids = {
            row[0] for row in
            self.db.query(Subject.parent_subject_id)
            .filter(Subject.parent_subject_id.isnot(None))
            .distinct()
            .all()
        }
        all_names = {s.name for s in self.db.query(Subject.name).all()}
        for name in list(all_names):
            for suffix in ("（初級）", "（中級）", "（高級）"):
                if name.endswith(suffix):
                    base = name[: -len(suffix)]
                    base_subj = self.db.query(Subject).filter_by(name=base).first()
                    if base_subj:
                        parent_ids.add(base_subj.id)
        return parent_ids

    def browse_subjects(self, user_id: str, category: str | None = None):
        """瀏覽科目分類。"""
        all_cats = {c.id: c.name for c in self.db.query(SubjectCategory).all()}
        parent_ids = self._get_parent_subject_ids()

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
                    "availableQuestions": s.available_questions or 0,
                }
                for s in subjects
                if s.id not in parent_ids and (s.available_questions or 0) > 0
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
                    "result_date": s.get("result_date"),
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

        if pref == "custom" and (minutes < 5 or minutes > 480):
            return {
                "error": True,
                "status_code": 400,
                "message": "每日學習時間需介於 5 至 480 分鐘",
            }

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
        subj_name = data["subject_name"]

        # 檢查是否已有此科目的學習歷程
        subject = self.db.query(Subject).filter_by(name=subj_name).first()
        if subject:
            existing = self.db.query(LearningJourney).filter_by(
                user_id=user_uuid, subject_id=subject.id
            ).first()
            if existing:
                if existing.is_archived:
                    # 重新啟用已封存的學習歷程，清除舊考試資料
                    existing.is_archived = False
                    exam_date_str = data.get("exam_date")
                    if exam_date_str:
                        existing.exam_date = date.fromisoformat(exam_date_str)
                    level = LEVEL_MAP.get(data.get("self_assessed_level", "beginner"), SelfAssessedLevel.BEGINNER)
                    existing.self_assessed_level = level

                    # 清除舊的考試和答題紀錄
                    old_exams = self.db.query(Exam).filter_by(
                        user_id=user_uuid, subject_id=subject.id
                    ).all()
                    old_exam_ids = [e.id for e in old_exams]
                    if old_exam_ids:
                        self.db.query(Answer).filter(
                            Answer.user_id == user_uuid,
                            Answer.question_id.in_(
                                self.db.query(Question.id).filter(
                                    Question.exam_id.in_(old_exam_ids)
                                )
                            ),
                        ).delete(synchronize_session=False)
                        self.db.query(Question).filter(
                            Question.exam_id.in_(old_exam_ids),
                            Question.historical_exam_id.is_(None),  # 只刪 AI 生成題，保留考古題引用
                        ).delete(synchronize_session=False)
                        self.db.query(Exam).filter(
                            Exam.id.in_(old_exam_ids)
                        ).delete(synchronize_session=False)

                    # 清除 node_mastery
                    from app.models.node_mastery import NodeMastery
                    from app.models.knowledge_node import KnowledgeNode
                    node_ids = [n.id for n in self.db.query(KnowledgeNode.id).filter(
                        KnowledgeNode.subject_id == subject.id
                    ).all()]
                    if node_ids:
                        self.db.query(NodeMastery).filter(
                            NodeMastery.user_id == user_uuid,
                            NodeMastery.node_id.in_(node_ids),
                        ).delete(synchronize_session=False)

                    self.db.commit()
                    return {"message": f"已重新啟用備考科目 {subj_name}，學習紀錄已重置"}
                return {"error": True, "status_code": 409, "message": f"已在備考 {subj_name}，無需重複新增"}

        self._create_journey(user_uuid, data)
        self.db.commit()
        return {"message": f"已新增備考科目 {subj_name}"}

    def get_available_subjects(self, user_id: str):
        """取得可選科目列表（排除已備考科目與無考古題的傘狀科目）。"""
        user_uuid = uuid.UUID(user_id)

        # 取得使用者已有的（未封存）學習歷程科目
        active_subject_ids = {
            row[0] for row in
            self.db.query(LearningJourney.subject_id)
            .filter_by(user_id=user_uuid, is_archived=False)
            .all()
        }

        parent_ids = self._get_parent_subject_ids()

        categories = self.db.query(SubjectCategory).all()
        result = []
        all_subjects = []
        for cat in categories:
            # PRD-033: 只列平台官方考科（scope=platform AND owner_user_id IS NULL）
            subjects = self.db.query(Subject).filter(
                Subject.category_id == cat.id,
                Subject.scope == "platform",
                Subject.owner_user_id.is_(None),
            ).all()
            cat_subjects = []
            for s in subjects:
                # 排除：已備考的、傘狀父科目、無考古題的
                if s.id in active_subject_ids:
                    continue
                if s.id in parent_ids:
                    continue
                if (s.available_questions or 0) == 0:
                    continue
                entry = {
                    "id": str(s.id),
                    "name": s.name,
                    "available_questions": s.available_questions or 0,
                }
                cat_subjects.append(entry)
                all_subjects.append(entry)
            if cat_subjects:
                result.append({"category": cat.name, "subjects": cat_subjects})

        return {"categories": result, "subjects": all_subjects}

    def remove_subject(self, user_id: str, subject_id: str):
        """移除備考科目。

        - 若有活躍 journey：回傳確認提示（封存流程）
        - 若是 scope=personal 的自訂考科且 owner 為本人：直接刪除 subject
        - 否則：404
        """
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        journey = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subj_uuid, is_archived=False
        ).first()

        if journey:
            return {
                "confirm_message": "移除後該科目的學習紀錄將被封存，確定要移除嗎？",
                "subject_id": subject_id,
            }

        # PRD-033：若是本人的自訂考科（scope=personal, owner=本人），直接刪除
        subj = self.db.query(Subject).filter_by(id=subj_uuid).first()
        if subj and subj.scope == "personal" and subj.owner_user_id == user_uuid:
            self.db.delete(subj)
            self.db.commit()
            return {"message": f"已刪除自訂考科 {subj.name}"}

        return {"error": True, "status_code": 404, "message": "找不到該學習歷程"}

    def _archive_journey(self, user_id: str, subject_id: str, *, active_only: bool = True):
        """ archive journey。"""
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
