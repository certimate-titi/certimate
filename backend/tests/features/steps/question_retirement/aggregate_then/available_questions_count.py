"""Then available_questions 計數隔離驗證 — Aggregate Then"""

from behave import then
from app.repositories.subject_repository import SubjectRepository


@then('科目 "{subject_name}" 的 available_questions 應為 {count:d}')
def step_impl(context, subject_name, count):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"

    # 驗證 API 回應中的 available_questions
    data = response.json()
    subjects = data if isinstance(data, list) else [data]

    found = False
    for s in subjects:
        if s.get("name") == subject_name or s.get("subject_name") == subject_name:
            assert s.get("available_questions") == count, \
                f"科目 '{subject_name}' available_questions 預期 {count}，實際 {s.get('available_questions')}"
            found = True
            break

    if not found:
        # 從 DB 直接驗證
        db = context.db_session
        subject_repo = SubjectRepository(db)
        subject = subject_repo.find_by_name(subject_name)
        assert subject is not None, f"科目 '{subject_name}' 不存在"
        assert subject.available_questions == count, \
            f"科目 '{subject_name}' available_questions 預期 {count}，實際 {subject.available_questions}"
