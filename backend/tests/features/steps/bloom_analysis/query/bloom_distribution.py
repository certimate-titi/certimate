"""Bloom 分佈與趨勢查詢 — 直接從 DB 計算（無對應 HTTP endpoint，B-route 候選）。"""

from behave import when

from app.models.subject import Subject
from app.models.historical_exam import HistoricalExam
from app.models.question import Question, BloomCategory


_ALL_BLOOMS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]


def _enum_to_str(v):
    return v.value if hasattr(v, "value") else (str(v) if v else None)


@when('使用者 "{email}" 查詢學科 "{subject_name}" 的 Bloom 分類統計')
def step_query_bloom_distribution(context, email, subject_name):
    db = context.db_session
    subj = db.query(Subject).filter_by(name=subject_name).first()
    assert subj, f"找不到學科 {subject_name}"

    # 查該 subject 名下所有 historical_exams 的 questions
    he_ids = [
        he.id for he in db.query(HistoricalExam).filter_by(subject_name=subject_name).all()
    ]
    counts = {b: 0 for b in _ALL_BLOOMS}
    if he_ids:
        questions = db.query(Question).filter(
            Question.historical_exam_id.in_(he_ids)
        ).all()
        for q in questions:
            b = _enum_to_str(q.bloom_category)
            if b in counts:
                counts[b] += 1

    total = sum(counts.values()) or 1
    distribution = []
    for b in _ALL_BLOOMS:
        c = counts[b]
        distribution.append({
            "bloom_category": b,
            "count": c,
            "percentage": round(c / total * 100, 1),
        })

    context.memo["bloom_distribution_response"] = distribution
    context.memo["queried_subject"] = subject_name
    context.memo["queried_email"] = email


@when('使用者 "{email}" 查詢學科 "{subject_name}" 的年度 Bloom 趨勢')
def step_query_bloom_trend(context, email, subject_name):
    db = context.db_session
    subj = db.query(Subject).filter_by(name=subject_name).first()
    assert subj, f"找不到學科 {subject_name}"

    he_records = db.query(HistoricalExam).filter_by(subject_name=subject_name).all()
    he_by_year: dict[int, list] = {}
    for he in he_records:
        if he.year is not None:
            he_by_year.setdefault(he.year, []).append(he.id)

    trend: dict[int, dict[str, int]] = {}
    for year, ids in he_by_year.items():
        counts = {b: 0 for b in _ALL_BLOOMS}
        questions = db.query(Question).filter(Question.historical_exam_id.in_(ids)).all()
        for q in questions:
            b = _enum_to_str(q.bloom_category)
            if b in counts:
                counts[b] += 1
        trend[year] = counts

    context.memo["bloom_trend_response"] = trend
    context.memo["queried_subject"] = subject_name
    context.memo["queried_email"] = email
