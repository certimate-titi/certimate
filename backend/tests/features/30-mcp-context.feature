# MCP Context Server — Structured User Learning Context
# =========================================================
# Purpose: Verify Context Server provides accurate user profiling
#
# Context Server Functions:
# - build_context_for_coach: Aggregate mastery, weak areas, recent errors
# - fetch_weak_area_details: Detailed error analysis for a topic
# - get_user_learning_style: User's learning preferences
# - fetch_recent_errors: Recent wrong answers with context

@backend
Feature: MCP Context Server builds structured user learning profiles

  @context_server
  Scenario: Build coach context with multiple weak areas
    Given a user named "coach_user" exists
    And user "coach_user" has answered 20 questions in "代數" subject
    And user "coach_user" got 15 correct answers (75% mastery)
    And user "coach_user" has answered 15 questions in "幾何" subject
    And user "coach_user" got 6 correct answers (40% mastery)
    And user "coach_user" has recent errors with various confidence levels

    When MCP Context Server builds context for "coach_user"

    Then the context includes "coach_user" user_id
    And the context shows mastery score for "代數" is 0.75
    And the context shows mastery score for "幾何" is 0.40
    And the context identifies "幾何" as a weak area (below 0.6 threshold)
    And the context does not identify "代數" as a weak area
    And the context includes recent_errors list
    And the context includes total_questions_attempted count
    And the context includes average_confidence score

  @context_server
  Scenario: Build context shows learning streak
    Given a user named "streak_user" exists
    And user "streak_user" attempted questions on today's date
    And user "streak_user" attempted questions yesterday
    And user "streak_user" attempted questions 2 days ago
    And user "streak_user" did not attempt on 3 days ago

    When MCP Context Server builds context for "streak_user"

    Then the context shows learning_streak of 3 days

  @context_server
  Scenario: Fetch weak area details shows error patterns
    Given a user named "weak_area_user" exists
    And user "weak_area_user" has 10 wrong answers in "代數" subject
    And user "weak_area_user" has 5 total attempts in "代數" subject
    And these wrong answers used options: ["B", "B", "C", "B", "A", "B", "D", "B", "C", "B"]

    When fetch weak area details for "weak_area_user" in "代數"

    Then weak area detail shows topic "代數"
    And error_rate is 2.0 (10 errors / 5 total attempts)
    And error_count is 10
    And total_attempts is 5
    And common_wrong_answers shows "B" as most frequent wrong answer
    And common_wrong_answers shows frequency distribution

  @context_server
  Scenario: Fetch weak area details with high confidence errors
    Given a user named "confidence_user" exists
    And user "confidence_user" has wrong answer with confidence "high"
    And user "confidence_user" has 5 wrong answers in "幾何" subject

    When fetch weak area details for "confidence_user" in "幾何"

    Then weak area detail shows confidence_gap > 0
    And confidence_gap indicates overconfidence (high confidence but wrong)

  @context_server
  Scenario: Fetch recent errors returns last N wrong answers
    Given a user named "error_user" exists
    And user "error_user" has 15 wrong answers with timestamps

    When fetch recent errors for "error_user" with limit 10

    Then recent errors list contains 10 entries
    And each error includes: question_id, topic, difficulty, user_selected, correct_answer
    And errors are ordered by most recent first (descending timestamp)
    And each error includes answered_at timestamp in ISO format

  @context_server
  Scenario: Handle user not found
    When MCP Context Server builds context for user "nonexistent_user_12345"

    Then response includes error
    And error type is "not_found"
    And error message mentions user not found

  @context_server
  Scenario: Context includes no weak areas when all mastery high
    Given a user named "master_user" exists
    And user "master_user" has 90% mastery in "代數"
    And user "master_user" has 85% mastery in "幾何"
    And user "master_user" has 88% mastery in "統計"

    When MCP Context Server builds context for "master_user"

    Then the context weak_areas list is empty
    And all mastery_scores are above 0.6 threshold
