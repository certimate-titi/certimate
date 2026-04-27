"""
Historical Exam Import Service — Phase 2 Database Integration.

Handles persistent storage of extracted exam questions to database.
Complements ExamPDFExtractionService (which handles extraction/validation).
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.historical_exam import HistoricalExam
from app.models.question import Question, QuestionType, DifficultyLevel
from app.models.subject import Subject
from app.schemas.exam_import import LegacyImportOutput, LegacyQuestionOutput
from app.services.base import BaseService

log = logging.getLogger(__name__)


class HistoricalExamImportService(BaseService):
    """
    Database integration for modern PDF extraction pipeline.

    Responsibilities:
    1. Create/update HistoricalExam record
    2. Batch insert extracted questions
    3. Update subject statistics
    4. Handle import failures and rollbacks
    5. Track import metadata
    """

    def __init__(self, db: Session):
        """初始化實例。"""
        super().__init__(db)

    def import_exam_paper(
        self,
        legacy_output: LegacyImportOutput,
        exam_code: str,
        category_code: str,
        subject_code: str,
        exam_name: Optional[str] = None,
        category_name: Optional[str] = None,
        subject_name: Optional[str] = None,
        year: Optional[int] = None,
        tenant_id: Optional[uuid.UUID] = None,
        skip_existing: bool = False,
    ) -> Dict:
        """
        Import extracted exam paper to database.

        Args:
            legacy_output: LegacyImportOutput from extraction pipeline
            exam_code: Exam code (e.g., "P")
            category_code: Category code (e.g., "01")
            subject_code: Subject code (e.g., "0101")
            exam_name: Optional exam name
            category_name: Optional category name
            subject_name: Optional subject name
            year: Optional ROC year
            tenant_id: Optional tenant ID (multi-tenancy)
            skip_existing: If True, skip if exam already exists

        Returns:
            Dict with import status, question count, errors
        """
        try:
            # Step 1: Check if exam already exists
            existing_exam = self.db.query(HistoricalExam).filter(
                HistoricalExam.exam_code == exam_code,
                HistoricalExam.category_code == category_code,
                HistoricalExam.subject_code == subject_code,
            ).first()

            if existing_exam:
                if skip_existing:
                    log.info(
                        f"Exam already exists ({exam_code}/{category_code}/{subject_code}), "
                        f"skipping import"
                    )
                    return {
                        "error": False,
                        "import_success": False,
                        "status_code": 200,
                        "message": "Exam already exists (skipped)",
                        "exam_id": str(existing_exam.id),
                        "questions_imported": 0,
                    }
                else:
                    # Update existing exam (for re-imports)
                    existing_exam.total_questions = len(legacy_output.questions)
                    self.db.flush()
                    exam = existing_exam
                    log.info(f"Updating existing exam: {exam_code}/{category_code}/{subject_code}")
            else:
                # Step 2: Create HistoricalExam record
                exam = HistoricalExam(
                    exam_code=exam_code,
                    category_code=category_code,
                    subject_code=subject_code,
                    exam_name=exam_name,
                    category_name=category_name,
                    subject_name=subject_name,
                    total_questions=len(legacy_output.questions),
                    source=legacy_output.import_meta.get("source", "Claude Vision Pipeline"),
                    year=year,
                    tenant_id=tenant_id,
                )
                self.db.add(exam)
                self.db.flush()  # Get the ID without committing
                log.info(f"Created HistoricalExam: {exam.id}")

            # Step 3: Batch insert questions
            questions_inserted = 0
            questions_errors = []

            for q_legacy in legacy_output.questions:
                try:
                    question = Question(
                        historical_exam_id=exam.id,
                        question_number=q_legacy.question_number,
                        type=QuestionType.SINGLE_CHOICE,
                        difficulty=DifficultyLevel.MEDIUM,  # Default; can be updated later
                        content=q_legacy.content,
                        option_a=q_legacy.option_a if q_legacy.option_a else None,
                        option_b=q_legacy.option_b if q_legacy.option_b else None,
                        option_c=q_legacy.option_c if q_legacy.option_c else None,
                        option_d=q_legacy.option_d if q_legacy.option_d else None,
                        correct_answer=q_legacy.correct_answer,
                        explanation=q_legacy.explanation if q_legacy.explanation else None,
                        bloom_category=q_legacy.bloom_category,
                        historical_source=exam_code,
                        source_type="historical",
                        quality_flag="ok",
                        validation_model="modern_pdf_pipeline_v1",
                        tenant_id=tenant_id,
                    )
                    self.db.add(question)
                    questions_inserted += 1

                except Exception as e:
                    questions_errors.append({
                        "question_number": q_legacy.question_number,
                        "error": str(e)
                    })
                    log.error(f"Failed to insert Q{q_legacy.question_number}: {e}")

            # Step 4: Flush and commit
            try:
                self.db.flush()
                log.info(f"Inserted {questions_inserted} questions for {exam_code}/{category_code}/{subject_code}")
            except IntegrityError as e:
                self.db.rollback()
                log.error(f"Database integrity error during flush: {e}")
                return {
                    "error": True,
                    "status_code": 400,
                    "message": f"Database integrity error: {str(e)}",
                    "questions_imported": 0,
                }

            # Step 5: Update subject statistics
            try:
                self._update_subject_statistics(subject_code, tenant_id)
            except Exception as e:
                log.warning(f"Failed to update subject statistics: {e}")

            # Commit transaction
            self.db.commit()
            log.info(f"✓ Successfully imported {questions_inserted} questions")

            return {
                "error": False,
                "import_success": True,
                "status_code": 201,
                "message": f"Successfully imported {questions_inserted} questions",
                "exam_id": str(exam.id),
                "exam_code": exam_code,
                "category_code": category_code,
                "subject_code": subject_code,
                "questions_imported": questions_inserted,
                "questions_failed": len(questions_errors),
                "import_errors": questions_errors if questions_errors else None,
            }

        except Exception as e:
            self.db.rollback()
            log.exception(f"Import failed: {e}")
            return {
                "error": True,
                "status_code": 500,
                "message": f"Import failed: {str(e)}",
                "questions_imported": 0,
            }

    def _update_subject_statistics(
        self,
        subject_code: str,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Update Subject.available_questions count after import.

        Args:
            subject_code: Subject code
            tenant_id: Optional tenant ID
        """
        # This is a simplified example; actual implementation depends on
        # how subject_code maps to Subject table
        try:
            from sqlalchemy import text

            # Query historical questions for this subject
            query = """
                SELECT COUNT(*) as cnt
                FROM questions q
                JOIN historical_exams he ON q.historical_exam_id = he.id
                WHERE he.subject_code = :subject_code
            """
            if tenant_id:
                query += " AND he.tenant_id = :tenant_id"

            params = {"subject_code": subject_code}
            if tenant_id:
                params["tenant_id"] = tenant_id

            result = self.db.execute(text(query), params).scalar()
            log.debug(f"Subject {subject_code} has {result} questions")

        except Exception as e:
            log.warning(f"Could not update subject statistics: {e}")

    def get_import_status(self, exam_code: str, category_code: str, subject_code: str) -> Dict:
        """
        Get import status for a specific exam.

        Returns detailed information about imported questions.
        """
        try:
            exam = self.db.query(HistoricalExam).filter(
                HistoricalExam.exam_code == exam_code,
                HistoricalExam.category_code == category_code,
                HistoricalExam.subject_code == subject_code,
            ).first()

            if not exam:
                return {
                    "found": False,
                    "message": "Exam not found in database",
                }

            # Count questions
            question_count = self.db.query(Question).filter(
                Question.historical_exam_id == exam.id
            ).count()

            return {
                "found": True,
                "exam_id": str(exam.id),
                "exam_code": exam.exam_code,
                "category_code": exam.category_code,
                "subject_code": exam.subject_code,
                "exam_name": exam.exam_name,
                "total_questions": exam.total_questions,
                "actual_questions": question_count,
                "created_at": exam.created_at.isoformat() if exam.created_at else None,
                "source": exam.source,
            }

        except Exception as e:
            log.error(f"Failed to get import status: {e}")
            return {
                "error": True,
                "message": str(e),
            }

    def list_historical_exams(
        self,
        limit: int = 50,
        offset: int = 0,
        exam_code: Optional[str] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> Dict:
        """
        List imported historical exams with pagination.

        Args:
            limit: Max results to return
            offset: Pagination offset
            exam_code: Optional filter by exam code
            tenant_id: Optional filter by tenant

        Returns:
            List of exams with metadata
        """
        try:
            query = self.db.query(HistoricalExam)

            if exam_code:
                query = query.filter(HistoricalExam.exam_code == exam_code)
            if tenant_id:
                query = query.filter(HistoricalExam.tenant_id == tenant_id)

            total = query.count()
            exams = query.order_by(
                HistoricalExam.created_at.desc()
            ).limit(limit).offset(offset).all()

            return {
                "error": False,
                "total": total,
                "limit": limit,
                "offset": offset,
                "exams": [
                    {
                        "exam_id": str(e.id),
                        "exam_code": e.exam_code,
                        "category_code": e.category_code,
                        "subject_code": e.subject_code,
                        "exam_name": e.exam_name,
                        "total_questions": e.total_questions,
                        "created_at": e.created_at.isoformat() if e.created_at else None,
                    }
                    for e in exams
                ],
            }

        except Exception as e:
            log.error(f"Failed to list historical exams: {e}")
            return {
                "error": True,
                "message": str(e),
            }

    def get_exam_questions(
        self,
        exam_code: str,
        category_code: str,
        subject_code: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict:
        """
        Get questions from a specific imported exam.

        Args:
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            limit: Pagination limit
            offset: Pagination offset

        Returns:
            List of questions with details
        """
        try:
            exam = self.db.query(HistoricalExam).filter(
                HistoricalExam.exam_code == exam_code,
                HistoricalExam.category_code == category_code,
                HistoricalExam.subject_code == subject_code,
            ).first()

            if not exam:
                return {
                    "error": True,
                    "message": "Exam not found",
                }

            total = self.db.query(Question).filter(
                Question.historical_exam_id == exam.id
            ).count()

            questions = self.db.query(Question).filter(
                Question.historical_exam_id == exam.id
            ).order_by(
                Question.question_number
            ).limit(limit).offset(offset).all()

            return {
                "error": False,
                "exam_id": str(exam.id),
                "exam_code": exam_code,
                "total_questions": total,
                "limit": limit,
                "offset": offset,
                "questions": [
                    {
                        "question_id": str(q.id),
                        "question_number": q.question_number,
                        "content": q.content,
                        "option_a": q.option_a,
                        "option_b": q.option_b,
                        "option_c": q.option_c,
                        "option_d": q.option_d,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation,
                    }
                    for q in questions
                ],
            }

        except Exception as e:
            log.error(f"Failed to get exam questions: {e}")
            return {
                "error": True,
                "message": str(e),
            }

    def validate_import(
        self,
        exam_code: str,
        category_code: str,
        subject_code: str,
    ) -> Dict:
        """
        Validate imported exam data for consistency.

        Checks:
        1. All questions have non-empty content
        2. Correct answers are valid (A-D)
        3. At least one non-null option per question
        4. Question numbers are sequential
        """
        try:
            exam = self.db.query(HistoricalExam).filter(
                HistoricalExam.exam_code == exam_code,
                HistoricalExam.category_code == category_code,
                HistoricalExam.subject_code == subject_code,
            ).first()

            if not exam:
                return {"error": True, "message": "Exam not found"}

            questions = self.db.query(Question).filter(
                Question.historical_exam_id == exam.id
            ).order_by(Question.question_number).all()

            errors = []
            warnings = []

            # Check sequential numbering
            expected_numbers = set(range(1, len(questions) + 1))
            actual_numbers = set(q.question_number for q in questions)
            if expected_numbers != actual_numbers:
                errors.append(f"Non-sequential question numbers: {sorted(actual_numbers)}")

            # Check each question
            for q in questions:
                # Empty content
                if not q.content or not q.content.strip():
                    errors.append(f"Q{q.question_number}: Empty content")

                # Invalid answer
                if q.correct_answer not in ["A", "B", "C", "D"]:
                    errors.append(f"Q{q.question_number}: Invalid answer '{q.correct_answer}'")

                # At least one option
                options_count = sum([
                    1 for opt in [q.option_a, q.option_b, q.option_c, q.option_d]
                    if opt and opt.strip()
                ])
                if options_count < 2:
                    warnings.append(f"Q{q.question_number}: Only {options_count} non-empty options")

                # Answer matches an option
                answer_option = getattr(q, f"option_{q.correct_answer.lower()}", None)
                if not answer_option or not answer_option.strip():
                    errors.append(
                        f"Q{q.question_number}: Answer '{q.correct_answer}' is empty/missing"
                    )

            return {
                "error": len(errors) > 0,
                "exam_id": str(exam.id),
                "total_questions": len(questions),
                "errors": errors,
                "warnings": warnings,
                "valid": len(errors) == 0,
            }

        except Exception as e:
            log.error(f"Validation failed: {e}")
            return {
                "error": True,
                "message": str(e),
            }
