"""Given 使用者的 Firebase Custom Claims — Aggregate Given"""

import json

from behave import given


@given('使用者 "{email}" 的 Firebase Custom Claims 為 {claims_json}')
def step_impl(context, email, claims_json):
    claims = json.loads(claims_json)
    if "firebase_claims" not in context.memo:
        context.memo["firebase_claims"] = {}
    context.memo["firebase_claims"][email] = claims
