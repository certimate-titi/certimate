"""錯題複習與 AI 教練 Service。"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question
from app.models.answer import Answer
from app.models.user import User
from app.models.subject import Subject
from app.models.resource import Resource
from app.models.knowledge_node import KnowledgeNode
from app.models.ai_chat import AiChatSession, AiChatMessage
from app.models.ai_cooldown import AiCooldown


class WrongAnswerService:
    def __init__(self, db: Session):
        self.db = db

    def list_by_subject(self, user_id: str, subject_id: str | None = None):
        """列出使用者的錯題，可按科目過濾。"""
        user_uuid = uuid.UUID(user_id)

        query = (
            self.db.query(Question, Answer, Exam, Subject)
            .join(Answer, Answer.question_id == Question.id)
            .join(Exam, Exam.id == Question.exam_id)
            .join(Subject, Subject.id == Exam.subject_id)
            .filter(Answer.user_id == user_uuid)
            .filter(Answer.is_correct == False)  # noqa: E712
        )

        if subject_id:
            query = query.filter(Exam.subject_id == uuid.UUID(subject_id))

        rows = query.all()

        wrong_answers = []
        for q, a, exam, subj in rows:
            wrong_answers.append({
                "question_id": str(q.id),
                "exam_id": str(exam.id),
                "content": q.content,
                "correct_answer": q.correct_answer,
                "selected_answer": a.selected_answer,
                "subject_name": subj.name,
            })

        return {"wrong_answers": wrong_answers}

    def get_wrong_answers_by_exam(self, exam_id: str, user_id: str):
        """查看特定測驗的錯題記錄。"""
        exam_uuid = uuid.UUID(exam_id)
        user_uuid = uuid.UUID(user_id)

        exam = self.db.query(Exam).filter_by(id=exam_uuid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != user_uuid:
            return {"error": True, "status_code": 403, "message": "無存取此錯題記錄的權限"}

        wrong = (
            self.db.query(Question, Answer)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Question.exam_id == exam_uuid)
            .filter(Answer.is_correct == False)  # noqa: E712
            .all()
        )

        items = []
        for q, a in wrong:
            items.append({
                "question_id": str(q.id),
                "content": q.content,
                "correct_answer": q.correct_answer,
                "selected_answer": a.selected_answer,
            })

        return {"wrong_answers": items}

    def get_analysis(self, exam_id: str, user_id: str, question_id: str):
        """查看特定錯題的解析。"""
        exam_uuid = uuid.UUID(exam_id)
        user_uuid = uuid.UUID(user_id)
        q_uuid = uuid.UUID(question_id)

        exam = self.db.query(Exam).filter_by(id=exam_uuid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != user_uuid:
            return {"error": True, "status_code": 403, "message": "無存取此錯題記錄的權限"}

        question = self.db.query(Question).filter_by(
            id=q_uuid, exam_id=exam_uuid
        ).first()
        if not question:
            return {"error": True, "status_code": 404, "message": "題目不存在"}

        answer = self.db.query(Answer).filter_by(
            question_id=q_uuid, user_id=user_uuid
        ).first()

        user = self.db.query(User).filter_by(id=user_uuid).first()
        plan = user.subscription_plan.value if user and user.subscription_plan else "FREE"

        # Get knowledge node info for tip
        node = None
        if question.node_id:
            node = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()

        # Build tip from node name or explanation
        tip = ""
        if question.explanation:
            tip = question.explanation if len(question.explanation) <= 80 else question.explanation[:80]
        elif node:
            tip = f"{node.name} 相關概念說明。"

        result = {
            "question": question.content,
            "correct": question.correct_answer,
            "selected": answer.selected_answer if answer else None,
            "tip": tip,
        }

        if plan == "FREE":
            result["deep_analysis_locked"] = True
            result["upgrade"] = {"target_plan": "PRO_199", "monthly_fee": 199}
        else:
            explanation = question.explanation or ""
            result["deep_analysis"] = f"## 深度解析\n\n{explanation}" if explanation else ""
            result["deep_analysis_locked"] = False

            resource = None
            if question.node_id:
                node_obj = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()
                if node_obj:
                    resource = self.db.query(Resource).filter_by(id=node_obj.resource_id).first()

            result["source_citation"] = {
                "source_resource": resource.name if resource else "關聯資源",
                "source_ref": question.source_citation or "p.1",
            }

        return result

    def _get_user_tone_context(self, user: User) -> str:
        """根據使用者個人資料決定回覆風格。"""
        age = user.age
        education = user.education
        career = user.career

        if not age and not education:
            return "general"

        if education and any(kw in education for kw in ["高中", "高職", "國中"]):
            return "simple"
        if education and any(kw in education for kw in ["碩士", "博士"]):
            if career and any(kw in career for kw in ["工程師", "開發", "軟體", "程式"]):
                return "technical"
            return "advanced"
        return "general"

    def _generate_coach_reply(self, question: Question, message: str, tone: str,
                              history_context: str | None = None) -> str:
        """生成 AI 教練回覆（模擬）。"""
        node = None
        if question.node_id:
            node = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()
        node_name = node.name if node else "此概念"

        if tone == "simple":
            reply = (
                f"別擔心，我來用簡單的方式幫你理解！😊\n\n"
                f"關於 {node_name}，想像一下，像是餐廳在尖峰時段自動增加服務生，"
                f"這就好比 Auto Scaling 的概念。\n\n"
                f"加油，你一定可以學會的！"
            )
        elif tone == "technical":
            reply = (
                f"關於 {node_name}，這涉及 CloudWatch Alarm 與 Target Tracking Policy 的整合。\n\n"
                f"當 CloudWatch 偵測到 CPU 使用率超過閾值時，會觸發 Scaling Policy。\n"
                f"你可以透過 AWS CLI 指令 `aws autoscaling describe-policies` 來查看設定。\n\n"
                f"相關 API 參數：`TargetTrackingConfiguration.TargetValue`。"
            )
        else:
            reply = (
                f"加油！讓我來幫你理解 {node_name} 的概念。\n\n"
                f"簡單來說，{question.explanation or '這個概念需要深入理解。'}\n\n"
                f"繼續努力，你做得很好！"
            )

        if history_context:
            reply += f"\n\n根據你之前的學習記錄，你在 {history_context} 相關的題目曾經答錯過，"
            reply += "建議你特別注意這個部分的概念。"

        return reply

    def _check_out_of_scope(self, message: str) -> bool:
        """檢查問題是否超出題庫範圍。"""
        out_of_scope_keywords = ["寫一首詩", "寫詩", "唱歌", "講笑話", "幫我寫", "幫我做"]
        return any(kw in message for kw in out_of_scope_keywords)

    def _check_cooldown(self, user_id: uuid.UUID) -> AiCooldown | None:
        """檢查使用者是否在冷卻期。"""
        now = datetime.now(timezone.utc)
        return self.db.query(AiCooldown).filter(
            AiCooldown.user_id == user_id,
            AiCooldown.cooldown_until > now,
        ).first()

    def _count_recent_out_of_scope(self, user_id: uuid.UUID) -> int:
        """計算過去 10 分鐘內的超綱提問次數。"""
        ten_min_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
        return self.db.query(AiCooldown).filter(
            AiCooldown.user_id == user_id,
            AiCooldown.reason == "out_of_scope",
            AiCooldown.created_at >= ten_min_ago,
        ).count()

    def ai_coach_chat(self, exam_id: str, user_id: str, question_id: str, message: str):
        """AI 教練對話。"""
        exam_uuid = uuid.UUID(exam_id)
        user_uuid = uuid.UUID(user_id)
        q_uuid = uuid.UUID(question_id)

        exam = self.db.query(Exam).filter_by(id=exam_uuid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        user = self.db.query(User).filter_by(id=user_uuid).first()
        plan = user.subscription_plan.value if user and user.subscription_plan else "FREE"

        if plan == "FREE":
            return {"error": True, "status_code": 403, "message": "AI 教練對話為 PRO 以上方案專屬功能"}

        # Check cooldown
        cooldown = self._check_cooldown(user_uuid)
        if cooldown:
            return {
                "error": True, "status_code": 429,
                "message": "您已暫時被限制使用 AI 教練，請 30 分鐘後再試",
            }

        question = self.db.query(Question).filter_by(
            id=q_uuid, exam_id=exam_uuid
        ).first()

        # Check out of scope
        if self._check_out_of_scope(message):
            # Record out-of-scope attempt
            oos_record = AiCooldown(
                user_id=user_uuid,
                reason="out_of_scope",
                cooldown_until=datetime.now(timezone.utc),
            )
            self.db.add(oos_record)
            self.db.commit()

            # Check if cooldown should be triggered (5th offense in 10 min)
            recent_count = self._count_recent_out_of_scope(user_uuid)
            if recent_count >= 5:
                trigger_cooldown = AiCooldown(
                    user_id=user_uuid,
                    reason="10min_5_out_of_scope",
                    cooldown_until=datetime.now(timezone.utc) + timedelta(minutes=30),
                )
                self.db.add(trigger_cooldown)
                self.db.commit()

                return {
                    "reply": "您已暫時被限制使用 AI 教練，請 30 分鐘後再試",
                    "content": "您已暫時被限制使用 AI 教練，請 30 分鐘後再試",
                    "streaming": False,
                    "cooldown": True,
                }

            return {
                "reply": "此問題超出目前題庫範圍，請聚焦在考試相關的問題上。",
                "content": "此問題超出目前題庫範圍，請聚焦在考試相關的問題上。",
                "streaming": True,
            }

        # Determine tone from user profile
        tone = self._get_user_tone_context(user)

        # Check history context
        history_context = None
        if question and question.node_id:
            node = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()
            if node:
                wrong_count = (
                    self.db.query(Answer)
                    .join(Question, Question.id == Answer.question_id)
                    .filter(Answer.user_id == user_uuid)
                    .filter(Answer.is_correct == False)  # noqa: E712
                    .filter(Question.node_id == question.node_id)
                    .count()
                )
                if wrong_count > 1:
                    history_context = node.name

        # Generate reply
        if question:
            reply = self._generate_coach_reply(question, message, tone, history_context)
        else:
            reply = f"加油！讓我來幫你理解這個概念。\n\n繼續努力，你做得很好！"

        # Save chat session + message
        context_id = q_uuid
        session = self.db.query(AiChatSession).filter_by(
            user_id=user_uuid, context_type="error_review", context_id=context_id
        ).first()
        if not session:
            session = AiChatSession(
                user_id=user_uuid,
                context_type="error_review",
                context_id=context_id,
                model_used="claude-3.5-sonnet",
                message_count=0,
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        user_msg = AiChatMessage(
            session_id=session.id, role="user", content=message,
        )
        assistant_msg = AiChatMessage(
            session_id=session.id, role="assistant", content=reply,
        )
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        session.message_count = (session.message_count or 0) + 2
        self.db.commit()

        return {
            "reply": reply,
            "content": reply,
            "streaming": True,
        }

    def get_coach_info(self, exam_id: str, user_id: str, question_id: str):
        """取得 AI 教練對話視窗資訊（含免責聲明）。"""
        return {
            "disclaimer": "AI 生成內容僅供參考，請隨時自行查證重要資訊。",
            "model": "claude-3.5-sonnet",
        }
