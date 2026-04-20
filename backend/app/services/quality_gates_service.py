"""Quality Gates service — Pre-import validation checks (Phase 3)."""

import logging
from pathlib import Path
from typing import Optional
import PyPDF2
from app.services.base import BaseService

logger = logging.getLogger(__name__)

# Quality gate configuration
MAX_PDF_SIZE_MB = 50
MIN_PDF_SIZE_BYTES = 1024  # At least 1 KB
MAX_PAGES_PER_PDF = 500
MIN_PAGES_PER_PDF = 1


class QualityGatesService(BaseService):
    """Run pre-import quality checks on PDF files before main extraction pipeline."""

    def __init__(self):
        """Initialize service (no DB dependency)."""
        super().__init__(None)

    def validate_pdf_file(self, file_path: str) -> dict:
        """Gate 1: Basic PDF file validation.

        Checks:
        - File exists and is readable
        - File size within limits
        - File is valid PDF format
        - Has readable content

        Args:
            file_path: Path to PDF file

        Returns:
            {"valid": bool, "errors": [str], "warnings": [str], "metadata": {...}}
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            path = Path(file_path)

            # Check file exists
            if not path.exists():
                return self.error(f"File not found: {file_path}", 400)

            # Check file size
            file_size = path.stat().st_size
            metadata["file_size_bytes"] = file_size
            metadata["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            if file_size < MIN_PDF_SIZE_BYTES:
                errors.append(f"File too small: {file_size} bytes (minimum {MIN_PDF_SIZE_BYTES})")

            if file_size > MAX_PDF_SIZE_MB * 1024 * 1024:
                errors.append(f"File too large: {metadata['file_size_mb']} MB (maximum {MAX_PDF_SIZE_MB} MB)")

            # Try to open as PDF
            try:
                with open(file_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    page_count = len(pdf_reader.pages)

                    metadata["page_count"] = page_count
                    metadata["is_valid_pdf"] = True

                    # Check page count
                    if page_count < MIN_PAGES_PER_PDF:
                        errors.append(f"PDF has no pages (need at least {MIN_PAGES_PER_PDF})")

                    if page_count > MAX_PAGES_PER_PDF:
                        warnings.append(
                            f"PDF has {page_count} pages (threshold: {MAX_PAGES_PER_PDF}). "
                            "Large PDFs may take longer to process."
                        )

                    # Try to extract text from first page
                    if page_count > 0:
                        first_page = pdf_reader.pages[0]
                        text = first_page.extract_text()
                        metadata["has_extractable_text"] = len(text.strip()) > 0

                        if not metadata["has_extractable_text"]:
                            errors.append(
                                "PDF appears to be image-only (no extractable text). "
                                "The system requires text-based PDFs."
                            )

            except PyPDF2.PdfReadError as e:
                errors.append(f"Invalid PDF format: {str(e)}")
                metadata["is_valid_pdf"] = False

            return self.ok({
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "metadata": metadata,
            })

        except Exception as e:
            logger.exception(f"PDF validation error: {str(e)}")
            return self.error(f"Failed to validate PDF: {str(e)}", 500)

    def validate_pdf_pair(
        self,
        question_pdf_path: str,
        answer_pdf_path: str,
    ) -> dict:
        """Gate 2: Validate question and answer PDFs together.

        Checks:
        - Both files are valid PDFs
        - Question PDF has more or equal pages than answer PDF
        - File sizes are comparable (within 2x ratio)

        Args:
            question_pdf_path: Path to question PDF
            answer_pdf_path: Path to answer PDF

        Returns:
            {"valid": bool, "errors": [str], "warnings": [str], "metadata": {...}}
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            # Validate both PDFs individually
            q_result = self.validate_pdf_file(question_pdf_path)
            a_result = self.validate_pdf_file(answer_pdf_path)

            if q_result.get("error") or a_result.get("error"):
                errors.extend(q_result.get("data", {}).get("errors", []))
                errors.extend(a_result.get("data", {}).get("errors", []))
                return self.ok({
                    "valid": False,
                    "errors": errors,
                    "warnings": [],
                    "metadata": {}
                })

            q_data = q_result.get("data", {})
            a_data = a_result.get("data", {})

            q_pages = q_data.get("metadata", {}).get("page_count", 0)
            a_pages = a_data.get("metadata", {}).get("page_count", 0)
            q_size = q_data.get("metadata", {}).get("file_size_bytes", 0)
            a_size = a_data.get("metadata", {}).get("file_size_bytes", 0)

            metadata["question_pages"] = q_pages
            metadata["answer_pages"] = a_pages
            metadata["question_size_mb"] = q_data.get("metadata", {}).get("file_size_mb", 0)
            metadata["answer_size_mb"] = a_data.get("metadata", {}).get("file_size_mb", 0)

            # Check page count relationship
            if q_pages < a_pages:
                errors.append(
                    f"Question PDF ({q_pages} pages) has fewer pages than answer PDF ({a_pages} pages). "
                    "Questions should have at least as many pages."
                )

            # Check size ratio (shouldn't be drastically different)
            if q_size > 0 and a_size > 0:
                ratio = max(q_size, a_size) / min(q_size, a_size)
                if ratio > 5:
                    warnings.append(
                        f"File size ratio is {ratio:.1f}x. Question and answer PDFs are very different sizes. "
                        "This may indicate a format mismatch."
                    )

            # Inherit warnings from individual validations
            warnings.extend(q_data.get("warnings", []))
            warnings.extend(a_data.get("warnings", []))

            return self.ok({
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "metadata": metadata,
            })

        except Exception as e:
            logger.exception(f"PDF pair validation error: {str(e)}")
            return self.error(f"Failed to validate PDF pair: {str(e)}", 500)

    def detect_corruption_indicators(self, file_path: str) -> dict:
        """Gate 3: Check for signs of file corruption or damage.

        Checks:
        - PDF structure integrity
        - Recoverable but suspicious patterns
        - Encoding issues

        Args:
            file_path: Path to PDF file

        Returns:
            {"suspicious": bool, "indicators": [str], "risk_level": "low|medium|high"}
        """
        indicators = []
        risk_level = "low"

        try:
            path = Path(file_path)

            if not path.exists():
                return self.error(f"File not found: {file_path}", 404)

            try:
                with open(file_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)

                    # Check for structural issues
                    if pdf_reader.is_encrypted:
                        indicators.append("PDF is encrypted - may prevent extraction")
                        risk_level = "medium"

                    # Check page integrity
                    for i, page in enumerate(pdf_reader.pages):
                        try:
                            # Try to extract and parse
                            text = page.extract_text()
                            if len(text.strip()) == 0 and i < 5:
                                indicators.append(
                                    f"Page {i+1} appears to be image-only (no extractable text)"
                                )
                                risk_level = "medium"
                        except Exception as e:
                            indicators.append(f"Page {i+1} extraction error: {str(e)}")
                            if risk_level == "low":
                                risk_level = "medium"

            except PyPDF2.PdfReadError as e:
                indicators.append(f"PDF structure error: {str(e)}")
                risk_level = "high"

            return self.ok({
                "suspicious": len(indicators) > 0,
                "indicators": indicators,
                "risk_level": risk_level,
            })

        except Exception as e:
            logger.exception(f"Corruption detection error: {str(e)}")
            return self.error(f"Failed to check for corruption: {str(e)}", 500)

    def estimate_processing_difficulty(self, question_pdf_path: str, answer_pdf_path: str) -> dict:
        """Gate 4: Estimate difficulty of processing these PDFs.

        Returns difficulty score (1-5) and estimated processing time.
        Factors:
        - Page count
        - File size
        - Text extractability
        - Potential layout complexity (inferred from file structure)

        Args:
            question_pdf_path: Path to question PDF
            answer_pdf_path: Path to answer PDF

        Returns:
            {"difficulty_score": 1-5, "estimated_time_seconds": float, "factors": [str]}
        """
        factors = []
        score = 1
        base_time = 2  # Base 2 seconds

        try:
            # Analyze question PDF
            q_result = self.validate_pdf_file(question_pdf_path)
            if not q_result.get("error"):
                q_metadata = q_result.get("data", {}).get("metadata", {})
                page_count = q_metadata.get("page_count", 0)
                file_size_mb = q_metadata.get("file_size_mb", 0)

                # Add time for pages (assume 2 seconds per page average)
                base_time += page_count * 2

                # Adjust score based on characteristics
                if page_count > 50:
                    score += 1
                    factors.append(f"Large document ({page_count} pages)")

                if file_size_mb > 10:
                    score += 1
                    factors.append(f"Large file size ({file_size_mb} MB)")

                if not q_metadata.get("has_extractable_text"):
                    score += 2
                    factors.append("Image-based PDF (slower processing)")
                    base_time *= 1.5

            # Analyze answer PDF
            a_result = self.validate_pdf_file(answer_pdf_path)
            if not a_result.get("error"):
                a_metadata = a_result.get("data", {}).get("metadata", {})
                a_pages = a_metadata.get("page_count", 0)

                if a_pages > 0 and not a_metadata.get("has_extractable_text"):
                    score += 1
                    factors.append("Answer PDF is image-based")

            # Check for corruption risks
            corruption_result = self.detect_corruption_indicators(question_pdf_path)
            if not corruption_result.get("error"):
                corruption_data = corruption_result.get("data", {})
                if corruption_data.get("risk_level") == "high":
                    score += 2
                    factors.append("Potential PDF corruption detected")
                elif corruption_data.get("risk_level") == "medium":
                    score += 1
                    factors.append("Possible PDF structure issues")

            # Cap score at 5
            score = min(score, 5)

            return self.ok({
                "difficulty_score": score,
                "estimated_time_seconds": round(base_time, 1),
                "factors": factors,
                "recommendation": "Standard" if score <= 2 else "Slow" if score <= 3 else "Very Slow"
            })

        except Exception as e:
            logger.exception(f"Difficulty estimation error: {str(e)}")
            return self.error(f"Failed to estimate difficulty: {str(e)}", 500)

    def run_all_gates(self, question_pdf_path: str, answer_pdf_path: str) -> dict:
        """Run all quality gates on a PDF pair.

        Returns comprehensive validation report with all gate results.

        Args:
            question_pdf_path: Path to question PDF
            answer_pdf_path: Path to answer PDF

        Returns:
            {
                "passed": bool,
                "gates": {
                    "pdf_validity": {...},
                    "pdf_pair": {...},
                    "corruption": {...},
                    "difficulty": {...}
                },
                "summary": str,
                "proceed_to_extraction": bool
            }
        """
        gates = {}
        all_passed = True

        try:
            # Gate 1: PDF validity
            gate1 = self.validate_pdf_file(question_pdf_path)
            gates["pdf_validity"] = {
                "passed": not gate1.get("error") and gate1.get("data", {}).get("valid"),
                "result": gate1
            }
            if not gates["pdf_validity"]["passed"]:
                all_passed = False

            # Gate 2: PDF pair validation
            gate2 = self.validate_pdf_pair(question_pdf_path, answer_pdf_path)
            gates["pdf_pair"] = {
                "passed": not gate2.get("error") and gate2.get("data", {}).get("valid"),
                "result": gate2
            }
            if not gates["pdf_pair"]["passed"]:
                all_passed = False

            # Gate 3: Corruption detection
            gate3 = self.detect_corruption_indicators(question_pdf_path)
            gates["corruption"] = {
                "high_risk": not gate3.get("error") and gate3.get("data", {}).get("risk_level") == "high",
                "result": gate3
            }
            if gates["corruption"]["high_risk"]:
                all_passed = False

            # Gate 4: Difficulty estimation
            gate4 = self.estimate_processing_difficulty(question_pdf_path, answer_pdf_path)
            gates["difficulty"] = {
                "result": gate4
            }

            # Determine proceed status
            proceed = all_passed and not gates["corruption"]["high_risk"]

            summary = "✓ All quality gates passed" if proceed else "✗ Quality gates failed - manual review recommended"

            return self.ok({
                "passed": all_passed,
                "proceed_to_extraction": proceed,
                "gates": gates,
                "summary": summary,
            })

        except Exception as e:
            logger.exception(f"Quality gates execution error: {str(e)}")
            return self.error(f"Failed to run quality gates: {str(e)}", 500)
