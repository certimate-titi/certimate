--
-- PostgreSQL database dump
--


-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: ab_test_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.ab_test_status AS ENUM (
    'running',
    'completed',
    'cancelled'
);


--
-- Name: bloom_category; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.bloom_category AS ENUM (
    'remember',
    'understand',
    'apply',
    'analyze',
    'evaluate',
    'create'
);


--
-- Name: difficulty_level; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.difficulty_level AS ENUM (
    'easy',
    'medium',
    'hard'
);


--
-- Name: exam_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.exam_status AS ENUM (
    'PENDING',
    'READY',
    'IN_PROGRESS',
    'SUBMITTED',
    'FAILED'
);


--
-- Name: learning_mode; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.learning_mode AS ENUM (
    'sprint',
    'standard',
    'mastery'
);


--
-- Name: learning_preference; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.learning_preference AS ENUM (
    'drill',
    'concept',
    'mixed'
);


--
-- Name: prompt_category; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.prompt_category AS ENUM (
    'safety',
    'knowledge',
    'exam',
    'teaching',
    'emotion'
);


--
-- Name: prompt_stage_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.prompt_stage_status AS ENUM (
    'active',
    'inactive'
);


--
-- Name: question_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.question_type AS ENUM (
    'single_choice',
    'multiple_choice',
    'fill_in',
    'calculation'
);


--
-- Name: resource_scope; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.resource_scope AS ENUM (
    'personal',
    'institution'
);


--
-- Name: resource_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.resource_status AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'COMPLETED_NO_MAP',
    'FAILED',
    'DELETED'
);


--
-- Name: resource_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.resource_type AS ENUM (
    'pdf',
    'markdown',
    'txt',
    'image',
    'youtube'
);


--
-- Name: reverse_engineering_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reverse_engineering_status AS ENUM (
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);


--
-- Name: self_assessed_level; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.self_assessed_level AS ENUM (
    'beginner',
    'intermediate',
    'advanced'
);


--
-- Name: subscription_plan; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.subscription_plan AS ENUM (
    'FREE',
    'PRO',
    'PRO_PLUS',
    'ULTRA',
    'EDU'
);


--
-- Name: subscription_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.subscription_status AS ENUM (
    'active',
    'cancelled',
    'expired',
    'trial'
);


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'user',
    'org_admin',
    'admin',
    'super_admin',
    'student'
);


--
-- Name: user_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_status AS ENUM (
    'pending',
    'active',
    'suspended',
    'cooling',
    'deleted'
);




--
-- Name: admin_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.admin_audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    admin_id uuid NOT NULL,
    action character varying(100) NOT NULL,
    target_type character varying(50),
    target_id uuid,
    details jsonb,
    ip_address character varying(50),
    user_agent text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: ai_chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_chat_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    role character varying(10) NOT NULL,
    content text NOT NULL,
    token_count integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: ai_chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_chat_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    context_type character varying(20) NOT NULL,
    context_id uuid NOT NULL,
    model_used character varying(50),
    message_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    tenant_id uuid
);


--
-- Name: ai_cooldowns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_cooldowns (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    reason character varying(100),
    cooldown_until timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: ai_model_routings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_model_routings (
    id uuid NOT NULL,
    plan character varying(50) NOT NULL,
    task_type character varying(50) NOT NULL,
    primary_model character varying(100) NOT NULL,
    fallback_model character varying(100),
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: anomaly_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_records (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    error_id character varying(50) NOT NULL,
    error_type character varying(200) NOT NULL,
    occurrence_count integer DEFAULT 1 NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    impact_scope character varying(100) NOT NULL,
    assigned_to character varying(200),
    first_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    last_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: answers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.answers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    exam_id uuid NOT NULL,
    question_id uuid NOT NULL,
    user_id uuid NOT NULL,
    selected_answer character varying(10),
    is_correct boolean,
    marked_for_review boolean DEFAULT false,
    answered_at timestamp with time zone,
    confidence character varying(10),
    tenant_id uuid
);

ALTER TABLE ONLY public.answers FORCE ROW LEVEL SECURITY;


--
-- Name: content_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content_reports (
    id uuid NOT NULL,
    report_ref character varying(50) NOT NULL,
    reporter_id integer NOT NULL,
    report_type character varying(50) NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id integer NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    resolution_action character varying(50),
    resolution_note text,
    resolved_by character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: coupons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coupons (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying(100) NOT NULL,
    discount_type character varying(20) NOT NULL,
    discount_value numeric(10,2) NOT NULL,
    applicable_plans text,
    max_uses integer,
    max_uses_per_user integer,
    used_count integer DEFAULT 0,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: early_warning_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.early_warning_rules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    min_avg_score numeric(5,2) DEFAULT '60'::numeric,
    max_decline_trend integer DEFAULT 3,
    max_inactive_days integer DEFAULT 5,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: exams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exams (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subject_id uuid NOT NULL,
    institution_assignment_id uuid,
    status public.exam_status DEFAULT 'PENDING'::public.exam_status,
    total_questions integer NOT NULL,
    duration_minutes integer,
    passing_score integer,
    difficulty_distribution jsonb,
    question_types text[],
    score integer,
    correct_count integer,
    started_at timestamp with time zone,
    submitted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    ai_summary text,
    custom_bloom_ratio json,
    historical_priority boolean DEFAULT false NOT NULL,
    tenant_id uuid
);


--
-- Name: feature_flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feature_flags (
    id uuid NOT NULL,
    flag_key character varying(100) NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    rollout_percentage integer DEFAULT 0 NOT NULL,
    target_plans character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: feedback_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_attachments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    feedback_id uuid NOT NULL,
    file_path text NOT NULL,
    file_size integer NOT NULL,
    mime_type character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: feedbacks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedbacks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    feedback_id character varying(50) NOT NULL,
    user_id uuid NOT NULL,
    type character varying(50) NOT NULL,
    subject character varying(100) NOT NULL,
    content text NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    admin_reply text,
    resolved_at timestamp with time zone,
    close_reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: historical_exams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.historical_exams (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    exam_code character varying(50) NOT NULL,
    category_code character varying(100),
    subject_code character varying(100),
    exam_name character varying(255),
    category_name character varying(255),
    subject_name character varying(255),
    source character varying(255) DEFAULT '考選部考畢試題查詢平臺'::character varying,
    total_questions integer,
    year integer,
    tenant_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: institution_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.institution_assignments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    group_id uuid NOT NULL,
    created_by uuid NOT NULL,
    exam_config jsonb NOT NULL,
    deadline timestamp with time zone,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: institutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.institutions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(200) NOT NULL,
    admin_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    dpa_signed_at timestamp with time zone,
    dpa_signer_name character varying(100),
    edu_student_limit integer DEFAULT 30 NOT NULL,
    surcharge_confirmed boolean DEFAULT false NOT NULL
);


--
-- Name: invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoices (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    stripe_invoice_id character varying(200),
    amount numeric(10,2) NOT NULL,
    currency character varying(3) DEFAULT 'TWD'::character varying,
    plan character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: knowledge_nodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_nodes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    resource_id uuid,
    parent_id uuid,
    name character varying(300) NOT NULL,
    depth integer DEFAULT 0,
    sort_order integer DEFAULT 0,
    source_page_number integer,
    source_timestamp_seconds integer,
    source_text text,
    available_questions integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    subject_id uuid,
    exam_frequency character varying(10),
    source_origin character varying(20) DEFAULT 'document'::character varying NOT NULL,
    tenant_id uuid
);


--
-- Name: learning_journeys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_journeys (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subject_id uuid NOT NULL,
    exam_date date,
    self_assessed_level public.self_assessed_level DEFAULT 'beginner'::public.self_assessed_level,
    learning_mode public.learning_mode DEFAULT 'standard'::public.learning_mode,
    is_archived boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    result_date date,
    exam_result_status character varying(20),
    data_expiry_date date
);


--
-- Name: maintenance_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    schedule_id uuid NOT NULL,
    scheduled_send_at timestamp with time zone NOT NULL,
    sent_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: maintenance_schedules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_schedules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(200) NOT NULL,
    status character varying(20) DEFAULT 'scheduled'::character varying NOT NULL,
    starts_at timestamp with time zone NOT NULL,
    ends_at timestamp with time zone NOT NULL,
    notify_channels character varying[] DEFAULT '{}'::character varying[],
    notify_targets character varying(100),
    notify_before character varying[] DEFAULT '{}'::character varying[],
    reason text,
    is_full_site boolean DEFAULT false,
    health_check_passed boolean DEFAULT false,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: maintenance_tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_tasks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    task_id character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    priority character varying(20) NOT NULL,
    related_error_id uuid,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    estimated_hours numeric(5,1),
    created_by uuid NOT NULL,
    assigned_to uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: merge_conflicts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.merge_conflicts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    subject_id uuid NOT NULL,
    existing_node_id uuid,
    incoming_node_name character varying(255) NOT NULL,
    similarity numeric(5,2),
    status character varying(20) DEFAULT 'pending_review'::character varying NOT NULL,
    suggestion character varying(30),
    resolution character varying(30),
    resolved_by uuid,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: merge_histories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.merge_histories (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    subject_id uuid NOT NULL,
    trigger_source character varying(20) NOT NULL,
    trigger_name character varying(255),
    nodes_added integer DEFAULT 0,
    nodes_merged integer DEFAULT 0,
    conflicts_count integer DEFAULT 0,
    merged_at timestamp with time zone DEFAULT now()
);


--
-- Name: node_mastery; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.node_mastery (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    node_id uuid NOT NULL,
    correct_count integer DEFAULT 0,
    total_count integer DEFAULT 0,
    mastery_rate numeric(5,2) DEFAULT '0'::numeric,
    color character varying(10),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: plan_quotas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_quotas (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan character varying(50) NOT NULL,
    monthly_uploads integer,
    monthly_exams integer,
    daily_ai_chats integer,
    monthly_vision_pages integer,
    max_file_size_mb integer,
    updated_by uuid,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: prompt_ab_tests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_ab_tests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    template_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    variant_a_version integer NOT NULL,
    variant_b_system_prompt text NOT NULL,
    variant_b_user_prompt text NOT NULL,
    variant_b_temperature numeric(2,1),
    traffic_split integer DEFAULT 50 NOT NULL,
    status public.ab_test_status DEFAULT 'running'::public.ab_test_status,
    metric_name character varying(100),
    variant_a_metric_value numeric(10,4),
    variant_b_metric_value numeric(10,4),
    winner character varying(1),
    started_at timestamp with time zone DEFAULT now(),
    ended_at timestamp with time zone,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: prompt_template_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_template_history (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    template_id uuid NOT NULL,
    version integer NOT NULL,
    content text,
    modified_by character varying(255),
    modified_at timestamp with time zone DEFAULT now()
);


--
-- Name: prompt_template_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_template_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    template_id uuid NOT NULL,
    version integer NOT NULL,
    model character varying(100) NOT NULL,
    max_tokens integer NOT NULL,
    max_tokens_by_plan jsonb,
    temperature numeric(2,1) NOT NULL,
    system_prompt text NOT NULL,
    user_prompt text NOT NULL,
    variables jsonb DEFAULT '[]'::jsonb NOT NULL,
    change_note text,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: prompt_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_templates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    stage_name character varying(100) NOT NULL,
    stage_order integer NOT NULL,
    status public.prompt_stage_status DEFAULT 'active'::public.prompt_stage_status,
    content text,
    version integer DEFAULT 1,
    modified_by character varying(255),
    modified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: prompt_templates_v2; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_templates_v2 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    template_id character varying(10) NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    category public.prompt_category NOT NULL,
    model character varying(100) NOT NULL,
    max_tokens integer NOT NULL,
    max_tokens_by_plan jsonb,
    temperature numeric(2,1) DEFAULT 0.5 NOT NULL,
    system_prompt text NOT NULL,
    user_prompt text NOT NULL,
    variables jsonb DEFAULT '[]'::jsonb NOT NULL,
    feature_refs text[] DEFAULT '{}'::text[],
    current_version integer DEFAULT 1 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: question_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_stats (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    node_id uuid NOT NULL,
    success_count integer DEFAULT 0,
    fail_count integer DEFAULT 0,
    ease_factor numeric(4,2) DEFAULT 2.5,
    next_review_date date,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    exam_id uuid,
    node_id uuid,
    question_number integer NOT NULL,
    type public.question_type DEFAULT 'single_choice'::public.question_type,
    difficulty public.difficulty_level DEFAULT 'medium'::public.difficulty_level,
    content text NOT NULL,
    option_a text,
    option_b text,
    option_c text,
    option_d text,
    correct_answer character varying(10) NOT NULL,
    explanation text,
    source_citation text,
    bloom_category public.bloom_category,
    historical_source character varying(255),
    quality_flag character varying(20) DEFAULT 'ok'::character varying,
    flag_reason text,
    flagged_at timestamp with time zone,
    validation_model character varying(50),
    validation_result jsonb,
    source_type character varying(20) DEFAULT 'historical'::character varying,
    expires_at timestamp with time zone,
    retired_at timestamp with time zone,
    retention_reason character varying(50),
    suggested_node_id uuid,
    tenant_id uuid,
    historical_exam_id uuid,
    CONSTRAINT ck_questions_has_parent CHECK (((exam_id IS NOT NULL) OR (historical_exam_id IS NOT NULL)))
);


--
-- Name: refunds; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refunds (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    refund_id character varying(100) NOT NULL,
    user_id uuid NOT NULL,
    transaction_id character varying(100) NOT NULL,
    amount numeric(10,2) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: resource_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_chunks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    resource_id uuid NOT NULL,
    node_id uuid,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    token_count integer NOT NULL,
    source_page_start integer,
    source_page_end integer,
    metadata_json json,
    embedding public.vector(1024),
    created_at timestamp with time zone DEFAULT now(),
    tenant_id uuid
);

ALTER TABLE ONLY public.resource_chunks FORCE ROW LEVEL SECURITY;


--
-- Name: resources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subject_id uuid NOT NULL,
    institution_id uuid,
    name character varying(500) NOT NULL,
    type public.resource_type NOT NULL,
    scope public.resource_scope DEFAULT 'personal'::public.resource_scope,
    status public.resource_status DEFAULT 'PENDING'::public.resource_status,
    file_size_bytes bigint,
    gcs_path text,
    youtube_url text,
    processing_engine character varying(50),
    implicit_consent boolean DEFAULT true,
    tags text[] DEFAULT '{}'::text[],
    error_message text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    tenant_id uuid
);


--
-- Name: reverse_engineering_tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reverse_engineering_tasks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    subject_id uuid NOT NULL,
    triggered_by uuid NOT NULL,
    status character varying(20) DEFAULT 'PROCESSING'::character varying,
    total_questions integer NOT NULL,
    node_count integer,
    coverage_rate numeric(5,2),
    max_depth integer,
    orphan_node_count integer,
    reliability character varying(10),
    error_message text,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: student_group_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_group_members (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    group_id uuid NOT NULL,
    user_id uuid NOT NULL,
    joined_at timestamp with time zone DEFAULT now()
);


--
-- Name: student_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_groups (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: subject_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subject_categories (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(50) NOT NULL,
    sort_order integer DEFAULT 0
);


--
-- Name: subjects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subjects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    category_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    name_en character varying(200),
    description text,
    is_popular boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    available_questions integer DEFAULT 0,
    parent_subject_id uuid
);


--
-- Name: system_announcements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_announcements (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    type character varying(50) DEFAULT 'info'::character varying NOT NULL,
    display_mode character varying(50) DEFAULT 'banner'::character varying NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    starts_at timestamp with time zone,
    ends_at timestamp with time zone,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: tenants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tenants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    slug character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    plan_tier character varying(50) DEFAULT 'b2c'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    max_users integer,
    storage_quota_bytes bigint,
    llm_monthly_budget_usd numeric(10,2),
    metadata_json json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    merchant_trade_no character varying(20) NOT NULL,
    target_plan character varying(50) NOT NULL,
    amount numeric(10,2) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    payment_provider character varying(20) DEFAULT 'ecpay'::character varying NOT NULL,
    trade_no character varying(50),
    payment_type character varying(50),
    rtn_code character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_usage (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    period character varying(10) NOT NULL,
    daily_ai_chats_used integer DEFAULT 0,
    monthly_uploads_used integer DEFAULT 0,
    monthly_exams_used integer DEFAULT 0,
    monthly_vision_pages_used integer DEFAULT 0,
    last_reset_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    display_name character varying(100),
    avatar_url text,
    auth_provider character varying(20) DEFAULT 'email'::character varying,
    password_hash text,
    subscription_plan public.subscription_plan DEFAULT 'FREE'::public.subscription_plan,
    subscription_status public.subscription_status DEFAULT 'active'::public.subscription_status,
    next_billing_date timestamp with time zone,
    stripe_customer_id character varying(100),
    role public.user_role DEFAULT 'user'::public.user_role,
    status public.user_status DEFAULT 'active'::public.user_status,
    onboarding_completed boolean DEFAULT false,
    daily_study_minutes integer DEFAULT 30,
    learning_preference public.learning_preference DEFAULT 'mixed'::public.learning_preference,
    age integer,
    education character varying(100),
    career character varying(100),
    agreed_to_terms boolean DEFAULT false,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    plan_source character varying(20),
    trial_start_date timestamp with time zone,
    trial_end_date timestamp with time zone,
    has_used_trial boolean DEFAULT false NOT NULL,
    pre_trial_plan character varying(20),
    org_id uuid
);


--
-- Name: weekly_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weekly_reports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    report_week date NOT NULL,
    study_hours numeric(5,1),
    exams_completed integer,
    questions_answered integer,
    progress_summary text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: admin_audit_logs admin_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admin_audit_logs
    ADD CONSTRAINT admin_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: ai_chat_messages ai_chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_chat_messages
    ADD CONSTRAINT ai_chat_messages_pkey PRIMARY KEY (id);


--
-- Name: ai_chat_sessions ai_chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_chat_sessions
    ADD CONSTRAINT ai_chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: ai_cooldowns ai_cooldowns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_cooldowns
    ADD CONSTRAINT ai_cooldowns_pkey PRIMARY KEY (id);


--
-- Name: ai_model_routings ai_model_routings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_model_routings
    ADD CONSTRAINT ai_model_routings_pkey PRIMARY KEY (id);


--
-- Name: anomaly_records anomaly_records_error_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_records
    ADD CONSTRAINT anomaly_records_error_id_key UNIQUE (error_id);


--
-- Name: anomaly_records anomaly_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_records
    ADD CONSTRAINT anomaly_records_pkey PRIMARY KEY (id);


--
-- Name: answers answers_exam_id_question_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_exam_id_question_id_user_id_key UNIQUE (exam_id, question_id, user_id);


--
-- Name: answers answers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_pkey PRIMARY KEY (id);


--
-- Name: content_reports content_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_reports
    ADD CONSTRAINT content_reports_pkey PRIMARY KEY (id);


--
-- Name: content_reports content_reports_report_ref_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_reports
    ADD CONSTRAINT content_reports_report_ref_key UNIQUE (report_ref);


--
-- Name: coupons coupons_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coupons
    ADD CONSTRAINT coupons_code_key UNIQUE (code);


--
-- Name: coupons coupons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coupons
    ADD CONSTRAINT coupons_pkey PRIMARY KEY (id);


--
-- Name: early_warning_rules early_warning_rules_institution_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.early_warning_rules
    ADD CONSTRAINT early_warning_rules_institution_id_key UNIQUE (institution_id);


--
-- Name: early_warning_rules early_warning_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.early_warning_rules
    ADD CONSTRAINT early_warning_rules_pkey PRIMARY KEY (id);


--
-- Name: exams exams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_pkey PRIMARY KEY (id);


--
-- Name: feature_flags feature_flags_flag_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_flag_key_key UNIQUE (flag_key);


--
-- Name: feature_flags feature_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_pkey PRIMARY KEY (id);


--
-- Name: feedback_attachments feedback_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_attachments
    ADD CONSTRAINT feedback_attachments_pkey PRIMARY KEY (id);


--
-- Name: feedbacks feedbacks_feedback_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedbacks
    ADD CONSTRAINT feedbacks_feedback_id_key UNIQUE (feedback_id);


--
-- Name: feedbacks feedbacks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedbacks
    ADD CONSTRAINT feedbacks_pkey PRIMARY KEY (id);


--
-- Name: historical_exams historical_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historical_exams
    ADD CONSTRAINT historical_exams_pkey PRIMARY KEY (id);


--
-- Name: institution_assignments institution_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institution_assignments
    ADD CONSTRAINT institution_assignments_pkey PRIMARY KEY (id);


--
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: knowledge_nodes knowledge_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT knowledge_nodes_pkey PRIMARY KEY (id);


--
-- Name: learning_journeys learning_journeys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_journeys
    ADD CONSTRAINT learning_journeys_pkey PRIMARY KEY (id);


--
-- Name: learning_journeys learning_journeys_user_id_subject_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_journeys
    ADD CONSTRAINT learning_journeys_user_id_subject_id_key UNIQUE (user_id, subject_id);


--
-- Name: maintenance_notifications maintenance_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_notifications
    ADD CONSTRAINT maintenance_notifications_pkey PRIMARY KEY (id);


--
-- Name: maintenance_schedules maintenance_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_schedules
    ADD CONSTRAINT maintenance_schedules_pkey PRIMARY KEY (id);


--
-- Name: maintenance_tasks maintenance_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_pkey PRIMARY KEY (id);


--
-- Name: maintenance_tasks maintenance_tasks_task_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_task_id_key UNIQUE (task_id);


--
-- Name: merge_conflicts merge_conflicts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merge_conflicts
    ADD CONSTRAINT merge_conflicts_pkey PRIMARY KEY (id);


--
-- Name: merge_histories merge_histories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merge_histories
    ADD CONSTRAINT merge_histories_pkey PRIMARY KEY (id);


--
-- Name: node_mastery node_mastery_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_mastery
    ADD CONSTRAINT node_mastery_pkey PRIMARY KEY (id);


--
-- Name: node_mastery node_mastery_user_id_node_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_mastery
    ADD CONSTRAINT node_mastery_user_id_node_id_key UNIQUE (user_id, node_id);


--
-- Name: plan_quotas plan_quotas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_quotas
    ADD CONSTRAINT plan_quotas_pkey PRIMARY KEY (id);


--
-- Name: plan_quotas plan_quotas_plan_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_quotas
    ADD CONSTRAINT plan_quotas_plan_key UNIQUE (plan);


--
-- Name: prompt_ab_tests prompt_ab_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ab_tests
    ADD CONSTRAINT prompt_ab_tests_pkey PRIMARY KEY (id);


--
-- Name: prompt_template_history prompt_template_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_template_history
    ADD CONSTRAINT prompt_template_history_pkey PRIMARY KEY (id);


--
-- Name: prompt_template_versions prompt_template_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_template_versions
    ADD CONSTRAINT prompt_template_versions_pkey PRIMARY KEY (id);


--
-- Name: prompt_template_versions prompt_template_versions_template_id_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_template_versions
    ADD CONSTRAINT prompt_template_versions_template_id_version_key UNIQUE (template_id, version);


--
-- Name: prompt_templates prompt_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_templates
    ADD CONSTRAINT prompt_templates_pkey PRIMARY KEY (id);


--
-- Name: prompt_templates_v2 prompt_templates_v2_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_templates_v2
    ADD CONSTRAINT prompt_templates_v2_name_key UNIQUE (name);


--
-- Name: prompt_templates_v2 prompt_templates_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_templates_v2
    ADD CONSTRAINT prompt_templates_v2_pkey PRIMARY KEY (id);


--
-- Name: prompt_templates_v2 prompt_templates_v2_template_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_templates_v2
    ADD CONSTRAINT prompt_templates_v2_template_id_key UNIQUE (template_id);


--
-- Name: question_stats question_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_stats
    ADD CONSTRAINT question_stats_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: refunds refunds_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refunds
    ADD CONSTRAINT refunds_pkey PRIMARY KEY (id);


--
-- Name: refunds refunds_refund_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refunds
    ADD CONSTRAINT refunds_refund_id_key UNIQUE (refund_id);


--
-- Name: resource_chunks resource_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chunks
    ADD CONSTRAINT resource_chunks_pkey PRIMARY KEY (id);


--
-- Name: resources resources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (id);


--
-- Name: reverse_engineering_tasks reverse_engineering_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reverse_engineering_tasks
    ADD CONSTRAINT reverse_engineering_tasks_pkey PRIMARY KEY (id);


--
-- Name: student_group_members student_group_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_group_members
    ADD CONSTRAINT student_group_members_pkey PRIMARY KEY (id);


--
-- Name: student_groups student_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_groups
    ADD CONSTRAINT student_groups_pkey PRIMARY KEY (id);


--
-- Name: subject_categories subject_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_categories
    ADD CONSTRAINT subject_categories_pkey PRIMARY KEY (id);


--
-- Name: subjects subjects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_pkey PRIMARY KEY (id);


--
-- Name: system_announcements system_announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_announcements
    ADD CONSTRAINT system_announcements_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_slug_key UNIQUE (slug);


--
-- Name: transactions transactions_merchant_trade_no_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_merchant_trade_no_key UNIQUE (merchant_trade_no);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: student_group_members uq_group_member; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_group_members
    ADD CONSTRAINT uq_group_member UNIQUE (group_id, user_id);


--
-- Name: historical_exams uq_historical_exam_identity; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historical_exams
    ADD CONSTRAINT uq_historical_exam_identity UNIQUE (exam_code, category_code, subject_code);


--
-- Name: question_stats uq_question_stats_user_node; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_stats
    ADD CONSTRAINT uq_question_stats_user_node UNIQUE (user_id, node_id);


--
-- Name: user_usage uq_user_usage_user_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage
    ADD CONSTRAINT uq_user_usage_user_period UNIQUE (user_id, period);


--
-- Name: weekly_reports uq_weekly_reports_user_week; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT uq_weekly_reports_user_week UNIQUE (user_id, report_week);


--
-- Name: user_usage user_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage
    ADD CONSTRAINT user_usage_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: weekly_reports weekly_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT weekly_reports_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_action ON public.admin_audit_logs USING btree (action);


--
-- Name: idx_audit_admin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_admin ON public.admin_audit_logs USING btree (admin_id);


--
-- Name: idx_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_embedding ON public.resource_chunks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_chunks_resource_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_resource_id ON public.resource_chunks USING btree (resource_id);


--
-- Name: idx_coupon_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coupon_code ON public.coupons USING btree (code);


--
-- Name: idx_coupon_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coupon_status ON public.coupons USING btree (status);


--
-- Name: idx_feedback_attachment_feedback_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_attachment_feedback_id ON public.feedback_attachments USING btree (feedback_id);


--
-- Name: idx_feedback_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_status ON public.feedbacks USING btree (status);


--
-- Name: idx_feedback_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_user_id ON public.feedbacks USING btree (user_id);


--
-- Name: idx_refund_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refund_status ON public.refunds USING btree (status);


--
-- Name: idx_refund_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refund_user_id ON public.refunds USING btree (user_id);


--
-- Name: idx_txn_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_status ON public.transactions USING btree (status);


--
-- Name: idx_txn_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_user_id ON public.transactions USING btree (user_id);


--
-- Name: idx_user_usage_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_usage_period ON public.user_usage USING btree (period);


--
-- Name: idx_user_usage_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_usage_user_id ON public.user_usage USING btree (user_id);


--
-- Name: idx_weekly_reports_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weekly_reports_user_id ON public.weekly_reports USING btree (user_id);


--
-- Name: ix_ai_chat_sessions_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_chat_sessions_tenant_id ON public.ai_chat_sessions USING btree (tenant_id);


--
-- Name: ix_answers_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_answers_tenant_id ON public.answers USING btree (tenant_id);


--
-- Name: ix_exams_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_exams_tenant_id ON public.exams USING btree (tenant_id);


--
-- Name: ix_historical_exams_exam_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_historical_exams_exam_code ON public.historical_exams USING btree (exam_code);


--
-- Name: ix_historical_exams_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_historical_exams_tenant_id ON public.historical_exams USING btree (tenant_id);


--
-- Name: ix_historical_exams_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_historical_exams_year ON public.historical_exams USING btree (year);


--
-- Name: ix_knowledge_nodes_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_nodes_tenant_id ON public.knowledge_nodes USING btree (tenant_id);


--
-- Name: ix_questions_historical_exam_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_historical_exam_id ON public.questions USING btree (historical_exam_id);


--
-- Name: ix_questions_retirement_scan; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_retirement_scan ON public.questions USING btree (source_type, retired_at, expires_at);


--
-- Name: ix_questions_source_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_source_type ON public.questions USING btree (source_type);


--
-- Name: ix_questions_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_tenant_id ON public.questions USING btree (tenant_id);


--
-- Name: ix_resource_chunks_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_chunks_embedding_hnsw ON public.resource_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_resource_chunks_tenant_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_chunks_tenant_embedding ON public.resource_chunks USING btree (tenant_id) WHERE (tenant_id IS NOT NULL);


--
-- Name: ix_resource_chunks_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_chunks_tenant_id ON public.resource_chunks USING btree (tenant_id);


--
-- Name: ix_resources_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resources_tenant_id ON public.resources USING btree (tenant_id);


--
-- Name: ix_subjects_parent_subject_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subjects_parent_subject_id ON public.subjects USING btree (parent_subject_id);


--
-- Name: ix_tenants_plan_tier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tenants_plan_tier ON public.tenants USING btree (plan_tier);


--
-- Name: ix_tenants_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tenants_slug ON public.tenants USING btree (slug);


--
-- Name: admin_audit_logs admin_audit_logs_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admin_audit_logs
    ADD CONSTRAINT admin_audit_logs_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.users(id);


--
-- Name: ai_chat_messages ai_chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_chat_messages
    ADD CONSTRAINT ai_chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.ai_chat_sessions(id) ON DELETE CASCADE;


--
-- Name: ai_chat_sessions ai_chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_chat_sessions
    ADD CONSTRAINT ai_chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: ai_cooldowns ai_cooldowns_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_cooldowns
    ADD CONSTRAINT ai_cooldowns_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: answers answers_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- Name: answers answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: answers answers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: early_warning_rules early_warning_rules_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.early_warning_rules
    ADD CONSTRAINT early_warning_rules_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id) ON DELETE CASCADE;


--
-- Name: exams exams_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: exams exams_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: feedback_attachments feedback_attachments_feedback_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_attachments
    ADD CONSTRAINT feedback_attachments_feedback_id_fkey FOREIGN KEY (feedback_id) REFERENCES public.feedbacks(id) ON DELETE CASCADE;


--
-- Name: feedbacks feedbacks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedbacks
    ADD CONSTRAINT feedbacks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: knowledge_nodes fk_knowledge_nodes_subject_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT fk_knowledge_nodes_subject_id FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: questions fk_questions_suggested_node_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT fk_questions_suggested_node_id FOREIGN KEY (suggested_node_id) REFERENCES public.knowledge_nodes(id);


--
-- Name: users fk_users_org_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_org_id FOREIGN KEY (org_id) REFERENCES public.institutions(id);


--
-- Name: institution_assignments institution_assignments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institution_assignments
    ADD CONSTRAINT institution_assignments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: institution_assignments institution_assignments_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institution_assignments
    ADD CONSTRAINT institution_assignments_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.student_groups(id);


--
-- Name: institution_assignments institution_assignments_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institution_assignments
    ADD CONSTRAINT institution_assignments_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- Name: institutions institutions_admin_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_admin_user_id_fkey FOREIGN KEY (admin_user_id) REFERENCES public.users(id);


--
-- Name: invoices invoices_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: knowledge_nodes knowledge_nodes_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT knowledge_nodes_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.knowledge_nodes(id);


--
-- Name: knowledge_nodes knowledge_nodes_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT knowledge_nodes_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resources(id) ON DELETE CASCADE;


--
-- Name: learning_journeys learning_journeys_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_journeys
    ADD CONSTRAINT learning_journeys_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: learning_journeys learning_journeys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_journeys
    ADD CONSTRAINT learning_journeys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: maintenance_notifications maintenance_notifications_schedule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_notifications
    ADD CONSTRAINT maintenance_notifications_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES public.maintenance_schedules(id) ON DELETE CASCADE;


--
-- Name: maintenance_schedules maintenance_schedules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_schedules
    ADD CONSTRAINT maintenance_schedules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: maintenance_tasks maintenance_tasks_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: maintenance_tasks maintenance_tasks_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: maintenance_tasks maintenance_tasks_related_error_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_related_error_id_fkey FOREIGN KEY (related_error_id) REFERENCES public.anomaly_records(id);


--
-- Name: merge_conflicts merge_conflicts_existing_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merge_conflicts
    ADD CONSTRAINT merge_conflicts_existing_node_id_fkey FOREIGN KEY (existing_node_id) REFERENCES public.knowledge_nodes(id);


--
-- Name: merge_conflicts merge_conflicts_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merge_conflicts
    ADD CONSTRAINT merge_conflicts_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id);


--
-- Name: merge_conflicts merge_conflicts_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merge_conflicts
    ADD CONSTRAINT merge_conflicts_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: merge_histories merge_histories_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merge_histories
    ADD CONSTRAINT merge_histories_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: node_mastery node_mastery_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_mastery
    ADD CONSTRAINT node_mastery_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.knowledge_nodes(id) ON DELETE CASCADE;


--
-- Name: node_mastery node_mastery_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_mastery
    ADD CONSTRAINT node_mastery_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: plan_quotas plan_quotas_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_quotas
    ADD CONSTRAINT plan_quotas_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: prompt_ab_tests prompt_ab_tests_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ab_tests
    ADD CONSTRAINT prompt_ab_tests_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: prompt_ab_tests prompt_ab_tests_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ab_tests
    ADD CONSTRAINT prompt_ab_tests_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.prompt_templates_v2(id) ON DELETE CASCADE;


--
-- Name: prompt_template_versions prompt_template_versions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_template_versions
    ADD CONSTRAINT prompt_template_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: prompt_template_versions prompt_template_versions_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_template_versions
    ADD CONSTRAINT prompt_template_versions_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.prompt_templates_v2(id) ON DELETE CASCADE;


--
-- Name: prompt_templates_v2 prompt_templates_v2_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_templates_v2
    ADD CONSTRAINT prompt_templates_v2_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: question_stats question_stats_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_stats
    ADD CONSTRAINT question_stats_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.knowledge_nodes(id) ON DELETE CASCADE;


--
-- Name: question_stats question_stats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_stats
    ADD CONSTRAINT question_stats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: questions questions_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- Name: questions questions_historical_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_historical_exam_id_fkey FOREIGN KEY (historical_exam_id) REFERENCES public.historical_exams(id) ON DELETE CASCADE;


--
-- Name: questions questions_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.knowledge_nodes(id);


--
-- Name: refunds refunds_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refunds
    ADD CONSTRAINT refunds_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: resource_chunks resource_chunks_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chunks
    ADD CONSTRAINT resource_chunks_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.knowledge_nodes(id) ON DELETE SET NULL;


--
-- Name: resource_chunks resource_chunks_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chunks
    ADD CONSTRAINT resource_chunks_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resources(id) ON DELETE CASCADE;


--
-- Name: resources resources_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- Name: resources resources_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: resources resources_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: reverse_engineering_tasks reverse_engineering_tasks_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reverse_engineering_tasks
    ADD CONSTRAINT reverse_engineering_tasks_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: reverse_engineering_tasks reverse_engineering_tasks_triggered_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reverse_engineering_tasks
    ADD CONSTRAINT reverse_engineering_tasks_triggered_by_fkey FOREIGN KEY (triggered_by) REFERENCES public.users(id);


--
-- Name: student_group_members student_group_members_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_group_members
    ADD CONSTRAINT student_group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.student_groups(id) ON DELETE CASCADE;


--
-- Name: student_group_members student_group_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_group_members
    ADD CONSTRAINT student_group_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_groups student_groups_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_groups
    ADD CONSTRAINT student_groups_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id) ON DELETE CASCADE;


--
-- Name: subjects subjects_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.subject_categories(id);


--
-- Name: subjects subjects_parent_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_parent_subject_id_fkey FOREIGN KEY (parent_subject_id) REFERENCES public.subjects(id);


--
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_usage user_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage
    ADD CONSTRAINT user_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: weekly_reports weekly_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT weekly_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: answers; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.answers ENABLE ROW LEVEL SECURITY;

--
-- Name: resource_chunks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.resource_chunks ENABLE ROW LEVEL SECURITY;

--
-- Name: answers tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.answers USING (((tenant_id = (current_setting('app.current_tenant_id'::text, true))::uuid) OR (current_setting('app.current_tenant_id'::text, true) IS NULL)));


--
-- Name: resource_chunks tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.resource_chunks USING (((tenant_id = (current_setting('app.current_tenant_id'::text, true))::uuid) OR (current_setting('app.current_tenant_id'::text, true) IS NULL)));


--
-- PostgreSQL database dump complete
--


