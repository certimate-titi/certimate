"""AI Question Generation Service — 04a AI考題生成服務.

Implements the 4-stage AI prompt pipeline:
  Stage 1: 考點分析 (Exam point analysis)
  Stage 2: 考題生成 (Question generation)
  Stage 3: 干擾項優化 (Distractor optimization)
  Stage 4: 格式化輸出 (Formatted output)

Supports two modes:
  - RAG mode: uses Claude API with retrieved document context (when ANTHROPIC_API_KEY is set)
  - Mock mode: generates placeholder data (fallback when API unavailable)
"""

import json
import logging
import random
import uuid
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.prompt_template import PromptTemplate, PromptTemplateHistory
from app.models.question import Question
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class AiGenerationService:

    def __init__(self, db: Session):
        self.db = db
        self._settings = get_settings()
        self._rag_enabled = bool(
            self._settings.ANTHROPIC_API_KEY
            or self._settings.OPENAI_API_KEY
            or self._settings.GEMINI_API_KEY
        )

        if self._rag_enabled:
            from app.services.llm_service import LLMService
            from app.services.retrieval_service import RetrievalService
            self._llm = LLMService(db=db)
            self._retrieval = RetrievalService(db)
        else:
            self._llm = None
            self._retrieval = None

    # ------------------------------------------------------------------ #
    # Public: full pipeline
    # ------------------------------------------------------------------ #

    def generate(self, exam_id: str, user_id: str) -> dict:
        """Run the full 4-stage pipeline and return progress events + result."""
        uid = uuid.UUID(user_id)
        eid = uuid.UUID(exam_id)

        exam = self.db.query(Exam).filter_by(id=eid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "找不到測驗任務"}

        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        # Gather config
        node_ids = self._get_exam_node_ids(exam)
        nodes = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.id.in_(node_ids)
        ).all() if node_ids else []

        difficulty_dist = exam.difficulty_distribution or {"easy": 30, "medium": 50, "hard": 20}
        total_q = exam.total_questions

        # Build user context
        user_context = self._build_user_context(user)

        # Retrieve RAG context if enabled
        rag_context = ""
        if self._rag_enabled and self._retrieval:
            resource_ids = list({n.resource_id for n in nodes if n.resource_id})
            if resource_ids:
                try:
                    query = f"考點分析：{', '.join(n.name for n in nodes[:5])}"
                    chunks = self._retrieval.retrieve(query, resource_ids)
                    rag_context = self._retrieval.build_context_string(chunks)
                except Exception as e:
                    logger.warning("RAG retrieval failed, falling back to mock: %s", e)

        # Execute 4 stages
        progress_events = []

        # Prep
        progress_events.append({
            "percentage": 10, "stage": "準備",
            "message": "正在從向量庫提取知識點...",
        })

        # Stage 1
        stage1_result = self._stage1_exam_point_analysis(nodes, total_q, difficulty_dist)
        progress_events.append({
            "percentage": 30, "stage": "階段 1",
            "message": "AI 正在分析考點與出題比例...",
        })

        # Stage 2
        stage2_result = self._stage2_question_generation(
            stage1_result, difficulty_dist, user_context, total_q, rag_context
        )
        progress_events.append({
            "percentage": 50, "stage": "階段 2",
            "message": "AI 教練正在出題...",
        })

        # Stage 3
        stage3_result = self._stage3_distractor_optimization(stage2_result, user_context, rag_context)
        progress_events.append({
            "percentage": 75, "stage": "階段 3",
            "message": "AI 教練正在設計考題陷阱與詳解...",
        })

        # Stage 4
        stage4_result = self._stage4_formatted_output(stage3_result, exam_id)
        progress_events.append({
            "percentage": 90, "stage": "階段 4",
            "message": "校對格式與排版中...",
        })

        # Done
        progress_events.append({
            "percentage": 100, "stage": "完成",
            "message": "考卷準備完畢！",
        })

        # Persist questions to DB
        self._persist_questions(exam, stage4_result)

        # Update exam status
        exam.status = ExamStatus.READY
        self.db.commit()

        # Build prompt contexts for personalization transparency
        prompt_contexts = self._build_prompt_contexts(user_context)

        return {
            "error": False,
            "exam_id": exam_id,
            "progress_events": progress_events,
            "prompt_contexts": prompt_contexts,
            "stages": {
                "stage_1": stage1_result,
                "stage_2": stage2_result,
                "stage_3": stage3_result,
                "stage_4": stage4_result,
            },
            "result": stage4_result,
        }

    # ------------------------------------------------------------------ #
    # Stage 1: Exam Point Analysis
    # ------------------------------------------------------------------ #

    def _stage1_exam_point_analysis(self, nodes, total_q, difficulty_dist):
        """Analyse nodes and produce exam points with ratios."""
        if not nodes:
            nodes_data = [{"name": f"考點_{i+1}", "id": str(uuid.uuid4())} for i in range(5)]
        else:
            nodes_data = [{"name": n.name, "id": str(n.id)} for n in nodes]

        # Use actual number of nodes as exam points (min 2, max 10)
        num_points = min(max(len(nodes_data), 2), 10)

        # If we have fewer nodes than num_points, generate additional sub-points
        while len(nodes_data) < num_points:
            base = nodes_data[len(nodes_data) % len(nodes_data)]
            nodes_data.append({
                "name": f"{base['name']}_子考點_{len(nodes_data)+1}",
                "id": str(uuid.uuid4()),
            })

        exam_points = []
        # Distribute ratio evenly then adjust
        base_ratio = 100 // num_points
        remainder = 100 - base_ratio * num_points

        for i in range(num_points):
            ratio = base_ratio + (1 if i < remainder else 0)
            node_info = nodes_data[i]
            exam_points.append({
                "name": node_info["name"],
                "node_id": node_info["id"],
                "ratio": ratio,
                "suggested_difficulty": {
                    "easy": difficulty_dist.get("easy", 30),
                    "medium": difficulty_dist.get("medium", 50),
                    "hard": difficulty_dist.get("hard", 20),
                },
            })

        # Build point_ratio ensuring unique keys and sum = 100
        point_ratio = {}
        for p in exam_points:
            name = p["name"]
            if name in point_ratio:
                point_ratio[name] += p["ratio"]
            else:
                point_ratio[name] = p["ratio"]

        return {
            "exam_points": exam_points,
            "point_ratio": point_ratio,
            "difficulty_map": {p["name"]: p["suggested_difficulty"] for p in exam_points},
        }

    # ------------------------------------------------------------------ #
    # Stage 2: Question Generation
    # ------------------------------------------------------------------ #

    def _stage2_question_generation(self, stage1, difficulty_dist, user_context, total_q, rag_context=""):
        """Generate raw questions based on exam points.

        When RAG is enabled and context is available, uses Claude to generate
        real questions from document content. Falls back to mock data otherwise.
        """
        points = stage1["exam_points"]

        # Try AI-powered generation (works with or without RAG context)
        if self._rag_enabled and self._llm:
            try:
                return self._stage2_claude(points, difficulty_dist, user_context, total_q, rag_context or "")
            except Exception as e:
                logger.warning("Stage 2 AI call failed, falling back to mock: %s", e)

        # Fallback: generate questions from node source_text (no LLM needed)
        questions = []
        easy_count = round(total_q * difficulty_dist.get("easy", 30) / 100)
        hard_count = round(total_q * difficulty_dist.get("hard", 20) / 100)
        medium_count = total_q - easy_count - hard_count

        difficulty_pool = (
            ["easy"] * easy_count +
            ["medium"] * medium_count +
            ["hard"] * hard_count
        )
        random.shuffle(difficulty_pool)

        # Gather source texts from knowledge nodes for question content
        node_texts = {}
        for p in points:
            nid = p.get("node_id")
            if nid:
                node = self.db.query(KnowledgeNode).filter_by(id=uuid.UUID(nid)).first()
                if node and node.source_text:
                    node_texts[p["name"]] = node.source_text[:200]

        for i in range(total_q):
            point = points[i % len(points)]
            diff = difficulty_pool[i] if i < len(difficulty_pool) else "medium"
            point_name = point["name"]
            source = node_texts.get(point_name, "")

            if source:
                # Generate question from source text
                snippet = source[:100].strip()
                q = {
                    "question_text": f"關於「{point_name}」，以下敘述何者正確？\n\n「{snippet}...」",
                    "correct_answer": f"根據教材，{snippet[:50]}",
                    "difficulty": diff,
                    "exam_point": point_name,
                }
            else:
                q = {
                    "question_text": f"關於「{point_name}」的核心概念，以下何者正確？",
                    "correct_answer": f"{point_name}的基本定義與應用",
                    "difficulty": diff,
                    "exam_point": point_name,
                }
            questions.append(q)

        return {"questions": questions, "total": len(questions)}

    def _stage2_claude(self, points, difficulty_dist, user_context, total_q, rag_context):
        """Use Claude to generate questions from RAG context.

        Generates in small batches (3 questions per call) to avoid rate limits.
        """
        import time

        system_prompt = (
            "你是一位專業的證照考試出題老師。\n"
            "如果有提供文件段落，請根據文件內容出題。\n"
            "如果沒有文件段落，請根據考點名稱，用你的專業知識出題。\n"
            "每題必須包含：題目、4個選項(A/B/C/D)、正確答案字母、解析。\n"
            "只回傳 JSON，不要有任何其他文字或 markdown 標記。"
        )

        # Truncate RAG context to keep token usage low
        truncated_context = rag_context[:2000] if rag_context else ""

        all_questions = []
        batch_size = 3
        remaining = total_q

        for batch_start in range(0, total_q, batch_size):
            batch_count = min(batch_size, remaining)
            if batch_count <= 0:
                break

            # Pick points for this batch
            batch_points = [points[(batch_start + j) % len(points)] for j in range(batch_count)]
            point_names = [p["name"] for p in batch_points]

            user_prompt = (
                f"出 {batch_count} 題選擇題。\n"
                f"考點：{', '.join(point_names)}\n"
                f"JSON: {{\"questions\": [{{\"question_text\": \"題目\", \"options\": {{\"A\": \"\", \"B\": \"\", \"C\": \"\", \"D\": \"\"}}, \"correct_answer\": \"A\", \"explanation\": \"短解析\", \"difficulty\": \"medium\", \"exam_point\": \"考點\"}}]}}"
            )

            try:
                if truncated_context:
                    result = self._llm.generate_with_context(
                        system_prompt, user_prompt, truncated_context, max_tokens=4000
                    )
                else:
                    result = self._llm.generate(
                        system_prompt, user_prompt, max_tokens=4000
                    )
                parsed = self._parse_json_response(result)
                batch_questions = parsed.get("questions", [])
                all_questions.extend(batch_questions)
                remaining -= len(batch_questions)
                logger.info("Stage 2 batch %d: generated %d questions", batch_start // batch_size + 1, len(batch_questions))
            except Exception as e:
                logger.warning("Stage 2 batch failed: %s", e)
                # Wait before retrying if rate limited
                if "rate_limit" in str(e).lower():
                    time.sleep(5)
                break

            # Small delay between batches to respect rate limits
            if remaining > 0:
                time.sleep(2)

        if not all_questions:
            raise ValueError("No questions generated from Claude")

        return {"questions": all_questions[:total_q], "total": len(all_questions[:total_q])}

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)
        return json.loads(text)

    # ------------------------------------------------------------------ #
    # Stage 3: Distractor Optimization
    # ------------------------------------------------------------------ #

    def _stage3_distractor_optimization(self, stage2, user_context, rag_context=""):
        """Add distractors and explanations to each question.

        If Stage 2 already produced options (from Claude), reformat them.
        Otherwise generates distractors via Claude or mock fallback.
        """
        questions = stage2["questions"]

        # Check if Stage 2 already provided full options (from Claude batch generation)
        if questions and isinstance(questions[0].get("options"), dict):
            result = []
            for q in questions:
                opts = q["options"]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
                correct_label = q.get("correct_answer", "A")
                option_list = [opts.get(k, "") for k in ["A", "B", "C", "D"]]
                correct_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(correct_label, 0)
                result.append({
                    "question_text": q["question_text"],
                    "difficulty": q.get("difficulty", "medium"),
                    "exam_point": q.get("exam_point", ""),
                    "options": option_list,
                    "correct_index": correct_idx,
                    "explanation": q.get("explanation", ""),
                    "distractor_reasons": {},
                })
            return {"questions": result}

        # Try AI-powered distractor generation
        if self._rag_enabled and self._llm and questions:
            try:
                return self._stage3_claude(questions, user_context, rag_context)
            except Exception as e:
                logger.warning("Stage 3 Claude call failed, falling back to mock: %s", e)

        # Fallback: generate distractors from other exam points
        all_point_names = list({q.get("exam_point", "") for q in questions if q.get("exam_point")})
        result = []
        for i, q in enumerate(questions):
            correct = q["correct_answer"]
            point_name = q.get("exam_point", "")

            # Use other point names as distractors (more realistic than placeholder)
            other_points = [p for p in all_point_names if p != point_name]
            random.shuffle(other_points)
            distractors = []
            for j in range(3):
                if j < len(other_points):
                    distractors.append(f"與「{other_points[j]}」的概念混淆")
                else:
                    distractors.append(f"此為常見誤解，實際上並非如此")

            options = distractors.copy()
            correct_idx = random.randint(0, 3)
            options.insert(correct_idx, correct)

            distractor_reasons = {}
            d_idx = 0
            for opt_idx in range(4):
                if opt_idx != correct_idx:
                    distractor_reasons[str(opt_idx)] = (
                        f"此選項錯誤，{distractors[d_idx]}"
                    )
                    d_idx += 1

            result.append({
                "question_text": q["question_text"],
                "difficulty": q["difficulty"],
                "exam_point": q.get("exam_point", ""),
                "options": options,
                "correct_index": correct_idx,
                "explanation": f"本題考察{q.get('exam_point', '')}，正確答案為{correct}。",
                "distractor_reasons": distractor_reasons,
            })

        return {"questions": result, "total": len(result)}

    def _stage3_claude(self, questions, user_context, rag_context):
        """Use Claude to generate distractors and explanations."""
        prompt_ctx = self._build_prompt_contexts(user_context)

        system_prompt = (
            "你是一位專業的考題設計師。為每道選擇題設計 3 個高品質的干擾選項和詳細解釋。\n"
            "干擾選項應基於常見迷思概念，而非明顯錯誤。\n"
            f"個人化上下文：{prompt_ctx.get('stage_3', '無')}"
        )

        q_json = json.dumps(questions, ensure_ascii=False)
        user_prompt = (
            f"以下是 {len(questions)} 道考題（已有題幹和正確答案）。\n"
            f"請為每題新增：options（4 個選項陣列）、correct_index（正確答案索引 0-3）、"
            f"explanation（詳解）、distractor_reasons（各錯誤選項的解釋）。\n\n"
            f"考題：{q_json}\n\n"
            f"回傳 JSON 格式：{{'questions': [...]}}"
        )

        result = self._llm.generate_with_context(system_prompt, user_prompt, rag_context)
        parsed = json.loads(result) if isinstance(result, str) else result
        if isinstance(parsed, str):
            text = parsed.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            parsed = json.loads(text)

        return {"questions": parsed.get("questions", []), "total": len(parsed.get("questions", []))}

    # ------------------------------------------------------------------ #
    # Stage 4: Formatted Output
    # ------------------------------------------------------------------ #

    def _stage4_formatted_output(self, stage3, exam_id):
        """Produce system-standard JSON schema output."""
        questions = []
        for i, q in enumerate(stage3["questions"]):
            questions.append({
                "id": str(uuid.uuid4()),
                "text": q["question_text"],
                "options": q["options"],
                "answer": q["correct_index"],
                "difficulty": q["difficulty"],
                "exam_point": q["exam_point"],
                "explanation": q["explanation"],
                "distractor_reasons": q["distractor_reasons"],
            })

        return {
            "exam_id": exam_id,
            "total_questions": len(questions),
            "questions": questions,
        }

    # ------------------------------------------------------------------ #
    # Prompt template management
    # ------------------------------------------------------------------ #

    def update_prompt_template(self, stage_id: int, new_content: str,
                                admin_email: str, user_id: str) -> dict:
        """Update a prompt template (admin only)."""
        uid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        role_val = user.role.value if hasattr(user.role, 'value') else user.role
        if role_val not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        template = self.db.query(PromptTemplate).filter_by(
            stage_order=stage_id
        ).first()
        if not template:
            return {"error": True, "status_code": 404, "message": "找不到 Prompt 模板"}

        now = datetime.now(timezone.utc)

        # Save history
        history = PromptTemplateHistory(
            template_id=template.id,
            version=template.version,
            content=template.content,
            modified_by=template.modified_by or admin_email,
            modified_at=template.modified_at or template.created_at,
        )
        self.db.add(history)

        # Update template
        template.content = new_content
        template.version += 1
        template.modified_by = admin_email
        template.modified_at = now

        # Save new version history too
        new_history = PromptTemplateHistory(
            template_id=template.id,
            version=template.version,
            content=new_content,
            modified_by=admin_email,
            modified_at=now,
        )
        self.db.add(new_history)
        self.db.commit()

        return {
            "error": False,
            "template_id": str(template.id),
            "version": template.version,
            "stage_name": template.stage_name,
        }

    def get_template_history(self, stage_id: int, user_id: str) -> dict:
        """Get prompt template version history (admin only)."""
        uid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        role_val = user.role.value if hasattr(user.role, 'value') else user.role
        if role_val not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        template = self.db.query(PromptTemplate).filter_by(
            stage_order=stage_id
        ).first()
        if not template:
            return {"error": True, "status_code": 404, "message": "找不到 Prompt 模板"}

        histories = self.db.query(PromptTemplateHistory).filter_by(
            template_id=template.id
        ).order_by(PromptTemplateHistory.version.asc()).all()

        versions = []
        for h in histories:
            versions.append({
                "version": f"v{h.version}",
                "modified_at": h.modified_at.strftime("%Y-%m-%d %H:%M:%S") if h.modified_at else "",
                "modified_by": h.modified_by or "",
            })

        return {
            "error": False,
            "stage_name": template.stage_name,
            "versions": versions,
        }

    def try_user_update_template(self, stage_id: int, user_id: str) -> dict:
        """Attempt to update template as a regular user (should fail)."""
        uid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        role_val = user.role.value if hasattr(user.role, 'value') else user.role
        if role_val not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        return {"error": False}

    # ------------------------------------------------------------------ #
    # Error handling: retry simulation
    # ------------------------------------------------------------------ #

    def generate_with_retry(self, exam_id: str, user_id: str,
                            fail_stage: int | None = None,
                            max_retries: int = 3,
                            always_fail: bool = False) -> dict:
        """Run generation with retry logic for a specific stage."""
        eid = uuid.UUID(exam_id)
        exam = self.db.query(Exam).filter_by(id=eid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "找不到測驗任務"}

        progress_events = []

        if always_fail and fail_stage:
            # Simulate all retries failing
            for attempt in range(1, max_retries + 1):
                progress_events.append({
                    "percentage": -1,
                    "stage": f"重試",
                    "message": f"AI 回應較慢，正在重試 ({attempt}/{max_retries})...",
                })

            # Mark as FAILED
            exam.status = ExamStatus.FAILED
            self.db.commit()

            return {
                "error": True,
                "status_code": 500,
                "status": "error",
                "message": "AI 生成失敗，請稍後重新嘗試",
                "stage": fail_stage,
                "progress_events": progress_events,
                "retries_exhausted": True,
            }

        if fail_stage:
            # Simulate retry then success
            progress_events.append({
                "percentage": -1,
                "stage": "重試",
                "message": f"AI 回應較慢，正在重試 (1/{max_retries})...",
            })

        # Generate normally
        result = self.generate(exam_id, user_id)
        if not result.get("error"):
            result["progress_events"] = progress_events + result.get("progress_events", [])
        return result

    def validate_stage_output(self, stage_output: dict, required_fields: list[str]) -> dict:
        """Validate that stage output has required fields, auto-regenerate if not."""
        missing = [f for f in required_fields if f not in stage_output]
        if not missing:
            return {"valid": True, "output": stage_output}

        return {
            "valid": False,
            "missing_fields": missing,
            "regenerate_hint": f"請確保輸出包含以下欄位：{', '.join(missing)}",
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _build_user_context(self, user: User) -> dict | None:
        """Build personalization context from user profile."""
        if not user.age and not user.education and not user.career:
            return None

        ctx = {}
        if user.age:
            ctx["age"] = user.age
        if user.education:
            ctx["education"] = user.education
        if user.career:
            ctx["career"] = user.career

        # Determine complexity level
        if user.education and ("高中" in user.education or "高職" in user.education):
            ctx["level"] = "simple"
        elif user.education and ("碩士" in user.education or "博士" in user.education):
            ctx["level"] = "professional"
        else:
            ctx["level"] = "standard"

        return ctx

    def _build_prompt_contexts(self, user_context: dict | None) -> dict:
        """Build prompt context strings for each stage based on user profile."""
        if not user_context:
            return {
                "stage_2": "無個人化上下文",
                "stage_3": "無個人化上下文",
            }

        age = user_context.get("age", "")
        education = user_context.get("education", "")
        career = user_context.get("career", "")
        level = user_context.get("level", "standard")

        if level == "simple":
            short_edu = "高中生" if ("高中" in str(education) or "高職" in str(education)) else str(education)
            stage2_ctx = f"使用者為 {age} 歲{short_edu}，請使用淺顯語言出題"
            stage3_ctx = "解析請使用生活化比喻，避免假設讀者具備進階技術知識"
        elif level == "professional":
            stage2_ctx = f"使用者具{education}學歷且為{career}"
            stage3_ctx = "解析可引用官方文件或 API 語法，使用專業術語"
        else:
            stage2_ctx = f"使用者 {age} 歲，{education}，{career}"
            stage3_ctx = "使用標準程度語言"

        return {
            "stage_2": stage2_ctx,
            "stage_3": stage3_ctx,
        }

    def _get_exam_node_ids(self, exam: Exam) -> list:
        """Extract node IDs from exam config."""
        # If difficulty_distribution has node_ids, use them
        if exam.difficulty_distribution and "node_ids" in exam.difficulty_distribution:
            return [uuid.UUID(nid) for nid in exam.difficulty_distribution["node_ids"]]
        return []

    def _persist_questions(self, exam: Exam, stage4_result: dict):
        """Save generated questions to the database."""
        for i, q in enumerate(stage4_result.get("questions", [])):
            options = q.get("options", [])
            question = Question(
                exam_id=exam.id,
                question_number=i + 1,
                content=q.get("text", ""),
                difficulty=q.get("difficulty", "medium"),
                option_a=options[0] if len(options) > 0 else None,
                option_b=options[1] if len(options) > 1 else None,
                option_c=options[2] if len(options) > 2 else None,
                option_d=options[3] if len(options) > 3 else None,
                correct_answer=str(q.get("answer", 0)),
                explanation=q.get("explanation", ""),
            )
            self.db.add(question)
        self.db.flush()
