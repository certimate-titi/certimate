"""Bloom 認知層次分佈/趨勢分析（Spec 18）。

對應 endpoint：GET /api/v1/subjects/{subject_id}/bloom-distribution
                   ?trend_by=year（可選）

不依賴 LLM；單純從 questions.bloom_category + historical_exams.year 聚合。
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.historical_exam import HistoricalExam
from app.models.question import Question


_ALL_BLOOMS: list[str] = [
    "remember", "understand", "apply", "analyze", "evaluate", "create",
]


def _enum_to_str(v) -> str | None:
    """將 enum 或字串 bloom_category 標準化為小寫字串。"""
    if v is None:
        return None
    return v.value if hasattr(v, "value") else str(v)


class BloomAnalyticsService:
    """Bloom 分佈/趨勢統計服務。

    使用方式：
        service = BloomAnalyticsService(db)
        dist = service.get_distribution(subject_id)
        trend = service.get_trend_by_year(subject_id)
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_subject_or_error(self, subject_id: str) -> Subject | dict:
        try:
            sid = uuid.UUID(subject_id)
        except (ValueError, AttributeError):
            return {"error": True, "status_code": 400, "message": "subject_id 格式錯誤"}
        subj = self.db.query(Subject).filter_by(id=sid).first()
        if not subj:
            return {"error": True, "status_code": 404, "message": "學科不存在"}
        return subj

    def _historical_exam_ids(self, subject: Subject) -> list[uuid.UUID]:
        """以 subject_name 對應 historical_exams（沿用 step 既有約定）。"""
        return [
            he.id
            for he in self.db.query(HistoricalExam)
            .filter_by(subject_name=subject.name)
            .all()
        ]

    def get_distribution(self, subject_id: str) -> dict:
        """取得整體 Bloom 分佈（不分年份）。

        回傳：
            {
              "subject_id": str,
              "subject_name": str,
              "total_questions": int,
              "distribution": [
                {"bloom_category": str, "count": int, "percentage": float}, ...
              ]
            }
        """
        subj_or_err = self._get_subject_or_error(subject_id)
        if isinstance(subj_or_err, dict):
            return subj_or_err
        subj = subj_or_err

        he_ids = self._historical_exam_ids(subj)
        counts = {b: 0 for b in _ALL_BLOOMS}
        if he_ids:
            for q in self.db.query(Question).filter(
                Question.historical_exam_id.in_(he_ids)
            ).all():
                b = _enum_to_str(q.bloom_category)
                if b in counts:
                    counts[b] += 1

        total = sum(counts.values())
        denom = total or 1  # 避免除零；total=0 時 percentage 全 0
        distribution = [
            {
                "bloom_category": b,
                "count": counts[b],
                "percentage": (
                    round(counts[b] / denom * 100, 1) if total > 0 else 0.0
                ),
            }
            for b in _ALL_BLOOMS
        ]

        # F23 題庫統計：計算有答案題目佔比
        answered_count = 0
        if he_ids:
            answered_count = self.db.query(Question).filter(
                Question.historical_exam_id.in_(he_ids),
                Question.correct_answer.isnot(None),
                Question.correct_answer != "",
            ).count()
        answer_rate = round(answered_count / total * 100, 1) if total > 0 else 0.0

        return {
            "error": False,
            "subject_id": str(subj.id),
            "subject_name": subj.name,
            "total_questions": total,
            "distribution": distribution,
            "bloom_distribution": distribution,  # F23 API contract alias
            "answer_rate": answer_rate,           # F23 題庫統計
        }

    def get_trend_by_year(self, subject_id: str) -> dict:
        """取得各年度 Bloom 分佈趨勢。

        回傳：
            {
              "subject_id": str,
              "subject_name": str,
              "trend": [
                {"year": int, "remember": int, "understand": int, ...,
                 "create": int, "total": int}
              ]
            }
        """
        subj_or_err = self._get_subject_or_error(subject_id)
        if isinstance(subj_or_err, dict):
            return subj_or_err
        subj = subj_or_err

        he_records = (
            self.db.query(HistoricalExam)
            .filter_by(subject_name=subj.name)
            .all()
        )
        he_by_year: dict[int, list[uuid.UUID]] = {}
        for he in he_records:
            if he.year is not None:
                he_by_year.setdefault(he.year, []).append(he.id)

        trend: list[dict] = []
        for year in sorted(he_by_year.keys()):
            counts = {b: 0 for b in _ALL_BLOOMS}
            for q in self.db.query(Question).filter(
                Question.historical_exam_id.in_(he_by_year[year])
            ).all():
                b = _enum_to_str(q.bloom_category)
                if b in counts:
                    counts[b] += 1
            trend.append(
                {"year": year, "total": sum(counts.values()), **counts}
            )

        return {
            "error": False,
            "subject_id": str(subj.id),
            "subject_name": subj.name,
            "trend": trend,
        }
