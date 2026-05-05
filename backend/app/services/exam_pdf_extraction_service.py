"""
Modern PDF extraction service using Claude Vision + Structured Outputs.

Replaces regex-based parsing with layout-aware PDF processing and LLM normalization.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, BinaryIO

from anthropic import Anthropic

from app.schemas.exam_import import (
    ExamPaperData,
    AnswerSheetData,
    ValidationReport,
    ValidationResult,
    LegacyQuestionOutput,
    LegacyImportOutput,
)
from app.services.base import BaseService

log = logging.getLogger(__name__)


class ExamPDFExtractionService(BaseService):
    """
    Modern PDF extraction pipeline:
    1. Layout-aware parsing (Claude Vision reads PDF as images)
    2. LLM normalization (Structured Outputs for consistency)
    3. Dual-track processing (separate question and answer PDFs)
    4. Validation gates (multi-layer checks)
    """

    def __init__(self, db=None):
        """初始化實例。"""
        super().__init__(db)
        self.client = Anthropic()
        self.model = "claude-sonnet-4-5"

    def extract_questions_from_pdf(
        self,
        pdf_content: bytes,
        exam_code: str,
        category_code: str,
        subject_code: str,
        exam_name: Optional[str] = None,
    ) -> Tuple[Optional[ExamPaperData], list]:
        """
        Extract questions from PDF using Claude Vision.

        Args:
            pdf_content: Raw PDF bytes
            exam_code: Exam code (e.g., 'P')
            category_code: Category code (e.g., '01')
            subject_code: Subject code (e.g., '0101')
            exam_name: Optional exam name

        Returns:
            Tuple of (ExamPaperData or None, list of error messages)
        """
        errors = []

        try:
            # Convert PDF to base64 (simplified - in production use pdf2image)
            pdf_base64 = base64.standard_b64encode(pdf_content).decode('utf-8')

            # Call Claude Vision with Structured Outputs
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 2000,
                },
                system="""You are an expert at parsing examination PDFs in Traditional Chinese.

Your task is to extract exam questions from PDF images with high accuracy.

For each question:
1. Identify the question number (usually 1-indexed)
2. Extract the complete question text
3. Identify all available options (①/②/③/④ for Chinese exams, or (A)/(B)/(C)/(D) for Western format)
4. Note if the question contains images/diagrams

CRITICAL: Some exams use "combination-style questions" (組合式題) where only certain judgments are shown.
- If an option is not shown in the PDF, set it to null (not empty string)
- This is DIFFERENT from questions with all 4 options present

Return results as valid JSON that can be parsed.""",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Extract all exam questions from this PDF.

Exam info:
- Exam code: {exam_code}
- Category: {category_code}
- Subject: {subject_code}
- Name: {exam_name or 'Unknown'}

Return valid JSON matching this structure:
{{
    "exam_name": "exam name from PDF or provided",
    "exam_code": "{exam_code}",
    "category_code": "{category_code}",
    "subject_code": "{subject_code}",
    "exam_date": "YYYY-MM-DD or null",
    "total_questions": number,
    "questions": [
        {{
            "question_number": 1,
            "question_text": "full question text",
            "options": {{
                "A": "option A text or null",
                "B": "option B text or null",
                "C": "option C text or null",
                "D": "option D text or null"
            }},
            "has_image": false
        }}
    ]
}}

IMPORTANT:
- For combination-style questions: set unavailable options to null
- Preserve all formatting and special characters
- Question text should be complete and readable""",
                            },
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                        ],
                    }
                ],
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response (might be wrapped in markdown code blocks)
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Validate against schema
            exam_paper = ExamPaperData(**data)
            log.info(
                f"✓ Extracted {len(exam_paper.questions)} questions from PDF "
                f"({exam_code}/{category_code}/{subject_code})"
            )
            return exam_paper, errors

        except json.JSONDecodeError as e:
            errors.append(f"Failed to parse JSON from Claude response: {str(e)}")
            log.error(f"JSON parse error: {errors[0]}")
            return None, errors
        except Exception as e:
            errors.append(f"PDF extraction failed: {str(e)}")
            log.error(f"Extraction error: {errors[0]}")
            return None, errors

    def extract_answer_key_from_pdf(
        self,
        pdf_content: bytes,
        exam_code: str,
        category_code: str,
        subject_code: str,
        expected_question_count: int,
    ) -> Tuple[Optional[AnswerSheetData], list]:
        """
        Extract answer key from solution PDF.

        Args:
            pdf_content: Raw PDF bytes of answer sheet
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            expected_question_count: Expected number of questions (for validation)

        Returns:
            Tuple of (AnswerSheetData or None, list of error messages)
        """
        errors = []

        try:
            pdf_base64 = base64.standard_b64encode(pdf_content).decode('utf-8')

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 1024,
                },
                system="""You are an expert at extracting answer keys from examination answer sheets.

Extract the correct answer (A/B/C/D) for each question number.

Return results as valid JSON that can be parsed.""",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Extract the answer key from this PDF.

Exam info:
- Exam code: {exam_code}
- Category: {category_code}
- Subject: {subject_code}
- Expected questions: {expected_question_count}

Return valid JSON matching this structure:
{{
    "exam_name": "exam name",
    "exam_code": "{exam_code}",
    "category_code": "{category_code}",
    "subject_code": "{subject_code}",
    "total_questions": {expected_question_count},
    "answers": [
        {{"question_number": 1, "correct_answer": "A"}},
        {{"question_number": 2, "correct_answer": "B"}},
        ...
    ]
}}

IMPORTANT:
- Extract answers in sequential order by question number
- Correct answer must be exactly A, B, C, or D
- Include all questions from 1 to {expected_question_count}""",
                            },
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                        ],
                    }
                ],
            )

            response_text = message.content[0].text
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)
            answer_sheet = AnswerSheetData(**data)

            log.info(
                f"✓ Extracted {len(answer_sheet.answers)} answers from answer sheet "
                f"({exam_code}/{category_code}/{subject_code})"
            )
            return answer_sheet, errors

        except json.JSONDecodeError as e:
            errors.append(f"Failed to parse JSON from Claude response: {str(e)}")
            return None, errors
        except Exception as e:
            errors.append(f"Answer key extraction failed: {str(e)}")
            return None, errors

    def validate_exam_paper(
        self,
        exam_paper: ExamPaperData,
        answer_sheet: AnswerSheetData,
    ) -> ValidationReport:
        """
        Multi-layer validation of extracted questions against answer key.

        Validation gates:
        1. Count check: total_questions matches
        2. Sequential check: question numbers 1..N
        3. Text length: no suspicious patterns
        4. Option validity: answer points to non-empty option
        5. Answer coverage: all questions have answers

        Args:
            exam_paper: Extracted questions
            answer_sheet: Extracted answer key

        Returns:
            ValidationReport with detailed results
        """
        validation_details: list[ValidationResult] = []
        critical_errors = []
        warnings = []

        # Gate 1: Count check
        if len(exam_paper.questions) != answer_sheet.total_questions:
            critical_errors.append(
                f"Question count mismatch: {len(exam_paper.questions)} questions but "
                f"{answer_sheet.total_questions} expected"
            )

        if len(answer_sheet.answers) != answer_sheet.total_questions:
            critical_errors.append(
                f"Answer count mismatch: {len(answer_sheet.answers)} answers but "
                f"{answer_sheet.total_questions} expected"
            )

        # Build answer map
        answer_map = {ans.question_number: ans.correct_answer for ans in answer_sheet.answers}

        # Validate each question
        valid_count = 0
        for q in exam_paper.questions:
            errors = []
            q_num = q.question_number

            # Gate 2: Sequential check (already done by Pydantic validator)

            # Gate 3: Text length check
            if len(q.question_text) > 2000:
                errors.append(f"Question text suspiciously long ({len(q.question_text)} chars)")

            # Gate 4: Answer validity - CRITICAL CHECK
            if q_num not in answer_map:
                errors.append(f"No answer found for question {q_num}")
            else:
                correct_ans = answer_map[q_num]
                ans_option = getattr(q.options, correct_ans, None)

                # THE CRITICAL CHECK: Answer must point to non-empty option
                if ans_option is None or not ans_option.strip():
                    errors.append(
                        f"CRITICAL: Correct answer '{correct_ans}' is empty/missing in PDF. "
                        f"Available options: {q.options.get_available_options()}"
                    )

            # Gate 5: Option insufficiency
            available_opts = q.options.get_available_options()
            if len(available_opts) < 2:
                errors.append(
                    f"Insufficient options: only {available_opts} found "
                    f"(need at least 2)"
                )

            is_valid = len(errors) == 0
            if is_valid:
                valid_count += 1

            validation_details.append(
                ValidationResult(
                    question_number=q_num,
                    is_valid=is_valid,
                    errors=errors,
                )
            )

        # Final report
        invalid_count = len(exam_paper.questions) - valid_count
        can_proceed = len(critical_errors) == 0 and invalid_count == 0

        return ValidationReport(
            total_questions=len(exam_paper.questions),
            valid_questions=valid_count,
            invalid_questions=invalid_count,
            validation_details=validation_details,
            critical_errors=critical_errors,
            warnings=warnings,
            can_proceed=can_proceed,
        )

    def merge_exam_with_answers(
        self,
        exam_paper: ExamPaperData,
        answer_sheet: AnswerSheetData,
    ) -> dict:
        """
        Merge normalized exam data with answer key.

        Returns merged structure with validated answer assignments.
        """
        answer_map = {ans.question_number: ans.correct_answer for ans in answer_sheet.answers}

        for q in exam_paper.questions:
            q.correct_answer = answer_map.get(q.question_number, "")

        return exam_paper.dict()

    def convert_to_legacy_format(
        self,
        exam_paper: ExamPaperData,
        answer_sheet: AnswerSheetData,
    ) -> LegacyImportOutput:
        """
        Convert normalized format to legacy JSON format (for backward compatibility).

        Returns structure matching current moex_simple.py output.
        """
        answer_map = {ans.question_number: ans.correct_answer for ans in answer_sheet.answers}

        legacy_questions = []
        for q in exam_paper.questions:
            legacy_q = LegacyQuestionOutput(
                question_number=q.question_number,
                content=q.question_text,
                type="single_choice",
                option_a=q.options.A or "",
                option_b=q.options.B or "",
                option_c=q.options.C or "",
                option_d=q.options.D or "",
                correct_answer=answer_map.get(q.question_number, ""),
                explanation="",
                bloom_category=None,
            )
            legacy_questions.append(legacy_q)

        return LegacyImportOutput(
            import_meta={
                "source": "Claude Vision + Structured Outputs (Modern Pipeline)",
                "exam_code": exam_paper.exam_code,
                "category_code": exam_paper.category_code,
                "subject_code": exam_paper.subject_code,
                "total_questions": len(legacy_questions),
                "questions_with_answer": sum(1 for q in legacy_questions if q.correct_answer),
                "extraction_method": "modern_pdf_pipeline_v1",
            },
            questions=legacy_questions,
        )
