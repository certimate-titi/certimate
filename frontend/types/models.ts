// ===========================
// Domain Models — 鏡像 PostgreSQL Schema
// ===========================

// --- Enums ---

export type SubscriptionTier = 'FREE' | 'PRO_199' | 'PRO_PLUS_399' | 'ULTRA_1599' | 'EDU';

export type UserRole = 'USER' | 'ADMIN' | 'STUDENT';

export type SubscriptionStatus = 'ACTIVE' | 'CANCELED' | 'PAST_DUE' | 'TRIAL';

export type DocumentSourceType = 'PDF' | 'MARKDOWN' | 'YOUTUBE_URL' | 'IMAGE_MATH';

export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'RATE_LIMITED';

export type ExamType = 'MOCK_EXAM' | 'SPACED_REPETITION' | 'FLASHCARD_SET';

export type QuestionType = 'MULTIPLE_CHOICE' | 'FILL_IN_BLANK' | 'MATH_FORMULA';

// --- Core Tables ---

export interface User {
  id: string;
  email: string;
  displayName: string;
  avatarUrl: string | null;
  subscriptionTier: SubscriptionTier;
  subscriptionStatus: SubscriptionStatus;
  currentPeriodEnd: string | null; // ISO timestamp
  stripeCustomerId: string | null;
  onboardingCompleted: boolean;
  role: UserRole;
  createdAt: string; // ISO timestamp
  age?: number | null;
  education?: string | null;
  occupation?: string | null;
  dailyStudyMinutes?: number;
  learningStyle?: LearningStyle;
}

export interface UserUsageLog {
  id: string;
  userId: string;
  billingCycleStart: string; // ISO timestamp
  claudeProQueriesCount: number;
  visionOcrPagesCount: number;
  youtubeMinutesParsed: number;
  documentsUploadedCount: number;
}

export interface Document {
  id: string;
  userId: string;
  subjectId: string;
  sourceType: DocumentSourceType;
  title: string;
  sourceUrl: string;
  mcpParsedTranscriptUrl: string | null;
  status: DocumentStatus;
  fileSizeBytes: number;
  visionRequired: boolean;
  createdAt: string; // ISO timestamp
}

export interface Exam {
  id: string;
  userId: string;
  documentId: string;
  title: string;
  examType: ExamType;
  score: number | null;
  totalQuestions: number;
  timeLimit: number; // seconds
  createdAt: string; // ISO timestamp
}

export interface QuestionOption {
  label: string; // e.g. 'A', 'B', 'C', 'D'
  text: string;
}

export interface Question {
  id: string;
  examId: string;
  questionType: QuestionType;
  contentText: string;
  contentImageUrl: string | null;
  options: QuestionOption[];
  correctAnswer: string; // option label e.g. 'B'
  explanationMarkdown: string;
  citationChunkId: string | null;
  citationDocTitle?: string | null;
  citationPage?: number | null;
  tags: string[]; // knowledge domain tags e.g. ['風險管理', 'IAM']
}

export interface UserAnswer {
  id: string;
  userId: string;
  questionId: string;
  examId: string;
  isCorrect: boolean;
  userChoice: string; // option label e.g. 'C'
  isMarkedForReview?: boolean;
  ebbinghausNextReview: string | null; // ISO timestamp
  ebbinghausMultiplier: number;
}

// ===========================
// Frontend-only Types
// ===========================

export interface KnowledgeNode {
  id: string;
  documentId: string;
  label: string;
  parentId: string | null;
  children: KnowledgeNode[];
  depth: number;
  citationChunkId: string | null;
  masteryLevel: 'mastered' | 'partial' | 'weak' | 'untested';
}

export interface ExamSetupConfig {
  selectedDocumentIds: string[];
  selectedNodeIds?: string[];
  questionCount: 10 | 20 | 50 | 100;
  difficulty: 1 | 2 | 3; // 1=基礎, 2=綜合, 3=魔王
  questionTypes: QuestionType[];
  examMode?: 'hybrid' | 'historical_only'; // hybrid=混合式(預設), historical_only=考古題模擬考
}

export interface DailyQuest {
  id: string;
  description: string;
  type: 'review' | 'explore' | 'quiz';
  completed: boolean;
  xpReward: number;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  iconEmoji: string;
  unlockedAt: string | null; // ISO timestamp, null = locked
}

export interface LearningStreak {
  currentStreak: number;
  longestStreak: number;
  freezesRemaining: number;
  freezesPerWeek: number;
  lastActiveDate: string; // ISO date YYYY-MM-DD
  freezeConsumedToday?: boolean; // true if a streak freeze was consumed since last active
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: string; // ISO timestamp
  citationSource?: {
    type: 'pdf' | 'youtube';
    label: string;
    page?: number;
    timestampSeconds?: number;
  };
}

export interface DomainAnalysis {
  domain: string;
  correct: number;
  total: number;
  percentage: number;
}

export interface ReviewCalendarDay {
  date: string; // YYYY-MM-DD
  reviewCount: number;
  topics: string[];
}

export interface ActivityItem {
  id: string;
  type: 'error_review' | 'incomplete_exam' | 'new_resource' | 'achievement';
  title: string;
  description: string;
  link: string;
  linkLabel: string;
}

export interface GrowthMilestone {
  date: string; // ISO date
  label: string;
  type: 'upload' | 'exam' | 'pass' | 'mastery' | 'streak';
}

// --- Subject Catalog & Onboarding Types ---

export type SubjectCategory = 'IT' | '金融' | '語言' | '醫療' | '公務員' | '其他';

export type SelfAssessmentLevel = 'beginner' | 'intermediate' | 'advanced';

export type LearningStyle = 'drill' | 'concept' | 'hybrid';

export interface SubjectCatalogItem {
  id: string;
  name: string;
  category: SubjectCategory;
  description: string;
  isPopular: boolean;
}

export interface UserSubject {
  id: string;
  subjectId: string;
  subjectName: string;
  examDate: string; // ISO date YYYY-MM-DD
  resultDate: string; // ISO date YYYY-MM-DD
  selfAssessment: SelfAssessmentLevel;
  createdAt: string; // ISO timestamp
}

export interface OnboardingFormData {
  displayName: string;
  age?: number;
  education?: string;
  occupation?: string;
  subjects: Array<{
    subjectId: string;
    subjectName: string;
    examDate: string; // YYYY-MM-DD
    resultDate: string; // YYYY-MM-DD
    selfAssessment: SelfAssessmentLevel;
  }>;
  dailyStudyMinutes: number;
  learningStyle: LearningStyle;
}

// --- B2B / Admin Types ---

export interface StudentCompetency {
  label: string;
  score: number; // 0-100
}

export interface Student {
  id: string;
  name: string;
  email: string;
  progress: number; // 0-100
  averageScore: number | null;
  trend: 'up' | 'down' | 'flat';
  status: 'active' | 'needs_attention' | 'inactive';
  competencies: StudentCompetency[];
  lastActiveAt: string | null; // ISO timestamp
  lastActiveLabel: string; // e.g. "今天", "3 天前"
  enrolledSubjectIds: string[]; // e.g. ["subj_pmp", "subj_aws_saa"]
  group?: string; // B2B group name
  groupId?: string; // B2B group UUID
}

export interface Organization {
  id: string;
  name: string;
  authorizedSeats: number;
  usedSeats: number;
}

// --- Super Admin Types ---

export interface AdminKPI {
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
}

export interface SystemAlert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
}

export interface PromoCode {
  id: string;
  code: string;
  discountType: 'percentage' | 'fixed' | 'free_trial_days';
  discountValue: number;
  applicablePlans: SubscriptionTier[];
  maxUses: number;
  currentUses: number;
  validFrom: string;
  validUntil: string;
  isActive: boolean;
}

export interface FeatureFlag {
  id: string;
  flagKey: string;
  name: string;
  description: string;
  isEnabled: boolean;
  rolloutPercentage: number;
}
