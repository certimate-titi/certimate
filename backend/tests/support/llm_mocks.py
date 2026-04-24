"""BDD LLM mock infrastructure.

提供確定性的 LLM 回應以支援 AI 生成 pipeline 測試。
使用方式：在 scenario 加 `@llm-mock` tag，environment.py 會自動套用。

Prompt 攔截後存在 `context.memo["captured_prompts"]`，格式：
    [{"stage": "stage1"|"stage2"|"stage3", "system": str, "user": str, "context": str|None}, ...]

回應根據 prompt 內容啟發式判斷 stage：
- system 含「考點分析」/「出題規劃」→ stage1 → exam_points JSON
- user 含「出 N 題選擇題」→ stage2 → questions JSON
- system 含「干擾項」/「設計高誘答性」→ stage3 → questions with options
"""

from __future__ import annotations

import json
import re


class MockLLMService:
    """攔截 AiGenerationService._llm 的呼叫，回傳確定性 JSON。"""

    def __init__(self, context_ref):
        self._context_ref = context_ref
        self._ensure_capture_list()

    def _ensure_capture_list(self):
        if "captured_prompts" not in self._context_ref.memo:
            self._context_ref.memo["captured_prompts"] = []

    def _capture(self, stage: str, system: str, user: str, ctx: str | None = None):
        self._ensure_capture_list()
        self._context_ref.memo["captured_prompts"].append({
            "stage": stage,
            "system": system or "",
            "user": user or "",
            "context": ctx,
        })

    @staticmethod
    def _detect_stage(system: str, user: str) -> str:
        blob = (system or "") + "\n" + (user or "")
        if "干擾項" in blob or "distractor" in blob.lower():
            return "stage3"
        if "出題規劃" in blob or "exam_points" in blob or "配方" in blob:
            return "stage1"
        if "選擇題" in blob or "questions" in blob.lower() and "options" in blob.lower():
            return "stage2"
        if "考題" in blob and "選項" in blob:
            return "stage2"
        return "stage1"

    def _build_response(self, stage: str, system: str, user: str) -> str:
        if stage == "stage1":
            # 從 user prompt 抽 total_questions，若有考古題統計則做 Bloom allocation
            m = re.search(r"總數[:：]\s*(\d+)", user)
            total = int(m.group(1)) if m else 10
            names = re.findall(r'"name"\s*:\s*"([^"]+)"', user)
            if not names:
                names = ["EC2 運算服務", "S3 儲存服務"]
            names = names[:max(1, len(names))]
            per = max(1, total // len(names))
            points = []
            for i, n in enumerate(names):
                cnt = per if i < len(names) - 1 else total - per * (len(names) - 1)
                points.append({
                    "name": n,
                    "ratio": round(100 / len(names)),
                    "question_count": cnt,
                    "bloom_allocation": {
                        "remember": max(0, round(cnt * 0.36)),
                        "understand": max(0, round(cnt * 0.28)),
                        "apply": max(0, round(cnt * 0.20)),
                        "analyze": max(0, round(cnt * 0.10)),
                        "evaluate": max(0, round(cnt * 0.04)),
                        "create": max(0, round(cnt * 0.02)),
                    },
                    "difficulty_map": {"easy": 3, "medium": 5, "hard": 2},
                })
            return json.dumps({"exam_points": points, "source": "historical"})

        if stage == "stage2":
            m = re.search(r"出\s*(\d+)\s*題", user)
            n = int(m.group(1)) if m else 3
            # 跨批次保持全域索引，讓 Easy:30% Medium:50% Hard:20% 可被驗證
            mem = self._context_ref.memo
            idx = mem.get("_stage2_global_idx", 0)
            # 題序列：前 3 題 easy，接 5 題 medium，末 2 題 hard（共 10 題一循環）
            seq = ["easy"] * 3 + ["medium"] * 5 + ["hard"] * 2
            qs = []
            for i in range(n):
                diff = seq[(idx + i) % len(seq)]
                qs.append({
                    "question_text": f"Mock Stage2 Q{idx + i + 1}",
                    "options": {"A": "A opt", "B": "B opt", "C": "C opt", "D": "D opt"},
                    "correct_answer": "A",
                    "explanation": "mock 解析",
                    "difficulty": diff,
                    "exam_point": "EC2 運算服務",
                })
            mem["_stage2_global_idx"] = idx + n
            return json.dumps({"questions": qs})

        # stage3 — 從 user prompt 抽取考題數
        m = re.search(r"(\d+)\s*道考題", user)
        n = int(m.group(1)) if m else 3
        qs = []
        labels = ["A", "B", "C", "D"]
        for i in range(n):
            correct_idx = i % 4  # 隨機分布：循環 0/1/2/3
            options = ["干擾 1", "干擾 2", "干擾 3"]
            options.insert(correct_idx, "正確")
            reasons = {}
            for j, lab in enumerate(labels):
                if j != correct_idx:
                    reasons[lab] = f"表面合理但本質錯誤（誘答 {j}）"
            qs.append({
                "question_text": f"Mock Stage3 Q{i+1}",
                "options": options,
                "correct_index": correct_idx,
                "correct_answer": labels[correct_idx],
                "explanation": "詳解：略",
                "distractor_reasons": reasons,
                "difficulty": ["easy", "medium", "hard"][i % 3],
                "exam_point": "EC2 運算服務",
            })
        return json.dumps({"questions": qs})

    # ---- AiGenerationService 呼叫的 API ----

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        plan: str = "FREE",
        task_type: str = "basic",
        max_tokens: int = 4096,
    ) -> str:
        stage = self._detect_stage(system_prompt, user_prompt)
        self._capture(stage, system_prompt, user_prompt)
        return self._build_response(stage, system_prompt, user_prompt)

    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        stage = self._detect_stage(system_prompt, user_prompt)
        self._capture(stage, system_prompt, user_prompt, context)
        return self._build_response(stage, system_prompt, user_prompt)

    def generate_json(self, *args, **kwargs):
        raw = self.generate(*args, **kwargs)
        return json.loads(raw)


def install_llm_mock(context) -> None:
    """在 AiGenerationService 中替換 _llm 為 MockLLMService。

    同時強制 _rag_enabled=True 讓 stage2/3 走 _stage2_claude 路徑。
    """
    from app.services import ai_generation_service as mod

    original_init = mod.AiGenerationService.__init__

    def patched_init(self, db):
        original_init(self, db)
        self._rag_enabled = True
        self._llm = MockLLMService(context)

    mod.AiGenerationService.__init__ = patched_init
    context.memo["_ai_gen_init_original"] = original_init


def uninstall_llm_mock(context) -> None:
    original = context.memo.get("_ai_gen_init_original") if hasattr(context, "memo") else None
    if original:
        from app.services import ai_generation_service as mod
        mod.AiGenerationService.__init__ = original
