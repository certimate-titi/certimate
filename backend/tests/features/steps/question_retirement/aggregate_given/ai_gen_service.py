"""Given AI 出題服務生成題目 — Aggregate Given"""

from behave import given
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 對科目 "{subject_name}" 發起 AI 出題')
def step_initiate_ai_gen(context, email, subject_name):
    user_id = context.ids[email]
    repo = SubjectRepository(context.db_session)
    subject = repo.find_by_name(subject_name)
    context.memo["ai_gen_user_id"] = user_id
    context.memo["ai_gen_subject_id"] = str(subject.id)
    context.memo["ai_gen_subject_name"] = subject_name


@given('管理員匯入一批考古題至科目 "{subject_name}"')
def step_admin_import(context, subject_name):
    repo = SubjectRepository(context.db_session)
    subject = repo.find_by_name(subject_name)
    context.memo["import_subject_id"] = str(subject.id)
    context.memo["import_subject_name"] = subject_name


@given('AI 出題服務生成以下題目：')
def step_ai_gen_with_table(context):
    questions_data = []
    for row in context.table:
        q = {
            "content": row["題幹"],
            "option_a": row["選項A"].strip() if row["選項A"].strip() else None,
            "option_b": row["選項B"].strip() if row["選項B"].strip() else None,
            "option_c": row["選項C"].strip() if row["選項C"].strip() else None,
            "option_d": row["選項D"].strip() if row["選項D"].strip() else None,
            "correct_answer": row["正確答案"],
        }
        questions_data.append(q)
    context.memo["ai_gen_questions_data"] = questions_data


@given('使用者 "{email}" 選擇「再次報考」同科目')
def step_retake(context, email):
    context.memo["retake_email"] = email
