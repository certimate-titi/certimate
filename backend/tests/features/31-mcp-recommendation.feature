# MCP Recommendation Server — Intelligent Question Selection and Scheduling
# ===========================================================================
# Purpose: Verify Recommendation Server provides intelligent recommendations
#
# Recommendation Server Functions:
# - recommend_questions: Suggest questions based on mastery, spacing, prerequisites
# - calculate_optimal_spacing: Ebbinghaus curve-based review scheduling
# - suggest_learning_path: Dependency-aware learning sequences
# - validate_knowledge_node_quality: Quality validation for nodes

@backend
Feature: MCP Recommendation Server provides intelligent recommendations

  @recommendation_server
  Scenario: Recommend questions prioritizes weak areas due for review
    Given a user named "rec_user" exists
    And user "rec_user" has mastery scores: {"代數": 0.3, "幾何": 0.7, "統計": 0.5}
    And user "rec_user" last attempted "代數" question 3 days ago
    And user "rec_user" last attempted "幾何" question 1 day ago
    And user "rec_user" last attempted "統計" question 5 days ago

    When recommend 5 questions for "rec_user"

    Then recommended questions include questions from weak areas first
    And "代數" questions are prioritized (low mastery)
    And questions include spacing_days information
    And questions include mastery_score for each recommendation
    And recommendation reasons explain why (low mastery, due for review, etc.)

  @recommendation_server
  Scenario: Recommend questions respects topic filter
    Given a user named "filter_user" exists
    And available questions in "代數" subject
    And available questions in "幾何" subject

    When recommend 5 questions for "filter_user" filtered by topic "代數"

    Then all recommended questions are from "代數" topic
    And no questions from other topics are included

  @recommendation_server
  Scenario: Calculate optimal spacing after first attempt
    Given a user named "spacing_user" exists
    And user "spacing_user" has never attempted question "q1"

    When calculate optimal spacing for "spacing_user" and question "q1"

    Then spacing calculation shows next_review_date is 1 day from today
    And ebbinghaus_interval is 1
    And reasoning mentions "First attempt"

  @recommendation_server
  Scenario: Calculate optimal spacing using Ebbinghaus intervals
    Given a user named "spacing_user" exists
    And user "spacing_user" correctly answered question "q2" 2 times
    And user "spacing_user" last correctly answered "q2" today with "high" confidence

    When calculate optimal spacing for "spacing_user" and question "q2"

    Then ebbinghaus_interval is one of [1, 3, 7, 14, 30, 60, 120]
    And next_review_date is properly calculated
    And confidence_factor is applied (> 1.0 if underconfident)

  @recommendation_server
  Scenario: Calculate optimal spacing resets for incorrect answer
    Given a user named "spacing_user" exists
    And user "spacing_user" incorrectly answered question "q3" previously

    When calculate optimal spacing for "spacing_user" and question "q3"

    Then ebbinghaus_interval is 1 (reset for incorrect)
    And next_review_date is 1 day from today

  @recommendation_server
  Scenario: Calculate spacing with confidence adjustment
    Given a user named "spacing_user" exists
    And user "spacing_user" correctly answered question "q4" with confidence "low"
    And this indicates underconfidence (user got it right but was unsure)

    When calculate optimal spacing for "spacing_user" and question "q4"

    Then confidence_factor is > 1.0 (extends interval)
    And reasoning mentions confidence adjustment

  @recommendation_server
  Scenario: Calculate spacing with overconfidence penalty
    Given a user named "spacing_user" exists
    And user "spacing_user" incorrectly answered question "q5" with confidence "high"
    And this indicates overconfidence (user was wrong but confident)

    When calculate optimal spacing for "spacing_user" and question "q5"

    Then confidence_factor is < 1.0 (reduces interval)
    And next_review_date is sooner than base interval
    And reasoning mentions overconfidence

  @recommendation_server
  Scenario: Validate knowledge node quality checks all fields
    Given a knowledge node with complete data:
      | concept_name | "積分" |
      | definition   | "計算面積的數學方法" |
      | examples     | ["∫x²dx", "∫sinx dx"] |
      | related_concepts | ["微分", "極限"] |

    When validate knowledge node quality

    Then validation shows is_valid true
    And score is 1.0 (all fields present)
    And issues list is empty
    And recommendations list is empty

  @recommendation_server
  Scenario: Validate knowledge node quality detects missing fields
    Given a knowledge node with missing definition and examples:
      | concept_name | "積分" |
      | definition   | null |
      | examples     | [] |

    When validate knowledge node quality

    Then validation shows is_valid false
    And score is < 0.6
    And issues include "missing_definition" (severity: high)
    And issues include "missing_examples" (severity: medium)
    And recommendations suggest adding definition and examples

  @recommendation_server
  Scenario: Validate knowledge node quality penalizes insufficient examples
    Given a knowledge node with only 1 example:
      | concept_name | "積分" |
      | definition   | "計算面積" |
      | examples     | ["∫x²dx"] |
      | related_concepts | ["微分"] |

    When validate knowledge node quality

    Then validation shows is_valid true
    And score is between 0.7 and 0.9
    And issues include "insufficient_examples" (severity: low)
    And recommendations suggest adding more examples

  @recommendation_server
  Scenario: Suggest learning path for single topic
    Given a user named "path_user" exists
    And target topic is "代數"

    When suggest learning path for "path_user" to learn "代數"

    Then learning path is returned
    And path includes target topic "代數"
    And path items include: topic, concept_id, prerequisites, difficulty, estimated_hours
    And each item indicates is_prerequisite_met status

  @recommendation_server @ignore
  Scenario: Learning path respects prerequisite dependencies
    Given a knowledge graph with prerequisites:
      | 微積分 | requires | 代數, 三角函數 |
      | 代數 | requires | 基礎運算 |
      | 三角函數 | requires | 基礎幾何 |

    When suggest learning path for user to learn "微積分"

    Then path is ordered: 基礎運算 → 基礎幾何 → 代數 → 三角函數 → 微積分
    And user's mastery affects is_prerequisite_met status
    And path respects prerequisite ordering

  @recommendation_server
  Scenario: Handle invalid question ID in spacing calculation
    When calculate optimal spacing for user with invalid question_id "nonexistent"

    Then response includes error
    And error type is "not_found"
    And error message mentions question not found
