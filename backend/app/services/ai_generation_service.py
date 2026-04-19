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
from app.models.resource import Resource
from app.models.subject import Subject
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

        # Prompt template service for DB-based prompts
        from app.services.prompt_template_service import PromptTemplateService
        self._prompt_svc = PromptTemplateService(db)

    # ------------------------------------------------------------------ #
    # Helper: load prompt from DB with fallback
    # ------------------------------------------------------------------ #

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """Load prompt template from DB by name, render variables.

        Returns dict with system_prompt, user_prompt, model, max_tokens, temperature
        or None if template not found (caller should fallback to hardcoded).
        """
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
            logger.error("Failed to load prompt template '%s': %s", name, e, exc_info=True)
            return None

    # ------------------------------------------------------------------ #
    # Helper: subject-level historical question queries
    # ------------------------------------------------------------------ #

    def _get_subject_ids_for_exam(self, exam) -> list:
        """取得考試對應的科目 ID 列表，用於 subject-level 考古題查詢。"""
        return [exam.subject_id]

    def _get_exam_subject_codes(self, exam) -> list[str]:
        """取得科目的 exam_subject_codes 映射（如 ["114080:0102", "FIN114:securities_*"]）。

        用於精確查詢該科目可用的考古題，支援共用科目（高普考）和專業證照。
        """
        subject = self.db.query(Subject).filter_by(id=exam.subject_id).first()
        if subject and subject.exam_subject_codes:
            return subject.exam_subject_codes

        # Fallback: 查同名父科目
        if subject:
            base_name = subject.name.split("（")[0].strip()
            if base_name != subject.name:
                parent = self.db.query(Subject).filter(Subject.name == base_name).first()
                if parent and parent.exam_subject_codes:
                    return parent.exam_subject_codes
        return []

    def _query_historical_by_subject(self, exam, limit: int = None,
                                      quality_filter: bool = False,
                                      exclude_ids: set = None):
        """透過 exam_subject_codes 查詢考古題。

        優先使用 subjects.exam_subject_codes 映射（精確匹配 exam_code:subject_code），
        Fallback 到舊的 subject_id 查詢。
        """
        from sqlalchemy.sql.expression import func as sqlfunc
        from app.models.historical_exam import HistoricalExam
        from sqlalchemy import or_, and_

        codes = self._get_exam_subject_codes(exam)

        if codes:
            # 解析 exam_code:subject_code 組合
            code_filters = []
            for code in codes:
                parts = code.split(":", 1)
                if len(parts) == 2:
                    exam_code, subject_code = parts
                    code_filters.append(
                        and_(
                            HistoricalExam.exam_code == exam_code,
                            HistoricalExam.subject_code == subject_code,
                        )
                    )

            if code_filters:
                query = (
                    self.db.query(Question)
                    .join(HistoricalExam, HistoricalExam.id == Question.historical_exam_id)
                    .filter(or_(*code_filters))
                )
            else:
                return []
        else:
            # Fallback: 舊邏輯，用 subject_id 查
            subject_ids = self._get_subject_ids_for_exam(exam)
            query = self.db.query(Question).join(
                Exam, Question.exam_id == Exam.id
            ).filter(
                Exam.subject_id.in_(subject_ids),
                Question.historical_source.isnot(None),
            )

        if quality_filter:
            query = query.filter(Question.quality_flag == "ok")

        if exclude_ids:
            query = query.filter(
                ~Question.id.in_([uuid.UUID(uid) if isinstance(uid, str) else uid
                                  for uid in exclude_ids])
            )

        query = query.order_by(sqlfunc.random())

        if limit:
            query = query.limit(limit)

        return query.all()

    def _count_historical_by_subject(self, exam, quality_filter: bool = False) -> int:
        """計算 subject-level 可用考古題數量。"""
        from app.models.historical_exam import HistoricalExam
        from sqlalchemy import or_, and_

        codes = self._get_exam_subject_codes(exam)

        if codes:
            code_filters = []
            for code in codes:
                parts = code.split(":", 1)
                if len(parts) == 2:
                    code_filters.append(
                        and_(
                            HistoricalExam.exam_code == parts[0],
                            HistoricalExam.subject_code == parts[1],
                        )
                    )
            if not code_filters:
                return 0
            query = (
                self.db.query(Question)
                .join(HistoricalExam, HistoricalExam.id == Question.historical_exam_id)
                .filter(or_(*code_filters))
            )
        else:
            subject_ids = self._get_subject_ids_for_exam(exam)
            query = self.db.query(Question).join(
                Exam, Question.exam_id == Exam.id
            ).filter(
                Exam.subject_id.in_(subject_ids),
                Question.historical_source.isnot(None),
            )

        if quality_filter:
            query = query.filter(Question.quality_flag == "ok")

        return query.count()

    # ------------------------------------------------------------------ #
    # Public: full pipeline
    # ------------------------------------------------------------------ #

    def generate(self, exam_id: str, user_id: str) -> dict:
        """Run the hybrid 4-layer pipeline (spec v2.0).

        Layer -1: Mode selection (sprint/standard/mastery)
        Layer  0: Weakness + memory + confidence analysis
        Layer  1: Quota allocation (mode x weakness x difficulty x Bloom)
        Layer  2: Hybrid generation (20% historical + 80% AI) + interleaving
        """
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

        # ── Hybrid Pipeline (spec v2.0) ──
        hybrid_result = self._hybrid_generate(exam, user, nodes, node_ids, total_q, difficulty_dist)
        if hybrid_result:
            return hybrid_result

        # ── Fallback: original 4-stage AI pipeline ──
        # Build user context
        user_context = self._build_user_context(user)

        # Retrieve RAG context if enabled (Mastery-aware: skip already-mastered nodes)
        rag_context = ""
        if self._rag_enabled and self._retrieval:
            resource_ids = list({n.resource_id for n in nodes if n.resource_id})
            if resource_ids:
                try:
                    query = f"考點分析：{', '.join(n.name for n in nodes[:5])}"
                    chunks = self._retrieval.retrieve(
                        query, resource_ids, user_id=user.id if user else None
                    )
                    rag_context = self._retrieval.build_context_string(chunks)
                except Exception as e:
                    logger.warning("RAG retrieval failed, falling back to mock: %s", e, exc_info=True)

        # Execute 4 stages
        progress_events = []

        # Prep
        progress_events.append({
            "percentage": 10, "stage": "準備",
            "message": "正在從向量庫提取知識點...",
        })

        # Stage 1
        stage1_result = self._stage1_exam_point_analysis(nodes, total_q, difficulty_dist, exam=exam)
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

    def _stage1_exam_point_analysis(self, nodes, total_q, difficulty_dist, exam=None):
        """Stage 1: 智慧出題配方 — 三層優先級鏈。

        優先級：教師自訂 > 考古題 DB 統計 > LLM 知識密度加權
        """
        if not nodes:
            return {"exam_points": [], "point_ratio": {}, "difficulty_map": {}}

        # Layer 1: 教師自訂配方（最高優先）
        if exam and getattr(exam, 'custom_point_ratio', None):
            return self._apply_custom_recipe(nodes, total_q, exam, difficulty_dist)

        # Layer 2 + 3: LLM 智慧配方（考古題統計 + 知識密度）
        return self._generate_smart_recipe(nodes, total_q, difficulty_dist)

    def _apply_custom_recipe(self, nodes, total_q, exam, difficulty_dist):
        """Layer 1: 套用教師自訂的出題配方。"""
        custom_ratio = exam.custom_point_ratio or {}
        custom_bloom = exam.custom_bloom_ratio or {}

        nodes_data = {n.name: str(n.id) for n in nodes}
        exam_points = []
        total_assigned = 0

        for node_name, ratio in custom_ratio.items():
            if node_name not in nodes_data:
                continue
            q_count = max(1, round(total_q * ratio / 100))
            total_assigned += q_count

            # Bloom allocation from custom or default
            bloom = custom_bloom.get(node_name, {
                "remember": 30, "understand": 25, "apply": 20,
                "analyze": 15, "evaluate": 7, "create": 3,
            })
            bloom_counts = {}
            bloom_total = sum(bloom.values())
            for level, pct in bloom.items():
                bloom_counts[level] = max(0, round(q_count * pct / bloom_total))

            exam_points.append({
                "name": node_name,
                "node_id": nodes_data[node_name],
                "ratio": ratio,
                "question_count": q_count,
                "bloom_allocation": bloom_counts,
                "suggested_difficulty": difficulty_dist,
            })

        # 補齊未列入的節點（每個至少 1 題）
        for n in nodes:
            if n.name not in custom_ratio:
                exam_points.append({
                    "name": n.name,
                    "node_id": str(n.id),
                    "ratio": 0,
                    "question_count": 1,
                    "bloom_allocation": {"remember": 1},
                    "suggested_difficulty": difficulty_dist,
                })
                total_assigned += 1

        # 調整總數
        diff = total_q - total_assigned
        if diff != 0 and exam_points:
            exam_points[0]["question_count"] = max(1, exam_points[0]["question_count"] + diff)

        point_ratio = {p["name"]: p["ratio"] for p in exam_points}
        return {
            "exam_points": exam_points,
            "point_ratio": point_ratio,
            "difficulty_map": {p["name"]: p["suggested_difficulty"] for p in exam_points},
            "source": "custom",
        }

    def _generate_smart_recipe(self, nodes, total_q, difficulty_dist):
        """Layer 2+3: LLM 生成智慧出題配方（考古題統計 + 知識密度加權）。"""
        nodes_data = [{"name": n.name, "id": str(n.id)} for n in nodes]

        # 收集考古題統計
        historical_stats = self._get_historical_exam_stats(nodes)
        has_historical = bool(historical_stats)

        # 收集知識密度（chunk 數量）
        chunk_counts = self._get_chunk_density(nodes)
        node_list = [
            {"name": n.name, "chunks": chunk_counts.get(str(n.id), 0)}
            for n in nodes
        ]

        # Bloom 指令
        if has_historical:
            # 從考古題統計計算 Bloom 分佈
            bloom_totals = {}
            for stat in historical_stats:
                for level, count in stat.get("bloom", {}).items():
                    bloom_totals[level] = bloom_totals.get(level, 0) + count
            total_bloom = sum(bloom_totals.values()) or 1
            bloom_pcts = {k: round(v / total_bloom * 100) for k, v in bloom_totals.items()}
            bloom_instruction = "依考古題統計：" + ", ".join(f"{k}:{v}%" for k, v in bloom_pcts.items())
        else:
            bloom_instruction = "使用預設配比：remember:30%, understand:25%, apply:20%, analyze:15%, evaluate:7%, create:3%"

        # 嘗試 LLM 生成
        db_prompt = self._load_prompt("stage1_exam_point_analysis", {
            "total_questions": str(total_q),
            "node_list": json.dumps(node_list, ensure_ascii=False),
            "historical_stats": json.dumps(historical_stats, ensure_ascii=False) if historical_stats else "（無考古題資料）",
            "bloom_instruction": bloom_instruction,
        })

        _FALLBACK_SYSTEM = f"""你是專業的考試出題規劃師。根據知識節點資訊和考古題統計，規劃最佳出題配方。
綜合考量：1. 考古題分佈 2. 知識密度（chunk 數量） 3. Bloom 認知層次
{bloom_instruction}
輸出 JSON：{{"exam_points": [{{"name": "節點", "ratio": 30, "question_count": 15, "bloom_allocation": {{"remember": 5}}, "difficulty_map": {{"easy": 4, "medium": 8, "hard": 3}}}}], "source": "historical|density"}}
所有 ratio 加總 = 100，question_count 加總 = {total_q}，每個節點至少 1 題。"""

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = _FALLBACK_SYSTEM
            user_prompt = (
                f"出題總數：{total_q}\n\n"
                f"知識節點：\n{json.dumps(node_list, ensure_ascii=False)}\n\n"
                f"考古題統計：\n{json.dumps(historical_stats, ensure_ascii=False) if historical_stats else '（無）'}"
            )

        try:
            if self._llm:
                raw = self._llm.generate(system_prompt, user_prompt, model="gemini-flash", max_tokens=2048)
                parsed = self._parse_json_response(raw)
                if parsed and parsed.get("exam_points"):
                    # Map node_id back
                    node_id_map = {n.name: str(n.id) for n in nodes}
                    for ep in parsed["exam_points"]:
                        ep["node_id"] = node_id_map.get(ep["name"], "")
                        ep["suggested_difficulty"] = ep.get("difficulty_map", difficulty_dist)
                    parsed["point_ratio"] = {p["name"]: p["ratio"] for p in parsed["exam_points"]}
                    parsed["difficulty_map"] = {p["name"]: p.get("suggested_difficulty", difficulty_dist) for p in parsed["exam_points"]}
                    return parsed
        except Exception as e:
            logger.warning("E-01 LLM stage1 failed: %s", e)

        # Fallback: 用知識密度加權的規則邏輯
        return self._density_weighted_fallback(nodes, total_q, difficulty_dist, chunk_counts)

    def _get_historical_exam_stats(self, nodes) -> list[dict]:
        """從 DB 統計考古題的各節點出題分佈。"""
        from sqlalchemy import func

        node_ids = [n.id for n in nodes]
        if not node_ids:
            return []

        # 查詢有 historical_exam_id 的題目，按 node_id 分組
        results = (
            self.db.query(
                Question.node_id,
                Question.bloom_category,
                func.count(Question.id).label("count"),
            )
            .filter(
                Question.historical_exam_id.isnot(None),
                Question.node_id.in_(node_ids),
            )
            .group_by(Question.node_id, Question.bloom_category)
            .all()
        )

        if not results:
            return []

        # 彙整成每個節點的統計
        node_stats = {}  # node_id -> {count, bloom: {level: count}}
        node_name_map = {str(n.id): n.name for n in nodes}

        for node_id, bloom_cat, count in results:
            nid = str(node_id)
            if nid not in node_stats:
                node_stats[nid] = {"node": node_name_map.get(nid, ""), "count": 0, "bloom": {}}
            node_stats[nid]["count"] += count
            bloom_key = bloom_cat.value if hasattr(bloom_cat, 'value') else (bloom_cat or "remember")
            node_stats[nid]["bloom"][bloom_key] = node_stats[nid]["bloom"].get(bloom_key, 0) + count

        total = sum(s["count"] for s in node_stats.values()) or 1
        stats_list = []
        for nid, stat in node_stats.items():
            stat["ratio"] = round(stat["count"] / total * 100)
            stats_list.append(stat)

        stats_list.sort(key=lambda x: x["count"], reverse=True)
        return stats_list

    def _get_chunk_density(self, nodes) -> dict:
        """計算各節點的 chunk 數量（知識密度）。"""
        from app.models.resource_chunk import ResourceChunk
        from sqlalchemy import func

        node_ids = [n.id for n in nodes]
        if not node_ids:
            return {}

        results = (
            self.db.query(
                ResourceChunk.node_id,
                func.count(ResourceChunk.id).label("count"),
            )
            .filter(ResourceChunk.node_id.in_(node_ids))
            .group_by(ResourceChunk.node_id)
            .all()
        )

        return {str(nid): count for nid, count in results}

    def _density_weighted_fallback(self, nodes, total_q, difficulty_dist, chunk_counts):
        """Fallback：用 chunk 數量加權分配比例。"""
        # 用 chunk 數量加權，無 chunk 的節點給基底權重 1
        weights = []
        for n in nodes:
            w = max(1, chunk_counts.get(str(n.id), 0))
            weights.append(w)

        total_weight = sum(weights) or 1
        exam_points = []
        assigned = 0

        for i, n in enumerate(nodes):
            ratio = round(weights[i] / total_weight * 100)
            q_count = max(1, round(total_q * weights[i] / total_weight))
            assigned += q_count

            exam_points.append({
                "name": n.name,
                "node_id": str(n.id),
                "ratio": ratio,
                "question_count": q_count,
                "suggested_difficulty": difficulty_dist,
            })

        # 調整總數
        diff = total_q - assigned
        if diff != 0 and exam_points:
            exam_points[0]["question_count"] = max(1, exam_points[0]["question_count"] + diff)

        # 調整 ratio 總和 = 100
        ratio_sum = sum(p["ratio"] for p in exam_points)
        if ratio_sum != 100 and exam_points:
            exam_points[0]["ratio"] += (100 - ratio_sum)

        return {
            "exam_points": exam_points,
            "point_ratio": {p["name"]: p["ratio"] for p in exam_points},
            "difficulty_map": {p["name"]: p["suggested_difficulty"] for p in exam_points},
            "source": "density",
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
                logger.error("Stage 2 AI call failed, falling back to mock: %s", e, exc_info=True)

        # Fallback: 從考古題庫抽取真實題目（不再產生 mock stub）
        from app.models.question import Question as QModel
        from sqlalchemy import func as sa_func

        historical_pool = (
            self.db.query(QModel)
            .filter(QModel.historical_exam_id.isnot(None))
            .filter(QModel.correct_answer.isnot(None))
            .filter(QModel.correct_answer != '')
            .order_by(sa_func.random())
            .limit(total_q)
            .all()
        )

        if historical_pool:
            questions = []
            for i, hq in enumerate(historical_pool):
                point = points[i % len(points)] if points else {"name": "general"}
                questions.append({
                    "question_text": hq.content,
                    "correct_answer": hq.correct_answer,
                    "option_a": hq.option_a or "",
                    "option_b": hq.option_b or "",
                    "option_c": hq.option_c or "",
                    "option_d": hq.option_d or "",
                    "difficulty": "medium",
                    "exam_point": point["name"],
                    "source_type": "historical",
                    "historical_question_id": str(hq.id),
                })
            return {"questions": questions, "total": len(questions)}

        # 最後 fallback：真的沒有任何題目，回傳錯誤而非 mock
        logger.error("No historical questions available and AI API not configured")
        return {"questions": [], "total": 0, "error": "無可用題目，請先匯入考古題或設定 AI API Key"}

    def _stage2_claude(self, points, difficulty_dist, user_context, total_q, rag_context):
        """Use Claude to generate questions from RAG context.

        Generates in small batches (3 questions per call) to avoid rate limits.
        """
        import time

        # Try loading prompt from DB (E-02: stage2_question_generation)
        db_prompt = self._load_prompt("stage2_question_generation")
        system_prompt = (
            db_prompt["system_prompt"] if db_prompt else
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
                logger.error("Stage 3 Claude call failed, falling back to mock: %s", e, exc_info=True)

        # Fallback: 如果題目已有 option_a~d（考古題），直接使用
        result = []
        for i, q in enumerate(questions):
            # 考古題已有完整選項
            if q.get("option_a") and q.get("option_b"):
                options = [q["option_a"], q["option_b"], q.get("option_c", ""), q.get("option_d", "")]
                correct = q["correct_answer"]
                answer_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                correct_idx = answer_map.get(correct, 0)
                result.append({
                    "question_text": q["question_text"],
                    "difficulty": q.get("difficulty", "medium"),
                    "exam_point": q.get("exam_point", ""),
                    "options": options,
                    "correct_index": correct_idx,
                    "explanation": q.get("explanation", ""),
                    "distractor_reasons": {},
                    "source_type": q.get("source_type", "historical"),
                })
            else:
                # AI 生成的題目但沒有選項 — 保持原樣
                result.append({
                    "question_text": q["question_text"],
                    "difficulty": q.get("difficulty", "medium"),
                    "exam_point": q.get("exam_point", ""),
                    "options": [q.get("correct_answer", ""), "選項待生成", "選項待生成", "選項待生成"],
                    "correct_index": 0,
                    "explanation": "",
                    "distractor_reasons": {},
                })

        return {"questions": result, "total": len(result)}

    def _stage3_claude(self, questions, user_context, rag_context):
        """Use Claude to generate distractors and explanations."""
        prompt_ctx = self._build_prompt_contexts(user_context)

        # Try loading prompt from DB (E-03: stage3_distractor_optimization)
        db_prompt = self._load_prompt("stage3_distractor_optimization")
        system_prompt = (
            db_prompt["system_prompt"] if db_prompt else
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

    def _historical_only_generate(self, exam, nodes, node_ids, total_q):
        """100% 考古題模擬考 — 直接從題庫隨機抽取，不呼叫 AI。

        讓使用者直接體驗真實考試題目。
        若題庫不足，自動調整為實際可用數量。
        """
        from app.services.exam_bank.question_planner import post_process_questions
        from sqlalchemy.sql.expression import func as sqlfunc

        # 計算可用考古題總量（僅 quality_flag='ok' 的高品質題目）
        available = self.db.query(Question).filter(
            Question.node_id.in_(node_ids),
            Question.historical_source.isnot(None),
            Question.quality_flag == "ok",
        ).count()

        # Fallback: subject-level query（匯入考古題 node_id = NULL）
        use_subject_fallback = (available == 0)
        if use_subject_fallback:
            available = self._count_historical_by_subject(exam, quality_filter=True)
            if available == 0:
                # 不限 quality_flag 再試一次
                available = self._count_historical_by_subject(exam, quality_filter=False)
            logger.info("Historical-only: using subject fallback, found %d questions", available)

        actual_count = min(total_q, available)
        auto_adjusted = actual_count < total_q
        adjustment_msg = None
        if auto_adjusted:
            adjustment_msg = f"此範圍考古題僅 {available} 題，已自動調整"
            logger.info("Historical-only: requested %d, available %d, adjusted to %d",
                        total_q, available, actual_count)

        if actual_count == 0:
            return {
                "error": True, "status_code": 400,
                "message": "此範圍沒有考古題，請選擇其他科目或使用混合模式",
            }

        # 隨機抽取（僅高品質題目）
        if use_subject_fallback:
            picked = self._query_historical_by_subject(
                exam, limit=actual_count, quality_filter=True
            )
            if not picked:
                picked = self._query_historical_by_subject(
                    exam, limit=actual_count, quality_filter=False
                )
        else:
            picked = self.db.query(Question).filter(
                Question.node_id.in_(node_ids),
                Question.historical_source.isnot(None),
                Question.quality_flag == "ok",
            ).order_by(sqlfunc.random()).limit(actual_count).all()

        # 建立題目 dict
        all_questions = []
        for src in picked:
            all_questions.append({
                "node_id": str(src.node_id) if src.node_id else None,
                "content": src.content,
                "type": src.type or "single_choice",
                "difficulty": src.difficulty or "medium",
                "bloom_category": src.bloom_category or "remember",
                "option_a": src.option_a or "",
                "option_b": src.option_b or "",
                "option_c": src.option_c or "",
                "option_d": src.option_d or "",
                "correct_answer": src.correct_answer or "A",
                "explanation": src.explanation or "",
                "historical_source": src.historical_source,
                "reliability": "green",
                "quality_flag": "ok",
            })

        # 後處理：交錯排列 + 難度平滑 + 開局保護
        all_questions = post_process_questions(all_questions)

        # 寫入 DB
        for q in all_questions:
            new_q = Question(
                exam_id=exam.id,
                node_id=uuid.UUID(q["node_id"]) if q.get("node_id") else None,
                question_number=q["question_number"],
                type=q.get("type", "single_choice"),
                difficulty=q.get("difficulty", "medium"),
                bloom_category=q.get("bloom_category"),
                content=q["content"],
                option_a=q.get("option_a", ""),
                option_b=q.get("option_b", ""),
                option_c=q.get("option_c", ""),
                option_d=q.get("option_d", ""),
                correct_answer=q.get("correct_answer", "A"),
                explanation=q.get("explanation", ""),
                historical_source=q.get("historical_source"),
                quality_flag="ok",
            )
            self.db.add(new_q)

        # 更新 exam
        exam.total_questions = actual_count
        exam.status = ExamStatus.READY
        self.db.commit()

        final_qs = self.db.query(Question).filter_by(exam_id=exam.id).order_by(
            Question.question_number
        ).all()

        result = {
            "error": False,
            "exam_id": str(exam.id),
            "exam": {"id": str(exam.id), "status": "READY", "total_questions": len(final_qs)},
            "composition": {
                "mode": "historical_only",
                "mode_reason": "考古題模擬考 — 100% 歷年真題",
                "historical_count": len(final_qs),
                "ai_count": 0,
                "wrong_review_count": 0,
                "interleaving": True,
            },
            "questions": [
                {
                    "id": str(q.id),
                    "question_number": q.question_number,
                    "content": q.content,
                    "type": q.type or "single_choice",
                    "difficulty": q.difficulty or "medium",
                    "bloom_category": q.bloom_category,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation or "",
                    "historical_source": q.historical_source,
                    "reliability": "green",
                }
                for q in final_qs
            ],
            "progress_events": [
                {"percentage": 30, "stage": "抽題", "message": f"從考古題庫隨機抽取 {len(final_qs)} 題"},
                {"percentage": 80, "stage": "排列", "message": "交錯排列 + 難度平滑"},
                {"percentage": 100, "stage": "完成", "message": "考古題模擬考準備完畢！"},
            ],
        }

        if adjustment_msg:
            result["adjustment_message"] = adjustment_msg

        return result

    def _hybrid_generate(self, exam, user, nodes, node_ids, total_q, difficulty_dist):
        """Hybrid pipeline: 20% historical + 80% AI, driven by QuestionPlanner.

        Implements spec v2.0 Layers -1 through 2:
        - P14: SM-2 ease_factor read
        - P15: Ebbinghaus review date detection
        - P16: Confidence four-quadrant (dangerous blindspot weighting)
        - P17: Sprint mode wrong-answer interleaving
        """
        from app.services.exam_bank.question_planner import (
            QuestionPlanner, NodeProfile, post_process_questions,
        )
        from app.models.node_mastery import NodeMastery
        from app.models.question_stat import QuestionStat
        from app.models.learning_journey import LearningJourney
        from app.models.answer import Answer
        from sqlalchemy.sql.expression import func as sqlfunc
        from sqlalchemy import and_

        if not node_ids:
            return None

        # ── 考古題模擬考模式：100% 考古題，不走 AI ──
        exam_mode = (difficulty_dist or {}).get("exam_mode", "hybrid")
        if exam_mode == "historical_only":
            return self._historical_only_generate(exam, nodes, node_ids, total_q)

        # ── Build NodeProfile for each node (P14 + P15 + P16) ──
        profiles = []
        for node in nodes:
            nid = node.id

            # P14/P15: SM-2 ease_factor + next_review_date
            mastery = self.db.query(NodeMastery).filter_by(
                user_id=user.id, node_id=nid
            ).first()
            stats = self.db.query(QuestionStat).filter_by(
                user_id=user.id, node_id=nid
            ).first()

            # P16: Confidence four-quadrant — count dangerous blindspots
            # Dangerous blindspot = confidence='high' AND is_correct=false
            blindspot_count = self.db.query(sqlfunc.count(Answer.id)).join(
                Question, Answer.question_id == Question.id
            ).filter(
                Answer.user_id == user.id,
                Question.node_id == nid,
                Answer.confidence == 'high',
                Answer.is_correct == False,
            ).scalar() or 0

            # Lucky guess count = confidence='low' AND is_correct=true
            lucky_count = self.db.query(sqlfunc.count(Answer.id)).join(
                Question, Answer.question_id == Question.id
            ).filter(
                Answer.user_id == user.id,
                Question.node_id == nid,
                Answer.confidence == 'low',
                Answer.is_correct == True,
            ).scalar() or 0

            hist_count = self.db.query(Question).filter(
                Question.node_id == nid,
                Question.historical_source.isnot(None),
            ).count()

            # Fallback: 若 node-level 無考古題，用 subject-level 計數
            # （匯入的考古題 node_id = NULL，透過 exam.subject_id 關聯）
            if hist_count == 0:
                hist_count = self._count_historical_by_subject(exam)

            profiles.append(NodeProfile(
                node_id=str(nid),
                name=node.name,
                mastery_rate=float(mastery.mastery_rate) if mastery else None,
                mastery_color=mastery.color if mastery else "gray",
                ease_factor=float(stats.ease_factor) if stats else 2.5,
                next_review_date=stats.next_review_date if stats else None,
                success_count=stats.success_count if stats else 0,
                fail_count=stats.fail_count if stats else 0,
                dangerous_blindspot_count=blindspot_count,
                lucky_guess_count=lucky_count,
                historical_count=hist_count,
            ))

        # Get exam_date from learning journey
        journey = self.db.query(LearningJourney).filter_by(
            user_id=user.id, subject_id=exam.subject_id,
        ).first()
        exam_date = journey.exam_date if journey else None

        # P17: Count wrong answers for sprint mode interleaving
        wrong_count = self.db.query(sqlfunc.count(Answer.id)).filter(
            Answer.user_id == user.id,
            Answer.is_correct == False,
        ).join(Question, Answer.question_id == Question.id).join(
            Exam, Question.exam_id == Exam.id
        ).filter(
            Exam.subject_id == exam.subject_id,
        ).scalar() or 0

        # Map difficulty level
        user_diff = 2
        if difficulty_dist:
            if difficulty_dist.get("easy", 0) >= 50:
                user_diff = 1
            elif difficulty_dist.get("hard", 0) >= 50:
                user_diff = 3

        # ── Run QuestionPlanner ──
        planner = QuestionPlanner()
        plan = planner.plan(
            nodes=profiles,
            total_q=total_q,
            user_difficulty=user_diff,
            exam_date=exam_date,
            wrong_answer_count=wrong_count,
            custom_bloom_ratio=getattr(exam, 'custom_bloom_ratio', None),
            historical_priority=getattr(exam, 'historical_priority', False),
        )

        logger.info("Hybrid plan: mode=%s, nodes=%d, wrong_review=%d",
                     plan.mode, len(plan.node_plans), plan.wrong_review_count)

        # ── Execute plan: pick historical + generate AI ──
        all_questions = []
        used_question_ids = set()  # 追蹤已使用的題目 ID，避免重複

        for np in plan.node_plans:
            node_uuid = uuid.UUID(np.node_id)

            # 1. Pick historical questions (20%)
            if np.historical_count > 0:
                hist_qs = self.db.query(Question).filter(
                    Question.node_id == node_uuid,
                    Question.historical_source.isnot(None),
                ).order_by(sqlfunc.random()).limit(np.historical_count).all()

                # Fallback: subject-level query（匯入考古題 node_id = NULL）
                if not hist_qs:
                    hist_qs = self._query_historical_by_subject(
                        exam, limit=np.historical_count, exclude_ids=used_question_ids
                    )
                    if hist_qs:
                        logger.info("Historical fallback: found %d via subject for node %s",
                                   len(hist_qs), np.name)

                for src in hist_qs:
                    used_question_ids.add(str(src.id))
                    all_questions.append({
                        "node_id": str(node_uuid),
                        "content": src.content,
                        "type": src.type or "single_choice",
                        "difficulty": src.difficulty or "medium",
                        "bloom_category": src.bloom_category or "remember",
                        "option_a": src.option_a or "",
                        "option_b": src.option_b or "",
                        "option_c": src.option_c or "",
                        "option_d": src.option_d or "",
                        "correct_answer": src.correct_answer or "A",
                        "explanation": src.explanation or "",
                        "historical_source": src.historical_source,
                        "reliability": "green",
                    })

            # 2. AI generate remainder (80%) — 多級補題策略
            if np.ai_count > 0:
                ai_qs = self._generate_ai_for_node(
                    node_uuid, np, all_questions[-np.historical_count:] if np.historical_count else [],
                    exam=exam,
                )
                all_questions.extend(ai_qs)

                # 檢查是否短缺
                shortfall = np.ai_count - len(ai_qs)
                if shortfall > 0:
                    logger.warning("AI generation shortfall: need %d more for node %s", shortfall, np.name)
                    补_qs = self._fill_shortfall(node_uuid, shortfall, used_question_ids, exam)
                    all_questions.extend(补_qs)

        # ── P17: Sprint/Standard wrong-answer interleaving ──
        if plan.wrong_review_count > 0:
            wrong_qs = self.db.query(Answer).filter(
                Answer.user_id == user.id,
                Answer.is_correct == False,
            ).join(Question, Answer.question_id == Question.id).join(
                Exam, Question.exam_id == Exam.id
            ).filter(
                Exam.subject_id == exam.subject_id,
            ).order_by(sqlfunc.random()).limit(plan.wrong_review_count).all()

            for wa in wrong_qs:
                src_q = self.db.query(Question).filter_by(id=wa.question_id).first()
                if src_q:
                    all_questions.append({
                        "node_id": str(src_q.node_id) if src_q.node_id else None,
                        "content": src_q.content,
                        "type": src_q.type or "single_choice",
                        "difficulty": src_q.difficulty or "medium",
                        "bloom_category": src_q.bloom_category or "remember",
                        "option_a": src_q.option_a or "",
                        "option_b": src_q.option_b or "",
                        "option_c": src_q.option_c or "",
                        "option_d": src_q.option_d or "",
                        "correct_answer": src_q.correct_answer or "A",
                        "explanation": src_q.explanation or "",
                        "historical_source": src_q.historical_source,
                        "reliability": "green" if src_q.historical_source else "yellow",
                    })

        if not all_questions:
            return None

        # ── Quality Assurance: Cross-LLM validation for AI questions ──
        from app.services.exam_bank.question_validator import (
            validate_with_cross_llm, handle_validation_result,
        )

        if self._llm:
            used_ids = set()
            validated_questions = []
            # Build replacement pool from historical questions of same nodes
            replacement_pool = []
            for np in plan.node_plans:
                pool_qs = self.db.query(Question).filter(
                    Question.node_id == uuid.UUID(np.node_id),
                    Question.historical_source.isnot(None),
                ).order_by(sqlfunc.random()).limit(5).all()
                # Fallback: subject-level pool
                if not pool_qs:
                    pool_qs = self._query_historical_by_subject(exam, limit=5)
                for pq in pool_qs:
                    replacement_pool.append({
                        "id": str(pq.id),
                        "node_id": str(pq.node_id),
                        "content": pq.content,
                        "type": pq.type or "single_choice",
                        "difficulty": pq.difficulty or "medium",
                        "bloom_category": pq.bloom_category or "remember",
                        "option_a": pq.option_a or "",
                        "option_b": pq.option_b or "",
                        "option_c": pq.option_c or "",
                        "option_d": pq.option_d or "",
                        "correct_answer": pq.correct_answer or "A",
                        "explanation": pq.explanation or "",
                        "historical_source": pq.historical_source,
                        "reliability": "green",
                    })

            for q in all_questions:
                if q.get("reliability") == "yellow":  # Only validate AI-generated
                    vr = validate_with_cross_llm(
                        question=q,
                        generated_answer=q.get("correct_answer", "A"),
                        llm_service=self._llm,
                        generation_model="claude",
                    )
                    q = handle_validation_result(q, vr, replacement_pool, used_ids)
                validated_questions.append(q)
            all_questions = validated_questions

        # ── Post-process: interleave + smooth + opening ──
        all_questions = post_process_questions(all_questions)

        # ── Persist to DB ──
        for q in all_questions:
            new_q = Question(
                exam_id=exam.id,
                node_id=uuid.UUID(q["node_id"]) if q.get("node_id") else None,
                question_number=q["question_number"],
                type=q.get("type", "single_choice"),
                difficulty=q.get("difficulty", "medium"),
                bloom_category=q.get("bloom_category"),
                content=q["content"],
                option_a=q.get("option_a", ""),
                option_b=q.get("option_b", ""),
                option_c=q.get("option_c", ""),
                option_d=q.get("option_d", ""),
                correct_answer=q.get("correct_answer", "A"),
                explanation=q.get("explanation", ""),
                historical_source=q.get("historical_source"),
                quality_flag=q.get("quality_flag", "ok"),
                validation_model=q.get("validation_model"),
            )
            self.db.add(new_q)

        exam.status = ExamStatus.READY
        self.db.commit()

        # Re-query for IDs
        final_qs = self.db.query(Question).filter_by(exam_id=exam.id).order_by(
            Question.question_number
        ).all()

        hist_total = sum(1 for q in final_qs if q.historical_source)
        ai_total = len(final_qs) - hist_total

        return {
            "error": False,
            "exam_id": str(exam.id),
            "exam": {"id": str(exam.id), "status": "READY", "total_questions": len(final_qs)},
            "composition": {
                "mode": plan.mode,
                "mode_reason": plan.mode_reason,
                "historical_count": hist_total,
                "ai_count": ai_total,
                "wrong_review_count": plan.wrong_review_count,
                "bloom_actual": plan.bloom_summary,
                "interleaving": True,
            },
            "questions": [
                {
                    "id": str(q.id),
                    "question_number": q.question_number,
                    "content": q.content,
                    "type": q.type or "single_choice",
                    "difficulty": q.difficulty or "medium",
                    "bloom_category": q.bloom_category,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation or "",
                    "historical_source": q.historical_source,
                    "reliability": "green" if q.historical_source else "yellow",
                }
                for q in final_qs
            ],
            "progress_events": [
                {"percentage": 10, "stage": "分析", "message": f"模式：{plan.mode_reason}"},
                {"percentage": 30, "stage": "規劃", "message": f"弱點分析完成，{len(plan.node_plans)} 個考點"},
                {"percentage": 60, "stage": "出題", "message": f"考古題 {hist_total} + AI {ai_total} 題"},
                {"percentage": 90, "stage": "排列", "message": "交錯排列 + 難度平滑 + 開局保護"},
                {"percentage": 100, "stage": "完成", "message": "考卷準備完畢！"},
            ],
        }

    def _fill_shortfall(self, node_uuid, shortfall: int, used_ids: set, exam=None) -> list:
        """多級補題策略 — 確保不會因 AI 生成失敗而短缺題目。

        Level 1: 同節點考古題擴大抽取（排除已使用）
        Level 2: 同科目跨節點考古題借題
        Level 3: 同科目所有歷史題（最後手段）
        Level 4: Subject-level 考古題（node_id = NULL 的匯入題目）
        """
        from sqlalchemy.sql.expression import func as sqlfunc
        filled = []

        def _pick(query, limit):
            """從 query 中排除已用 ID 後隨機抽取"""
            candidates = query.filter(
                ~Question.id.in_([uuid.UUID(uid) for uid in used_ids] if used_ids else [uuid.UUID("00000000-0000-0000-0000-000000000000")])
            ).order_by(sqlfunc.random()).limit(limit).all()
            result = []
            for src in candidates:
                if str(src.id) in used_ids:
                    continue
                used_ids.add(str(src.id))
                result.append({
                    "node_id": str(src.node_id) if src.node_id else str(node_uuid),
                    "content": src.content,
                    "type": src.type or "single_choice",
                    "difficulty": src.difficulty or "medium",
                    "bloom_category": src.bloom_category or "remember",
                    "option_a": src.option_a or "",
                    "option_b": src.option_b or "",
                    "option_c": src.option_c or "",
                    "option_d": src.option_d or "",
                    "correct_answer": src.correct_answer or "A",
                    "explanation": src.explanation or "",
                    "historical_source": src.historical_source,
                    "reliability": "green" if src.historical_source else "yellow",
                })
            return result

        remaining = shortfall

        # Level 1: 同節點考古題
        if remaining > 0:
            base_q = self.db.query(Question).filter(
                Question.node_id == node_uuid,
                Question.historical_source.isnot(None),
            )
            level1 = _pick(base_q, remaining)
            filled.extend(level1)
            remaining -= len(level1)
            if level1:
                logger.info("Shortfall L1: filled %d from same node", len(level1))

        # Level 2: 同科目跨節點
        if remaining > 0:
            # 找同科目的其他節點
            from app.models.resource import Resource
            resource = self.db.query(Resource).join(
                KnowledgeNode, KnowledgeNode.resource_id == Resource.id
            ).filter(KnowledgeNode.id == node_uuid).first()

            if resource:
                sibling_nodes = self.db.query(KnowledgeNode.id).filter(
                    KnowledgeNode.resource_id == resource.id,
                    KnowledgeNode.id != node_uuid,
                    KnowledgeNode.depth == 1,
                ).all()
                sibling_ids = [n.id for n in sibling_nodes]

                if sibling_ids:
                    cross_q = self.db.query(Question).filter(
                        Question.node_id.in_(sibling_ids),
                        Question.historical_source.isnot(None),
                    )
                    level2 = _pick(cross_q, remaining)
                    filled.extend(level2)
                    remaining -= len(level2)
                    if level2:
                        logger.info("Shortfall L2: filled %d from sibling nodes", len(level2))

        # Level 3: 同科目所有歷史題
        if remaining > 0:
            if resource:
                all_nodes = self.db.query(KnowledgeNode.id).filter(
                    KnowledgeNode.resource_id == resource.id,
                ).all()
                all_node_ids = [n.id for n in all_nodes]

                all_q = self.db.query(Question).filter(
                    Question.node_id.in_(all_node_ids),
                    Question.historical_source.isnot(None),
                )
                level3 = _pick(all_q, remaining)
                filled.extend(level3)
                remaining -= len(level3)
                if level3:
                    logger.info("Shortfall L3: filled %d from all subject nodes", len(level3))

        # Level 4: Subject-level 考古題（node_id = NULL 的匯入題目）
        if remaining > 0 and exam:
            subject_qs = self._query_historical_by_subject(
                exam, limit=remaining, exclude_ids=used_ids
            )
            for src in subject_qs:
                if str(src.id) in used_ids:
                    continue
                used_ids.add(str(src.id))
                filled.append({
                    "node_id": str(src.node_id) if src.node_id else str(node_uuid),
                    "content": src.content,
                    "type": src.type or "single_choice",
                    "difficulty": src.difficulty or "medium",
                    "bloom_category": src.bloom_category or "remember",
                    "option_a": src.option_a or "",
                    "option_b": src.option_b or "",
                    "option_c": src.option_c or "",
                    "option_d": src.option_d or "",
                    "correct_answer": src.correct_answer or "A",
                    "explanation": src.explanation or "",
                    "historical_source": src.historical_source,
                    "reliability": "green" if src.historical_source else "yellow",
                })
            remaining -= len(subject_qs)
            if subject_qs:
                logger.info("Shortfall L4: filled %d from subject-level historical", len(subject_qs))

        if remaining > 0:
            logger.warning("Could not fill %d questions — subject has insufficient question bank", remaining)

        return filled

    def _generate_ai_for_node(self, node_uuid, node_plan, few_shot_examples, exam=None):
        """Generate AI questions for a single node.

        Strategy (spec v2.0 Layer 2):
        1. LLM available + historical examples → few-shot prompt with exam style
        2. LLM available + no examples → generate from node name/context
        3. No LLM + historical → cycle through historical pool (marked as AI)
        4. No LLM + no historical → return empty (caller handles)
        """
        ai_questions = []
        count = node_plan.ai_count
        if count <= 0:
            return ai_questions

        # Gather few-shot examples from historical pool
        hist_pool = self.db.query(Question).filter(
            Question.node_id == node_uuid,
            Question.historical_source.isnot(None),
        ).order_by(Question.id).limit(10).all()

        # Fallback: subject-level few-shot（匯入考古題 node_id = NULL）
        if not hist_pool and exam:
            hist_pool = self._query_historical_by_subject(exam, limit=10)

        # ── Path 1: LLM available → real AI generation ──
        if self._llm:
            try:
                ai_questions = self._llm_generate_for_node(
                    node_name=node_plan.name,
                    count=count,
                    difficulty_dist=node_plan.difficulty_dist,
                    bloom_target=node_plan.bloom_target,
                    few_shot=hist_pool[:5],
                    node_uuid=node_uuid,
                )
                if ai_questions:
                    return ai_questions
            except Exception as e:
                logger.warning("LLM generation failed for node %s, falling back: %s",
                               node_plan.name, e)

        # ── Path 2: Fallback — cycle historical pool ──
        for i in range(count):
            if hist_pool:
                src = hist_pool[i % len(hist_pool)]
                ai_questions.append({
                    "node_id": str(node_uuid),
                    "content": src.content,
                    "type": src.type or "single_choice",
                    "difficulty": src.difficulty or "medium",
                    "bloom_category": src.bloom_category or "remember",
                    "option_a": src.option_a or "",
                    "option_b": src.option_b or "",
                    "option_c": src.option_c or "",
                    "option_d": src.option_d or "",
                    "correct_answer": src.correct_answer or "A",
                    "explanation": src.explanation or "",
                    "historical_source": None,
                    "reliability": "yellow",
                })
            else:
                break

        return ai_questions

    def _llm_generate_for_node(self, node_name, count, difficulty_dist,
                                bloom_target, few_shot, node_uuid):
        """Use LLM to generate questions with few-shot historical examples.

        P10: Few-shot prompt design per exam-generation-spec v2.0.
        """
        # Build few-shot examples string
        examples_str = ""
        if few_shot:
            examples_str = "以下是該考點的考古題範例（供參考出題風格和概念範圍）：\n---\n"
            for i, q in enumerate(few_shot, 1):
                examples_str += (
                    f"題目 {i}: {q.content}\n"
                    f"(A) {q.option_a or ''}\n"
                    f"(B) {q.option_b or ''}\n"
                    f"(C) {q.option_c or ''}\n"
                    f"(D) {q.option_d or ''}\n"
                    f"正確答案: {q.correct_answer}\n\n"
                )
            examples_str += "---\n\n"

        # Build difficulty instruction
        diff_str = "、".join(
            f"{k} {v} 題" for k, v in difficulty_dist.items() if v > 0
        )

        # Build Bloom instruction
        bloom_str = "、".join(
            f"{k} {v} 題" for k, v in bloom_target.items() if v > 0
        )

        # Try loading prompt from DB (E-02: stage2_question_generation)
        db_prompt = self._load_prompt("stage2_question_generation")
        system_prompt = (
            db_prompt["system_prompt"] if db_prompt else
            "你是專業的證照考試出題老師。請根據提供的考點和考古題範例，"
            "生成高品質的選擇題。題目必須與考古題相關但不重複。"
            "每題必須有題幹、4 個選項（A/B/C/D）、正確答案字母、和 50 字以內的解析。"
            "回傳純 JSON 格式，不要 markdown code block。"
        )

        user_prompt = (
            f"{examples_str}"
            f"考點：{node_name}\n"
            f"請生成 {count} 題選擇題。\n"
            f"難度分佈：{diff_str}\n"
            f"Bloom 認知層次分佈：{bloom_str}\n\n"
            f"回傳格式（JSON array）：\n"
            f'[{{"content": "題幹", "option_a": "選項A", "option_b": "選項B", '
            f'"option_c": "選項C", "option_d": "選項D", "correct_answer": "A", '
            f'"difficulty": "medium", "bloom_category": "remember", '
            f'"explanation": "解析"}}]'
        )

        try:
            result = self._llm.generate_json(system_prompt, user_prompt)
        except Exception as e:
            logger.warning("LLM generate_json failed: %s, trying generate()", e)
            raw = self._llm.generate(system_prompt, user_prompt)
            result = self._parse_json_from_text(raw)

        if not result:
            return []

        # Normalize to list
        questions_data = result if isinstance(result, list) else result.get("questions", [result])

        ai_questions = []
        for q in questions_data[:count]:
            if not isinstance(q, dict) or "content" not in q:
                continue
            answer = q.get("correct_answer", "A")
            if answer not in ("A", "B", "C", "D"):
                answer = "A"
            ai_questions.append({
                "node_id": str(node_uuid),
                "content": q["content"],
                "type": "single_choice",
                "difficulty": q.get("difficulty", "medium"),
                "bloom_category": q.get("bloom_category", "remember"),
                "option_a": q.get("option_a", ""),
                "option_b": q.get("option_b", ""),
                "option_c": q.get("option_c", ""),
                "option_d": q.get("option_d", ""),
                "correct_answer": answer,
                "explanation": q.get("explanation", ""),
                "historical_source": None,
                "reliability": "yellow",
            })

        return ai_questions

    @staticmethod
    def _parse_json_from_text(text):
        """Try to extract JSON from LLM text response."""
        if not text:
            return None
        # Strip markdown code blocks
        import re
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON array in text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return None

    def _get_exam_node_ids(self, exam: Exam) -> list:
        """Extract node IDs from exam config.

        Fallback chain:
        1. difficulty_distribution.node_ids（前端選擇的節點）
        2. 透過 subject_id 查找該科目下所有知識節點（含父科目的 Resource）
        """
        # Priority 1: explicit node_ids from exam config
        if exam.difficulty_distribution and "node_ids" in exam.difficulty_distribution:
            node_ids = exam.difficulty_distribution["node_ids"]
            if node_ids:
                return [uuid.UUID(nid) for nid in node_ids]

        # Priority 2: find nodes via subject_id → Resource → KnowledgeNode
        subject_ids = self._get_subject_ids_for_exam(exam)
        resources = self.db.query(Resource).filter(
            Resource.subject_id.in_(subject_ids)
        ).all()
        resource_ids = [r.id for r in resources]

        if resource_ids:
            nodes = self.db.query(KnowledgeNode).filter(
                KnowledgeNode.resource_id.in_(resource_ids)
            ).all()
            if nodes:
                logger.info("_get_exam_node_ids: found %d nodes via subject fallback for exam %s",
                           len(nodes), exam.id)
                return [n.id for n in nodes]

        return []

    def _try_historical_questions(self, exam: Exam, node_ids: list, total_q: int):
        """If selected nodes have historical exam questions, randomly pick from DB.

        Returns a complete result dict if successful, None if no historical questions.
        """
        from sqlalchemy.sql.expression import func as sqlfunc

        if not node_ids:
            return None

        # Count available historical questions for these nodes
        available = self.db.query(Question).filter(
            Question.node_id.in_(node_ids),
            Question.historical_source.isnot(None),
        ).count()

        # Fallback: subject-level query（匯入考古題 node_id = NULL）
        use_subject_fallback = (available == 0)
        if use_subject_fallback:
            available = self._count_historical_by_subject(exam)

        if available == 0:
            return None

        logger.info("Historical question bank: %d available (subject_fallback=%s), need %d",
                    available, use_subject_fallback, total_q)

        # Randomly select questions from the bank
        if use_subject_fallback:
            picked = self._query_historical_by_subject(exam, limit=total_q)
        else:
            picked = self.db.query(Question).filter(
                Question.node_id.in_(node_ids),
                Question.historical_source.isnot(None),
            ).order_by(sqlfunc.random()).limit(total_q).all()

        if not picked:
            return None

        # Create new Question records linked to this exam
        result_questions = []
        for i, src in enumerate(picked):
            new_q = Question(
                exam_id=exam.id,
                node_id=src.node_id,
                question_number=i + 1,
                type=src.type or "single_choice",
                difficulty=src.difficulty or "medium",
                bloom_category=src.bloom_category,
                content=src.content,
                option_a=src.option_a,
                option_b=src.option_b,
                option_c=src.option_c,
                option_d=src.option_d,
                correct_answer=src.correct_answer,
                explanation=src.explanation or "",
                source_citation=src.source_citation,
                historical_source=src.historical_source,
            )
            self.db.add(new_q)
            result_questions.append({
                "id": None,  # will be set after flush
                "question_number": i + 1,
                "text": src.content,
                "options": [src.option_a or "", src.option_b or "", src.option_c or "", src.option_d or ""],
                "answer": src.correct_answer,
                "difficulty": src.difficulty or "medium",
                "explanation": src.explanation or "",
                "bloom_category": src.bloom_category,
                "historical_source": src.historical_source,
            })

        # Update exam status
        exam.status = ExamStatus.READY
        self.db.commit()

        # Re-query to get IDs
        final_questions = self.db.query(Question).filter_by(exam_id=exam.id).order_by(
            Question.question_number
        ).all()

        return {
            "error": False,
            "exam_id": str(exam.id),
            "exam": {
                "id": str(exam.id),
                "status": "READY",
                "total_questions": len(final_questions),
            },
            "questions": [
                {
                    "id": str(q.id),
                    "question_number": q.question_number,
                    "text": q.content,
                    "content": q.content,
                    "type": q.type or "single_choice",
                    "difficulty": q.difficulty or "medium",
                    "bloom_category": q.bloom_category,
                    "options": [q.option_a or "", q.option_b or "", q.option_c or "", q.option_d or ""],
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation or "",
                    "historical_source": q.historical_source,
                }
                for q in final_questions
            ],
            "progress_events": [
                {"percentage": 20, "stage": "準備", "message": "從考古題題庫抽取題目..."},
                {"percentage": 80, "stage": "組卷", "message": f"已從 {available} 題中隨機抽取 {len(final_questions)} 題"},
                {"percentage": 100, "stage": "完成", "message": "考卷準備完畢！"},
            ],
        }

    def _persist_questions(self, exam: Exam, stage4_result: dict):
        """Save generated questions to the database.

        使用 commit() 而非 flush()，確保資料持久化。
        """
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
        self.db.commit()
