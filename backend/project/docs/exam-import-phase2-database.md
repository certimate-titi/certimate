# Phase 2: Database Integration — Complete Guide

**Status:** Implementation Complete ✅  
**What:** Persistent storage of extracted exam questions  
**Where:** `backend/app/services/historical_exam_import_service.py`  
**API:** 4 new endpoints in `backend/app/api/exam_import.py`

---

## Overview

Phase 2 connects the extraction pipeline (Phase 1) with the database, allowing imported questions to be permanently stored and retrieved.

### Architecture

```
PDF Upload
    ↓
[Phase 1: Extract & Validate]
├─ Claude Vision
├─ Structured Outputs
├─ 6-layer validation
└─ Returns: LegacyImportOutput
    ↓
[Phase 2: DATABASE IMPORT] ← NEW
├─ HistoricalExamImportService
├─ Create HistoricalExam record
├─ Batch insert Questions
├─ Update Subject statistics
└─ Commit transaction
    ↓
Database (PostgreSQL)
├─ historical_exams table
├─ questions table (with historical_exam_id FK)
└─ subjects (updated)
```

---

## What Was Built

### 1. HistoricalExamImportService (`historical_exam_import_service.py`)

**Main Service Class** with 5 methods:

#### Method 1: `import_exam_paper()`
**Imports extracted questions to database**

```python
result = import_service.import_exam_paper(
    legacy_output=extracted_data,
    exam_code="P",
    category_code="01",
    subject_code="0101",
    exam_name="114年初等考試",
    skip_existing=False,
)
```

**What it does:**
1. ✅ Check if exam already exists (unique constraint: exam_code + category_code + subject_code)
2. ✅ Create or update `HistoricalExam` record
3. ✅ Batch insert `Question` records with `historical_exam_id` FK
4. ✅ Update `Subject.available_questions` statistics
5. ✅ Handle failures with rollback

**Response:**
```json
{
  "error": false,
  "import_success": true,
  "message": "Successfully imported 50 questions",
  "exam_id": "uuid-here",
  "questions_imported": 50,
  "questions_failed": 0
}
```

#### Method 2: `get_import_status()`
**Check if exam is in database**

```python
status = import_service.get_import_status(
    exam_code="P",
    category_code="01", 
    subject_code="0101"
)
```

**Returns:**
```json
{
  "found": true,
  "exam_id": "uuid",
  "exam_code": "P",
  "exam_name": "114年初等考試",
  "total_questions": 50,
  "actual_questions": 50,
  "created_at": "2026-04-10T12:00:00",
  "source": "Claude Vision Pipeline"
}
```

#### Method 3: `list_historical_exams()`
**Paginated list of all imported exams**

```python
exams = import_service.list_historical_exams(
    limit=20,
    offset=0,
    exam_code="P"  # Optional filter
)
```

#### Method 4: `get_exam_questions()`
**Get all questions from an exam**

```python
questions = import_service.get_exam_questions(
    exam_code="P",
    category_code="01",
    subject_code="0101",
    limit=50,
    offset=0
)
```

**Returns:** Paginated list of questions with full details

#### Method 5: `validate_import()`
**Post-import validation**

```python
validation = import_service.validate_import(
    exam_code="P",
    category_code="01",
    subject_code="0101"
)
```

**Checks:**
- ✅ Non-sequential question numbers
- ✅ Empty content
- ✅ Invalid answers (not A-D)
- ✅ Insufficient options
- ✅ Answers pointing to empty options

---

## Database Schema

### HistoricalExam Table
```
historical_exams
├── id (UUID, PK)
├── exam_code (String) ─┐
├── category_code (String) ├─ UNIQUE constraint
├── subject_code (String) ─┘
├── exam_name (String)
├── category_name (String)
├── subject_name (String)
├── total_questions (Integer)
├── source (String, default: "Claude Vision Pipeline")
├── year (Integer)
├── tenant_id (UUID, nullable, for multi-tenancy)
└── created_at (DateTime)
```

### Question Table (Updated Fields)
```
questions
├── id (UUID, PK)
├── historical_exam_id (UUID, FK → HistoricalExam) ← NEW
├── question_number (Integer)
├── content (Text)
├── option_a, option_b, option_c, option_d (Text)
├── correct_answer (String)
├── explanation (Text)
├── bloom_category (Enum)
├── validation_model (String, default: "modern_pdf_pipeline_v1")
├── quality_flag (String, default: "ok")
├── flag_reason (Text)
├── historical_source (String)
├── tenant_id (UUID)
└── created_at (DateTime)
```

### Subject Table (Updated)
```
subjects
├── ...existing fields...
└── available_questions (Integer) ← Updated after import
```

---

## API Endpoints

### 1. Import Endpoint (Updated)
```http
POST /api/v1/exam-import/import
```

**Now includes database persistence.**

Request:
```bash
curl -X POST http://localhost:8000/api/v1/exam-import/import \
  -F "question_pdf=@questions.pdf" \
  -F "answer_pdf=@answers.pdf" \
  -F "exam_code=P" \
  -F "category_code=01" \
  -F "subject_code=0101"
```

Response:
```json
{
  "error": false,
  "import_success": true,
  "message": "Successfully imported 50 questions",
  "exam_id": "550e8400-e29b-41d4-a716-446655440000",
  "exam_info": {
    "exam_code": "P",
    "total_questions": 50,
    "questions_imported": 50
  }
}
```

### 2. List Exams Endpoint (NEW)
```http
GET /api/v1/exam-import/exams?limit=20&offset=0&exam_code=P
```

Returns paginated list of all imported exams.

### 3. Get Exam Status Endpoint (NEW)
```http
GET /api/v1/exam-import/exams/{exam_code}/{category_code}/{subject_code}
```

Get details about a specific imported exam.

### 4. Get Questions Endpoint (NEW)
```http
GET /api/v1/exam-import/exams/{exam_code}/{category_code}/{subject_code}/questions?limit=50&offset=0
```

Get paginated questions from an exam.

### 5. Validate Exam Endpoint (NEW)
```http
POST /api/v1/exam-import/exams/{exam_code}/{category_code}/{subject_code}/validate
```

Run post-import validation checks.

---

## Usage Examples

### Example 1: Complete Import Flow
```python
import requests

# Step 1: Extract and validate
extract_response = requests.post(
    "http://localhost:8000/api/v1/exam-import/extract",
    headers={"Authorization": f"Bearer {token}"},
    files={
        "question_pdf": open("questions.pdf", "rb"),
        "answer_pdf": open("answers.pdf", "rb"),
    },
    data={
        "exam_code": "P",
        "category_code": "01",
        "subject_code": "0101",
    }
)

extract = extract_response.json()
if not extract["can_import"]:
    print("Validation failed")
    exit(1)

# Step 2: Import to database
import_response = requests.post(
    "http://localhost:8000/api/v1/exam-import/import",
    headers={"Authorization": f"Bearer {token}"},
    files={
        "question_pdf": open("questions.pdf", "rb"),
        "answer_pdf": open("answers.pdf", "rb"),
    },
    data={
        "exam_code": "P",
        "category_code": "01",
        "subject_code": "0101",
    }
)

result = import_response.json()
if result["import_success"]:
    exam_id = result["exam_id"]
    print(f"✅ Imported exam {exam_id}")
    
    # Step 3: Verify in database
    verify = requests.get(
        f"http://localhost:8000/api/v1/exam-import/exams/P/01/0101",
        headers={"Authorization": f"Bearer {token}"}
    )
    status = verify.json()
    print(f"Questions in DB: {status['actual_questions']}")
```

### Example 2: List All Imported Exams
```python
response = requests.get(
    "http://localhost:8000/api/v1/exam-import/exams?limit=50&offset=0",
    headers={"Authorization": f"Bearer {token}"}
)

exams = response.json()
for exam in exams["exams"]:
    print(f"{exam['exam_code']}/{exam['category_code']}: {exam['total_questions']} questions")
```

### Example 3: Get Questions from Exam
```python
response = requests.get(
    "http://localhost:8000/api/v1/exam-import/exams/P/01/0101/questions?limit=5&offset=0",
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
for q in result["questions"]:
    print(f"Q{q['question_number']}: {q['content'][:50]}...")
    print(f"  Answer: {q['correct_answer']}")
```

### Example 4: Validate Imported Exam
```python
response = requests.post(
    "http://localhost:8000/api/v1/exam-import/exams/P/01/0101/validate",
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
if result["valid"]:
    print(f"✅ Exam is valid ({result['total_questions']} questions)")
else:
    print("❌ Validation errors:")
    for error in result["errors"]:
        print(f"  {error}")
```

---

## Data Flow

### Input: LegacyImportOutput
```json
{
  "import_meta": {
    "source": "Claude Vision Pipeline",
    "exam_code": "P",
    "category_code": "01",
    "subject_code": "0101",
    "total_questions": 50,
    "questions_with_answer": 50
  },
  "questions": [
    {
      "question_number": 1,
      "content": "題目文字...",
      "option_a": "選項A",
      "option_b": "",  // Empty if not in PDF
      "option_c": "選項C",
      "option_d": "",  // Empty if not in PDF
      "correct_answer": "A",
      "explanation": ""
    }
    // ... 50 questions total
  ]
}
```

### Processing
```
1. Create HistoricalExam
   └─ exam_id = uuid4()
   
2. For each question:
   └─ Create Question with historical_exam_id = exam_id
   
3. Update Subject statistics
   └─ available_questions += 50
   
4. Commit transaction
```

### Output: Database State
```
historical_exams
├─ id: uuid
├─ exam_code: "P"
├─ category_code: "01"
├─ subject_code: "0101"
├─ total_questions: 50
└─ created_at: 2026-04-10T12:00:00Z

questions (50 rows)
├─ historical_exam_id: uuid (same as above)
├─ question_number: 1, 2, 3, ..., 50
├─ content: "題目文字..."
├─ option_a, option_b, option_c, option_d
├─ correct_answer: "A", "B", "C", or "D"
└─ validation_model: "modern_pdf_pipeline_v1"
```

---

## Error Handling

### Duplicate Exam
```json
{
  "error": false,
  "import_success": false,
  "status_code": 200,
  "message": "Exam already exists (skipped)",
  "exam_id": "existing-uuid"
}
```

Control with `skip_existing` parameter:
- `true` — Skip if exam exists
- `false` — Update existing exam

### Database Integrity Error
```json
{
  "error": true,
  "status_code": 400,
  "message": "Database integrity error: ...",
  "questions_imported": 0
}
```

**Causes:**
- Duplicate question numbers in same exam
- Invalid foreign key references
- Constraint violations

**Resolution:** Transaction is automatically rolled back. Check data integrity.

### Partial Import Failure
```json
{
  "error": false,
  "import_success": true,
  "message": "Successfully imported 49 questions",
  "exam_id": "uuid",
  "questions_imported": 49,
  "questions_failed": 1,
  "import_errors": [
    {
      "question_number": 25,
      "error": "Invalid content"
    }
  ]
}
```

**Note:** Main transaction commits with successfully imported questions. Failed questions listed for manual review.

---

## Transaction Safety

### ACID Compliance
- **Atomicity:** Entire exam import commits or rolls back together
- **Consistency:** Unique constraint on (exam_code, category_code, subject_code) prevents duplicates
- **Isolation:** Concurrent imports on different exams work independently
- **Durability:** PostgreSQL transaction log ensures persistence

### Rollback Scenarios
```python
try:
    # All operations in a single transaction
    create_exam()      # HistoricalExam
    insert_questions() # 50 Questions
    update_subject()   # Subject.available_questions
    db.commit()        # ← All or nothing
except:
    db.rollback()      # Entire transaction reverted
```

---

## Multi-Tenancy

Questions can be filtered by `tenant_id` for multi-tenant deployments:

```python
import_service.import_exam_paper(
    legacy_output=data,
    exam_code="P",
    # ...
    tenant_id=uuid.UUID("org-12345"),  # Optional
)
```

The `tenant_id` is stored on both `HistoricalExam` and `Question` records for complete data isolation.

---

## Statistics & Monitoring

### Available Queries

**Total imported exams:**
```sql
SELECT COUNT(*) FROM historical_exams WHERE created_at > now() - interval '7 days'
```

**Total imported questions:**
```sql
SELECT COUNT(*) FROM questions WHERE historical_source IS NOT NULL
```

**Questions per exam:**
```sql
SELECT he.exam_code, COUNT(q.id) as cnt
FROM historical_exams he
LEFT JOIN questions q ON q.historical_exam_id = he.id
GROUP BY he.exam_code
```

**Import validation status:**
```sql
SELECT validation_model, COUNT(*) as cnt
FROM questions
WHERE historical_exam_id IS NOT NULL
GROUP BY validation_model
```

---

## Phase 3: Future Enhancements

### Planned Features
- [ ] Async job processing (large batch imports)
- [ ] Import status webhooks/notifications
- [ ] Question difficulty auto-calibration
- [ ] Bloom category auto-tagging
- [ ] Duplicate question detection
- [ ] Quality scoring (QA gate before import)
- [ ] Import audit log (who, when, how many)
- [ ] Rollback mechanism (delete specific import)

### Estimated Effort
- Async processing: 4-6 hours
- Quality gates: 3-4 hours
- Audit log: 2-3 hours
- Rollback mechanism: 2-3 hours

---

## Testing

### Manual Test Flow
```bash
# 1. Start backend
cd backend
.venv/bin/python -m uvicorn app.main:app --reload

# 2. Extract and validate (no import)
curl -X POST http://localhost:8000/api/v1/exam-import/extract \
  -H "Authorization: Bearer test_token" \
  -F "question_pdf=@test_questions.pdf" \
  -F "answer_pdf=@test_answers.pdf" \
  -F "exam_code=TEST" \
  -F "category_code=00" \
  -F "subject_code=0000"

# 3. Import to database
curl -X POST http://localhost:8000/api/v1/exam-import/import \
  -H "Authorization: Bearer test_token" \
  -F "question_pdf=@test_questions.pdf" \
  -F "answer_pdf=@test_answers.pdf" \
  -F "exam_code=TEST" \
  -F "category_code=00" \
  -F "subject_code=0000"

# 4. Verify in database
curl -X GET "http://localhost:8000/api/v1/exam-import/exams/TEST/00/0000" \
  -H "Authorization: Bearer test_token"

# 5. Get questions
curl -X GET "http://localhost:8000/api/v1/exam-import/exams/TEST/00/0000/questions?limit=5" \
  -H "Authorization: Bearer test_token"

# 6. Validate
curl -X POST "http://localhost:8000/api/v1/exam-import/exams/TEST/00/0000/validate" \
  -H "Authorization: Bearer test_token"
```

### BDD Tests
Update feature file `32-考古題現代化匯入.feature` with database import scenarios.

---

## Troubleshooting

### "Exam already exists"
**Cause:** Attempted to import exam with same (exam_code, category_code, subject_code)

**Solutions:**
1. Use different subject_code if legitimately different
2. Set `skip_existing=true` to skip
3. Manually delete old exam and retry

### "Database integrity error"
**Cause:** Foreign key violation or constraint failure

**Solutions:**
1. Verify HistoricalExam exists (should be created first)
2. Check for duplicate question_numbers
3. Verify all fields are valid

### "Questions not in database after import"
**Cause:** Import failed silently or transaction rolled back

**Solutions:**
1. Check import response for `import_success: false`
2. Check `questions_failed` count
3. Review import error messages
4. Check PostgreSQL error logs

---

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Database schema | ✅ Existing | HistoricalExam + Question FK in place |
| Import service | ✅ Complete | HistoricalExamImportService with 5 methods |
| API endpoints | ✅ Complete | 5 endpoints (1 updated + 4 new) |
| Transaction safety | ✅ Implemented | ACID compliant with rollback |
| Multi-tenancy | ✅ Supported | tenant_id filtering |
| Error handling | ✅ Complete | Detailed error messages + rollback |
| Statistics | ✅ Tracked | Query examples provided |
| Documentation | ✅ Complete | This guide + code comments |

---

**Last Updated:** 2026-04-10  
**Phase 2 Status:** ✅ COMPLETE  
**Next Phase:** Phase 3 (Async processing, quality gates)
