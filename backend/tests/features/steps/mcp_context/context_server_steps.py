"""Step definitions for MCP Context Server feature."""

from behave import given, when, then
from datetime import datetime, timedelta
from uuid import UUID
import json

from app.mcp import ContextServer
from app.models.user import User
from app.models.answer import Answer
from app.models.question import Question
from app.models.exam import Exam
from app.models.subject import Subject


@given('user "{user_name}" has answered {count} questions in "{subject_name}" subject')
def step_user_answered_questions_in_subject(context, user_name, count, subject_name):
    """Create answers for a user in a specific subject."""
    count = int(count)

    # Get or create user
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        user = User(
            id=context.ids.get(user_name),
            email=f"{user_name}@test.com",
            password_hash="hash",
            is_email_verified=True
        )
        context.db.add(user)
        context.db.flush()
        context.ids[user_name] = str(user.id)

    # Get or create subject
    subject = context.db.query(Subject).filter(Subject.name == subject_name).first()
    if not subject:
        from app.models.subject import SubjectCategory
        category = context.db.query(SubjectCategory).first()
        if not category:
            category = SubjectCategory(name="Test Category")
            context.db.add(category)
            context.db.flush()

        subject = Subject(name=subject_name, category_id=category.id)
        context.db.add(subject)
        context.db.flush()

    # Create exam
    exam = Exam(
        user_id=user.id,
        subject_id=subject.id,
        total_questions=count
    )
    context.db.add(exam)
    context.db.flush()

    # Create questions and answers
    for i in range(count):
        question = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"Question {i + 1}",
            correct_answer="A",
            difficulty="medium"
        )
        context.db.add(question)
        context.db.flush()

        answer = Answer(
            exam_id=exam.id,
            question_id=question.id,
            user_id=user.id,
            selected_answer="A",
            is_correct=False,
            confidence="medium",
            answered_at=datetime.now()
        )
        context.db.add(answer)

    context.db.commit()

    # Store subject_name for later use
    if not hasattr(context, 'subjects'):
        context.subjects = {}
    context.subjects[subject_name] = str(subject.id)


@given('user "{user_name}" got {correct_count} correct answers ({percentage}% mastery)')
def step_user_correct_answers(context, user_name, correct_count, percentage):
    """Set the correct answer count for previous answers."""
    correct_count = int(correct_count)

    # Find user
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        raise ValueError(f"User {user_name} not found")

    # Get all answers for this user
    answers = context.db.query(Answer).filter(Answer.user_id == user.id).all()

    # Mark first N as correct
    for i, answer in enumerate(answers):
        if i < correct_count:
            answer.is_correct = True
        else:
            answer.is_correct = False

    context.db.commit()


@given('user "{user_name}" has recent errors with various confidence levels')
def step_user_has_errors_with_confidence(context, user_name):
    """Create errors with different confidence levels."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        raise ValueError(f"User {user_name} not found")

    # Get some wrong answers and set different confidence levels
    answers = context.db.query(Answer).filter(
        (Answer.user_id == user.id) & (Answer.is_correct == False)
    ).limit(5).all()

    confidence_levels = ["high", "medium", "low", "high", "low"]
    for answer, confidence in zip(answers, confidence_levels):
        answer.confidence = confidence

    context.db.commit()


@given('user "{user_name}" attempted questions on today\'s date')
def step_user_attempted_today(context, user_name):
    """Create answer with today's timestamp."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        user = User(
            email=f"{user_name}@test.com",
            password_hash="hash",
            is_email_verified=True
        )
        context.db.add(user)
        context.db.flush()
        context.ids[user_name] = str(user.id)

    # Create question and answer for today
    from app.models.subject import SubjectCategory
    category = context.db.query(SubjectCategory).first()
    if not category:
        category = SubjectCategory(name="Test Category")
        context.db.add(category)
        context.db.flush()

    subject = context.db.query(Subject).filter(Subject.name == "Test Subject").first()
    if not subject:
        subject = Subject(name="Test Subject", category_id=category.id)
        context.db.add(subject)
        context.db.flush()

    exam = Exam(user_id=user.id, subject_id=subject.id, total_questions=1)
    context.db.add(exam)
    context.db.flush()

    question = Question(
        exam_id=exam.id,
        question_number=1,
        content="Test Question",
        correct_answer="A",
        difficulty="medium"
    )
    context.db.add(question)
    context.db.flush()

    answer = Answer(
        exam_id=exam.id,
        question_id=question.id,
        user_id=user.id,
        selected_answer="A",
        is_correct=True,
        answered_at=datetime.now()
    )
    context.db.add(answer)
    context.db.commit()


@given('user "{user_name}" attempted questions yesterday')
def step_user_attempted_yesterday(context, user_name):
    """Create answer with yesterday's timestamp."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        raise ValueError(f"User {user_name} not found")

    # Create answer with yesterday's timestamp
    from app.models.subject import SubjectCategory
    category = context.db.query(SubjectCategory).first()
    if not category:
        category = SubjectCategory(name="Test Category")
        context.db.add(category)
        context.db.flush()

    subject = context.db.query(Subject).filter(Subject.name == "Test Subject").first()
    if not subject:
        subject = Subject(name="Test Subject", category_id=category.id)
        context.db.add(subject)
        context.db.flush()

    exam = Exam(user_id=user.id, subject_id=subject.id, total_questions=1)
    context.db.add(exam)
    context.db.flush()

    question = Question(
        exam_id=exam.id,
        question_number=1,
        content="Test Question",
        correct_answer="A",
        difficulty="medium"
    )
    context.db.add(question)
    context.db.flush()

    answer = Answer(
        exam_id=exam.id,
        question_id=question.id,
        user_id=user.id,
        selected_answer="A",
        is_correct=True,
        answered_at=datetime.now() - timedelta(days=1)
    )
    context.db.add(answer)
    context.db.commit()


@given('user "{user_name}" attempted questions 2 days ago')
def step_user_attempted_2_days_ago(context, user_name):
    """Create answer 2 days ago."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        raise ValueError(f"User {user_name} not found")

    from app.models.subject import SubjectCategory
    category = context.db.query(SubjectCategory).first()
    if not category:
        category = SubjectCategory(name="Test Category")
        context.db.add(category)
        context.db.flush()

    subject = context.db.query(Subject).filter(Subject.name == "Test Subject").first()
    if not subject:
        subject = Subject(name="Test Subject", category_id=category.id)
        context.db.add(subject)
        context.db.flush()

    exam = Exam(user_id=user.id, subject_id=subject.id, total_questions=1)
    context.db.add(exam)
    context.db.flush()

    question = Question(
        exam_id=exam.id,
        question_number=1,
        content="Test Question",
        correct_answer="A",
        difficulty="medium"
    )
    context.db.add(question)
    context.db.flush()

    answer = Answer(
        exam_id=exam.id,
        question_id=question.id,
        user_id=user.id,
        selected_answer="A",
        is_correct=True,
        answered_at=datetime.now() - timedelta(days=2)
    )
    context.db.add(answer)
    context.db.commit()


@given('user "{user_name}" did not attempt on 3 days ago')
def step_user_no_attempt_3_days_ago(context, user_name):
    """This is just a marker - no action needed."""
    pass


@when('MCP Context Server builds context for "{user_name}"')
def step_build_context(context, user_name):
    """Build context using MCP Context Server."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        user_id = context.ids.get(user_name)
        if not user_id:
            raise ValueError(f"User {user_name} not found")
    else:
        user_id = str(user.id)

    server = ContextServer(context.db, enable_caching=False)
    response = server.build_context_for_coach(user_id)

    context.last_response = response
    context.mcp_result = response.to_dict()


@when('fetch weak area details for "{user_name}" in "{topic}"')
def step_fetch_weak_area(context, user_name, topic):
    """Fetch weak area details for a topic."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        raise ValueError(f"User {user_name} not found")

    server = ContextServer(context.db, enable_caching=False)
    response = server.fetch_weak_area_details(str(user.id), topic)

    context.last_response = response
    context.mcp_result = response.to_dict()


@when('fetch recent errors for "{user_name}" with limit {limit}')
def step_fetch_recent_errors(context, user_name, limit):
    """Fetch recent errors."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    if not user:
        raise ValueError(f"User {user_name} not found")

    server = ContextServer(context.db, enable_caching=False)
    response = server.fetch_recent_errors(str(user.id), int(limit))

    context.last_response = response
    context.mcp_result = response.to_dict()


@then('the context includes "{user_name}" user_id')
def step_context_has_user_id(context, user_name):
    """Verify context includes user ID."""
    user = context.db.query(User).filter(User.email == f"{user_name}@test.com").first()
    data = context.mcp_result.get("data", {})

    assert data.get("user_id") == str(user.id), f"Expected user_id {str(user.id)}, got {data.get('user_id')}"


@then('the context shows mastery score for "{subject}" is {score}')
def step_context_mastery_score(context, subject, score):
    """Verify mastery score for a subject."""
    data = context.mcp_result.get("data", {})
    mastery = data.get("mastery_scores", {})
    actual_score = mastery.get(subject)

    assert actual_score is not None, f"No mastery score for {subject}"
    assert abs(actual_score - float(score)) < 0.01, f"Expected {score}, got {actual_score}"


@then('the context identifies "{subject}" as a weak area (below {threshold} threshold)')
def step_context_weak_area(context, subject, threshold):
    """Verify subject is identified as weak area."""
    data = context.mcp_result.get("data", {})
    weak_areas = data.get("weak_areas", [])
    threshold = float(threshold)

    weak_area = next((w for w in weak_areas if w["topic"] == subject), None)
    assert weak_area is not None, f"{subject} not in weak areas"
    assert weak_area["mastery"] < threshold


@then('the context does not identify "{subject}" as a weak area')
def step_context_no_weak_area(context, subject):
    """Verify subject is NOT a weak area."""
    data = context.mcp_result.get("data", {})
    weak_areas = data.get("weak_areas", [])

    weak_area = next((w for w in weak_areas if w["topic"] == subject), None)
    assert weak_area is None, f"{subject} should not be in weak areas"


@then('the context includes recent_errors list')
def step_context_has_recent_errors(context):
    """Verify context has recent_errors."""
    data = context.mcp_result.get("data", {})
    assert "recent_errors" in data, "recent_errors not in context"
    assert isinstance(data["recent_errors"], list)


@then('the context includes total_questions_attempted count')
def step_context_has_total_count(context):
    """Verify context has total_questions_attempted."""
    data = context.mcp_result.get("data", {})
    assert "total_questions_attempted" in data


@then('the context includes average_confidence score')
def step_context_has_avg_confidence(context):
    """Verify context has average_confidence."""
    data = context.mcp_result.get("data", {})
    assert "average_confidence" in data


@then('the context shows learning_streak of {days} days')
def step_context_streak(context, days):
    """Verify learning streak."""
    data = context.mcp_result.get("data", {})
    assert data.get("learning_streak") == int(days)


@then('weak area detail shows topic "{topic}"')
def step_weak_area_topic(context, topic):
    """Verify weak area detail topic."""
    data = context.mcp_result.get("data", {})
    assert data.get("topic") == topic


@then('error_rate is {rate} ({count_desc})')
def step_error_rate(context, rate, count_desc):
    """Verify error rate."""
    data = context.mcp_result.get("data", {})
    expected_rate = float(rate)
    actual_rate = data.get("error_rate")

    assert actual_rate is not None
    assert abs(actual_rate - expected_rate) < 0.01


@then('error_count is {count}')
def step_error_count(context, count):
    """Verify error count."""
    data = context.mcp_result.get("data", {})
    assert data.get("error_count") == int(count)


@then('total_attempts is {count}')
def step_total_attempts(context, count):
    """Verify total attempts."""
    data = context.mcp_result.get("data", {})
    assert data.get("total_attempts") == int(count)


@then('response includes error')
def step_response_has_error(context):
    """Verify response includes error."""
    result = context.mcp_result
    assert "error" in result
    assert result.get("success") == False


@then('error type is "{error_type}"')
def step_error_type(context, error_type):
    """Verify error type."""
    error = context.mcp_result.get("error", {})
    assert error.get("type") == error_type


@then('error message mentions user not found')
def step_error_message(context):
    """Verify error message."""
    error = context.mcp_result.get("error", {})
    message = error.get("message", "").lower()
    assert "not found" in message or "user" in message
