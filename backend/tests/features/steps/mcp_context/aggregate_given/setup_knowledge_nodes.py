"""
設置知識節點和用戶錯誤記錄
"""

from behave import given
import uuid
from datetime import datetime, timezone, timedelta
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.subject import Subject
from app.models.answer import Answer
from app.models.exam import Exam


@given('用戶 "{email}" 有知識節點 "{topic}" 及關聯 {question_count:d} 道題目')
def step_create_knowledge_node_with_questions(context, email, topic, question_count):
    """創建知識節點並關聯指定數量的題目"""
    user_id = context.ids.get(email)
    if not user_id:
        raise ValueError(f"User {email} not found in context")

    # 創建科目（如果不存在）
    subject = context.db_session.query(Subject).filter_by(name="General").first()
    if not subject:
        subject = Subject(
            id=uuid.uuid4(),
            name="General",
            code="GEN"
        )
        context.db_session.add(subject)
        context.db_session.commit()

    # 創建知識節點
    node_id = uuid.uuid4()
    node = KnowledgeNode(
        id=node_id,
        name=topic,
        subject_id=subject.id,
        depth=0,
        source_origin="document"
    )
    context.db_session.add(node)
    context.db_session.commit()

    # 創建關聯的題目
    exam = context.db_session.query(Exam).first()
    if not exam:
        exam = Exam(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            subject_id=subject.id,
            exam_type="mock",
            total_questions=question_count
        )
        context.db_session.add(exam)
        context.db_session.commit()

    for i in range(question_count):
        question = Question(
            id=uuid.uuid4(),
            exam_id=exam.id,
            node_id=node_id,
            text=f"{topic} Question {i+1}",
            option_a="Option A",
            option_b="Option B",
            option_c="Option C",
            option_d="Option D",
            correct_answer="A"
        )
        context.db_session.add(question)

    context.db_session.commit()

    # 在 memo 中記錄節點 ID
    if "knowledge_nodes" not in context.memo:
        context.memo["knowledge_nodes"] = {}
    context.memo["knowledge_nodes"][topic] = str(node_id)


@given('用戶 "{email}" 在知識節點 "{topic}" 上答錯 {error_count:d} 次')
def step_create_user_errors(context, email, topic, error_count):
    """為用戶創建指定數量的錯誤記錄"""
    user_id = context.ids.get(email)
    if not user_id:
        raise ValueError(f"User {email} not found")

    # 獲取知識節點
    node = context.db_session.query(KnowledgeNode).filter_by(name=topic).first()
    if not node:
        raise ValueError(f"Knowledge node '{topic}' not found")

    # 獲取關聯的題目
    questions = context.db_session.query(Question).filter_by(node_id=node.id).all()
    if not questions:
        raise ValueError(f"No questions found for node '{topic}'")

    # 創建錯誤記錄
    for i in range(error_count):
        question = questions[i % len(questions)]
        exam = context.db_session.query(Exam).filter_by(id=question.exam_id).first()

        answer = Answer(
            id=uuid.uuid4(),
            exam_id=exam.id,
            question_id=question.id,
            user_id=uuid.UUID(user_id),
            selected_answer="B",  # Wrong answer
            is_correct=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=error_count - i)
        )
        context.db_session.add(answer)

    context.db_session.commit()


@given('用戶 "{email}" 有知識節點 "{topic}"')
def step_create_knowledge_node(context, email, topic):
    """創建知識節點"""
    # 首先調用上面的 step 但不指定題目數
    context.execute_steps(f'''
        Given 用戶 "{email}" 有知識節點 "{topic}" 及關聯 3 道題目
    ''')


@given('用戶 "{email}" 在該知識節點上有 {error_count:d} 筆錯誤記錄')
def step_create_errors_on_current_node(context, email, error_count):
    """為當前知識節點創建錯誤記錄"""
    topic = context.memo.get("last_topic")
    if not topic:
        # 使用最後創建的節點
        if "knowledge_nodes" in context.memo:
            topic = list(context.memo["knowledge_nodes"].keys())[-1]

    if not topic:
        raise ValueError("No topic found for error creation")

    context.execute_steps(f'''
        Given 用戶 "{email}" 在知識節點 "{topic}" 上答錯 {error_count} 次
    ''')


@given('用戶 "{email}" 在過去 {days:d} 天內有 {error_count:d} 筆錯誤記錄')
def step_create_recent_errors(context, email, days, error_count):
    """為用戶創建最近N天內的錯誤記錄"""
    user_id = context.ids.get(email)
    if not user_id:
        raise ValueError(f"User {email} not found")

    # 獲取或創建知識節點和題目
    subject = context.db_session.query(Subject).filter_by(name="General").first()
    if not subject:
        subject = Subject(
            id=uuid.uuid4(),
            name="General",
            code="GEN"
        )
        context.db_session.add(subject)
        context.db_session.commit()

    node = context.db_session.query(KnowledgeNode).first()
    if not node:
        node = KnowledgeNode(
            id=uuid.uuid4(),
            name="Test Topic",
            subject_id=subject.id,
            depth=0
        )
        context.db_session.add(node)
        context.db_session.commit()

    # 創建題目（如需）
    exam = context.db_session.query(Exam).first()
    if not exam:
        exam = Exam(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            subject_id=subject.id,
            exam_type="mock",
            total_questions=error_count
        )
        context.db_session.add(exam)
        context.db_session.commit()

    questions = context.db_session.query(Question).filter_by(exam_id=exam.id).all()
    if not questions:
        for i in range(error_count):
            question = Question(
                id=uuid.uuid4(),
                exam_id=exam.id,
                node_id=node.id,
                text=f"Question {i+1}",
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
                correct_answer="A"
            )
            context.db_session.add(question)
        context.db_session.commit()
        questions = context.db_session.query(Question).filter_by(exam_id=exam.id).all()

    # 創建錯誤記錄（分散在N天內）
    for i in range(error_count):
        question = questions[i % len(questions)]
        answer = Answer(
            id=uuid.uuid4(),
            exam_id=exam.id,
            question_id=question.id,
            user_id=uuid.UUID(user_id),
            selected_answer="B",
            is_correct=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=days - i)
        )
        context.db_session.add(answer)

    context.db_session.commit()


@given('用戶 "{email}" 從未答過題目 "{question_id}"')
def step_ensure_no_answer(context, email, question_id):
    """確保用戶從未答過特定題目"""
    user_id = context.ids.get(email)
    if not user_id:
        raise ValueError(f"User {email} not found")

    # 檢查並刪除任何既存的答題記錄
    context.db_session.query(Answer).filter(
        Answer.user_id == uuid.UUID(user_id),
        Answer.question_id == uuid.UUID(question_id)
    ).delete()

    context.db_session.commit()

    context.memo[f"question_{question_id}"] = question_id
