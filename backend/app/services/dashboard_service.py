"""個人儀表板 Service。"""

import uuid
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney
from app.models.exam import Exam, ExamStatus
from app.models.answer import Answer
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.resource import Resource


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, user_id: str, subject_name: str | None = None, subject_id: str | None = None) -> dict:
        """取得儀表板資料。"""
        user_uuid = uuid.UUID(user_id)

        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        # Get active (non-archived) learning journeys with subjects
        journeys = (
            self.db.query(LearningJourney, Subject)
            .join(Subject, LearningJourney.subject_id == Subject.id)
            .filter(
                LearningJourney.user_id == user_uuid,
                LearningJourney.is_archived == False,  # noqa: E712
            )
            .all()
        )

        if not journeys:
            return {
                "subjects": [],
                "active_subject": None,
                "guidance": "請至少新增一個備考科目",
                "add_subject_entry": True,
            }

        # Build subjects list sorted by exam_date (ascending, nulls last)
        subjects_list = []
        for journey, subject in journeys:
            subjects_list.append({
                "name": subject.name,
                "exam_date": journey.exam_date.isoformat() if journey.exam_date else None,
                "journey_id": str(journey.id),
                "subject_id": str(subject.id),
            })

        subjects_list.sort(key=lambda s: (s["exam_date"] is None, s["exam_date"] or ""))

        # Determine active subject (prefer subject_id over subject_name)
        if subject_id:
            active = next((s for s in subjects_list if s["subject_id"] == subject_id), subjects_list[0])
        elif subject_name:
            active = next((s for s in subjects_list if s["name"] == subject_name), subjects_list[0])
        else:
            active = subjects_list[0]

        active_subject_name = active["name"]
        active_exam_date = active["exam_date"]

        # Compute exam countdown
        today = date.today()
        if active_exam_date:
            exam_dt = date.fromisoformat(active_exam_date)
            days_left = (exam_dt - today).days
        else:
            days_left = None

        exam_countdown = {
            "exam_date": active_exam_date,
            "days_left": days_left,
        }

        # --- Exam statistics ---
        active_subject_id = uuid.UUID(active["subject_id"])

        # Total questions answered
        total_answered = (
            self.db.query(func.count(Answer.id))
            .join(Exam, Exam.id == Answer.exam_id)
            .filter(
                Answer.user_id == user_uuid,
                Exam.subject_id == active_subject_id,
                Answer.selected_answer.isnot(None),
            )
            .scalar() or 0
        )

        # Correct answers
        correct_answered = (
            self.db.query(func.count(Answer.id))
            .join(Exam, Exam.id == Answer.exam_id)
            .filter(
                Answer.user_id == user_uuid,
                Exam.subject_id == active_subject_id,
                Answer.is_correct == True,  # noqa: E712
            )
            .scalar() or 0
        )

        # Wrong answers count
        wrong_count = (
            self.db.query(func.count(Answer.id))
            .join(Exam, Exam.id == Answer.exam_id)
            .filter(
                Answer.user_id == user_uuid,
                Exam.subject_id == active_subject_id,
                Answer.is_correct == False,  # noqa: E712
            )
            .scalar() or 0
        )

        # Incomplete exams
        incomplete_exams = (
            self.db.query(func.count(Exam.id))
            .filter(
                Exam.user_id == user_uuid,
                Exam.subject_id == active_subject_id,
                Exam.status.in_([ExamStatus.READY, ExamStatus.IN_PROGRESS]),
            )
            .scalar() or 0
        )

        overall_accuracy = round((correct_answered / total_answered * 100)) if total_answered > 0 else 0
        predicted_pass = min(100, overall_accuracy + 10) if total_answered >= 10 else 0

        stats = {
            "totalQuestionsAnswered": total_answered,
            "overallAccuracy": overall_accuracy,
            "predictedPassRate": predicted_pass,
            "totalMocksCompleted": (
                self.db.query(func.count(Exam.id))
                .filter(
                    Exam.user_id == user_uuid,
                    Exam.subject_id == active_subject_id,
                    Exam.status == ExamStatus.SUBMITTED,
                )
                .scalar() or 0
            ),
            "examCountdown": {
                "examName": active_subject_name,
                "daysRemaining": days_left,
            } if days_left is not None else None,
        }

        # Domain strengths: grouped by root nodes (max 6 groups)
        domain_strengths = self._build_domain_strengths(
            user_uuid, active_subject_id, overall_accuracy
        )

        # Get submitted exams + resource_ids for tasks below
        submitted_exams = (
            self.db.query(Exam)
            .filter(
                Exam.user_id == user_uuid,
                Exam.subject_id == active_subject_id,
                Exam.status == ExamStatus.SUBMITTED,
            )
            .order_by(Exam.submitted_at.desc())
            .limit(5)
            .all()
        )
        resources = self.db.query(Resource).filter_by(subject_id=active_subject_id).all()
        resource_ids = [r.id for r in resources]

        # --- Study mode & today's tasks (per 動態任務模式與學習權重策略.md) ---
        # Determine study mode based on days_left
        if days_left is not None and days_left <= 14:
            study_mode = "sprint"
            mode_label = "Sprint 衝刺"
        elif days_left is not None and days_left <= 90:
            study_mode = "standard"
            mode_label = "Standard 正常準備"
        else:
            study_mode = "mastery"
            mode_label = "Mastery 長期學習"

        # Generate today's tasks based on mode + actual data
        today_tasks = []

        # Wrong answers → 錯題任務
        if wrong_count > 0:
            wrong_questions = (
                self.db.query(Question.content)
                .join(Answer, Answer.question_id == Question.id)
                .join(Exam, Exam.id == Question.exam_id)
                .filter(
                    Answer.user_id == user_uuid,
                    Exam.subject_id == active_subject_id,
                    Answer.is_correct == False,  # noqa: E712
                )
                .order_by(Answer.answered_at.desc())
                .limit(3)
                .all()
            )
            for q in wrong_questions:
                title = (q[0] or "")[:40]
                today_tasks.append({"title": title, "type": "wrong"})

        # Fill remaining slots based on mode
        remaining = 3 - len(today_tasks)
        if remaining > 0 and resource_ids:
            # Get unseen knowledge nodes
            unseen_nodes = (
                self.db.query(KnowledgeNode.name)
                .filter(
                    KnowledgeNode.resource_id.in_(resource_ids),
                    KnowledgeNode.depth >= 1,
                )
                .order_by(KnowledgeNode.sort_order)
                .limit(remaining)
                .all()
            )
            for n in unseen_nodes:
                task_type = "unseen" if study_mode in ("sprint", "standard") else "review"
                today_tasks.append({"title": (n[0] or "")[:40], "type": task_type})

        streak = {
            "currentStreak": user.current_streak or 0,
            "longestStreak": user.longest_streak or 0,
            "freezesRemaining": user.freezes_remaining if user.freezes_remaining is not None else 2,
            "freezesPerWeek": user.freezes_per_week if user.freezes_per_week is not None else 2,
            "lastActiveDate": user.last_active_date.isoformat() if user.last_active_date else None,
            "freezeConsumedToday": bool(user.freeze_consumed_today),
        }

        activity_items = self._build_activity_items(
            user_uuid=user_uuid,
            subject_id=active_subject_id,
            wrong_count=wrong_count,
            incomplete_exams=incomplete_exams,
            recent_resources=resources[:3],
        )

        return {
            "subjects": subjects_list,
            "active_subject": active_subject_name,
            "add_subject_entry": True,
            "exam_countdown": exam_countdown,
            "stats": stats,
            "streak": streak,
            "activityItems": activity_items,
            "domainStrengths": domain_strengths,
            "radar_chart": {
                "subject": active_subject_name,
                "domains": domain_strengths,
            },
            "studyMode": {"mode": study_mode, "label": mode_label},
            "todayTasks": today_tasks[:3],
            "quick_upload": {"enabled": True},
            "todo_reminders": {"wrong_answers": wrong_count, "incomplete_exams": incomplete_exams},
        }

    def _build_activity_items(self, user_uuid, subject_id, wrong_count, incomplete_exams, recent_resources):
        """Aggregate actionable reminders from existing data. No new table."""
        items: list[dict] = []
        if wrong_count > 0:
            items.append({
                "id": "act_wrong",
                "type": "error_review",
                "title": f"有 {wrong_count} 題錯題待複習",
                "description": "針對錯題進行複習練習可提升正確率",
                "link": "/review",
                "linkLabel": "去複習",
            })
        if incomplete_exams > 0:
            items.append({
                "id": "act_incomplete",
                "type": "incomplete_exam",
                "title": f"有 {incomplete_exams} 份未完成測驗",
                "description": "繼續作答以獲得完整成績分析",
                "link": "/exam/workspace",
                "linkLabel": "繼續作答",
            })
        for r in recent_resources[:2]:
            items.append({
                "id": f"act_res_{r.id}",
                "type": "new_resource",
                "title": f"新資源：{r.name}",
                "description": "查看知識心智圖與題目",
                "link": "/knowledge",
                "linkLabel": "查看",
            })
        return items

    # ── 能力分佈：分組雷達圖資料 ─────────────────────────────────

    MAX_RADAR_GROUPS = 6

    def _build_domain_strengths(
        self,
        user_uuid: uuid.UUID,
        subject_id: uuid.UUID | None,
        overall_accuracy: int,
    ) -> list[dict]:
        """
        建構能力分佈資料（方案 B：分組雷達圖）。

        策略：
        1. 查詢該科目下所有 root 節點（depth=0）及其子節點
        2. 使用 NodeMastery 取得真實的 per-node 答題統計
        3. 將子節點聚合到 root 節點，root 節點最多 6 個
        4. 回傳 { domain, correct, total, percentage, children[] }
        """
        if not subject_id:
            return []

        # 查詢該科目的 knowledge nodes（直接用 subject_id）
        # 科目隔離規則：只查當前科目，不混入父科目節點
        subject_ids_to_query = [subject_id]

        all_nodes = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.subject_id.in_(subject_ids_to_query))
            .order_by(KnowledgeNode.depth, KnowledgeNode.sort_order)
            .all()
        )

        # 也查 resource-based 節點（使用者上傳文件產生的）
        if not all_nodes:
            resource_ids = [
                r.id for r in
                self.db.query(Resource.id).filter_by(subject_id=subject_id).all()
            ]
            if resource_ids:
                all_nodes = (
                    self.db.query(KnowledgeNode)
                    .filter(KnowledgeNode.resource_id.in_(resource_ids))
                    .order_by(KnowledgeNode.depth, KnowledgeNode.sort_order)
                    .all()
                )
        if not all_nodes:
            return []

        # 查詢該使用者的 NodeMastery 資料
        node_ids = [n.id for n in all_nodes]
        masteries = (
            self.db.query(NodeMastery)
            .filter(
                NodeMastery.user_id == user_uuid,
                NodeMastery.node_id.in_(node_ids),
            )
            .all()
        )
        mastery_map = {m.node_id: m for m in masteries}

        # 分離頂層節點（parent_id 為空）和子節點
        roots = [n for n in all_nodes if n.parent_id is None]
        children_by_parent: dict[uuid.UUID, list[KnowledgeNode]] = {}
        for n in all_nodes:
            if n.parent_id is not None:
                children_by_parent.setdefault(n.parent_id, []).append(n)

        # 建構分組資料
        groups: list[dict] = []
        for root in roots[:self.MAX_RADAR_GROUPS]:
            children = children_by_parent.get(root.id, [])

            # 計算子概念的統計
            child_items = []
            group_correct = 0
            group_total = 0

            if children:
                for child in children:
                    m = mastery_map.get(child.id)
                    c = m.correct_count if m else 0
                    t = m.total_count if m else 0
                    # 使用 mastery_rate（含 EMA + 傳播結果），而非僅 correct/total
                    pct = round(float(m.mastery_rate)) if m and m.mastery_rate is not None else 0
                    group_correct += c
                    group_total += t
                    child_items.append({
                        "domain": child.name[:20],
                        "correct": c,
                        "total": t,
                        "percentage": pct,
                    })
            else:
                # root 節點本身就是葉子
                m = mastery_map.get(root.id)
                c = m.correct_count if m else 0
                t = m.total_count if m else 0
                group_correct += c
                group_total += t

            # 分組的整體百分比 — 優先使用 NodeMastery 的 mastery_rate
            root_mastery = mastery_map.get(root.id)
            if children:
                # 有子節點：用子節點的 mastery_rate 平均值
                child_rates = [
                    float(mastery_map[c.id].mastery_rate)
                    for c in children
                    if c.id in mastery_map and mastery_map[c.id].mastery_rate is not None
                ]
                if child_rates:
                    group_pct = round(sum(child_rates) / len(child_rates))
                elif group_total > 0:
                    group_pct = round((group_correct / group_total) * 100)
                else:
                    group_pct = 0
            elif root_mastery and root_mastery.mastery_rate is not None:
                group_pct = round(float(root_mastery.mastery_rate))
            elif group_total > 0:
                group_pct = round((group_correct / group_total) * 100)
            else:
                group_pct = 0

            groups.append({
                "domain": root.name[:20],
                "correct": group_correct,
                "total": group_total,
                "percentage": group_pct,
                "children": child_items if len(child_items) > 1 else [],
            })

        # 如果完全沒有節點資料，使用通用 Bloom 分類（全部 0%）
        if not groups:
            labels = ["記憶", "理解", "應用", "分析", "評估", "創造"]
            for label in labels:
                groups.append({
                    "domain": label,
                    "correct": 0,
                    "total": 0,
                    "percentage": 0,
                    "children": [],
                })

        return groups

    def get_profile(self, user_id: str) -> dict:
        """取得個人資料。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        fields = [
            {"label": "姓名", "type": "文字輸入", "value": user.display_name or ""},
            {"label": "年齡", "type": "下拉選單", "value": user.age or 0},
            {"label": "最高學歷", "type": "下拉選單", "value": user.education or ""},
            {"label": "職業 / 領域", "type": "文字輸入", "value": user.career or ""},
            {"label": "每日學習時間", "type": "按鈕選擇", "value": user.daily_study_minutes or 0},
            {"label": "偏好學習方式", "type": "卡片選擇", "value": user.learning_preference or ""},
        ]

        return {"error": False, "fields": fields}

    def update_profile(self, user_id: str, data: dict) -> dict:
        """更新個人資料。"""
        user_uuid = uuid.UUID(user_id)

        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        learning_style_map = {
            "大量刷題": "drill",
            "觀念優先": "concept",
            "混合模式": "mixed",
        }
        allowed_fields = {"display_name", "age", "education", "career", "daily_study_minutes"}
        for field, value in data.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)
            elif field == "learning_style" and value is not None:
                user.learning_preference = learning_style_map.get(value, value)

        self.db.commit()
        return {"message": "已儲存"}
