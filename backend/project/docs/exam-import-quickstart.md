# Modern Exam PDF Import — Quick Start Guide

**For:** Developers & Administrators  
**Time to read:** 5 minutes  
**Setup time:** <1 minute  

---

## What This Does

Extracts exam questions from PDF files using AI (Claude Vision) and validates them before importing to database.

**One-liner:** Replaces brittle regex-based crawler with modern PDF parsing that prevents data corruption.

---

## How to Use It

### Option 1: Simple Validation Only

Just extract and validate PDFs without importing:

```bash
curl -X POST "http://localhost:8000/api/v1/exam-import/extract" \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -F "question_pdf=@questions.pdf" \
  -F "answer_pdf=@answers.pdf" \
  -F "exam_code=P" \
  -F "category_code=01" \
  -F "subject_code=0101" \
  -F "exam_name=114年初等考試"
```

**Response:**
- ✅ If valid: `"can_import": true`
- ❌ If invalid: `"can_import": false` + detailed errors

### Option 2: Extract + Validate + Import

Full pipeline (import to database):

```bash
curl -X POST "http://localhost:8000/api/v1/exam-import/import" \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -F "question_pdf=@questions.pdf" \
  -F "answer_pdf=@answers.pdf" \
  -F "exam_code=P" \
  -F "category_code=01" \
  -F "subject_code=0101"
```

**Response:**
- ✅ `"import_success": true` or
- ❌ `"import_success": false` + validation errors

### Option 3: Admin Override

Skip validation gates (use with caution):

```bash
curl -X POST "http://localhost:8000/api/v1/exam-import/import" \
  ...params... \
  -F "skip_validation=true"
```

---

## Python Client Example

```python
import requests
import json

# Configuration
API_URL = "http://localhost:8000/api/v1/exam-import"
TOKEN = "your_jwt_token_here"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Step 1: Extract and validate
with open("questions.pdf", "rb") as qf, open("answers.pdf", "rb") as af:
    files = {
        "question_pdf": qf,
        "answer_pdf": af,
    }
    data = {
        "exam_code": "P",
        "category_code": "01",
        "subject_code": "0101",
        "exam_name": "114年初等考試",
    }
    
    response = requests.post(
        f"{API_URL}/extract",
        headers=HEADERS,
        files=files,
        data=data
    )

result = response.json()

# Check validation results
if result["can_import"]:
    print(f"✅ Validation passed!")
    print(f"   Valid questions: {result['summary']['valid_questions']}")
    
    # Step 2: Import (if validation passed)
    with open("questions.pdf", "rb") as qf, open("answers.pdf", "rb") as af:
        files = {
            "question_pdf": qf,
            "answer_pdf": af,
        }
        import_response = requests.post(
            f"{API_URL}/import",
            headers=HEADERS,
            files=files,
            data=data
        )
    
    import_result = import_response.json()
    if import_result["import_success"]:
        print(f"✅ Import successful: {import_result['message']}")
else:
    print(f"❌ Validation failed!")
    for error in result["validation"]["critical_errors"]:
        print(f"   ERROR: {error}")
    
    # Show details for each failed question
    for detail in result["validation"]["validation_details"]:
        if not detail["is_valid"]:
            print(f"   Q{detail['question_number']}: {detail['errors']}")
```

---

## What Gets Validated

The system runs 6 validation "gates" on every import:

| # | Check | What It Does |
|---|-------|---|
| 1️⃣ | **Count Match** | Questions PDF ≠ Answers PDF → ERROR |
| 2️⃣ | **Sequential** | Missing question numbers → ERROR |
| 3️⃣ | **Text Length** | Suspiciously long text → WARNING |
| 4️⃣ | **Answer Validity** ⭐ | Answer points to empty option → **CRITICAL ERROR** |
| 5️⃣ | **Options** | Question has <2 options → ERROR |
| 6️⃣ | **Coverage** | Question missing from answers → ERROR |

### Gate 4 (The Important One)

If a question has:
```json
{
  "options": {
    "A": "This is option A",
    "B": null,                    // ← Not in the PDF
    "C": "This is option C",
    "D": null
  },
  "correct_answer": "B"          // ← ERROR! B doesn't exist!
}
```

It will fail validation with:
```
CRITICAL: Correct answer 'B' is empty/missing in PDF. 
Available options: ['A', 'C']
```

**Why?** This prevents corrupting your database with questions where the "correct" answer isn't actually in the PDF.

---

## Common Patterns

### Pattern 1: Check Before Import

```python
# Best practice: Always validate first
extract = requests.post(f"{API_URL}/extract", ...)
if extract.json()["can_import"]:
    import_result = requests.post(f"{API_URL}/import", ...)
```

### Pattern 2: Handle Errors Gracefully

```python
response = requests.post(f"{API_URL}/extract", ...)
result = response.json()

if not result.get("extraction_successful"):
    print("PDF extraction failed:")
    for error in result.get("details", []):
        print(f"  - {error}")
    exit(1)

if not result["can_import"]:
    print("Validation failed:")
    for error in result["validation"]["critical_errors"]:
        print(f"  CRITICAL: {error}")
    exit(1)

print("✅ Ready to import")
```

### Pattern 3: Combination Questions

If you have PDFs with combination-style questions (partial options shown):

```json
{
  "question_number": 5,
  "question_text": "下列敘述何者正確？",
  "options": {
    "A": "First judgment statement",
    "B": null,              // ← Not shown in PDF (intentional)
    "C": "Third judgment statement",
    "D": null               // ← Not shown in PDF (intentional)
  }
}
```

The system handles this correctly! Options that aren't in the PDF are `null` (not empty strings), so validation works properly.

---

## Troubleshooting

### "Failed to extract questions from PDF"

**Causes:**
1. PDF is image-only (no text layer) → Need OCR
2. PDF is damaged → Re-download the PDF
3. PDF format is unusual → Check exam catalog

**Fix:**
```bash
# Verify PDF is readable
pdftotext questions.pdf - | head  # Should show text

# If no text, need OCR:
# Use tools like: tesseract, pytesseract, or upload to Claude Vision manually
```

### "CRITICAL: Correct answer 'B' is empty/missing"

**This is correct behavior!** The system prevented data corruption.

**Options:**
1. Check the PDF manually — is option B actually there?
2. If it's a combination question, this is expected
3. Use admin override only if you're certain: `skip_validation=true`

### "Question count mismatch: 50 questions but 48 expected"

**Cause:** Question and Answer PDFs have different counts.

**Fix:**
1. Verify both PDFs are from the same exam
2. Re-download if corrupted
3. Check answer key — does it really have 48 answers?

### "No answer found for question 25"

**Cause:** Question PDF has Q25, but Answer PDF doesn't.

**Fix:**
1. Verify Answer PDF is complete
2. Check if Q25 should really have an answer
3. Add missing answer manually if appropriate

---

## API Response Format

### Success Response (Extract)
```json
{
  "extraction_successful": true,
  "exam_info": {
    "exam_code": "P",
    "category_code": "01",
    "subject_code": "0101",
    "exam_name": "114年初等考試",
    "total_questions": 50
  },
  "validation": {
    "total_questions": 50,
    "valid_questions": 48,
    "invalid_questions": 2,
    "can_proceed": false,
    "critical_errors": [
      "CRITICAL: Correct answer 'B' is empty/missing in PDF..."
    ],
    "validation_details": [...]
  },
  "can_import": false
}
```

### Error Response
```json
{
  "error": true,
  "status_code": 400,
  "message": "Failed to extract questions from PDF",
  "details": [
    "Error message 1",
    "Error message 2"
  ]
}
```

---

## Configuration

**Environment Variables:**
- `ANTHROPIC_API_KEY` — Required (for Claude Vision)
  - Get from: https://console.anthropic.com/

**That's it!** No other configuration needed.

---

## Limitations (Phase 1)

❌ Not yet supported:
- Batch imports (multiple PDFs at once)
- Progress monitoring (takes 30-60 seconds per PDF)
- Background job processing
- Web UI (API only)

✅ Supported:
- Single PDF extraction
- Validation gating
- Detailed error messages
- Admin override
- Backward compatibility

---

## Next Steps (Phase 2)

Coming soon:
- Database integration (persistent storage)
- Async processing (no more 60-second wait)
- Batch import endpoint
- Admin dashboard for monitoring
- Human review queue for failures
- Scheduled retry mechanism

---

## Need Help?

1. **Read the full guide:** `backend/project/docs/exam-import-modern-pipeline.md`
2. **Check implementation:** `EXAM_IMPORT_IMPLEMENTATION.md`
3. **See the code:** `backend/app/services/exam_pdf_extraction_service.py`
4. **Browse schemas:** `backend/app/schemas/exam_import.py`
5. **Review tests:** `backend/tests/features/32-考古題現代化匯入.feature`

---

## Quick Test

Try it right now:

```bash
# 1. Start backend
cd backend
.venv/bin/python -m uvicorn app.main:app --reload

# 2. In another terminal, test the endpoint
curl -X GET "http://localhost:8000/api/v1/exam-import/validation-schema" \
  -H "Authorization: Bearer test_token"

# 3. You should see the validation rules documentation
```

---

**Last Updated:** 2026-04-10  
**Status:** Phase 1 Complete, Ready for Phase 2  
