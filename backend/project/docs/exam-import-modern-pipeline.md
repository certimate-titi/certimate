# Modern PDF Extraction Pipeline — Exam Question Import

## Overview

Replaces the legacy regex-based `moex_simple.py` crawler with a modern architecture using Claude Vision + Structured Outputs.

**Status:** Phase 1 complete (extraction service + validation framework)

### Key Improvements

| Issue | Legacy (Regex) | Modern (Claude Vision) |
|-------|---|---|
| **PDF Parsing** | Line-by-line text extraction (loses layout) | Layout-aware image processing (preserves structure) |
| **Question Extraction** | Regex patterns (brittle) | Claude Vision + LLM understanding | 
| **Format Consistency** | Manual string parsing | Structured Outputs (Pydantic validation) |
| **Combination Questions** | ❌ Breaks on partial options | ✓ Handles gracefully (options = null) |
| **Answer Validation** | ❌ No check if answer points to empty option | ✓ Critical validation gate |
| **Error Handling** | Silent failures (1,221 invalid questions) | Detailed validation report |

---

## Architecture

### 4-Step ETL Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Layout-Aware PDF Parsing                            │
│ • Claude Vision reads PDF as images                          │
│ • Extracts structure-preserving Markdown representation     │
│ • Handles: question numbers, options, images, tables       │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ STEP 2: LLM Normalization (Structured Outputs)              │
│ • Claude parses Markdown using Pydantic schema              │
│ • Outputs consistent JSON format                            │
│ • Validates structure (question_number, options, text)      │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ STEP 3: Dual-Track Answer Processing                        │
│ • Separate answer PDF processed independently               │
│ • Extract: question_number → correct_answer mapping        │
│ • Cross-validate question count                             │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ STEP 4: Multi-Layer Validation Gates                        │
│ Gate 1: Count check (questions == answers)                  │
│ Gate 2: Sequential numbering (1..N without gaps)           │
│ Gate 3: Text length anomalies                               │
│ Gate 4: Answer validity (answer points to non-null option) │
│ Gate 5: Option insufficiency (>= 2 options per question)   │
│ Gate 6: Answer coverage (all questions have answers)       │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ OUTPUT: ValidationReport + Legacy JSON Format               │
│ • Detailed validation results for each question             │
│ • Can proceed flag (true if all critical gates pass)        │
│ • Legacy format for backward compatibility with DB import   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Models

### Input: Raw PDFs
```
Question PDF
  ├── Page 1: Questions 1-10
  ├── Page 2: Questions 11-20
  └── [Contains images, text, unicode symbols]

Answer PDF
  ├── Question numbers: 1, 2, 3, ..., 50
  └── Answers: A, B, C, D, ...
```

### Processing: Structured Outputs

#### ExamPaperData
```json
{
  "exam_name": "114年初等考試",
  "exam_code": "P",
  "category_code": "01",
  "subject_code": "0101",
  "exam_date": "2024-06-15",
  "total_questions": 50,
  "questions": [
    {
      "question_number": 1,
      "question_text": "題目內容...",
      "options": {
        "A": "選項A文字",
        "B": null,            // ← Combination question: B not shown in PDF
        "C": "選項C文字",
        "D": null
      },
      "has_image": false
    }
  ]
}
```

#### AnswerSheetData
```json
{
  "exam_name": "114年初等考試",
  "exam_code": "P",
  "category_code": "01",
  "subject_code": "0101",
  "total_questions": 50,
  "answers": [
    {"question_number": 1, "correct_answer": "A"},
    {"question_number": 2, "correct_answer": "C"},
    ...
  ]
}
```

### Output: ValidationReport

```json
{
  "total_questions": 50,
  "valid_questions": 48,
  "invalid_questions": 2,
  "can_proceed": true,
  "validation_details": [
    {
      "question_number": 1,
      "is_valid": true,
      "errors": []
    },
    {
      "question_number": 5,
      "is_valid": false,
      "errors": [
        "CRITICAL: Correct answer 'B' is empty/missing in PDF. Available options: ['A', 'C', 'D']"
      ]
    }
  ],
  "critical_errors": [],
  "warnings": []
}
```

---

## API Endpoints

### 1. Extract & Validate Only
```http
POST /api/v1/exam-import/extract

Parameters:
  - question_pdf: File
  - answer_pdf: File
  - exam_code: string (e.g., "P")
  - category_code: string (e.g., "01")
  - subject_code: string (e.g., "0101")
  - exam_name: string (optional)

Response:
{
  "extraction_successful": true,
  "exam_info": { ... },
  "validation": { ... },
  "can_import": true,
  "summary": {
    "valid_questions": 48,
    "invalid_questions": 2,
    "critical_errors": 0,
    "warnings": 0
  }
}
```

### 2. Extract, Validate, and Import
```http
POST /api/v1/exam-import/import

Parameters:
  - question_pdf: File
  - answer_pdf: File
  - exam_code: string
  - category_code: string
  - subject_code: string
  - exam_name: string (optional)
  - skip_validation: boolean (admin only, default: false)

Response:
{
  "error": false,
  "import_success": true,
  "message": "Successfully imported 50 questions",
  "exam_info": { ... },
  "validation": { ... },
  "import_data": { ... }  // Would be saved to DB
}
```

### 3. Get Validation Schema
```http
GET /api/v1/exam-import/validation-schema

Response:
{
  "validation_gates": [
    {
      "name": "Count Check",
      "description": "Total questions must match between PDFs",
      "severity": "critical",
      "rule": "len(questions) == len(answers)"
    },
    ...
  ],
  "combination_style_questions": { ... }
}
```

---

## Validation Gates

### Gate 1: Count Check ⚠️ CRITICAL
**Rule:** `len(questions) == len(answers)`

Ensures question PDF and answer PDF have matching question counts.

**Failure Example:**
```
Question PDF: 50 questions
Answer PDF: 48 answers
Result: CRITICAL ERROR - Cannot import
```

### Gate 2: Sequential Numbering ⚠️ CRITICAL
**Rule:** Question numbers must be `[1, 2, 3, ..., N]` (no gaps)

**Failure Example:**
```
Question numbers: [1, 2, 4, 5, 6]  // Missing 3
Result: CRITICAL ERROR - Non-sequential
```

### Gate 3: Text Length Anomalies ⚠️ WARNING
**Rule:** `len(question_text) <= 2000 chars`

Detects when OCR extracted unusually long text (possible parsing error).

**Failure Example:**
```
Question 15 text length: 2500 chars (suspiciously long)
Result: WARNING - Review manually
```

### Gate 4: Answer Validity ⚠️ CRITICAL (Most Important)
**Rule:** `correct_answer points to non-null option`

**THE CRITICAL CHECK:** Ensures the answer key doesn't point to a missing option.

**Failure Example (From Legacy Data):**
```
Question 3:
  option_a: "臺南點心之多，屈指難數..."
  option_b: null      // ← Not in PDF
  option_c: "擔麵是清晨熱賣食品..."
  option_d: null      // ← Not in PDF
  correct_answer: "B" // ← CRITICAL ERROR: B is null!

Result: CRITICAL ERROR - Answer points to empty option
```

**Why This Matters:**
- Legacy crawler failed because it didn't validate this
- 1,221 questions (15.3%) had this issue
- Prevents corrupted data in production database

### Gate 5: Option Insufficiency ⚠️ CRITICAL
**Rule:** `available_options >= 2` (at least 2 non-null options)

Handles combination-style questions properly:
- Normal question: `[A, B, C, D]` → Valid
- Combination question: `[A, null, C, null]` → Valid (only 2 options shown)
- Broken question: `[A, null, null, null]` → Invalid (only 1 option)

### Gate 6: Answer Coverage ⚠️ CRITICAL
**Rule:** `all(question_number in answer_map)`

Every question must have a corresponding answer.

---

## Combination-Style Questions (組合式題)

Some Taiwan civil service exams use "combination-style questions" where only certain judgments/options are presented.

### Example
```
Question 5: 下列敘述何者正確？
① 政府應保護人民知識產權
③ 著作權可無限期續展
④ 著作權人可拋棄著作權

Note: ② is deliberately omitted from the PDF
```

### How Legacy Crawler Failed
```python
# Old code assumed all 4 options always present
options = {
    "A": "選項1文字",
    "B": "",           # ← Returned empty string
    "C": "選項3文字",
    "D": "",           # ← Returned empty string
}
correct_answer = "B"   # ← ERROR: Points to empty string!
```

### How Modern Pipeline Handles It
```json
{
  "question_number": 5,
  "question_text": "下列敘述何者正確？",
  "options": {
    "A": "政府應保護人民知識產權",
    "B": null,          // ← Set to null (not empty string)
    "C": "著作權可無限期續展",
    "D": "著作權人可拋棄著作權"
  },
  "correct_answer": "A"  // ← Valid: points to non-null option
}
```

---

## Usage Examples

### Python Client Example
```python
import requests
from pathlib import Path

# Prepare files
question_pdf = open("questions.pdf", "rb")
answer_pdf = open("answers.pdf", "rb")

files = {
    "question_pdf": question_pdf,
    "answer_pdf": answer_pdf,
}

data = {
    "exam_code": "P",
    "category_code": "01",
    "subject_code": "0101",
    "exam_name": "114年初等考試",
}

# Extract and validate (without importing)
response = requests.post(
    "http://localhost:8000/api/v1/exam-import/extract",
    files=files,
    data=data,
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
print(f"✓ Extracted {result['exam_info']['total_questions']} questions")
print(f"✓ Valid: {result['validation']['valid_questions']}")
print(f"✓ Can import: {result['can_import']}")

if result['can_import']:
    # Proceed with import
    import_response = requests.post(
        "http://localhost:8000/api/v1/exam-import/import",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"✓ Import successful!")
```

### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/exam-import/extract" \
  -H "Authorization: Bearer $TOKEN" \
  -F "question_pdf=@questions.pdf" \
  -F "answer_pdf=@answers.pdf" \
  -F "exam_code=P" \
  -F "category_code=01" \
  -F "subject_code=0101" \
  -F "exam_name=114年初等考試"
```

---

## Implementation Status

### Phase 1: ✅ Complete
- [x] Pydantic schemas (`app/schemas/exam_import.py`)
- [x] Extraction service with Claude Vision (`app/services/exam_pdf_extraction_service.py`)
- [x] Validation gates (6 layers)
- [x] FastAPI endpoints (`app/api/exam_import.py`)
- [x] Router registration
- [x] Documentation

### Phase 2: 🔄 In Progress
- [ ] Database integration (insert questions → historical_exams)
- [ ] n8n workflow orchestration (optional)
- [ ] Async processing for large PDFs
- [ ] Batch import endpoint
- [ ] Admin dashboard for import monitoring
- [ ] Human review queue for failed validations
- [ ] Retry mechanism for transient failures

### Phase 3: 📋 Planned
- [ ] Performance optimization (caching extracted data)
- [ ] Streaming responses for large imports
- [ ] Export merged result to legacy JSON format
- [ ] Integration tests with real exam PDFs
- [ ] Migration script from legacy moex_simple.py

---

## Database Integration (Phase 2)

Current endpoint returns prepared data but doesn't persist to DB. Next phase will:

1. **Create HistoricalExam record**
   ```python
   historical_exam = HistoricalExam(
       exam_code=exam_code,
       category_code=category_code,
       subject_code=subject_code,
       exam_name=exam_name,
       import_date=datetime.now(),
       import_source="modern_pdf_pipeline_v1",
   )
   db.add(historical_exam)
   db.flush()  # Get ID
   ```

2. **Insert Questions with historical_exam_id**
   ```python
   for q in legacy_output.questions:
       question = Question(
           historical_exam_id=historical_exam.id,
           question_number=q.question_number,
           content=q.content,
           option_a=q.option_a,
           option_b=q.option_b,
           option_c=q.option_c,
           option_d=q.option_d,
           correct_answer=q.correct_answer,
       )
       db.add(question)
   db.commit()
   ```

3. **Update Subject statistics**
   ```python
   subject.available_questions = len(legacy_output.questions)
   db.commit()
   ```

---

## Comparison: Legacy vs Modern

### Legacy moex_simple.py Issues
```python
# Line 198-201: Returns empty string for missing options
options.get("A", "")  # ← Empty if not found
options.get("B", "")  # ← Empty if not found

# Line 304-308: Direct assignment without validation
q["correct_answer"] = answer_key[q_num]  # ← No check if answer is valid!
```

**Result:** 1,221 questions with answer pointing to empty option

### Modern Pipeline Validation
```python
# Validates answer validity before import
if ans_option is None or not ans_option.strip():
    errors.append(
        f"CRITICAL: Correct answer '{correct_ans}' is empty/missing in PDF. "
        f"Available options: {q.options.get_available_options()}"
    )
```

**Result:** Prevents corrupted data, provides detailed error report

---

## Troubleshooting

### Issue: "Failed to extract questions from PDF"
**Causes:**
1. PDF format not supported by Claude Vision
2. PDF is image-only (no text layer)
3. PDF is corrupted or encrypted

**Solution:**
1. Verify PDF is readable (text extraction works in Acrobat)
2. Run OCR if image-only
3. Check PDF file integrity

### Issue: "Answer validity check failed"
**Causes:**
1. Answer sheet references option not present in question PDF
2. Combination-style question with unusual option layout
3. OCR error preventing option recognition

**Solution:**
1. Review PDF manually to confirm options
2. Check if it's a combination question (intentional)
3. Re-run OCR on answer sheet

### Issue: "Validation report shows 0 questions extracted"
**Causes:**
1. Claude Vision didn't understand PDF layout
2. PDF uses non-standard format
3. Question numbers not recognized

**Solution:**
1. Check PDF format against exam catalog
2. Verify exam code/category/subject are correct
3. Try manually extracting single page first

---

## Integration with n8n (Phase 2 Optional)

For non-linear workflows, can optionally use n8n:

```
[PDF Upload] → [Extract Questions] → [Extract Answers] → [Validate]
                                                            ↓
                                    [If Valid] → [Import to DB]
                                    ↓
                                    [If Invalid] → [Human Review Queue]
```

Benefits:
- Retry failed extractions automatically
- Queue for manual review without blocking
- Monitor import progress in real-time
- Scale to multiple PDF imports

---

## References

- **Schemas:** `backend/app/schemas/exam_import.py`
- **Service:** `backend/app/services/exam_pdf_extraction_service.py`
- **API:** `backend/app/api/exam_import.py`
- **Legacy Crawler:** `backend/scripts/crawlers/moex_simple.py` (for migration)
- **Tests:** `backend/tests/features/` (BDD test plans in progress)

---

## Next Steps

1. **Immediate:** Test with real exam PDFs (phase 2 data fixture)
2. **Week 2:** Implement database import logic
3. **Week 3:** Add n8n workflow (optional)
4. **Week 4:** Performance testing at scale
5. **Week 5:** Migrate legacy questions from moex_simple.py

---

**Status:** Ready for Phase 2 implementation
**Last Updated:** 2026-04-10
**Maintainer:** CertiMate AI Team
