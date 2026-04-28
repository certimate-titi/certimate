"""Feature 18 Background — 學科 + 歷年考古題 (含 Bloom)。"""

import uuid
from behave import given

from app.models.subject import Subject, SubjectCategory
from app.models.historical_exam import HistoricalExam
from app.models.question import Question, QuestionType, DifficultyLevel, BloomCategory


def _ensure_category(db):
    cat = db.query(SubjectCategory).filter_by(name="Bloom 測試分類").first()
    if not cat:
        cat = SubjectCategory(name="Bloom 測試分類")
        db.add(cat)
        db.flush()
    return cat


def _ensure_subject(db, name: str) -> Subject:
    subj = db.query(Subject).filter_by(name=name).first()
    if subj:
        return subj
    cat = _ensure_category(db)
    subj = Subject(name=name, category_id=cat.id)
    db.add(subj)
    db.flush()
    return subj


@given('系統中有以下學科：')
def step_subjects(context):
    db = context.db_session
    for row in context.table:
        subj = _ensure_subject(db, row["名稱"])
        # 記錄 row 中的學科 ID（feature 用整數，僅作 alias）
        sid_alias = row.get("學科 ID") if hasattr(row, "get") else None
        try:
            sid_alias = row["學科 ID"]
        except Exception:
            sid_alias = None
        if sid_alias:
            context.ids[f"subject_alias_{sid_alias}"] = str(subj.id)
        context.ids[f"subject_{row['名稱']}"] = str(subj.id)
    db.commit()


_TYPE_MAP = {
    "single_choice": QuestionType.SINGLE_CHOICE,
    "multiple_choice": QuestionType.MULTIPLE_CHOICE,
    "fill_in": QuestionType.FILL_IN,
    "calculation": QuestionType.CALCULATION,
}
_DIFF_MAP = {
    "easy": DifficultyLevel.EASY,
    "medium": DifficultyLevel.MEDIUM,
    "hard": DifficultyLevel.HARD,
}
_BLOOM_MAP = {
    "remember": BloomCategory.REMEMBER,
    "understand": BloomCategory.UNDERSTAND,
    "apply": BloomCategory.APPLY,
    "analyze": BloomCategory.ANALYZE,
    "evaluate": BloomCategory.EVALUATE,
    "create": BloomCategory.CREATE,
}


@given('系統中有以下歷年考古題（含 Bloom 分類）：')
def step_historical_questions(context):
    db = context.db_session
    # group rows by (subject_alias, year) for HistoricalExam record
    he_cache: dict[tuple, HistoricalExam] = {}

    bloom_by_subject_year: dict[tuple, dict[str, int]] = {}

    for row in context.table:
        subj_alias = row["學科 ID"]
        year = int(row["年份"])
        subj_id_str = context.ids.get(f"subject_alias_{subj_alias}")
        if not subj_id_str:
            raise AssertionError(f"找不到 alias={subj_alias} 的學科，請確認 Background 順序")
        subj_id = uuid.UUID(subj_id_str)
        subj = db.query(Subject).filter_by(id=subj_id).first()

        key = (subj_id_str, year)
        he = he_cache.get(key)
        if not he:
            he = HistoricalExam(
                exam_code=f"BLOOM-TEST-{subj_alias}",
                category_code=f"cat-{subj_alias}",
                subject_code=f"subj-{subj_alias}-{year}",
                exam_name=f"{subj.name} {year}年考古題",
                subject_name=subj.name,
                year=year,
                source="bdd_fixture",
            )
            db.add(he)
            db.flush()
            he_cache[key] = he

        # 順便把 subject 的 exam_subject_codes 寫上，讓 historical_only 模式找得到
        codes = list(subj.exam_subject_codes or [])
        full_code = f"{he.exam_code}:{he.subject_code}"
        if full_code not in codes:
            codes.append(full_code)
            subj.exam_subject_codes = codes

        bloom_str = row["Bloom 分類"].strip()
        bloom_enum = _BLOOM_MAP[bloom_str]

        q = Question(
            historical_exam_id=he.id,
            question_number=int(row["題目 ID"]),
            type=_TYPE_MAP[row["題型"].strip()],
            difficulty=_DIFF_MAP[row["難度"].strip()],
            content=f"題 {row['題目 ID']}（{bloom_str}）",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            bloom_category=bloom_enum,
            source_type="historical",
            quality_flag="ok",
        )
        db.add(q)

        bloom_by_subject_year.setdefault((subj.name, year), {}).setdefault(bloom_str, 0)
        bloom_by_subject_year[(subj.name, year)][bloom_str] += 1

    db.commit()
    context.memo["bloom_by_subject_year"] = bloom_by_subject_year
