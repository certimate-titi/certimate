"""
Pydantic schemas for modern PDF extraction pipeline.

Provides structured output types for layout-aware PDF parsing and LLM normalization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class OptionData(BaseModel):
    """Single multiple-choice option."""
    A: Optional[str] = Field(None, description="Option A text")
    B: Optional[str] = Field(None, description="Option B text")
    C: Optional[str] = Field(None, description="Option C text")
    D: Optional[str] = Field(None, description="Option D text")

    class Config:
        use_enum_values = True

    def get_available_options(self) -> List[str]:
        """Return list of available option letters."""
        return [k for k in ['A', 'B', 'C', 'D'] if getattr(self, k)]

    def is_valid(self) -> bool:
        """Check if at least 2 options are present."""
        return len(self.get_available_options()) >= 2


class QuestionData(BaseModel):
    """Single exam question with normalized structure."""
    question_number: int = Field(..., description="Question number (1-based)")
    question_text: str = Field(..., description="Question stem/content", min_length=10)
    options: OptionData = Field(..., description="Multiple choice options")
    has_image: bool = Field(default=False, description="Whether question contains embedded image")

    class Config:
        use_enum_values = True

    @validator('question_number')
    def validate_question_number(cls, v):
        if v <= 0:
            raise ValueError("Question number must be positive")
        return v

    @validator('question_text')
    def validate_question_text(cls, v):
        if not v.strip():
            raise ValueError("Question text cannot be empty")
        return v.strip()


class ExamPaperData(BaseModel):
    """Complete exam paper with all questions."""
    exam_name: str = Field(..., description="Name of exam (e.g., '114年初等考試')")
    exam_code: str = Field(..., description="Exam code from catalog (e.g., 'P')")
    category_code: str = Field(..., description="Category code (e.g., '01')")
    subject_code: str = Field(..., description="Subject code (e.g., '0101')")
    exam_date: Optional[str] = Field(None, description="Exam date (YYYY-MM-DD format)")
    total_questions: int = Field(..., description="Total number of questions", ge=1)
    questions: List[QuestionData] = Field(..., description="List of parsed questions")

    class Config:
        use_enum_values = True

    @validator('total_questions')
    def validate_total_questions(cls, v, values):
        if 'questions' in values and v != len(values['questions']):
            raise ValueError(f"total_questions ({v}) doesn't match questions count ({len(values['questions'])})")
        return v

    @validator('questions')
    def validate_questions_unique(cls, v):
        """Ensure no duplicate question numbers."""
        numbers = [q.question_number for q in v]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Duplicate question numbers detected")
        return v

    @validator('questions')
    def validate_questions_ordered(cls, v):
        """Ensure questions are sequentially numbered."""
        if not v:
            return v
        numbers = sorted([q.question_number for q in v])
        expected = list(range(1, len(v) + 1))
        if numbers != expected:
            raise ValueError(f"Questions not sequentially numbered: {numbers} vs expected {expected}")
        return v


class AnswerKeyData(BaseModel):
    """Answer key mapping from answer PDF."""
    question_number: int = Field(..., description="Question number")
    correct_answer: str = Field(..., description="Correct answer (A/B/C/D)", pattern="^[A-D]$")

    class Config:
        use_enum_values = True


class AnswerSheetData(BaseModel):
    """Complete answer sheet from solution PDF."""
    exam_name: str = Field(..., description="Exam name (for validation)")
    exam_code: str = Field(..., description="Exam code")
    category_code: str = Field(..., description="Category code")
    subject_code: str = Field(..., description="Subject code")
    total_questions: int = Field(..., description="Total expected questions")
    answers: List[AnswerKeyData] = Field(..., description="Answer key mappings")

    class Config:
        use_enum_values = True

    @validator('answers')
    def validate_answers_count(cls, v, values):
        if 'total_questions' in values and len(v) != values['total_questions']:
            raise ValueError(f"Expected {values['total_questions']} answers, got {len(v)}")
        return v


class ValidationResult(BaseModel):
    """Result of question validation against answer key."""
    question_number: int
    is_valid: bool
    errors: List[str] = Field(default_factory=list, description="Validation error messages")

    class Config:
        use_enum_values = True


class ValidationReport(BaseModel):
    """Full validation report for imported exam paper."""
    total_questions: int
    valid_questions: int
    invalid_questions: int
    validation_details: List[ValidationResult]
    critical_errors: List[str] = Field(default_factory=list, description="Critical validation failures")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    can_proceed: bool = Field(description="Whether import can proceed (no critical errors)")

    class Config:
        use_enum_values = True


# Legacy format output (for backward compatibility with existing JSON)
class LegacyQuestionOutput(BaseModel):
    """Question in legacy JSON format (matches current moex_simple.py output)."""
    question_number: int
    content: str
    type: str = "single_choice"
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str = ""
    bloom_category: Optional[str] = None

    class Config:
        use_enum_values = True


class LegacyImportOutput(BaseModel):
    """Full import output in legacy JSON format."""
    import_meta: dict = Field(description="Metadata about import")
    questions: List[LegacyQuestionOutput]

    class Config:
        use_enum_values = True
