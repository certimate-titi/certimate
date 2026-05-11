"""When step actions — Feature 43 BDD."""

import logging

from behave import when, use_step_matcher


def _auth_get(context, path):
    """共用：以 alice JWT 發 GET。"""
    from tests.features.steps.sm2.commands.actions import (
        _resolve_user_id, _auth_headers,
    )
    user_id = _resolve_user_id(context)
    # 若呼叫 /concept-center 但無 scaffold，自動建幾筆「機器學習」資料避免空 result
    if "/concept-center" in path and "concept_seeded" not in context.memo:
        from tests.features.steps.semantic_search.aggregate_given.setup import (
            step_alice_has_many_scaffolds,
        )
        try:
            step_alice_has_many_scaffolds(context, "5", "機器學習")
        except Exception:
            pass
        context.memo["concept_seeded"] = True
    # 順便捕捉 logger 輸出（給 fallback log 斷言）
    captured = []

    class _H(logging.Handler):
        def emit(self, record):
            try:
                captured.append(record.getMessage())
            except Exception:
                captured.append(str(record.msg))

    # 直接 monkeypatch concept-center logger.warning（與 pitfall pattern 一致）
    cc_logger = logging.getLogger("concept-center")
    real_warning = cc_logger.warning

    def _cap_warning(msg, *args, **kwargs):
        try:
            captured.append(msg % args if args else msg)
        except Exception:
            captured.append(str(msg))
        return real_warning(msg, *args, **kwargs)

    cc_logger.warning = _cap_warning
    import time as _time
    t0 = _time.time()
    try:
        resp = context.api_client.get(path, headers=_auth_headers(context, user_id))
    finally:
        context.memo["concept_latency_ms"] = (_time.time() - t0) * 1000
        cc_logger.warning = real_warning
    context.last_response = resp
    context.memo["parse_logs"] = captured
    # 清掉 voyage mock
    for fn in getattr(context, "_cleanups", []):
        try:
            fn()
        except Exception:
            pass
    context._cleanups = []


@when('GET /dashboard/today')
def step_get_today_short(context):
    _auth_get(context, "/api/v1/dashboard/today")


use_step_matcher("re")


@when(r'GET /concept-center\?q=(?P<q>[^&\s]+)(?!&)')
def step_get_concept(context, q):
    _auth_get(context, f"/api/v1/concept-center?q={q}")


@when(r'GET /concept-center\?q=(?P<q>[^&\s]+)&semantic=(?P<flag>\w+)')
def step_get_concept_with_flag(context, q, flag):
    _auth_get(context, f"/api/v1/concept-center?q={q}&semantic={flag}")


use_step_matcher("parse")
