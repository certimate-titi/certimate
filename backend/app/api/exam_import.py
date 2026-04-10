"""
Exam import API — Modern PDF extraction pipeline.

Provides endpoints for uploading and processing exam PDFs using Claude Vision + Structured Outputs.
Replaces legacy regex-based moex_simple.py crawler.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.exam_pdf_extraction_service import ExamPDFExtractionService
from app.services.historical_exam_import_service import HistoricalExamImportService
from app.schemas.exam_import import ValidationReport

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/exam-import")


def _handle_result(result: dict):
    """Convert service result dict to HTTPException if error."""
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.post("/extract")
async def extract_exam_paper(
    question_pdf: UploadFile = File(..., description="PDF containing exam questions"),
    answer_pdf: UploadFile = File(..., description="PDF containing answer key"),
    exam_code: str = Form(..., description="Exam code (e.g., 'P')"),
    category_code: str = Form(..., description="Category code (e.g., '01')"),
    subject_code: str = Form(..., description="Subject code (e.g., '0101')"),
    exam_name: Optional[str] = Form(None, description="Exam name (optional)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Extract and validate exam paper from PDFs.

    **Step 1: Layout-Aware Parsing**
    - Claude Vision reads PDF images and extracts question structure
    - Handles combination-style questions (optional options)

    **Step 2: LLM Normalization**
    - Structured Outputs ensure consistent JSON format
    - Validates question/option structure

    **Step 3: Dual-Track Processing**
    - Separate question and answer PDFs processed independently
    - Answer key extracted with question count validation

    **Step 4: Multi-Layer Validation**
    - Count check (questions vs answers)
    - Sequential numbering (1..N)
    - Text length anomaly detection
    - **Critical: Answer validity** (answer points to non-empty option)

    Returns detailed validation report with errors/warnings.
    """
    try:
        # Read PDF contents
        q_bytes = await question_pdf.read()
        a_bytes = await answer_pdf.read()

        if not q_bytes or len(q_bytes) < 100:
            raise HTTPException(status_code=400, detail={"message": "Question PDF is empty or invalid"})
        if not a_bytes or len(a_bytes) < 100:
            raise HTTPException(status_code=400, detail={"message": "Answer PDF is empty or invalid"})

        service = ExamPDFExtractionService(db)

        # Step 1 & 2: Extract questions with Claude Vision
        log.info(f"📄 Extracting questions from PDF ({exam_code}/{category_code}/{subject_code})")
        exam_paper, q_errors = service.extract_questions_from_pdf(
            q_bytes,
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            exam_name=exam_name,
        )

        if exam_paper is None:
            return {
                "error": True,
                "status_code": 400,
                "message": "Failed to extract questions from PDF",
                "details": q_errors,
            }

        # Step 3: Extract answer key
        log.info(f"📝 Extracting answer key ({exam_code}/{category_code}/{subject_code})")
        answer_sheet, a_errors = service.extract_answer_key_from_pdf(
            a_bytes,
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            expected_question_count=len(exam_paper.questions),
        )

        if answer_sheet is None:
            return {
                "error": True,
                "status_code": 400,
                "message": "Failed to extract answer key from PDF",
                "details": a_errors,
            }

        # Step 4: Multi-layer validation
        log.info(f"🔍 Validating exam paper ({len(exam_paper.questions)} questions)")
        validation = service.validate_exam_paper(exam_paper, answer_sheet)

        return {
            "extraction_successful": True,
            "exam_info": {
                "exam_code": exam_code,
                "category_code": category_code,
                "subject_code": subject_code,
                "exam_name": exam_name or exam_paper.exam_name,
                "exam_date": exam_paper.exam_date,
                "total_questions": len(exam_paper.questions),
            },
            "validation": validation.dict(),
            "can_import": validation.can_proceed,
            "summary": {
                "valid_questions": validation.valid_questions,
                "invalid_questions": validation.invalid_questions,
                "critical_errors": len(validation.critical_errors),
                "warnings": len(validation.warnings),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Extract endpoint error: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Internal error: {str(e)}"})


@router.post("/import")
async def import_exam_paper(
    question_pdf: UploadFile = File(..., description="PDF containing exam questions"),
    answer_pdf: UploadFile = File(..., description="PDF containing answer key"),
    exam_code: str = Form(..., description="Exam code (e.g., 'P')"),
    category_code: str = Form(..., description="Category code (e.g., '01')"),
    subject_code: str = Form(..., description="Subject code (e.g., '0101')"),
    exam_name: Optional[str] = Form(None, description="Exam name (optional)"),
    skip_validation: bool = Form(False, description="Skip validation gates (admin only)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Extract, validate, and import exam paper to database.

    This endpoint performs the complete pipeline:
    1. Extract questions and answers
    2. Validate against all gates
    3. Import to database (if validation passes)

    The response includes:
    - Validation report with detailed error information
    - Import status and metadata
    - Question count and statistics

    Requires validation to pass unless skip_validation is True (admin only).
    """
    try:
        # Read PDF contents
        q_bytes = await question_pdf.read()
        a_bytes = await answer_pdf.read()

        if not q_bytes or len(q_bytes) < 100:
            raise HTTPException(status_code=400, detail={"message": "Question PDF is empty or invalid"})
        if not a_bytes or len(a_bytes) < 100:
            raise HTTPException(status_code=400, detail={"message": "Answer PDF is empty or invalid"})

        service = ExamPDFExtractionService(db)

        # Extract
        exam_paper, q_errors = service.extract_questions_from_pdf(
            q_bytes,
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            exam_name=exam_name,
        )

        if exam_paper is None:
            return {
                "error": True,
                "status_code": 400,
                "import_success": False,
                "message": "Failed to extract questions",
                "details": q_errors,
            }

        answer_sheet, a_errors = service.extract_answer_key_from_pdf(
            a_bytes,
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            expected_question_count=len(exam_paper.questions),
        )

        if answer_sheet is None:
            return {
                "error": True,
                "status_code": 400,
                "import_success": False,
                "message": "Failed to extract answer key",
                "details": a_errors,
            }

        # Validate
        validation = service.validate_exam_paper(exam_paper, answer_sheet)

        if not validation.can_proceed and not skip_validation:
            return {
                "error": True,
                "status_code": 400,
                "import_success": False,
                "message": "Validation failed - cannot import",
                "validation": validation.dict(),
            }

        # Convert to legacy format and save
        legacy_output = service.convert_to_legacy_format(exam_paper, answer_sheet)

        # Database import (Phase 2)
        import_service = HistoricalExamImportService(db)
        db_result = import_service.import_exam_paper(
            legacy_output=legacy_output,
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            exam_name=exam_name or exam_paper.exam_name,
            tenant_id=None,  # TODO: Extract from user context
            skip_existing=False,
        )

        if db_result.get("error"):
            log.error(f"Database import failed: {db_result.get('message')}")
            return {
                "error": True,
                "import_success": False,
                "status_code": db_result.get("status_code", 500),
                "message": db_result.get("message"),
                "validation": validation.dict(),
            }

        log.info(
            f"✓ Successfully imported {db_result['questions_imported']} questions "
            f"({exam_code}/{category_code}/{subject_code}) "
            f"with exam_id={db_result['exam_id']}"
        )

        return {
            "error": False,
            "import_success": True,
            "message": db_result.get("message"),
            "exam_info": {
                "exam_code": exam_code,
                "category_code": category_code,
                "subject_code": subject_code,
                "exam_name": exam_name or exam_paper.exam_name,
                "total_questions": len(legacy_output.questions),
                "questions_with_answer": sum(1 for q in legacy_output.questions if q.correct_answer),
                "questions_imported": db_result.get("questions_imported"),
            },
            "exam_id": db_result.get("exam_id"),
            "validation": validation.dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Import endpoint error: {e}")
        return {
            "error": True,
            "status_code": 500,
            "import_success": False,
            "message": f"Internal error: {str(e)}",
        }


@router.get("/validation-schema")
async def get_validation_schema(
    user_id: str = Depends(get_current_user_id),
):
    """
    Get validation schema and rules.

    Returns information about the 6 validation gates applied during import:
    1. Count check (total_questions matches)
    2. Sequential check (question numbers 1..N)
    3. Text length check (detect suspicious patterns)
    4. Option validity (answer points to non-empty option) - CRITICAL
    5. Option insufficiency (at least 2 options per question)
    6. Answer coverage (all questions have answers)
    """
    return {
        "validation_gates": [
            {
                "name": "Count Check",
                "description": "Total questions must match between question PDF and answer PDF",
                "severity": "critical",
                "rule": "len(questions) == len(answers)",
            },
            {
                "name": "Sequential Numbering",
                "description": "Questions must be numbered 1..N without gaps",
                "severity": "critical",
                "rule": "question_numbers == list(range(1, N+1))",
            },
            {
                "name": "Text Length Anomaly",
                "description": "Question text should not exceed 2000 characters",
                "severity": "warning",
                "rule": "len(question_text) <= 2000",
            },
            {
                "name": "Answer Validity (CRITICAL)",
                "description": "Correct answer must point to non-empty option in PDF",
                "severity": "critical",
                "rule": "answer_sheet[q_num][answer_letter] is not None and not empty",
                "rationale": "This prevents data corruption where answer keys point to missing options",
            },
            {
                "name": "Option Insufficiency",
                "description": "Each question must have at least 2 options",
                "severity": "critical",
                "rule": "len([o for o in options if o is not None]) >= 2",
                "note": "Combination-style questions (組合式題) may have fewer options",
            },
            {
                "name": "Answer Coverage",
                "description": "All questions must have corresponding answers",
                "severity": "critical",
                "rule": "all(q_num in answer_map for q_num in question_numbers)",
            },
        ],
        "combination_style_questions": {
            "name": "組合式題 (Combination-Style Questions)",
            "description": "Some exams use combination questions where only certain judgments are shown",
            "example": "Question 5 might only show options A and C, with B and D being null",
            "handling": "Options not present in PDF are set to null, not empty string",
        },
    }


# ─────────────────────────────────────────────────────────────
# Phase 2: Database Management Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/exams")
async def list_historical_exams(
    limit: int = 50,
    offset: int = 0,
    exam_code: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    List imported historical exams with pagination.

    Returns paginated list of exams that have been imported to database.
    """
    service = HistoricalExamImportService(db)
    result = service.list_historical_exams(
        limit=limit,
        offset=offset,
        exam_code=exam_code,
    )
    return result


@router.get("/exams/{exam_code}/{category_code}/{subject_code}")
async def get_exam_status(
    exam_code: str,
    category_code: str,
    subject_code: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get import status and details for a specific exam.

    Returns metadata about an imported exam including question count and import date.
    """
    service = HistoricalExamImportService(db)
    result = service.get_import_status(exam_code, category_code, subject_code)
    return result


@router.get("/exams/{exam_code}/{category_code}/{subject_code}/questions")
async def get_exam_questions(
    exam_code: str,
    category_code: str,
    subject_code: str,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get questions from a specific imported exam.

    Returns paginated list of questions from the exam with all details
    (content, options, answers, explanations).
    """
    service = HistoricalExamImportService(db)
    result = service.get_exam_questions(
        exam_code, category_code, subject_code,
        limit=limit,
        offset=offset,
    )
    return result


@router.post("/exams/{exam_code}/{category_code}/{subject_code}/validate")
async def validate_imported_exam(
    exam_code: str,
    category_code: str,
    subject_code: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Validate imported exam data for consistency.

    Runs post-import validation checks:
    - All questions have content
    - Correct answers are valid (A-D)
    - At least one non-empty option per question
    - Question numbers are sequential
    - Answers point to non-empty options
    """
    service = HistoricalExamImportService(db)
    result = service.validate_import(exam_code, category_code, subject_code)
    return result
