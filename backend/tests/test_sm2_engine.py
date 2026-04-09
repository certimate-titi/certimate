"""SM-2 State Machine Engine 單元測試."""

import math
from datetime import datetime, timedelta, timezone

import pytest

from app.services.sm2_engine import SM2Engine, TopicState


@pytest.fixture
def engine():
    return SM2Engine()


@pytest.fixture
def now():
    return datetime(2026, 4, 9, 12, 0, 0, tzinfo=timezone.utc)


# ── process_answer ───────────────────────────────────────────────

class TestProcessAnswer:
    def test_unseen_correct(self, engine, now):
        state = TopicState(0.0, 2.5, None, None, "UNSEEN")
        result = engine.process_answer(state, True, now=now)
        assert result.base_mastery == pytest.approx(0.3, abs=0.01)
        assert result.status == "CRITICAL"
        assert result.last_tested_at == now
        assert result.next_review_at > now

    def test_unseen_wrong(self, engine, now):
        state = TopicState(0.0, 2.5, None, None, "UNSEEN")
        result = engine.process_answer(state, False, now=now)
        assert result.base_mastery == 0.0
        assert result.status == "UNSEEN"

    def test_five_correct_reaches_mastered(self, engine, now):
        state = TopicState(0.0, 2.5, None, None, "UNSEEN")
        for _ in range(5):
            state = engine.process_answer(state, True, now=now)
        assert state.base_mastery > 0.7
        assert state.status == "MASTERED"

    def test_ease_factor_decreases_on_wrong(self, engine, now):
        state = TopicState(0.5, 2.5, now, now + timedelta(days=7), "PENDING")
        result = engine.process_answer(state, False, now=now)
        assert result.ease_factor < 2.5

    def test_ease_factor_minimum(self, engine, now):
        state = TopicState(0.5, 1.3, now, now + timedelta(days=1), "CRITICAL")
        result = engine.process_answer(state, False, now=now)
        assert result.ease_factor >= engine.MIN_EASE_FACTOR

    def test_wrong_answer_shortens_review(self, engine, now):
        state = TopicState(0.8, 2.5, now, now + timedelta(days=14), "MASTERED")
        result = engine.process_answer(state, False, now=now)
        # 答錯 → 明天就要複習
        assert result.next_review_at <= now + timedelta(days=2)


# ── calculate_retention ──────────────────────────────────────────

class TestCalculateRetention:
    def test_fresh_retention_is_1(self, engine, now):
        state = TopicState(0.9, 2.5, now - timedelta(days=1), now + timedelta(days=13), "MASTERED")
        assert engine.calculate_retention(state, now) == 1.0

    def test_unseen_retention_is_0(self, engine, now):
        state = TopicState(0.0, 2.5, None, None, "UNSEEN")
        assert engine.calculate_retention(state, now) == 0.0

    def test_decayed_retention_below_1(self, engine, now):
        state = TopicState(0.8, 2.5, now - timedelta(days=30), now - timedelta(days=16), "MASTERED")
        retention = engine.calculate_retention(state, now)
        assert 0.0 < retention < 1.0

    def test_retention_floor(self, engine, now):
        # Very long decay
        state = TopicState(0.8, 2.5, now - timedelta(days=365), now - timedelta(days=350), "MASTERED")
        retention = engine.calculate_retention(state, now)
        assert retention >= engine.RETENTION_FLOOR


# ── calculate_effective_progress ─────────────────────────────────

class TestEffectiveProgress:
    def test_fresh_effective_equals_base(self, engine, now):
        state = TopicState(0.85, 2.5, now, now + timedelta(days=14), "MASTERED")
        effective = engine.calculate_effective_progress(state, now)
        assert effective == pytest.approx(0.85, abs=0.01)

    def test_decayed_effective_less_than_base(self, engine, now):
        state = TopicState(0.85, 2.5, now - timedelta(days=30), now - timedelta(days=16), "MASTERED")
        effective = engine.calculate_effective_progress(state, now)
        assert effective < 0.85

    def test_unseen_effective_is_0(self, engine, now):
        state = TopicState(0.0, 2.5, None, None, "UNSEEN")
        assert engine.calculate_effective_progress(state, now) == 0.0


# ── get_decay_status ─────────────────────────────────────────────

class TestDecayStatus:
    def test_fresh(self, engine, now):
        state = TopicState(0.9, 2.5, now, now + timedelta(days=14), "MASTERED")
        assert engine.get_decay_status(state, now) == "fresh"

    def test_unseen(self, engine, now):
        state = TopicState(0.0, 2.5, None, None, "UNSEEN")
        assert engine.get_decay_status(state, now) == "unseen"

    def test_decaying(self, engine, now):
        # 2 hours past review date — very slight decay
        state = TopicState(0.8, 2.5, now - timedelta(days=15), now - timedelta(hours=2), "MASTERED")
        status = engine.get_decay_status(state, now)
        assert status in ("fresh", "decaying", "critical")  # Any non-unseen

    def test_critical(self, engine, now):
        state = TopicState(0.8, 2.5, now - timedelta(days=60), now - timedelta(days=45), "MASTERED")
        assert engine.get_decay_status(state, now) == "critical"


# ── process_exam_answers (batch) ─────────────────────────────────

class TestBatchExamProcessing:
    def test_batch_updates_multiple_topics(self, engine, now):
        topic_answers = {
            "topic_a": [True, True, False],
            "topic_b": [True, True, True],
        }
        states = {
            "topic_a": TopicState(0.5, 2.5, None, None, "PENDING"),
            "topic_b": TopicState(0.3, 2.5, None, None, "CRITICAL"),
        }
        results = engine.process_exam_answers(topic_answers, states, now)
        assert "topic_a" in results
        assert "topic_b" in results
        # topic_b (3 correct) should have higher mastery than topic_a (2/3)
        assert results["topic_b"].base_mastery > results["topic_a"].base_mastery

    def test_new_topic_created(self, engine, now):
        topic_answers = {"new_topic": [True]}
        results = engine.process_exam_answers(topic_answers, {}, now)
        assert "new_topic" in results
        assert results["new_topic"].base_mastery > 0


# ── process_refresh_quiz ─────────────────────────────────────────

class TestRefreshQuiz:
    def test_all_correct_extends_review(self, engine, now):
        state = TopicState(0.8, 2.5, now - timedelta(days=30), now - timedelta(days=16), "MASTERED")
        result = engine.process_refresh_quiz(state, True, now)
        assert result.next_review_at > now + timedelta(days=5)
        assert result.status in ("MASTERED", "PENDING")

    def test_failed_shortens_review(self, engine, now):
        state = TopicState(0.8, 2.5, now - timedelta(days=30), now - timedelta(days=16), "MASTERED")
        result = engine.process_refresh_quiz(state, False, now)
        assert result.next_review_at <= now + timedelta(days=2)
        assert result.status == "CRITICAL"
        assert result.ease_factor < 2.5
