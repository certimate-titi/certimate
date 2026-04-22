"""Resource LLM parsing + question extraction + learning scaffolds schema.

Revision ID: 068
Revises: 067

EPIC-035 M1-M7 schema changes:
  - 3 new tables: resource_parse_jobs / question_candidates / resource_scaffolds
  - resources: parsed_markdown, parsed_text (TOAST), source_type, detected_content_type,
    exam_code, trust_level
  - resource_chunks: section_path, figure_urls
  - questions: source_resource_id, owner_user_id, answer_source, confidence,
    needs_answer, never_for_scoring, user_concept_note, user_concept_note_at
    (scope 'personal' is enforced at app layer; questions has no scope column yet
     — instead owner_user_id != NULL marks personal)
  - plan_quotas: monthly_resource_parse_limit
  - GIN index on questions.user_concept_note (for future FB-035-C3 concept drift search)
  - RLS policies on 3 new tables (NULLIF pattern from migration 064)

Idempotent: IF NOT EXISTS.
"""

from alembic import op


revision = "068"
down_revision = "067"
branch_labels = None
depends_on = None


RLS_TABLES = ["resource_parse_jobs", "question_candidates", "resource_scaffolds"]


def upgrade() -> None:
    # ------------------------------------------------------------------ enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE parse_job_status AS ENUM
                ('queued', 'parsing', 'success', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE question_candidate_tier AS ENUM ('T2', 'T3');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE question_candidate_decision AS ENUM
                ('pending', 'approved', 'rejected');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE resource_scaffold_type AS ENUM
                ('takeaway', 'elaborative', 'strategy');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)

    # ------------------------------------------------------ resource_parse_jobs
    op.execute("""
        CREATE TABLE IF NOT EXISTS resource_parse_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            tenant_id UUID,
            status parse_job_status NOT NULL DEFAULT 'queued',
            gemini_model VARCHAR(50),
            input_tokens INT,
            output_tokens INT,
            cost_usd NUMERIC(10,4),
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            failure_reason TEXT,
            critical_pages INT[] NOT NULL DEFAULT '{}',
            detected_content_type VARCHAR(30),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_resource_parse_jobs_resource ON resource_parse_jobs(resource_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resource_parse_jobs_tenant ON resource_parse_jobs(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resource_parse_jobs_status ON resource_parse_jobs(status)")

    # ------------------------------------------------------ question_candidates
    op.execute("""
        CREATE TABLE IF NOT EXISTS question_candidates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            tenant_id UUID,
            question_text TEXT NOT NULL,
            options JSONB NOT NULL DEFAULT '[]'::jsonb,
            ai_inferred_answer VARCHAR(10),
            confidence NUMERIC(3,2),
            source_page INT,
            figure_refs TEXT[] NOT NULL DEFAULT '{}',
            tier question_candidate_tier NOT NULL,
            decision question_candidate_decision NOT NULL DEFAULT 'pending',
            decided_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_question_candidates_resource ON question_candidates(resource_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_question_candidates_tenant ON question_candidates(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_question_candidates_decision ON question_candidates(decision)")

    # ------------------------------------------------------- resource_scaffolds
    op.execute("""
        CREATE TABLE IF NOT EXISTS resource_scaffolds (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            tenant_id UUID,
            chapter_heading TEXT,
            type resource_scaffold_type NOT NULL,
            content TEXT NOT NULL,
            user_response TEXT,
            responded_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_resource_scaffolds_resource ON resource_scaffolds(resource_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resource_scaffolds_tenant ON resource_scaffolds(tenant_id)")

    # --------------------------------------------------- resources: extensions
    op.execute("""
        ALTER TABLE resources
            ADD COLUMN IF NOT EXISTS parsed_markdown TEXT,
            ADD COLUMN IF NOT EXISTS parsed_text TEXT,
            ADD COLUMN IF NOT EXISTS source_type VARCHAR(20),
            ADD COLUMN IF NOT EXISTS detected_content_type VARCHAR(30),
            ADD COLUMN IF NOT EXISTS exam_code VARCHAR(50),
            ADD COLUMN IF NOT EXISTS trust_level SMALLINT
    """)
    # Ensure parsed_text uses EXTENDED storage so TOAST kicks in for full-text
    op.execute("ALTER TABLE resources ALTER COLUMN parsed_text SET STORAGE EXTENDED")

    # ---------------------------------------------- resource_chunks: extensions
    op.execute("""
        ALTER TABLE resource_chunks
            ADD COLUMN IF NOT EXISTS section_path TEXT[] NOT NULL DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS figure_urls TEXT[] NOT NULL DEFAULT '{}'
    """)

    # --------------------------------------------------- questions: extensions
    op.execute("""
        ALTER TABLE questions
            ADD COLUMN IF NOT EXISTS source_resource_id UUID
                REFERENCES resources(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS owner_user_id UUID
                REFERENCES users(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS answer_source VARCHAR(20),
            ADD COLUMN IF NOT EXISTS confidence NUMERIC(3,2),
            ADD COLUMN IF NOT EXISTS needs_answer BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS never_for_scoring BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS user_concept_note TEXT,
            ADD COLUMN IF NOT EXISTS user_concept_note_at TIMESTAMPTZ
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_questions_source_resource ON questions(source_resource_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_questions_owner_user ON questions(owner_user_id)")
    # GIN index for future FB-035-C3 concept drift search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_questions_user_concept_note_gin
            ON questions USING GIN (to_tsvector('simple', COALESCE(user_concept_note, '')))
    """)

    # ------------------------------------------------- plan_quotas: extensions
    op.execute("""
        ALTER TABLE plan_quotas
            ADD COLUMN IF NOT EXISTS monthly_resource_parse_limit INTEGER
    """)

    # ------------------------------------------------ RLS on new tables (NULLIF)
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} USING ("
            f"  NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL"
            f"  OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
            f")"
        )


def downgrade() -> None:
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE plan_quotas DROP COLUMN IF EXISTS monthly_resource_parse_limit")

    op.execute("DROP INDEX IF EXISTS ix_questions_user_concept_note_gin")
    op.execute("DROP INDEX IF EXISTS ix_questions_owner_user")
    op.execute("DROP INDEX IF EXISTS ix_questions_source_resource")
    op.execute("""
        ALTER TABLE questions
            DROP COLUMN IF EXISTS user_concept_note_at,
            DROP COLUMN IF EXISTS user_concept_note,
            DROP COLUMN IF EXISTS never_for_scoring,
            DROP COLUMN IF EXISTS needs_answer,
            DROP COLUMN IF EXISTS confidence,
            DROP COLUMN IF EXISTS answer_source,
            DROP COLUMN IF EXISTS owner_user_id,
            DROP COLUMN IF EXISTS source_resource_id
    """)

    op.execute("""
        ALTER TABLE resource_chunks
            DROP COLUMN IF EXISTS figure_urls,
            DROP COLUMN IF EXISTS section_path
    """)

    op.execute("""
        ALTER TABLE resources
            DROP COLUMN IF EXISTS trust_level,
            DROP COLUMN IF EXISTS exam_code,
            DROP COLUMN IF EXISTS detected_content_type,
            DROP COLUMN IF EXISTS source_type,
            DROP COLUMN IF EXISTS parsed_text,
            DROP COLUMN IF EXISTS parsed_markdown
    """)

    op.execute("DROP TABLE IF EXISTS resource_scaffolds")
    op.execute("DROP TABLE IF EXISTS question_candidates")
    op.execute("DROP TABLE IF EXISTS resource_parse_jobs")

    op.execute("DROP TYPE IF EXISTS resource_scaffold_type")
    op.execute("DROP TYPE IF EXISTS question_candidate_decision")
    op.execute("DROP TYPE IF EXISTS question_candidate_tier")
    op.execute("DROP TYPE IF EXISTS parse_job_status")
