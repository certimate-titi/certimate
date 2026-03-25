from behave import given


@given('該使用者尚未建立任何學習歷程')
def step_impl(context):
    # 新使用者預設沒有學習歷程，此步驟為宣告性質
    # E2E 測試中，確認 onboarding_completed = False 即可
    # 不需要額外操作（Background 建立的使用者預設無學習歷程）
    pass
