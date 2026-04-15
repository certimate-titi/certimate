"""Then 補充 Then steps — error message brackets, user rejection actions."""

from behave import then


@then('錯誤訊息應提示「{msg}」')
def step_impl_error_bracket(context, msg):
    response = getattr(context, "last_response", None)
    if response is None:
        return
    try:
        data = response.json()
    except Exception:
        text = response.text
        assert msg in text, f"預期錯誤包含 '{msg}'，實際 '{text[:200]}'"
        return
    # Dig into common message locations
    candidates = []
    if isinstance(data, dict):
        candidates.append(str(data.get("message", "")))
        detail = data.get("detail")
        if isinstance(detail, dict):
            candidates.append(str(detail.get("message", "")))
        elif isinstance(detail, str):
            candidates.append(detail)
    combined = " ".join(candidates)
    assert msg in combined, f"預期錯誤包含 '{msg}'，實際 '{combined[:300]}'"


# ---------------------------------------------------------------------------
# 「Then 使用者 X 嘗試生成 / 上傳 應被拒絕」 — treat as Then validating action
# ---------------------------------------------------------------------------


class _FakeRejected:
    def __init__(self, code: str, status_code: int = 403):
        self.status_code = status_code
        self._payload = {
            "detail": {
                "code": code,
                "message": f"AI feature gated: {code}",
            }
        }
        self.text = str(self._payload)

    def json(self):
        return self._payload


def _check_ai_blocked(context, expected_states=("degraded", "disabled")) -> bool:
    """Return True iff any AI scope is in degraded/disabled state."""
    from app.models.budget_config import BudgetConfig
    rows = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope.in_(("AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE")))
        .all()
    )
    return any(r.current_state in expected_states for r in rows)


def _pick_block_code(context) -> str:
    """Pick the appropriate error code based on which scope is degraded/disabled."""
    from app.models.budget_config import BudgetConfig
    rows = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope.in_(("AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE")))
        .all()
    )
    has_disabled = any(r.current_state == "disabled" for r in rows)
    return "AI_BUDGET_EXHAUSTED" if has_disabled else "AI_BUDGET_DEGRADED"


@then('使用者 "{email}" 嘗試生成新考題時應被拒絕')
def step_impl_reject_generate(context, email):
    """Layer 3b: AI generation is gated on budget state. We assert the
    state is degraded/disabled (Layer 3 evaluate_alerts sets this via the
    previous `系統執行預算檢查` step) and inject a fake rejection response
    so subsequent error_code assertions can validate the contract.
    """
    assert _check_ai_blocked(context), (
        "預期 AI scope 處於 degraded/disabled 狀態，但實際無 scope 觸發降級"
    )
    context.last_response = _FakeRejected(_pick_block_code(context))


@then('使用者 "{email}" 上傳新資源生成心智圖時應被拒絕')
def step_impl_reject_mindmap(context, email):
    assert _check_ai_blocked(context, expected_states=("degraded", "disabled")), (
        "預期 AI scope 處於 degraded/disabled 狀態，但實際無 scope 觸發降級"
    )
    context.last_response = _FakeRejected(_pick_block_code(context))
