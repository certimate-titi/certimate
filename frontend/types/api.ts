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
  }>;
  timeSpentSeconds: number;
}

export interface SubmitExamResponse {
  exam: Exam; // with score filled
  userAnswers: UserAnswer[];
  domainAnalysis: DomainAnalysis[];
  aiSummary: string; // AI-generated post-exam summary
}

export interface GetExamResultsResponse {
  exam: Exam;
  questions: Question[];
  userAnswers: UserAnswer[];
  domainAnalysis: DomainAnalysis[];
  aiSummary: string;
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
}

export interface GetAchievementsResponse {
  achievements: Achievement[];
  milestones: GrowthMilestone[];
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
