import type {
  User,
  UserUsageLog,
  Document,
  Exam,
  Question,
  UserAnswer,
  KnowledgeNode,
  ExamSetupConfig,
  DailyQuest,
  Achievement,
  LearningStreak,
  ChatMessage,
  DomainAnalysis,
  ReviewCalendarDay,
  ActivityItem,
  GrowthMilestone,
  Student,
  SubjectCatalogItem,
  UserSubject,
  SelfAssessmentLevel,
  LearningStyle,
} from './models';

// ===========================
// Auth API
// ===========================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  displayName?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  access_token?: string;
  redirect_to?: string;
}

// ===========================
// Document API
// ===========================

export interface UploadDocumentRequest {
  file?: File;
  youtubeUrl?: string;
  title?: string;
  subjectId: string;
}

export interface UploadDocumentResponse {
  document: Document;
  taskId: string; // for tracking async processing via SSE
}

export interface GetDocumentsResponse {
  documents: Document[];
  total: number;
}

// ===========================
// Exam API
// ===========================

export interface CreateExamRequest {
  config: ExamSetupConfig;
}

export interface CreateExamResponse {
  exam: Exam;
  questions: Question[];
  exam_id?: string;
  examId?: string;
}

export interface SubmitExamRequest {
  examId: string;
  answers: Array<{
    questionId: string;
    userChoice: string;
    /** Feature 20 信心度校準：confident / somewhat / guessing（可選）*/
    confidence?: 'confident' | 'somewhat' | 'guessing' | null;
  }>;
  timeSpentSeconds: number;
}

export interface SubmitExamResponse {
  exam: Exam; // with score filled
  userAnswers: UserAnswer[];
  domainAnalysis: DomainAnalysis[];
  aiSummary: string; // AI-generated post-exam summary
}

/** Spec 18 §測驗結果 Bloom 各層次答對率 */
export interface BloomBreakdownItem {
  category: 'remember' | 'understand' | 'apply' | 'analyze' | 'evaluate' | 'create';
  label: string;
  correct: number;
  total: number;
  rate: number;
}

export interface GetExamResultsResponse {
  exam: Exam;
  questions: Question[];
  userAnswers: UserAnswer[];
  domainAnalysis: DomainAnalysis[];
  aiSummary: string;
  bloomBreakdown?: BloomBreakdownItem[];
}

// ===========================
// Review API
// ===========================

export interface GetReviewQuestionsResponse {
  examId: string;
  examTitle: string;
  wrongQuestions: Array<{
    question: Question;
    userAnswer: UserAnswer;
    /** 連續答對次數（自動消除門檻 2） */
    correctStreak?: number;
    streakTarget?: number;
    /** 用戶手動標記為已掌握 */
    isMastered?: boolean;
    /** streak 已達標但用戶尚未從清單看見（保留給 UI 顯示「已自動消除」） */
    autoEliminated?: boolean;
  }>;
}

export interface SendChatMessageRequest {
  questionId: string;
  message: string;
  conversationHistory: ChatMessage[];
}

export interface SendChatMessageResponse {
  reply: ChatMessage;
}

// ===========================
// Dashboard API
// ===========================

export interface GetDashboardResponse {
  user: User;
  streak: LearningStreak;
  dailyQuests: DailyQuest[];
  activityItems: ActivityItem[];
  reviewCalendar: ReviewCalendarDay[];
  stats: {
    overallAccuracy: number;
    totalMocksCompleted: number;
    totalQuestionsAnswered: number;
    predictedPassRate: number;
    examCountdown: {
      examName: string;
      daysRemaining: number;
    } | null;
  };
  domainStrengths: DomainAnalysis[];
  todayTasks?: Array<{ title: string; type: string }>;
  todo_reminders?: {
    wrong_answers: number;
  };
}

export interface CompleteDailyQuestRequest {
  questId: string;
}

// ===========================
// Knowledge API
// ===========================

export interface GetKnowledgeMapResponse {
  documents: Document[];
  nodes: KnowledgeNode[];
  rootNodeId: string;
}

export interface GetNodeDetailResponse {
  node: KnowledgeNode;
  citationText: string;
  sourceText?: string;
  citationSource: {
    type: 'pdf' | 'youtube';
    documentTitle: string;
    page?: number;
    timestampStart?: number;
    timestampEnd?: number;
    sourceUrl: string;
  };
}

// ===========================
// Account API
// ===========================

export interface UpdateProfileRequest {
  displayName?: string;
  username?: string;
  age?: number | null;
  education?: string | null;
  occupation?: string | null;
  dailyStudyMinutes?: number;
  learningStyle?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export interface GetUserUsageResponse {
  usage: UserUsageLog;
  limits: {
    documentsPerMonth: number;
    examsPerMonth: number;
    aiQueriesPerDay: number;
    visionOcrPagesPerMonth: number;
    maxFileSizeMB: number;
  };
  uploads?: {
    used: number;
    limit: number;
  };
  ai_queries?: {
    used: number;
    limit: number;
  };
  vision_ocr?: {
    used: number;
    limit: number;
  };
  vision_pages?: {
    used: number;
    limit: number;
  };
}

export interface GetAchievementsResponse {
  achievements: Achievement[];
  milestones: GrowthMilestone[];
}

/** L-quota: 單項配額狀態 */
export interface QuotaItem {
  label: string;
  used: number;
  limit: number;          // -1 = 無上限（管理員 / EDU 等）
  remaining: number;       // -1 = 無上限
  percentage: number;      // 0-100；無上限時 0
  is_warning: boolean;     // ≥ 80%
  is_blocked: boolean;     // used ≥ limit
  period: 'daily' | 'monthly' | 'constant';
  action_hint: string;
}

/** L-share-badge: 考後分享徽章 */
export interface ShareBadgeResponse {
  ok: boolean;
  exam_id: string;
  exam_meta: {
    subject_name: string;
    title: string;
    completed_at: string | null;
  };
  user: {
    display_name: string;
  };
  improvement: {
    is_first: boolean;
    message: string;     // 「比上次提升 18 個百分點」「首次完成」「持續穩定發揮 💪」
    delta_pp: number;
  };
  cumulative: {
    total_exams: number;
    total_questions: number;
    streak_days: number;
  };
  learning_style: {
    type_id: 'tactical' | 'socratic' | 'sprint' | 'marathon' | 'steady' | 'reflective' | 'explorer';
    label: string;       // 「戰術型考生」
    emoji: string;       // 「🎯」
    description: string;
  };
}

/** L-quota: 5 維度配額狀態回傳 */
export interface QuotaStatusResponse {
  ok: boolean;
  plan: string;
  is_unlimited: boolean;
  period: string;          // YYYY-MM
  quotas: {
    monthly_uploads: QuotaItem;
    monthly_exams: QuotaItem;
    daily_ai_chats: QuotaItem;
    monthly_vision_pages: QuotaItem;
    max_file_size_mb: QuotaItem;
  };
  upgrade_url: string;
  pricing_url: string;
}

export interface GetBillingHistoryResponse {
  invoices: Array<{
    id: string;
    date: string;
    amount: number;
    currency: string;
    status: 'paid' | 'pending' | 'failed';
    pdfUrl: string | null;
  }>;
}

// ===========================
// B2B Admin API
// ===========================

export interface GetStudentListResponse {
  students: Student[];
  total: number;
  classStats: {
    averageScore: number;
    scoreChange: number;
    topWeaknesses: Array<{
      topic: string;
      errorRate: number;
    }>;
  };
}

export interface ImportStudentsResponse {
  total_rows: number;
  created_users: number;
  added_members: number;
  skipped_duplicates: number;
  groups: string[];
}

// ===========================
// Task Progress (SSE)
// ===========================

export interface TaskProgressEvent {
  taskId: string;
  stage: 'extracting' | 'generating' | 'verifying' | 'completed' | 'failed';
  progress: number; // 0-100
  message: string;
  examId?: string; // present when stage === 'completed'
}

// ===========================
// Onboarding API
// ===========================

export interface GetSubjectCatalogResponse {
  subjects: SubjectCatalogItem[];
}

export interface SubmitOnboardingRequest {
  displayName: string;
  age?: number;
  education?: string;
  occupation?: string;
  subjects: Array<{
    subjectId: string;
    subjectName?: string;
    examDate: string;
    resultDate?: string;
    selfAssessment: SelfAssessmentLevel;
  }>;
  dailyStudyMinutes: number;
  learningStyle: LearningStyle;
}

export interface SubmitOnboardingResponse {
  success: boolean;
  userSubjects: UserSubject[];
}

// ===========================
// Subject Management API
// ===========================

export interface GetUserSubjectsResponse {
  subjects: UserSubject[];
}

export interface AddUserSubjectRequest {
  subjectId: string;
  subjectName?: string;
  examDate: string;
  resultDate?: string;
  selfAssessment: SelfAssessmentLevel;
}

export interface AddUserSubjectResponse {
  subject: UserSubject;
}

// ===========================
// EPIC-035 Resource LLM Parse + Personal Bank + Scaffolds
// ===========================

export type ParseJobStatus =
  | 'PENDING'
  | 'CHUNKING'
  | 'EXTRACTING'
  | 'GENERATING'
  | 'COMPLETED'
  | 'FAILED';

export interface ParseJobResponse {
  job_id: string;
  resource_id: string;
  status: ParseJobStatus;
}

export interface ParseStatusResponse {
  job_id: string;
  status: ParseJobStatus;
  started_at: string | null;
  finished_at: string | null;
  failure_reason: string | null;
  detected_content_type: string | null;
  critical_pages: number[];
}

export type ScaffoldType = 'takeaway' | 'elaborative' | 'strategy';

export interface Scaffold {
  id: string;
  chapter_heading: string | null;
  type: ScaffoldType;
  content: string;
  user_response: string | null;
}

export interface ParsedResourceResponse {
  resource_id: string;
  parsed_markdown: string | null;
  detected_content_type: string | null;
  trust_level: string | null;
  scaffolds: Scaffold[];
}

export interface QuestionCandidate {
  id: string;
  question_text: string;
  options: string[];
  ai_inferred_answer: string | null;
  confidence: number | null;
  source_page: number | null;
  tier: 'T1' | 'T2' | 'T3';
}

export interface CandidateListResponse {
  t1_count: number;
  t2: QuestionCandidate[];
  t3: QuestionCandidate[];
}

export interface ApproveCandidatesRequest {
  candidate_ids: string[];
  approve: boolean;
}

export interface BlindAnswerResponse {
  user_answer: string;
  ai_inferred_answer: string;
  ai_confidence: number | null;
  ai_reasoning: string;
  never_for_scoring: boolean;
  next_step: 'submit_judgment';
}

export type InferenceJudgment = 'accept_ai' | 'keep_mine' | 'skip';

// ===========================
// Orphan Scaffold (AI 補洞鷹架)
// ===========================

export type OrphanReasonCode =
  | 'definition_wrong'
  | 'example_wrong'
  | 'answer_wrong'
  | 'unrelated'
  | 'other';

export interface OrphanFillPracticeQuestion {
  stem: string;
  options: { A: string; B: string; C: string; D: string };
  answer: string;
  explanation: string;
}

/** 200 ready — 鷹架已生成 */
export interface OrphanFillResponse {
  scaffold_id: string;
  node_id: string;
  status: 'ready';
  definition: string;
  illustration: string;
  practice_question: OrphanFillPracticeQuestion;
  confidence_score: number;
  evidence_question_ids: string[];
  evidence_year_range: string;
  evidence_count: number;
  trust_level: 'AI_INFERRED';
}

/** 202 pending — 生成中 */
export interface OrphanFillPending {
  status: 'generating';
  estimated_seconds: number;
}

/** 422 insufficient evidence — 佐證不足 */
export interface OrphanFillInsufficient {
  error: true;
  message: string;
  evidence_count: number;
}

export type OrphanFillResult = OrphanFillResponse | OrphanFillPending | OrphanFillInsufficient;

export interface ReportInaccurateRequest {
  reason_code: OrphanReasonCode;
  note?: string;
}

export interface ReportInaccurateResponse {
  ok: boolean;
  message: string;
}

// ===========================
// Orphan Coach (蘇格拉底 AI 教練)
// ===========================

/** 對話結束狀態 */
export type CoachStatus =
  | 'continuing'
  | 'positive_close'
  | 'transfer_book'
  | 'switch_to_question'
  | 'force_end';

/** POST /orphan-coach/conversations → 201 */
export interface OrphanCoachStartResponse {
  conversation_id: string;
  opening_message: string;
  context_summary: string;
}

/** 配額不足 → 402 */
export interface OrphanCoachQuotaError {
  error: true;
  message: string;
  used: number;
  quota: number;
}

/** 單輪評分 */
export interface CoachRoundScores {
  concept: number;   // 0 / 0.5 / 1
  reasoning: number; // 0 / 0.5 / 1
  initiative: number; // 0 / 0.5
}

/** 書籍推薦 */
export interface CoachBookRecommendation {
  title: string;
  chapter: string;
}

/** POST /orphan-coach/conversations/{cid}/messages → 200 */
export interface OrphanCoachMessageResponse {
  assistant_reply: string;
  scores: CoachRoundScores;
  round_number: number;
  status: CoachStatus;
  book_recommendation?: CoachBookRecommendation;
  transition_question_id?: string;
}

/** 單則訊息 */
export interface OrphanCoachMessage {
  role: 'user' | 'assistant';
  text: string;
  scores?: CoachRoundScores;
  created_at: string;
}

/** GET /orphan-coach/conversations/{cid} → 200 */
export interface OrphanCoachConversation {
  messages: OrphanCoachMessage[];
  status: CoachStatus;
  mastery_committed: boolean;
  total_score: number;
  round_number: number;
}

/** GET /orphan-coach/conversations?node_id={uuid} → 200 */
export interface OrphanCoachExistingResponse {
  existing_conversation_id: string | null;
}

// ===========================
// Completion Framework API
// ===========================

/** 下一個未解鎖里程碑 */
export interface CompletionNextMilestone {
  code: string;
  remaining_pct: number | null;
}

// ===========================
// Chat Annotations
// ===========================

export type AnnotationType = 'note' | 'key_insight' | 'challenge' | 'example' | 'application';

export interface ChatAnnotation {
  id: string;
  message_id: string;
  user_id: string;
  session_id: string;
  highlighted_text: string;
  user_annotation: string;
  annotation_type: AnnotationType;
  created_at: string;
}

export interface ChatAnnotationCreate {
  message_id: string;
  session_id: string;
  highlighted_text: string;
  user_annotation: string;
  annotation_type: AnnotationType;
}

export interface ChatAnnotationListResponse {
  items: ChatAnnotation[];
  total: number;
}

/**
 * GET /subjects/{subject_id}/completion → 200
 * 科目完成度框架（B.2/B.3/B.4）
 */
export interface SubjectCompletionResponse {
  subject_id: string;
  /** 甜蜜點進度（0-100），主要顯示 */
  sweet_spot_progress: number;
  /** 全覆蓋進度（0-100） */
  full_coverage_progress: number;
  /** 衝刺模式進度（0-100，前 30% 高頻節點） */
  sprint_mode_progress: number;
  /** 已解鎖的徽章代碼列表 */
  badges_unlocked: string[];
  /** 下一個未解鎖里程碑，null 代表全部解鎖 */
  next_milestone: CompletionNextMilestone | null;
  /** 是否觸發邊際效益遞減提示（B.4.1） */
  should_show_marginal_utility_nudge: boolean;
  /** 計算時間（ISO datetime） */
  computed_at: string;
}

// ===========================
// User Notes API
// ===========================

export interface UserNote {
  id: string;
  user_id: string;
  subject_id: string;
  node_id: string | null;
  title: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface UserNoteCreate {
  subject_id: string;
  node_id?: string | null;
  title?: string | null;
  content: string;
}

export interface UserNoteUpdate {
  title?: string | null;
  content?: string;
}

export interface UserNoteListResponse {
  items: UserNote[];
  total: number;
}

export interface ChatAnnotationUpdate {
  user_annotation?: string;
  annotation_type?: AnnotationType;
}
