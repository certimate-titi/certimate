"""088 seed plan-tier model routing — Sprint 8 T72.

PRO_PLUS_399 結構性虧損 -31% 的最大兇手是 ai_coach_chat（task_type="advanced"）
走 Sonnet 模型（in $3/M, out $15/M）。換 Haiku 後單次成本降 92%，
PRO_PLUS 整體毛利率從 -31% → +24%（救 55 個百分點）。

策略：
- (PRO_PLUS, advanced) → claude-haiku-4-5 + fallback gemini-2.5-flash
- (ULTRA, advanced) → claude-sonnet-4-5 + fallback claude-haiku-4-5
  （ULTRA 1599 留高階體驗，毛利仍正）
- (FREE / PRO, basic) → gemini-2.5-flash（最便宜）
- (PRO_PLUS / ULTRA, basic) → gemini-2.5-flash（basic 任務不需 Sonnet）
- 加 UNIQUE INDEX (plan, task_type) 避免重複 routing 行

對應 docs/finance/cost-breakdown-by-feature-2026-05-08.md 推薦組合策略 A。
"""

from alembic import op


revision = "088"
down_revision = "087"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_model_routings_plan_task
        ON ai_model_routings (plan, task_type)
        """
    )
    op.execute(
        """
        INSERT INTO ai_model_routings (id, plan, task_type, primary_model, fallback_model, updated_at)
        VALUES
          (gen_random_uuid(), 'FREE',     'basic',    'gemini-2.5-flash', NULL, NOW()),
          (gen_random_uuid(), 'PRO',      'basic',    'gemini-2.5-flash', NULL, NOW()),
          (gen_random_uuid(), 'PRO_PLUS', 'basic',    'gemini-2.5-flash', NULL, NOW()),
          (gen_random_uuid(), 'ULTRA',    'basic',    'gemini-2.5-flash', NULL, NOW()),
          (gen_random_uuid(), 'PRO',      'advanced', 'claude-haiku-4-5', 'gemini-2.5-flash', NOW()),
          (gen_random_uuid(), 'PRO_PLUS', 'advanced', 'claude-haiku-4-5', 'gemini-2.5-flash', NOW()),
          (gen_random_uuid(), 'ULTRA',    'advanced', 'claude-sonnet-4-5', 'claude-haiku-4-5', NOW())
        ON CONFLICT (plan, task_type) DO UPDATE SET
          primary_model = EXCLUDED.primary_model,
          fallback_model = EXCLUDED.fallback_model,
          updated_at = NOW()
        """
    )


def downgrade() -> None:
    # 不刪除 routing 行（避免線上 LLM 失去路由 fallback）
    # 僅卸 UNIQUE 索引讓未來可再加同 (plan, task_type) 行
    op.execute(
        "DROP INDEX IF EXISTS uq_ai_model_routings_plan_task"
    )
