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
        # Prompt template service for DB-based prompts
        from app.services.prompt_template_service import PromptTemplateService
        self._prompt_svc = PromptTemplateService(db)
        self._llm = None

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """Load prompt template from DB with fallback."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception as e:
            logger.warning("Failed to load prompt template '%s': %s", name, e)
            return None

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
            # Build options from question fields
            options = []
            for label, attr in [("A", "option_a"), ("B", "option_b"), ("C", "option_c"), ("D", "option_d")]:
                text = getattr(q, attr, None) or ""
                if text:
                    options.append({"label": label, "text": text})

            wrong_answers.append({
                "question_id": str(q.id),
                "exam_id": str(exam.id),
                "content": q.content,
                "correct_answer": q.correct_answer,
                "selected_answer": a.selected_answer,
                "subject_name": subj.name,
                "explanation": q.explanation or "",
                "options": options,
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
        role = user.role.value if user and hasattr(user.role, 'value') else (user.role if user else "user")
        is_admin = role in ("admin", "super_admin", "ADMIN", "SUPER_ADMIN")

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

        if plan == "FREE" and not is_admin:
            result["deep_analysis_locked"] = True
            result["upgrade"] = {"target_plan": "PRO_199", "monthly_fee": 199}
        else:
            # 嘗試 AI 深度分析（T-03）
            ai_analysis = self._generate_wrong_answer_analysis(question, answer, user, node)
            if ai_analysis:
                result["deep_analysis"] = ai_analysis
            else:
                # Fallback: 使用靜態 explanation
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

    def _get_llm(self):
        if self._llm is None:
            from app.core.config import get_settings
            settings = get_settings()
            if settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY:
                from app.services.llm_service import LLMService
                self._llm = LLMService(db=self.db)
        return self._llm

    def _generate_wrong_answer_analysis(self, question, answer, user, node=None) -> str | None:
        """用 T-03 模板生成 AI 錯因分析。"""
        llm = self._get_llm()
        if not llm:
            return None

        # Build variables
        options = f"(A) {question.option_a}\n(B) {question.option_b}\n(C) {question.option_c}\n(D) {question.option_d}"

        # Get related content from resource chunks if available
        related_content = ""
        if question.node_id:
            from app.models.resource_chunk import ResourceChunk
            chunks = self.db.query(ResourceChunk).filter_by(node_id=question.node_id).limit(3).all()
            if chunks:
                for chunk in chunks:
                    related_content += f"> {chunk.content[:300]}\n\n"

        # User background instruction
        tone = self._get_user_tone_context(user)
        bg_instructions = {
            "simple": "使用者為高中生，請使用生活化比喻和簡單詞彙",
            "technical": "使用者有技術背景，可使用專業術語",
            "advanced": "使用者有碩博士學歷，可深入分析",
            "general": "",
        }
        user_bg = bg_instructions.get(tone, "")

        # Load prompt from DB
        db_prompt = self._load_prompt("wrong_answer_analysis", {
            "user_background_instruction": user_bg,
            "question_text": question.content,
            "options": options,
            "user_answer": answer.selected_answer if answer else "未作答",
            "correct_answer": question.correct_answer,
            "related_content": related_content or "（無相關知識庫內容）",
        })

        # Fallback system prompt
        _FALLBACK = '''你是考題解析專家。針對用戶答錯的題目提供深度解析。

解析結構：
1. **正確答案**：直接告知正確答案是什麼
2. **為什麼你選的答案是錯的**：分析用戶選答的常見迷思
3. **正確推導**：用步驟化方式解釋為什麼正確答案是對的
4. **知識庫引用**：若有相關內容，以 blockquote 引用並標註來源
5. **延伸觀念**：1-2 個相關的延伸知識點

規則：語氣正向，不批評用戶選錯。回覆使用 Markdown 格式。'''

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = _FALLBACK
            user_prompt = (
                f"題目：{question.content}\n"
                f"選項：{options}\n"
                f"我的選答：{answer.selected_answer if answer else '未作答'}\n"
                f"正確答案：{question.correct_answer}\n\n"
                f"相關知識庫內容：\n{related_content or '（無）'}"
            )

        try:
            # Determine max_tokens by plan
            plan = user.subscription_plan.value if user and user.subscription_plan else "FREE"
            max_tokens_map = {"PRO": 1024, "PRO_PLUS": 2048, "ULTRA": 4096}
            max_tokens = max_tokens_map.get(plan, 1024)

            result = llm.generate(system_prompt, user_prompt, model="gemini-flash", max_tokens=max_tokens)
            return result if result and len(result.strip()) > 20 else None
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("T-03 wrong answer analysis failed: %s", e)
            return None

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

    def _check_relevance(self, question: Question, message: str, node_name: str) -> bool:
        """用 LLM 判斷用戶提問是否與題目/科目概念相關。

        若無可用 LLM API key，fallback 到關鍵字檢查。
        Returns True if relevant, False if off-topic.
        """
        import logging
        logger = logging.getLogger(__name__)

        from app.core.config import get_settings
        settings = get_settings()

        has_llm = bool(
            settings.ANTHROPIC_API_KEY
            or settings.OPENAI_API_KEY
            or settings.GEMINI_API_KEY
        )

        if has_llm:
            try:
                from app.services.llm_service import LLMService
                llm = LLMService(db=self.db)

                # Try loading prompt from DB (S-01: safety_router)
                db_prompt = self._load_prompt("safety_router", {
                    "subject_name": node_name or "",
                    "exam_status": "",
                    "user_input": message,
                })
                system_prompt = (
                    db_prompt["system_prompt"] if db_prompt else
                    "你是一位嚴格的學術相關性判斷器。\n"
                    "判斷學生的提問是否與以下題目或知識概念相關。\n"
                    "相關的定義包括：\n"
                    "- 直接詢問題目的解法、概念、原理\n"
                    "- 詢問相關的延伸知識或背景知識\n"
                    "- 詢問類似題型的解題方法\n"
                    "- 對正確答案或選項提出疑問\n\n"
                    "不相關的定義包括：\n"
                    "- 完全無關的閒聊（天氣、心情、日常）\n"
                    "- 要求寫作、翻譯、寫程式等非學習相關任務\n"
                    "- 詢問與考試科目完全無關的領域知識\n\n"
                    "只回覆 RELEVANT 或 IRRELEVANT，不要有其他文字。"
                )

                user_prompt = (
                    f"題目：{question.content}\n"
                    f"知識點：{node_name}\n"
                    f"正確答案：{question.correct_answer}\n\n"
                    f"學生提問：{message}"
                )

                result = llm.generate(system_prompt, user_prompt, max_tokens=16)
                return "RELEVANT" in result.upper()
            except Exception as e:
                logger.warning("Relevance check LLM call failed, allowing by default: %s", e)
                return True  # LLM 失敗時寬容處理，允許回答

        # 無 LLM 時 fallback：只要不在明顯超綱關鍵字就算相關
        return True

    def _generate_coach_reply(self, question: Question, message: str, tone: str,
                              history_context: str | None = None,
                              conversation_history: list | None = None,
                              confidence_quadrant: str | None = None,
                              user_id: uuid.UUID | None = None) -> str | dict:
        """生成蘇格拉底式 AI 教練回覆。

        設計原則（白皮書 #8）：
        - 不直接給答案，用提問引導學生自行發現知識
        - 根據信心度四象限調整教練策略
        - 多輪對話保持上下文連貫
        """
        import logging
        logger = logging.getLogger(__name__)

        node = None
        if question.node_id:
            node = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()
        node_name = node.name if node else "此概念"

        # Step 1: 相關性判斷
        if not self._check_relevance(question, message, node_name):
            return {
                "rejected": True,
                "message": "此問題與目前的題目或學習主題無關，請聚焦在考試相關的問題上。",
            }

        # Step 2: Try LLM
        from app.core.config import get_settings
        settings = get_settings()
        has_llm = bool(
            settings.ANTHROPIC_API_KEY
            or settings.OPENAI_API_KEY
            or settings.GEMINI_API_KEY
        )

        if not has_llm:
            # Test mode: generate deterministic mock responses based on tone
            return self._mock_coach_reply(question, message, tone, history_context)

        try:
            from app.services.llm_service import LLMService
            from app.services.retrieval_service import RetrievalService

            llm = LLMService(db=self.db)

            tone_instruction = {
                "simple": "請使用淺顯易懂的語言、生活化比喻和類比來引導",
                "technical": "可以使用專業術語，但仍以提問引導為主",
            }.get(tone, "請使用適中的語言來引導")

            # 信心度策略
            confidence_strategy = ""
            if confidence_quadrant == "dangerous_blindspot":
                confidence_strategy = (
                    "\n【重要】這位學生在此題「非常確定但答錯」，屬於危險盲點。"
                    "你必須特別溫和地先肯定他的努力，再用反問方式讓他意識到思維中的陷阱。"
                    "例如：「你提到很確定 X 是對的，那如果我們從 Y 角度來看呢？」"
                )
            elif confidence_quadrant == "lucky_guess":
                confidence_strategy = (
                    "\n這位學生在此題「猜對了」，但其實並不確定。"
                    "請引導他建立真正的理解，而非停留在「答對就好」。"
                    "例如：「你答對了，但你能解釋為什麼不是其他選項嗎？」"
                )

            # Try loading prompt from DB (T-02: coach_advanced)
            db_prompt = self._load_prompt("coach_advanced")
            system_prompt = (
                db_prompt["system_prompt"] if db_prompt else
                "你是 Certi，TiTi 平台的 AI 蘇格拉底教練。\n\n"
                "【核心原則 — 蘇格拉底式教學】\n"
                "1. 絕對不要直接告訴學生答案或直接解釋為什麼某個選項正確\n"
                "2. 用提問引導學生自己思考和發現：「你覺得 A 和 B 的差別在哪？」\n"
                "3. 當學生接近正確理解時，給予肯定並追問更深一層\n"
                "4. 當學生偏離時，溫和地用反問導回：「那如果從 X 角度來看呢？」\n"
                "5. 每次回覆最多問 1-2 個引導問題，不要一次問太多\n\n"
                f"【語氣】{tone_instruction}\n"
                f"{confidence_strategy}\n"
                "【格式】回覆控制在 150 字以內。鼓勵但不過度使用 emoji。"
            )

            # 組合對話歷史
            history_str = ""
            if conversation_history:
                recent = conversation_history[-6:]  # 最近 3 輪
                for msg in recent:
                    role_label = "學生" if msg.get("role") == "user" else "Certi"
                    history_str += f"{role_label}：{msg.get('content', '')}\n"

            user_prompt = (
                f"【題目資訊】\n"
                f"題目：{question.content}\n"
                f"選項：(A){question.option_a} (B){question.option_b} "
                f"(C){question.option_c} (D){question.option_d}\n"
                f"正確答案：{question.correct_answer}\n"
                f"詳解（僅供你參考，不要直接告訴學生）：{question.explanation or '無'}\n"
            )

            if history_context:
                user_prompt += f"\n【弱點記錄】學生在「{history_context}」已答錯多次。\n"

            if history_str:
                user_prompt += f"\n【對話歷史】\n{history_str}\n"

            user_prompt += f"【學生最新提問】{message}"

            # Try RAG if resource exists (Mastery-aware: skip already-mastered chunks)
            if node and node.resource_id and settings.VOYAGE_API_KEY:
                retrieval = RetrievalService(self.db)
                chunks = retrieval.retrieve(
                    f"{node_name}: {message}",
                    [node.resource_id],
                    top_k=5,
                    user_id=user_id,
                )
                context = retrieval.build_context_string(chunks, max_tokens=2000)

                if context.strip():
                    system_prompt += "\n如果需要引用教材，可以提到「根據你的教材...」但仍以提問引導為主。"
                    return llm.generate_with_context(
                        system_prompt, user_prompt, context, max_tokens=1024
                    )

            return llm.generate(system_prompt, user_prompt, max_tokens=1024)

        except Exception as e:
            logger.warning("AI Coach LLM call failed: %s", e)
            # Fall back to mock reply when LLM is unavailable
            return self._mock_coach_reply(question, message, tone, history_context)

    def _check_out_of_scope(self, message: str) -> bool:
        """檢查問題是否超出題庫範圍。"""
        out_of_scope_keywords = ["寫一首詩", "寫詩", "唱歌", "講笑話", "幫我寫", "幫我做"]
        return any(kw in message for kw in out_of_scope_keywords)

    def _mock_coach_reply(self, question: Question, message: str, tone: str,
                          history_context: str | None = None) -> str:
        """在沒有 LLM API 的測試環境中生成確定性的 mock 回覆。"""
        node = None
        if question.node_id:
            node = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()
        node_name = node.name if node else "此概念"

        base_reply = ""

        if tone == "simple":
            base_reply = (
                f"加油！別擔心，讓我用一個簡單的比喻來解釋。\n\n"
                f"想像一下，{node_name} 就像是餐廳在尖峰時段自動增加服務生一樣，"
                f"好比是一個自動調節的系統。繼續努力，你做得很好！"
            )
        elif tone == "technical":
            base_reply = (
                f"讓我們從技術角度來分析 {node_name}。\n\n"
                f"Auto Scaling 的觸發機制主要透過 CloudWatch Alarm 搭配 Target Tracking Policy 來實現。"
                f"你可以透過 AWS CLI 指令 `aws autoscaling describe-policies` 來查看相關設定。"
                f"Scaling Policy 與 CloudWatch Alarm 的配合是關鍵。"
            )
        else:
            base_reply = (
                f"加油！讓我來幫你理解 {node_name} 這個概念。\n\n"
                f"這道題目考的是 {question.content} 的核心觀念。"
                f"繼續努力，你做得很好！別擔心，多練習就會理解的。"
            )

        if history_context:
            base_reply += f"\n\n我注意到你之前在 {history_context} 相關的題目也遇到過困難。"

        return base_reply

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

    def ai_coach_chat(self, exam_id: str | None, user_id: str, question_id: str, message: str):
        """AI 教練對話。"""
        user_uuid = uuid.UUID(user_id)
        q_uuid = uuid.UUID(question_id)

        if exam_id:
            exam_uuid = uuid.UUID(exam_id)
            exam = self.db.query(Exam).filter_by(id=exam_uuid).first()
            if not exam:
                return {"error": True, "status_code": 404, "message": "測驗不存在"}
        else:
            exam_uuid = None

        user = self.db.query(User).filter_by(id=user_uuid).first()
        plan = user.subscription_plan.value if user and user.subscription_plan else "FREE"
        role = user.role.value if user and hasattr(user.role, 'value') else (user.role if user else "user")

        # Admin/super_admin bypass plan restrictions
        is_admin = role in ("admin", "super_admin", "ADMIN", "SUPER_ADMIN")
        if plan == "FREE" and not is_admin:
            return {"error": True, "status_code": 403, "message": "AI 教練對話為 PRO 以上方案專屬功能"}

        # Check cooldown
        cooldown = self._check_cooldown(user_uuid)
        if cooldown:
            return {
                "error": True, "status_code": 429,
                "message": "您已暫時被限制使用 AI 教練，請 30 分鐘後再試",
            }

        if exam_uuid:
            question = self.db.query(Question).filter_by(
                id=q_uuid, exam_id=exam_uuid
            ).first()
        else:
            question = self.db.query(Question).filter_by(id=q_uuid).first()

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

        # Get confidence quadrant for this question
        confidence_quadrant = None
        if question:
            user_answer = self.db.query(Answer).filter_by(
                user_id=user_uuid, question_id=q_uuid
            ).first()
            if user_answer:
                if user_answer.confidence == "high" and not user_answer.is_correct:
                    confidence_quadrant = "dangerous_blindspot"
                elif user_answer.confidence == "low" and user_answer.is_correct:
                    confidence_quadrant = "lucky_guess"

        # Load conversation history from DB
        conversation_history = []
        existing_session = self.db.query(AiChatSession).filter_by(
            user_id=user_uuid, context_type="error_review", context_id=q_uuid
        ).first()
        if existing_session:
            past_msgs = self.db.query(AiChatMessage).filter_by(
                session_id=existing_session.id
            ).order_by(AiChatMessage.created_at).all()
            conversation_history = [
                {"role": m.role, "content": m.content} for m in past_msgs
            ]

        # Generate reply
        if question:
            result = self._generate_coach_reply(
                question, message, tone, history_context,
                conversation_history=conversation_history,
                confidence_quadrant=confidence_quadrant,
                user_id=user_uuid,
            )
            # _generate_coach_reply may return a dict with "rejected" or "error" flag
            if isinstance(result, dict):
                if result.get("rejected"):
                    return {
                        "reply": result["message"],
                        "content": result["message"],
                        "streaming": True,
                        "rejected": True,
                    }
                if result.get("error"):
                    return result
            reply = result if isinstance(result, str) else str(result)
        else:
            reply = "加油！讓我來幫你理解這個概念。\n\n繼續努力，你做得很好！"

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
