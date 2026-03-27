/**
 * API Service Layer
 *
 * 每個函式目前返回 mock 資料，後端就緒後改為呼叫 apiClient。
 * 函式簽名即 API 契約——後端實作時不應改變。
 */

import type {
  AuthResponse,
  LoginRequest,
  SignupRequest,
  UploadDocumentRequest,
  UploadDocumentResponse,
  GetDocumentsResponse,
  KnowledgeNode,
  CreateExamRequest,
  CreateExamResponse,
  SubmitExamRequest,
  SubmitExamResponse,
  GetExamResultsResponse,
  GetReviewQuestionsResponse,
  SendChatMessageRequest,
  SendChatMessageResponse,
  GetDashboardResponse,
  CompleteDailyQuestRequest,
  GetKnowledgeMapResponse,
  GetNodeDetailResponse,
  UpdateProfileRequest,
  GetUserUsageResponse,
  GetAchievementsResponse,
  GetBillingHistoryResponse,
  GetStudentListResponse,
  GetSubjectCatalogResponse,
  SubmitOnboardingRequest,
  SubmitOnboardingResponse,
  GetUserSubjectsResponse,
  AddUserSubjectRequest,
  AddUserSubjectResponse,
  ExamSetupConfig,
  DailyQuest,
  Achievement,
  LearningStreak,
  GrowthMilestone,
  Student,
  SubjectCatalogItem,
  UserSubject,
  SelfAssessmentLevel,
  LearningStyle,
  AdminKPI,
  SystemAlert,
  PromoCode,
  FeatureFlag,
  ChatMessage,
} from '@/types';

import {
  mockUser,
  mockUsage,
  mockDocuments,
  mockExams,
  mockExam,
  mockQuestions,
  mockUserAnswers,
  mockDomainAnalysis,
  mockKnowledgeNodes,
  mockStreak,
  mockDailyQuests,
  mockActivityItems,
  mockReviewCalendar,
  mockChatMessages,
  mockAchievements,
  mockMilestones,
  mockStudents,
  mockSubjectCatalog,
  mockUserSubjects,
  mockNodeDetails,
  mockAdminSubjectStats,
} from './mock-data';

// Simulate network delay
const delay = (ms = 300) => new Promise(r => setTimeout(r, ms));

// ===========================
// Auth Service
// ===========================

export const authService = {
  async login(_req: LoginRequest): Promise<AuthResponse> {
    await delay();
    return { user: mockUser, token: 'mock-jwt-token' };
  },

  async signup(_req: SignupRequest): Promise<AuthResponse> {
    await delay();
    return { user: { ...mockUser, email: _req.email, displayName: _req.displayName }, token: 'mock-jwt-token' };
  },

  async getCurrentUser(): Promise<AuthResponse | null> {
    await delay(100);
    return { user: mockUser, token: 'mock-jwt-token' };
  },
};

// ===========================
// Document Service
// ===========================

export const documentService = {
  async upload(_req: UploadDocumentRequest): Promise<UploadDocumentResponse> {
    await delay(500);
    const title = _req.title || _req.file?.name || 'YouTube 影片';
    return {
      document: {
        ...mockDocuments[0],
        id: `doc_${Date.now()}`,
        subjectId: _req.subjectId,
        title,
        sourceType: _req.youtubeUrl ? 'YOUTUBE_URL' : 'PDF',
        status: 'PROCESSING',
        createdAt: new Date().toISOString(),
      },
      taskId: `task_${Date.now()}`,
    };
  },

  async list(): Promise<GetDocumentsResponse> {
    await delay();
    return { documents: mockDocuments, total: mockDocuments.length };
  },

  async getById(documentId: string): Promise<GetDocumentsResponse['documents'][0] | null> {
    await delay(100);
    return mockDocuments.find(d => d.id === documentId) ?? null;
  },
};

// ===========================
// Exam Service
// ===========================

export const examService = {
  async create(_req: CreateExamRequest): Promise<CreateExamResponse> {
    // Simulate multi-stage generation (the UI shows progress via stages)
    await delay(2000);
    return {
      exam: { ...mockExam, id: `exam_${Date.now()}`, score: null, createdAt: new Date().toISOString() },
      questions: mockQuestions,
    };
  },

  async getExam(examId: string): Promise<CreateExamResponse> {
    await delay();
    return {
      exam: { ...mockExam, id: examId },
      questions: mockQuestions,
    };
  },

  async submit(req: SubmitExamRequest): Promise<SubmitExamResponse> {
    await delay(800);
    // Calculate score from submitted answers
    let correct = 0;
    const userAnswers = req.answers.map((a, i) => {
      const question = mockQuestions.find(q => q.id === a.questionId);
      const isCorrect = question ? a.userChoice === question.correctAnswer : false;
      if (isCorrect) correct++;
      return {
        id: `ua_${Date.now()}_${i}`,
        userId: mockUser.id,
        questionId: a.questionId,
        examId: req.examId,
        isCorrect,
        userChoice: a.userChoice,
        ebbinghausNextReview: isCorrect ? null : new Date(Date.now() + 86400000).toISOString(),
        ebbinghausMultiplier: isCorrect ? 2.0 : 1.0,
      };
    });

    const score = Math.round((correct / req.answers.length) * 100);

    return {
      exam: { ...mockExam, id: req.examId, score },
      userAnswers,
      domainAnalysis: mockDomainAnalysis,
      aiSummary: `你在本次測驗中答對了 ${correct}/${req.answers.length} 題（${score}%）。風險管理章節表現最需加強，建議重點複習「風險回應策略」與「定性風險分析」的核心概念。整合管理部分表現優異，繼續保持！`,
    };
  },

  async getResults(examId: string): Promise<GetExamResultsResponse> {
    await delay();
    const exam = mockExams.find(e => e.id === examId) || mockExam;
    return {
      exam,
      questions: mockQuestions.filter(q => q.examId === examId),
      userAnswers: mockUserAnswers.filter(ua => ua.examId === examId),
      domainAnalysis: mockDomainAnalysis,
      aiSummary: '你在風險管理章節表現最需加強，建議重點複習「風險回應策略」與「定性風險分析」。整合管理與範圍管理章節表現優異，繼續保持！',
    };
  },
};

// ===========================
// Review Service
// ===========================

export const reviewService = {
  async getWrongQuestions(examId?: string, subjectId?: string): Promise<GetReviewQuestionsResponse> {
    await delay();
    let wrongAnswers = mockUserAnswers.filter(ua => !ua.isCorrect);

    if (examId) {
      wrongAnswers = wrongAnswers.filter(ua => ua.examId === examId);
    } else if (subjectId) {
      // 根據學科過濾：找出該學科下的所有文檔，再找出關聯這些文檔的考試
      const subjectDocIds = mockDocuments.filter(d => d.subjectId === subjectId).map(d => d.id);
      const subjectExamIds = mockExams.filter(e => subjectDocIds.includes(e.documentId)).map(e => e.id);
      wrongAnswers = wrongAnswers.filter(ua => subjectExamIds.includes(ua.examId));
    }

    const firstWrongExam = mockExams.find(e => e.id === (examId || (wrongAnswers[0]?.examId)));

    return {
      examId: examId || (subjectId ? `all_${subjectId}` : 'all'),
      examTitle: examId ? (firstWrongExam?.title ?? '專屬測驗') : subjectId ? `${subjectId === 'subj_pmp' ? 'PMP' : 'AWS'} 全學科錯題本` : '所有錯題本',
      wrongQuestions: wrongAnswers.map(ua => ({
        question: mockQuestions.find(q => q.id === ua.questionId)!,
        userAnswer: ua,
      })),
    };
  },

  async getChatHistory(_questionId: string): Promise<ChatMessage[]> {
    await delay(200);
    return mockChatMessages;
  },

  async sendMessage(req: SendChatMessageRequest): Promise<SendChatMessageResponse> {
    await delay(1200);
    return {
      reply: {
        id: `msg_${Date.now()}`,
        role: 'ai',
        content: `針對你的問題「${req.message}」，讓我從另一個角度來解釋。\n\n在這個情境中，關鍵在於理解「正式流程」與「緊急處理」的區別。專案管理框架中，大多數變更都需要經過正式審查，但緊急情況下可以有例外機制。\n\n重點是：即使在緊急情況下，事後仍需要補辦正式流程。`,
        timestamp: new Date().toISOString(),
      },
    };
  },
};

// ===========================
// Dashboard Service
// ===========================

export const dashboardService = {
  async get(): Promise<GetDashboardResponse> {
    await delay();
    return {
      user: mockUser,
      streak: mockStreak,
      dailyQuests: mockDailyQuests,
      activityItems: mockActivityItems,
      reviewCalendar: mockReviewCalendar,
      stats: {
        overallAccuracy: 76,
        totalMocksCompleted: 8,
        totalQuestionsAnswered: 482,
        predictedPassRate: 72,
        examCountdown: { examName: 'PMP 考試', daysRemaining: 14 },
      },
      domainStrengths: mockDomainAnalysis,
    };
  },

  async completeDailyQuest(_req: CompleteDailyQuestRequest): Promise<void> {
    await delay(200);
    // In real implementation, updates the quest status on the server
  },
};

// ===========================
// Knowledge Service
// ===========================

export const knowledgeService = {
  async getMap(_documentId?: string): Promise<GetKnowledgeMapResponse> {
    await delay();
    return {
      documents: mockDocuments,
      nodes: mockKnowledgeNodes,
      rootNodeId: 'kn_pmp_root',
    };
  },

  async getNodeDetail(nodeId: string): Promise<GetNodeDetailResponse> {
    await delay(200);
    // 遞迴展平節點以尋找任何深度的節點
    const flattenNodes = (nodes: KnowledgeNode[]): KnowledgeNode[] => {
      let result: KnowledgeNode[] = [];
      nodes.forEach(n => {
        result.push(n);
        if (n.children && n.children.length > 0) {
          result = result.concat(flattenNodes(n.children));
        }
      });
      return result;
    };

    const flatNodes = flattenNodes(mockKnowledgeNodes);
    const node = flatNodes.find(n => n.id === nodeId) ?? flatNodes[0];

    // 優先使用專屬的詳細 Mock 資料
    if (mockNodeDetails[nodeId]) {
      return mockNodeDetails[nodeId];
    }

    // 後備方案：生成基本的溯源資訊
    const doc = mockDocuments.find(d => d.id === node.documentId);
    return {
      node,
      citationText: '「該節點的詳細原文正在解析中。此處為 Mock 的基礎溯源文本，用於展示佈局效果。」',
      citationSource: {
        type: doc?.sourceType === 'YOUTUBE_URL' ? 'youtube' : 'pdf',
        documentTitle: doc?.title ?? '參考文件',
        page: 1,
        sourceUrl: doc?.sourceUrl ?? '',
      },
    };
  },
};

// ===========================
// Account Service
// ===========================

export const accountService = {
  async updateProfile(_req: UpdateProfileRequest): Promise<void> {
    await delay(500);
  },

  async getUsage(): Promise<GetUserUsageResponse> {
    await delay();
    return {
      usage: mockUsage,
      limits: {
        documentsPerMonth: 5,
        examsPerMonth: 3,
        aiQueriesPerDay: 10,
        visionOcrPagesPerMonth: 5,
        maxFileSizeMB: 10,
      },
    };
  },

  async getAchievements(): Promise<GetAchievementsResponse> {
    await delay();
    return {
      achievements: mockAchievements,
      milestones: mockMilestones,
    };
  },

  async getBillingHistory(): Promise<GetBillingHistoryResponse> {
    await delay();
    return {
      invoices: [
        { id: 'inv_001', date: '2026-03-01', amount: 0, currency: 'TWD', status: 'paid', pdfUrl: null },
      ],
    };
  },
};

// ===========================
// B2B Admin Service
// ===========================

export const adminService = {
  async getStudentList(subjectId?: string): Promise<GetStudentListResponse> {
    await delay();
    
    // 過濾學員：如果指定了學科，則僅顯示已報名該學科的學員
    const filteredStudents = subjectId 
      ? mockStudents.filter(s => s.enrolledSubjectIds?.includes(subjectId))
      : mockStudents;

    // 獲取學科專屬統計（如果有的話，否則回退到 PMP 預設值）
    const stats = subjectId && mockAdminSubjectStats[subjectId] 
      ? mockAdminSubjectStats[subjectId]
      : mockAdminSubjectStats['subj_pmp'];

    return {
      students: filteredStudents,
      total: filteredStudents.length,
      classStats: stats,
    };
  },
};

// ===========================
// Onboarding Service
// ===========================

export const onboardingService = {
  async getSubjectCatalog(): Promise<GetSubjectCatalogResponse> {
    await delay();
    return { subjects: mockSubjectCatalog };
  },

  async submit(req: SubmitOnboardingRequest): Promise<SubmitOnboardingResponse> {
    await delay(800);
    const userSubjects: UserSubject[] = req.subjects.map((s, i) => ({
      id: `us_${Date.now()}_${i}`,
      subjectId: s.subjectId,
      subjectName: mockSubjectCatalog.find(c => c.id === s.subjectId)?.name ?? s.subjectId,
      examDate: s.examDate,
      selfAssessment: s.selfAssessment,
      createdAt: new Date().toISOString(),
    }));
    return { success: true, userSubjects };
  },
};

// ===========================
// Subject Service
// ===========================

export const subjectService = {
  async getUserSubjects(): Promise<GetUserSubjectsResponse> {
    await delay();
    return { subjects: mockUserSubjects };
  },

  async addSubject(req: AddUserSubjectRequest): Promise<AddUserSubjectResponse> {
    await delay(500);
    const catalog = mockSubjectCatalog.find(s => s.id === req.subjectId);
    const subject: UserSubject = {
      id: `us_${Date.now()}`,
      subjectId: req.subjectId,
      subjectName: catalog?.name ?? req.subjectId,
      examDate: req.examDate,
      selfAssessment: req.selfAssessment,
      createdAt: new Date().toISOString(),
    };
    return { subject };
  },
};
