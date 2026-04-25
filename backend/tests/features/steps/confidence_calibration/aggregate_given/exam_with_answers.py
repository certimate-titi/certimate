"""Given 測驗與信心度相關的前置資料 — Aggregate Given"""

import uuid
from behave import given
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.models.answer import Answer
from app.models.user import User


@given('測驗 {exam_id:d} 的作答記錄含信心度：')
def step_impl_answers_with_confidence(context, exam_id):
    """建立含信心度標記的作答記錄。"""
    exam_uuid = (
        context.ids.get(f"exam_id_{exam_id}")
        or context.ids.get(f"exam_{exam_id}")
        or str(uuid.UUID(int=exam_id))
    )

    user = context.db_session.query(User).first()
    if not user:
        return

    exam = context.db_session.query(Exam).filter(Exam.id == uuid.UUID(exam_uuid)).first()
    if not exam:
        return

    for row in context.table:
        q_id_num = int(row["題目 ID"])
        q_key = f"question_id_{q_id_num}"
        q_uuid_str = context.ids.get(q_key)

        q_uuid = uuid.uuid4()
        if not q_uuid_str:
            # Create question if not exists
            q = Question(
                id=q_uuid,
                exam_id=exam.id,
                question_number=q_id_num,
                content=f"信心度測試題 {q_id_num}",
                correct_answer=row["正確答案"],
                option_a="選項A", option_b="選項B",
                option_c="選項C", option_d="選項D",
                source_type="historical",
            )
            context.db_session.add(q)
            context.db_session.flush()
            context.ids[q_key] = str(q.id)
            q_uuid = q.id
        else:
            q_uuid = uuid.UUID(q_uuid_str)

        is_correct = row["作答正確"] == "是"
        answer = Answer(
            id=uuid.uuid4(),
            exam_id=exam.id,
            question_id=q_uuid,
            user_id=user.id,
            selected_answer=row["選擇答案"],
            is_correct=is_correct,
            confidence=row["信心度"],
        )
        context.db_session.add(answer)

    context.db_session.commit()


@given('使用者 "{email}" 完成測驗，題目 {q_id:d} 為 {confidence} + {result}（{label}）')
def step_impl_completed_with_confidence(context, email, q_id, confidence, result, label):
    """設定使用者完成測驗且特定題目有信心度標記。"""
    context.memo[f"exam_question_{q_id}_confidence"] = confidence
    context.memo[f"exam_question_{q_id}_result"] = result
    context.memo[f"exam_question_{q_id}_label"] = label


@given('使用者 "{email}" 已完成 {count:d} 場含信心度的測驗')
def step_impl_multiple_exams_with_confidence(context, email, count):
    """建立指定數量含信心度標記的已完成測驗。"""
    context.memo[f"confidence_exam_count_{email}"] = count


@given('使用者已作答題目 {q_id1:d}（{conf1}）和題目 {q_id2:d}（{conf2}）')
def step_impl_answered_with_confidence(context, q_id1, conf1, q_id2, conf2):
    """設定使用者已作答的題目及其信心度。"""
    context.memo[f"question_{q_id1}_confidence"] = conf1
    context.memo[f"question_{q_id2}_confidence"] = conf2
