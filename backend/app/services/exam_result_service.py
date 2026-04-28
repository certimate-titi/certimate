"""Exam Result Service — 測驗結果業務邏輯。"""

import uuid
from collections import Counter

from sqlalchemy import func, Integer as SAInteger
from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamStatus
from app.models.answer import Answer
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource
from app.models.user import User


class ExamResultService:

    """Exam Result Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self._llm = None
        self._prompt_svc = None

    def get_result(self, exam_id: str, user_id: str) -> dict:
        """取得 result。"""
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗結果的權限"}

        if exam.status != ExamStatus.SUBMITTED:
            return {"error": True, "status_code": 400, "message": "測驗尚未提交，無法查看結果"}

        score = exam.score or 0
        passing_score = exam.passing_score or 0
        pass_status = "通過" if score >= passing_score else "未達門檻"

        # Find previous exam for comparison
        comparison = self._get_comparison(exam, uid)

        # Build user_answers from answers + questions
        questions = self.db.query(Question).filter_by(exam_id=exam.id).order_by(
            Question.question_number
        ).all()
        answers = self.db.query(Answer).filter_by(
            exam_id=exam.id, user_id=uid
        ).all()
        answer_map = {str(a.question_id): a for a in answers}

        user_answers = []
        for q in questions:
            a = answer_map.get(str(q.id))
            user_answers.append({
                "questionId": str(q.id),
                "questionNumber": q.question_number,
                "userChoice": a.selected_answer if a else None,
                "isCorrect": a.is_correct if a else False,
                "correctAnswer": q.correct_answer,
                "content": q.content,
                "optionA": q.option_a,
                "optionB": q.option_b,
                "optionC": q.option_c,
                "optionD": q.option_d,
                "explanation": q.explanation or "",
                "difficulty": getattr(q, 'difficulty', None),
                "bloomCategory": getattr(q, 'bloom_category', None),
                "reliability": "green" if getattr(q, 'historical_source', None) else "yellow",
            })

        time_spent = 0
        if exam.started_at and exam.submitted_at:
            time_spent = int((exam.submitted_at - exam.started_at).total_seconds())

        # Generate AI summary (cached in DB)
        ai_summary = self._get_or_generate_ai_summary(exam, questions, answer_map)

        # Generate domain analysis from knowledge nodes
        domain_analysis = self._build_domain_analysis(exam.id, answers)

        # Spec 18 §測驗結果頁顯示 Bloom 各層次答對率
        bloom_breakdown = self._build_bloom_breakdown(questions, answer_map)

        result = {
            "error": False,
            "exam_id": str(exam.id),
            "score": str(score),
            "pass_status": pass_status,
            "passing_score": str(passing_score),
            "correct_count": exam.correct_count,
            "total_questions": exam.total_questions,
            "time_spent_seconds": time_spent,
            "started_at": exam.started_at.isoformat() if exam.started_at else None,
            "submitted_at": exam.submitted_at.isoformat() if exam.submitted_at else None,
            "user_answers": user_answers,
            "ai_summary": ai_summary,
            "domain_analysis": domain_analysis,
            "bloom_breakdown": bloom_breakdown,
            "questions": [
                {
                    "id": str(q.id),
                    "questionNumber": q.question_number,
                    "content": q.content,
                    "optionA": q.option_a,
                    "optionB": q.option_b,
                    "optionC": q.option_c,
                    "optionD": q.option_d,
                    "correctAnswer": q.correct_answer,
                    "explanation": q.explanation or "",
                }
                for q in questions
            ],
        }

        if comparison:
            result["comparison"] = comparison

        return result

    def _build_bloom_breakdown(self, questions, answer_map) -> list[dict]:
        """Spec 18 §Bloom 各層次答對率 — 統計每個 Bloom 認知層次的正確 / 總數 / 百分比。"""
        bloom_labels = {
            "remember": "記憶", "understand": "理解", "apply": "應用",
            "analyze": "分析", "evaluate": "評估", "create": "創造",
        }
        stats: dict[str, list[int]] = {}
        for q in questions:
            b_raw = getattr(q, 'bloom_category', None)
            b = (b_raw.value if hasattr(b_raw, 'value') else b_raw) or 'remember'
            a = answer_map.get(str(q.id))
            is_correct = 1 if (a and a.is_correct) else 0
            stats.setdefault(b, [0, 0])
            stats[b][0] += is_correct
            stats[b][1] += 1
        # 確保 6 層級都有（即使 0 題）
        ordered = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        result = []
        for b in ordered:
            c, t = stats.get(b, [0, 0])
            result.append({
                "category": b,
                "label": bloom_labels[b],
                "correct": c,
                "total": t,
                "rate": round(c / t * 100) if t > 0 else 0,
            })
        return result

    def _get_or_generate_ai_summary(self, exam, questions, answer_map) -> str:
        """Generate and cache AI analysis summary based on exam performance."""
        if exam.ai_summary:
            return exam.ai_summary

        total = len(questions)
        if total == 0:
            return ""

        correct = sum(
            1 for q in questions
            if answer_map.get(str(q.id)) and answer_map[str(q.id)].is_correct
        )

        # 嘗試用 T-04 LLM 生成考後總評
        ai_summary = self._generate_llm_summary(exam, questions, answer_map, total, correct)
        if ai_summary:
            exam.ai_summary = ai_summary
            self.db.commit()
            return ai_summary

        # Fallback: 規則生成摘要（以下是既有邏輯）
        rate = round(correct / total * 100)

        # Analyze by difficulty
        diff_stats: dict[str, list[int]] = {}
        bloom_stats: dict[str, list[int]] = {}
        for q in questions:
            d = getattr(q, 'difficulty', 'medium') or 'medium'
            b = getattr(q, 'bloom_category', 'remember') or 'remember'
            a = answer_map.get(str(q.id))
            is_correct = 1 if (a and a.is_correct) else 0

            diff_stats.setdefault(d, [0, 0])
            diff_stats[d][0] += is_correct
            diff_stats[d][1] += 1

            bloom_stats.setdefault(b, [0, 0])
            bloom_stats[b][0] += is_correct
            bloom_stats[b][1] += 1

        diff_labels = {"easy": "基礎題", "medium": "中等題", "hard": "進階題"}
        bloom_labels = {
            "remember": "記憶", "understand": "理解", "apply": "應用",
            "analyze": "分析", "evaluate": "評鑑", "create": "創造",
        }

        # Build summary parts
        parts = []

        # Overall performance
        if rate >= 90:
            parts.append(f"整體表現優異，答對率 {rate}%，展現了紮實的知識掌握度。")
        elif rate >= 70:
            parts.append(f"整體表現不錯，答對率 {rate}%，大部分知識點已掌握。")
        elif rate >= 50:
            parts.append(f"答對率 {rate}%，部分知識點需要加強，建議針對錯題進行複習。")
        else:
            parts.append(f"答對率 {rate}%，建議重新複習核心概念，並透過錯題本進行針對性練習。")

        # Difficulty analysis
        weak_diffs = []
        strong_diffs = []
        for d, (c, t) in diff_stats.items():
            r = round(c / t * 100) if t > 0 else 0
            label = diff_labels.get(d, d)
            if r < 50 and t >= 2:
                weak_diffs.append(f"{label}（{r}%）")
            elif r >= 80 and t >= 2:
                strong_diffs.append(f"{label}（{r}%）")

        if weak_diffs:
            parts.append(f"在{', '.join(weak_diffs)}的表現較弱，建議加強練習。")
        if strong_diffs:
            parts.append(f"在{', '.join(strong_diffs)}表現出色，繼續保持！")

        # Bloom taxonomy analysis
        weak_blooms = []
        for b, (c, t) in bloom_stats.items():
            r = round(c / t * 100) if t > 0 else 0
            label = bloom_labels.get(b, b)
            if r < 50 and t >= 2:
                weak_blooms.append(label)

        if weak_blooms:
            parts.append(f"在「{', '.join(weak_blooms)}」層次的題目需要多加練習，建議搭配錯題本深入理解。")

        summary = " ".join(parts)

        # Cache to DB
        exam.ai_summary = summary
        self.db.commit()

        return summary

    def _get_llm(self):
        """取得 llm。"""
        if self._llm is None:
            from app.core.config import get_settings
            settings = get_settings()
            if settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY:
                from app.services.llm_service import LLMService
                self._llm = LLMService(db=self.db)
        return self._llm

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """載入 prompt。"""
        if not self._prompt_svc:
            try:
                from app.services.prompt_template_service import PromptTemplateService
                self._prompt_svc = PromptTemplateService(self.db)
            except Exception:
                return None
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception:
            return None

    def _generate_llm_summary(self, exam, questions, answer_map, total, correct) -> str | None:
        """用 T-04 模板生成 AI 考後總評。"""
        llm = self._get_llm()
        if not llm:
            return None

        import json
        accuracy = round(correct / total * 100) if total > 0 else 0

        # 取得科目名稱
        subject_name = ""
        if exam.subject_id:
            from app.models.subject import Subject
            subject = self.db.query(Subject).filter_by(id=exam.subject_id).first()
            subject_name = subject.name if subject else ""

        # 計算各考點表現（從 domain_analysis）
        node_perf = []
        node_answers = {}
        for a in [answer_map[k] for k in answer_map]:
            q = next((q for q in questions if str(q.id) == str(a.question_id)), None)
            if q and q.node_id:
                nid = str(q.node_id)
                node_answers.setdefault(nid, {"correct": 0, "total": 0})
                node_answers[nid]["total"] += 1
                if a.is_correct:
                    node_answers[nid]["correct"] += 1

        weak_nodes = []
        for nid, stats in node_answers.items():
            node = self.db.query(KnowledgeNode).filter_by(id=uuid.UUID(nid)).first()
            name = node.name if node else "未分類"
            rate = round(stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            node_perf.append({"point": name, "correct": stats["correct"], "total": stats["total"], "rate": rate})
            if rate < 60:
                weak_nodes.append({"name": name, "mastery_rate": rate})

        # Determine summary level instruction by plan
        user = self.db.query(User).filter_by(id=exam.user_id).first() if exam.user_id else None
        plan = user.subscription_plan.value if user and user.subscription_plan else "FREE"

        level_instructions = {
            "FREE": "列出前 3 個最弱考點，每個一句話點評。不提供複習計劃。全文上限 150 字。",
            "PRO": "列出前 3 個最弱考點，每個一句話點評。不提供複習計劃。全文上限 150 字。",
            "PRO_PLUS": "分析所有弱點考點：每個弱點一句話說明問題所在。最後給出 3 條具體複習行動建議（每條一句話）。全文上限 300 字。",
            "ULTRA": "分析所有弱點考點：每個弱點一句話說明。若有歷史趨勢用「上次 X%→這次 Y%」簡述。3 條個人化複習建議。3 個考前衝刺重點關鍵字。全文上限 400 字。",
        }
        summary_instruction = level_instructions.get(plan, level_instructions["FREE"])

        db_prompt = self._load_prompt("post_exam_summary", {
            "summary_level_instruction": summary_instruction,
            "subject_name": subject_name,
            "total_questions": str(total),
            "correct_count": str(correct),
            "accuracy": str(accuracy),
            "point_performance": json.dumps(node_perf, ensure_ascii=False),
            "weak_nodes": json.dumps(weak_nodes, ensure_ascii=False),
        })

        _FALLBACK_SYSTEM = (
            "你是學習成效分析師，為考生撰寫精簡考後總評。"
            "開頭一句話總結表現，不要寒暄自我介紹。"
            "用純文字段落，用「▸」作項目符號，不用 Markdown 標題/表格/分隔線。"
            "絕不使用「不及格」「失敗」「退步」等負面詞彙。"
            "不要重複列出滿分強項，一句帶過。不要加結尾鼓勵套話。"
        )

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = _FALLBACK_SYSTEM + "\n" + summary_instruction
            user_prompt = (
                f"科目：{subject_name}\n總題數：{total}，答對：{correct}，答對率：{accuracy}%\n\n"
                f"各考點表現：\n{json.dumps(node_perf, ensure_ascii=False)}\n\n"
                f"弱點節點：\n{json.dumps(weak_nodes, ensure_ascii=False)}\n\n"
                f"請直接輸出總評，不要加標題。"
            )

        try:
            max_tokens_map = {"PRO": 512, "PRO_PLUS": 768, "ULTRA": 1024}
            max_tokens = max_tokens_map.get(plan, 512)
            result = llm.generate(system_prompt, user_prompt, model="gemini-flash", max_tokens=max_tokens)
            return result if result and len(result.strip()) > 30 else None
        except Exception:
            import logging
            logging.getLogger(__name__).warning("T-04 post exam summary LLM failed")
            return None

    def _build_domain_analysis(self, exam_id, answers) -> list:
        """全維度知識節點掌握度分析。

        四維度加權計算 mastery_score：
        - SM-2 累計掌握度 (40%)：跨考試 EMA + 記憶衰退
        - Bloom 認知層次覆蓋 (20%)：已答對的 Bloom 層次數 / 6
        - 信心度校準 (25%)：confident_correct / (confident_correct + confident_incorrect)
        - 本次考試答對率 (15%)：correct / total
        """
        if not answers:
            return []

        from app.models.node_mastery import NodeMastery
        from app.services.sm2_engine import SM2Engine, TopicState

        sm2 = SM2Engine()
        exam_obj = self.db.query(Exam).filter_by(id=exam_id).first()
        user_id = exam_obj.user_id if exam_obj else None

        # Step 1: 按知識節點分組答案
        node_answers: dict[str, list] = {}  # node_id → [(answer, question)]
        for a in answers:
            q = self.db.query(Question).filter_by(id=a.question_id).first()
            if not q or not q.node_id:
                node_answers.setdefault("__unlinked__", []).append((a, q))
                continue
            nid = str(q.node_id)
            node_answers.setdefault(nid, []).append((a, q))

        # 如果所有題目都沒有 node_id，fallback 到「全部題目」
        if not node_answers or (len(node_answers) == 1 and "__unlinked__" in node_answers):
            correct_count = sum(1 for a in answers if a.is_correct)
            return [{
                "domain": "全部題目",
                "correct": correct_count,
                "total": len(answers),
                "percentage": round(correct_count / len(answers) * 100) if answers else 0,
            }]

        # Step 2: 為每個節點計算四維度分數
        W_SM2 = 0.40
        W_BLOOM = 0.20
        W_CONFIDENCE = 0.25
        W_EXAM = 0.15

        domain_list = []
        for nid, aq_pairs in node_answers.items():
            if nid == "__unlinked__":
                continue

            node = self.db.query(KnowledgeNode).filter_by(id=uuid.UUID(nid)).first()
            node_name = node.name if node else "未分類"

            # (a) 本次考試答對率
            correct = sum(1 for a, q in aq_pairs if a.is_correct)
            total = len(aq_pairs)
            exam_accuracy = correct / total if total > 0 else 0

            # (b) SM-2 累計掌握度（含記憶衰退）
            effective = 0.0
            decay_status = "unseen"
            sm2_detail = {"base_mastery": 0, "retention": 1.0, "effective": 0}
            if user_id:
                nm = self.db.query(NodeMastery).filter_by(
                    user_id=user_id, node_id=uuid.UUID(nid)
                ).first()
                if nm and nm.base_mastery and nm.base_mastery > 0:
                    state = TopicState(
                        base_mastery=nm.base_mastery,
                        ease_factor=nm.ease_factor or SM2Engine.DEFAULT_EASE_FACTOR,
                        last_tested_at=nm.last_tested_at,
                        next_review_at=nm.next_review_at,
                        status=nm.status or "UNSEEN",
                    )
                    effective = sm2.calculate_effective_progress(state)
                    decay_status = sm2.get_decay_status(state)
                    retention = sm2.calculate_retention(state)
                    sm2_detail = {
                        "base_mastery": round(nm.base_mastery, 3),
                        "retention": round(retention, 3),
                        "effective": round(effective, 3),
                    }

            # (c) Bloom 認知層次覆蓋度
            bloom_correct = set()
            for a, q in aq_pairs:
                if a.is_correct and q and q.bloom_category:
                    cat = q.bloom_category.value if hasattr(q.bloom_category, 'value') else q.bloom_category
                    bloom_correct.add(cat)
            bloom_coverage = len(bloom_correct) / 6.0
            bloom_detail = {"covered": sorted(bloom_correct), "total": 6}

            # (d) 信心度校準分數
            confident_correct = 0
            confident_incorrect = 0
            for a, q in aq_pairs:
                conf = getattr(a, 'confidence', None) or 'somewhat'
                if conf == 'confident':
                    if a.is_correct:
                        confident_correct += 1
                    else:
                        confident_incorrect += 1
            conf_total = confident_correct + confident_incorrect
            calibration_rate = confident_correct / conf_total if conf_total > 0 else exam_accuracy  # fallback
            blind_spots = confident_incorrect
            conf_detail = {"calibration_rate": round(calibration_rate, 3), "blind_spots": blind_spots}

            # 加權計算 mastery_score
            mastery_score = (
                W_SM2 * effective +
                W_BLOOM * bloom_coverage +
                W_CONFIDENCE * calibration_rate +
                W_EXAM * exam_accuracy
            )
            mastery_pct = round(mastery_score * 100)

            domain_list.append({
                "domain": node_name,
                "correct": correct,
                "total": total,
                "percentage": mastery_pct,
                "exam_accuracy": round(exam_accuracy * 100),
                "mastery": round(effective * 100),
                "bloom_coverage": round(bloom_coverage * 100),
                "confidence_calibration": round(calibration_rate * 100),
                "decay_status": decay_status,
                "dimensions": {
                    "sm2": sm2_detail,
                    "bloom": bloom_detail,
                    "confidence": conf_detail,
                },
            })

        domain_list.sort(key=lambda x: x["percentage"])
        return domain_list

    def _get_comparison(self, current_exam: Exam, user_id: uuid.UUID) -> str | None:
        # Find previous submitted exam (before current one)
        """取得 comparison。"""
        previous = self.db.query(Exam).filter(
            Exam.user_id == user_id,
            Exam.status == ExamStatus.SUBMITTED,
            Exam.id != current_exam.id,
            Exam.submitted_at < current_exam.submitted_at,
        ).order_by(Exam.submitted_at.desc()).first()

        if not previous or previous.score is None:
            return None

        diff = (current_exam.score or 0) - (previous.score or 0)
        if diff > 0:
            return f"+{diff} 分進步"
        elif diff < 0:
            return f"{diff} 分退步"
        else:
            return "持平"

    def get_node_analysis(self, exam_id: str, user_id: str) -> dict:
        """取得 node analysis。"""
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗結果的權限"}

        # Aggregate by knowledge node
        results = (
            self.db.query(
                KnowledgeNode.name,
                func.sum(func.cast(Answer.is_correct, SAInteger)).label("correct"),
                func.count(Answer.id).label("total"),
            )
            .join(Question, Question.id == Answer.question_id)
            .join(KnowledgeNode, KnowledgeNode.id == Question.node_id)
            .filter(Answer.exam_id == exam.id)
            .group_by(KnowledgeNode.name)
            .all()
        )

        nodes = []
        for name, correct, total in results:
            rate = round(correct / total * 100) if total > 0 else 0
            color = "綠色" if rate >= 60 else "紅色"
            nodes.append({
                "name": name,
                "correct": correct,
                "total": total,
                "accuracy_rate": f"{rate}%",
                "color": color,
            })

        return {"error": False, "nodes": nodes}
