# MCP (Model Context Protocol) API Contract for CertiMate

**Version:** 1.0.0  
**Last Updated:** 2026-04-10  
**Status:** Phase 1 (Context & Recommendation Servers)

---

## Overview

This document defines the JSON request/response contract for all MCP Server functions in CertiMate. MCP servers provide structured access to user context, intelligent recommendations, and data fetching capabilities.

### Design Principles

- **Consistency:** All responses follow the same `MCPResponse` structure
- **Traceability:** All requests include `user_id` where applicable
- **Versioning:** API contract is versioned independently from code
- **Extensibility:** Fields are added without breaking existing clients
- **Documentation:** Each function includes examples and error cases

---

## Standard Response Format

All MCP responses follow this structure:

```json
{
  "success": true,
  "data": { /* function-specific data */ },
  "error": null
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "error_type",
    "message": "Human-readable error message",
    "details": { /* optional context */ }
  }
}
```

### Error Types

- `not_found`: Resource doesn't exist (HTTP 404)
- `validation_error`: Request validation failed (HTTP 400)
- `internal_error`: Server error occurred (HTTP 500)
- `unauthorized`: Authentication/authorization failed (HTTP 401)
- `invalid_request`: Malformed request (HTTP 400)

---

## Context Server APIs

### 1. BuildContextForCoach

**Purpose:** Build structured learning profile for AI Coach

**Request:**

```json
{
  "function": "build_context_for_coach",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_history": [
    "How should I study algebra?",
    "You struggle with equations..."
  ]
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "weak_areas": [
      {
        "topic": "幾何",
        "mastery": 0.40,
        "error_rate": 0.60,
        "count": 8
      }
    ],
    "mastery_scores": {
      "代數": 0.75,
      "幾何": 0.40,
      "統計": 0.65
    },
    "recent_errors": [
      {
        "question_id": "q1",
        "topic": "幾何",
        "difficulty": "medium",
        "user_selected": "B",
        "correct_answer": "C",
        "user_confidence": "high",
        "answered_at": "2026-04-10T14:30:00Z"
      }
    ],
    "learning_style": {
      "preferred_modality": "visual",
      "optimal_spacing_days": 3,
      "preferred_explanation_style": "example-driven",
      "learning_pace": "medium"
    },
    "learning_streak": 5,
    "total_questions_attempted": 42,
    "average_confidence": 0.62
  }
}
```

**Error Response:**

```json
{
  "success": false,
  "error": {
    "type": "not_found",
    "message": "User 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": { "user_id": "550e8400-e29b-41d4-a716-446655440000" }
  }
}
```

### 2. FetchWeakAreaDetails

**Purpose:** Get detailed analysis of a weak area

**Request:**

```json
{
  "function": "fetch_weak_area_details",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic": "幾何"
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": {
    "topic": "幾何",
    "error_rate": 0.60,
    "total_attempts": 15,
    "error_count": 9,
    "misconceptions": [],
    "common_wrong_answers": [
      {
        "answer": "B",
        "frequency": 5,
        "percentage": 55.6
      },
      {
        "answer": "C",
        "frequency": 3,
        "percentage": 33.3
      }
    ],
    "last_attempt_date": "2026-04-09T10:15:00Z",
    "confidence_gap": 0.33
  }
}
```

### 3. GetUserLearningStyle

**Purpose:** Get user's learning preferences

**Request:**

```json
{
  "function": "get_user_learning_style",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": {
    "preferred_modality": "visual",
    "optimal_spacing_days": 3,
    "preferred_explanation_style": "example-driven",
    "learning_pace": "medium"
  }
}
```

### 4. FetchRecentErrors

**Purpose:** Get recent wrong answers with context

**Request:**

```json
{
  "function": "fetch_recent_errors",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "limit": 10
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": [
    {
      "question_id": "q1",
      "topic": "幾何",
      "difficulty": "medium",
      "user_selected": "B",
      "correct_answer": "C",
      "user_confidence": "high",
      "answered_at": "2026-04-09T10:15:00Z"
    },
    {
      "question_id": "q2",
      "topic": "代數",
      "difficulty": "hard",
      "user_selected": "No answer",
      "correct_answer": "D",
      "user_confidence": "low",
      "answered_at": "2026-04-08T15:30:00Z"
    }
  ]
}
```

---

## Recommendation Server APIs

### 1. RecommendQuestions

**Purpose:** Recommend questions based on mastery and spacing

**Request:**

```json
{
  "function": "recommend_questions",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "count": 5,
  "filters": {
    "topic": "代數",
    "min_difficulty": 1,
    "max_difficulty": 10,
    "bloom_level": "apply"
  }
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": [
    {
      "question_id": "q10",
      "topic": "代數",
      "difficulty_level": 6,
      "bloom_level": "apply",
      "reason": "Due for spaced repetition; Low mastery (35%); Confidence calibration needed",
      "mastery_score": 0.35,
      "spacing_days": 0,
      "prerequisite_ready": true,
      "confidence_calibration_ready": true
    },
    {
      "question_id": "q11",
      "topic": "代數",
      "difficulty_level": 5,
      "bloom_level": "understand",
      "reason": "Low mastery (42%)",
      "mastery_score": 0.42,
      "spacing_days": 2,
      "prerequisite_ready": true,
      "confidence_calibration_ready": false
    }
  ]
}
```

**Empty Result:**

```json
{
  "success": true,
  "data": []
}
```

### 2. CalculateOptimalSpacing

**Purpose:** Calculate Ebbinghaus-based spaced repetition interval

**Request:**

```json
{
  "function": "calculate_optimal_spacing",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_id": "q10"
}
```

**Response (Success - First Attempt):**

```json
{
  "success": true,
  "data": {
    "next_review_date": "2026-04-11",
    "days_from_today": 1,
    "ebbinghaus_interval": 1,
    "reasoning": "First attempt - initial review",
    "confidence_factor": 1.0
  }
}
```

**Response (Success - Later Attempt with Adjustment):**

```json
{
  "success": true,
  "data": {
    "next_review_date": "2026-04-28",
    "days_from_today": 18,
    "ebbinghaus_interval": 14,
    "reasoning": "Ebbinghaus interval 14 days, adjusted 1.2x for confidence",
    "confidence_factor": 1.2
  }
}
```

**Ebbinghaus Intervals:**
- After 1st correct: 1 day
- After 2nd correct: 3 days
- After 3rd correct: 7 days
- After 4th correct: 14 days
- After 5th correct: 30 days
- After 6th correct: 60 days
- After 7th correct: 120 days

**Confidence Adjustments:**
- Underconfident (Low confidence but correct): `confidence_factor > 1.0` (extend interval)
- Overconfident (High confidence but incorrect): `confidence_factor < 1.0` (reduce interval)
- Normal: `confidence_factor = 1.0`

### 3. SuggestLearningPath

**Purpose:** Suggest dependency-aware learning sequence

**Request:**

```json
{
  "function": "suggest_learning_path",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_topic": "微積分"
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": [
    {
      "topic": "基礎運算",
      "concept_id": "concept_arithmetic",
      "prerequisites": [],
      "difficulty": 2,
      "estimated_hours": 2.0,
      "is_prerequisite_met": true,
      "mastery_progress": 0.0
    },
    {
      "topic": "代數",
      "concept_id": "concept_algebra",
      "prerequisites": ["concept_arithmetic"],
      "difficulty": 4,
      "estimated_hours": 4.0,
      "is_prerequisite_met": false,
      "mastery_progress": 0.35
    },
    {
      "topic": "微積分",
      "concept_id": "concept_calculus",
      "prerequisites": ["concept_algebra", "concept_trigonometry"],
      "difficulty": 7,
      "estimated_hours": 6.0,
      "is_prerequisite_met": false,
      "mastery_progress": 0.0
    }
  ]
}
```

### 4. ValidateKnowledgeNodeQuality

**Purpose:** Validate quality of extracted knowledge nodes

**Request:**

```json
{
  "function": "validate_knowledge_node_quality",
  "node_data": {
    "concept_name": "積分",
    "definition": "計算面積下的數學方法",
    "examples": ["∫x²dx = x³/3 + C"],
    "related_concepts": ["微分", "極限"],
    "prerequisite_concepts": ["微分"]
  }
}
```

**Response (Valid):**

```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "issues": [],
    "score": 1.0,
    "recommendations": []
  }
}
```

**Response (Invalid - Missing Fields):**

```json
{
  "success": true,
  "data": {
    "is_valid": false,
    "issues": [
      {
        "type": "missing_definition",
        "severity": "high"
      },
      {
        "type": "missing_examples",
        "severity": "medium"
      }
    ],
    "score": 0.42,
    "recommendations": [
      "Add comprehensive definition",
      "Add at least 2-3 concrete examples"
    ]
  }
}
```

**Issue Types & Severity:**
- `missing_concept_name` (high): Impact -0.3
- `missing_definition` (high): Impact -0.3
- `missing_examples` (medium): Impact -0.2
- `insufficient_examples` (low): Impact -0.1
- `missing_relationships` (low): Impact -0.1

**Quality Score Formula:**
- Start: 1.0
- Subtract severity impacts
- Min: 0.0, Max: 1.0
- Valid threshold: ≥ 0.6

---

## Data Fetching Server APIs (Phase 2)

### 1. FetchContextForGeneration

**Purpose:** Get relevant document chunks for RAG

**Request:**

```json
{
  "function": "fetch_context_for_generation",
  "doc_id": "doc_123",
  "topic": "代數"
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": [
    {
      "chunk_id": "chunk_1",
      "content": "二次方程式是形如 ax² + bx + c = 0 的方程式...",
      "source_doc_id": "doc_123",
      "page_number": 45,
      "section_title": "二次方程式",
      "relevance_score": 0.95,
      "metadata": { "language": "zh", "grade_level": "10" }
    }
  ]
}
```

### 2. ExtractKnowledgeNodes

**Purpose:** Extract structured knowledge nodes from text

**Request:**

```json
{
  "function": "extract_knowledge_nodes",
  "document_text": "二次方程式...",
  "taxonomy": "bloom"
}
```

**Response (Success):**

```json
{
  "success": true,
  "data": [
    {
      "concept_name": "二次方程式",
      "definition": "形如 ax² + bx + c = 0 的方程式",
      "examples": ["x² - 3x + 2 = 0"],
      "related_concepts": ["一次方程式", "因式分解"],
      "prerequisite_concepts": ["基礎代數"],
      "bloom_level": "understand",
      "source_doc_id": "doc_123",
      "source_page": 45
    }
  ]
}
```

---

## Error Handling

### Common Error Scenarios

1. **User Not Found (404):**
```json
{
  "success": false,
  "error": {
    "type": "not_found",
    "message": "User 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": { "user_id": "550e8400-e29b-41d4-a716-446655440000" }
  }
}
```

2. **Validation Error (400):**
```json
{
  "success": false,
  "error": {
    "type": "validation_error",
    "message": "count must be between 1 and 50",
    "details": { "field": "count", "value": 0, "constraint": "1-50" }
  }
}
```

3. **Internal Error (500):**
```json
{
  "success": false,
  "error": {
    "type": "internal_error",
    "message": "Database connection failed",
    "details": { "error": "Connection timeout after 30s" }
  }
}
```

---

## Rate Limiting & Caching

### Caching Recommendations

| Function | TTL | Key Generation |
|----------|-----|-----------------|
| `build_context_for_coach` | 5 min | `{function}:{user_id}` |
| `get_user_learning_style` | 1 hour | `{function}:{user_id}` |
| `recommend_questions` | 5 min | `{function}:{user_id}:{filters_hash}` |
| `validate_knowledge_node_quality` | No cache | - |

### Rate Limits

- Per user, per minute: 100 requests
- Per function, per minute: 1,000 requests
- Burst allowance: 20 requests over 1 second

---

## Integration Points

### AI Coach Service
- Calls: `build_context_for_coach`, `fetch_weak_area_details`, `fetch_recent_errors`
- Purpose: Provide user context for intelligent tutoring

### Schedule Service
- Calls: `recommend_questions`, `calculate_optimal_spacing`
- Purpose: Intelligent question scheduling using Ebbinghaus curve

### Knowledge Map Service
- Calls: `validate_knowledge_node_quality`
- Purpose: Validate AI-generated knowledge nodes before insertion

### Retrieval Service (RAG)
- Calls: `fetch_context_for_generation` (Phase 2)
- Purpose: Fetch relevant document chunks for context

---

## Versioning

**Current Version:** 1.0.0 (Phase 1)

- **Phase 1:** Context Server, Recommendation Server
- **Phase 2:** Data Fetching Server, RAG integration
- **Future:** Additional servers based on AI needs

### Backward Compatibility

All future changes will:
- Add new fields without removing old ones
- Introduce new endpoints rather than modifying existing ones
- Support client fallbacks for missing fields

---

## Testing & Validation

All MCP functions have:
- ✅ Unit tests (via BDD step definitions)
- ✅ Integration tests (via BDD scenarios)
- ✅ Contract tests (response structure validation)
- ✅ Load tests (planned for Phase 3)
- ✅ Error handling tests

See `backend/tests/features/30-mcp-context.feature` and `31-mcp-recommendation.feature`.
