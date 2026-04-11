"""
TiTi 出題品質驗證模組

Layer 1: 匯入時品質閘門（validate_question）
Layer 2: Cross-LLM 交叉驗證（validate_with_cross_llm）

依據 question-quality-assurance.md 規格書。
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Layer 1：匯入時品質閘門 ──────────────────────────────

@dataclass
class ValidationResult:
    status: str = "ok"        # ok / review / replace / rejected
    issues: list = field(default_factory=list)
    validation_model: Optional[str] = None
    cross_llm_answer: Optional[str] = None
    cross_llm_confidence: Optional[str] = None


def validate_question(q: dict) -> ValidationResult:
    """匯入時品質閘門 — 5 項自動檢查。

    Returns ValidationResult with status:
      ok       — 通過全部 5 項
      review   — 1-2 項不通過，匯入但標記待審
      rejected — 答案無效或嚴重問題，不匯入
    """
    issues = []

    # 1. 題幹完整性
    content = q.get("content", "")
    if len(content) < 10:
        issues.append("題幹過短（<10字），可能被截斷")
    if content and re.match(r'^[數列者項的個為]', content):
        issues.append("題幹開頭疑似截斷碎片（中文）")
    if content and re.match(r'^[A-Za-z()\[\]）】，,。；;]', content):
        issues.append("題幹以英文/標點開頭，疑似跨頁截斷碎片")

    # 2. 四選項完整
    for opt_key in ["option_a", "option_b", "option_c", "option_d"]:
        opt = q.get(opt_key, "")
        if not opt or len(opt) < 2:
            issues.append(f"{opt_key} 為空或過短")
        if len(opt) > 200:
            issues.append(f"{opt_key} 過長（>200字），可能溢出")

    # 3. 答案有效性
    answer = q.get("correct_answer", "")
    if answer not in ("A", "B", "C", "D"):
        issues.append(f"答案格式無效: '{answer}'")
        return ValidationResult(status="rejected", issues=issues)

    # 4. 選項不重複
    opts = [q.get(f"option_{x}", "") for x in "abcd"]
    non_empty = [o for o in opts if o and len(o) > 2]
    if len(set(non_empty)) < len(non_empty):
        issues.append("有重複選項")

    # 5. 頁首殘留偵測
    pollution_keywords = ["頁，共", "公告試題", "答案 題 目", "試題公告日期", "請填應試號碼"]
    for kw in pollution_keywords:
        if kw in content:
            issues.append(f"題幹含頁首污染: '{kw}'")

    if not issues:
        return ValidationResult(status="ok")
    elif len(issues) <= 2:
        return ValidationResult(status="review", issues=issues)
    else:
        return ValidationResult(status="rejected", issues=issues)


# ── Layer 2：Cross-LLM 交叉驗證 ──────────────────────────

_FALLBACK_VALIDATION_PROMPT = """你是考題品質審查員。你的工作是獨立判斷以下選擇題的正確性。
不要假設提供的答案是對的——你必須自己推理出正確答案。

只回傳純 JSON，不要 markdown code block：
{"your_answer": "A/B/C/D", "confidence": "high/medium/low", "reasoning": "簡短推理", "issues": ["問題1"]}"""

# Legacy alias
VALIDATION_SYSTEM_PROMPT = _FALLBACK_VALIDATION_PROMPT


def _load_validation_prompt(db=None) -> str:
    """嘗試從 DB 載入 cross_llm_validation 模板，fallback 到 hardcoded。"""
    if not db:
        return _FALLBACK_VALIDATION_PROMPT
    try:
        from app.services.prompt_template_service import PromptTemplateService
        svc = PromptTemplateService(db)
        result = svc.get_prompt_for_ai("cross_llm_validation")
        if not result.get("error") and result.get("system_prompt"):
            return result["system_prompt"]
    except Exception:
        pass
    return _FALLBACK_VALIDATION_PROMPT


def build_validation_prompt(q: dict) -> str:
    """建構驗證 Prompt"""
    return (
        f"【題目】{q.get('content', '')}\n"
        f"(A) {q.get('option_a', '')}\n"
        f"(B) {q.get('option_b', '')}\n"
        f"(C) {q.get('option_c', '')}\n"
        f"(D) {q.get('option_d', '')}\n\n"
        f"請獨立判斷正確答案，回傳 JSON。"
    )


def get_validator_model_name(generation_model: str) -> str:
    """選擇驗證模型（不同於出題模型，使用低階模型控制成本）。

    規則：不同廠商 + 低階模型。
    """
    gen = generation_model.lower()
    if "claude" in gen or "anthropic" in gen:
        return "gemini-flash"       # Claude 出題 → Gemini Flash 驗證
    elif "gemini" in gen or "google" in gen:
        return "claude-haiku"       # Gemini 出題 → Claude Haiku 驗證
    elif "gpt" in gen or "openai" in gen:
        return "gemini-flash"       # GPT 出題 → Gemini Flash 驗證
    else:
        return "gemini-flash"       # 預設用最便宜的


def validate_with_cross_llm(
    question: dict,
    generated_answer: str,
    llm_service,
    generation_model: str = "claude",
) -> ValidationResult:
    """用不同 LLM 交叉驗證 AI 生成的題目。

    Args:
        question: 題目 dict（content, option_a-d）
        generated_answer: 出題模型標記的正確答案（A/B/C/D）
        llm_service: LLMService 實例
        generation_model: 出題時用的模型名稱

    Returns:
        ValidationResult with cross-LLM validation status
    """
    validator_model = get_validator_model_name(generation_model)

    try:
        user_prompt = build_validation_prompt(question)

        # 使用低階模型驗證
        raw = llm_service.generate(
            VALIDATION_SYSTEM_PROMPT,
            user_prompt,
            model=validator_model,
            max_tokens=256,
        )

        result = _parse_validation_response(raw)
        if not result:
            return ValidationResult(
                status="review",
                issues=["Cross-LLM 驗證回應解析失敗"],
                validation_model=validator_model,
            )

        validator_answer = result.get("your_answer", "").upper()
        confidence = result.get("confidence", "low")
        issues = result.get("issues", [])

        # 判定結果
        if generated_answer == validator_answer and not issues:
            return ValidationResult(
                status="ok",
                validation_model=validator_model,
                cross_llm_answer=validator_answer,
                cross_llm_confidence=confidence,
            )

        if generated_answer != validator_answer:
            if confidence == "high":
                return ValidationResult(
                    status="replace",
                    issues=[f"Cross-LLM 不同意答案: 出題={generated_answer}, 驗證={validator_answer} (高信心)"],
                    validation_model=validator_model,
                    cross_llm_answer=validator_answer,
                    cross_llm_confidence=confidence,
                )
            else:
                return ValidationResult(
                    status="review",
                    issues=[f"Cross-LLM 答案不一致: 出題={generated_answer}, 驗證={validator_answer} ({confidence}信心)"],
                    validation_model=validator_model,
                    cross_llm_answer=validator_answer,
                    cross_llm_confidence=confidence,
                )

        if issues:
            return ValidationResult(
                status="review",
                issues=issues,
                validation_model=validator_model,
                cross_llm_answer=validator_answer,
                cross_llm_confidence=confidence,
            )

        return ValidationResult(
            status="ok",
            validation_model=validator_model,
            cross_llm_answer=validator_answer,
            cross_llm_confidence=confidence,
        )

    except Exception as e:
        logger.warning("Cross-LLM validation failed: %s", e)
        return ValidationResult(
            status="review",
            issues=[f"Cross-LLM 驗證異常: {str(e)[:100]}"],
            validation_model=validator_model,
        )


def _parse_validation_response(raw) -> Optional[dict]:
    """解析 LLM 回傳的 JSON"""
    import json
    if not raw:
        return None

    text = raw if isinstance(raw, str) else str(raw)
    # Strip markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


# ── 抽換邏輯 ──────────────────────────────

def handle_validation_result(
    question: dict,
    result: ValidationResult,
    replacement_pool: list,
    used_ids: set,
) -> dict:
    """根據驗證結果處理題目：ok 直接用，replace 抽換，review 標記。

    Args:
        question: 原始題目
        result: 驗證結果
        replacement_pool: 可用的替換題目列表
        used_ids: 已使用的題目 ID（避免重複）

    Returns:
        最終使用的題目 dict（可能是原題或替換題）
    """
    question["quality_flag"] = result.status
    question["validation_model"] = result.validation_model
    question["validation_issues"] = result.issues

    if result.status == "replace":
        # 從替換池找一題
        for candidate in replacement_pool:
            cid = candidate.get("id") or candidate.get("content", "")[:30]
            if cid not in used_ids:
                used_ids.add(cid)
                candidate["quality_flag"] = "ok"
                candidate["reliability"] = candidate.get("reliability", "green")
                logger.info("Replaced question (Cross-LLM reject) with pool candidate")
                return candidate

        # 無可用替換 → 降級為 review（仍出題，但標記）
        question["quality_flag"] = "review"
        logger.warning("No replacement available, downgrading to review")
        return question

    return question
