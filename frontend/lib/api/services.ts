/**
 * API Service Layer
 *
 * All service functions call the real backend API via apiClient.
 * The function signatures are the API contract.
 */

import { apiClient } from './client';

import type {
  DocumentSourceType,
  DocumentStatus,
  ImportTask,
  ImportTaskStatus,
  ImportDashboardStats,
  RecentJob,
  FailedJob,
  JobDetails,
  ImportPerformanceMetrics,
  StatusBreakdown,
} from '@/types/models';
import type {
  AuthResponse,
  LoginRequest,
  SignupRequest,
  UploadDocumentRequest,
  UploadDocumentResponse,
  GetDocumentsResponse,
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
  ImportStudentsResponse,
  GetSubjectCatalogResponse,
  SubmitOnboardingRequest,
  SubmitOnboardingResponse,
  GetUserSubjectsResponse,
  AddUserSubjectRequest,
  AddUserSubjectResponse,
  ChatMessage,
} from '@/types';

// ===========================
// Auth Service
// ===========================

/**
 * 認證服務：登入、註冊、Email 驗證、Google SSO 與目前使用者查詢。
 */
export const authService = {
  /**
   * 帳密登入。
   *
   * @param req - 含 email / password / rememberMe 的登入表單
   * @returns 含 JWT token 與 user 資訊的回應
   */
  async login(req: LoginRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/login', req);
  },

  async signup(req: SignupRequest): Promise<any> {
    return apiClient.post('/auth/register', {
      email: req.email,
      password: req.password,
      agreed_to_terms: true,
    });
  },

  async verifyEmail(token: string): Promise<{ error: boolean; message: string }> {
    return apiClient.post('/auth/verify-email', { token });
  },

  async resendVerification(email: string): Promise<{ error: boolean; message: string }> {
    return apiClient.post('/auth/resend-verification', { email });
  },

  async googleSSO(googleIdToken: string): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/google-sso', { google_id_token: googleIdToken });
  },

  async getCurrentUser(): Promise<AuthResponse | null> {
    try {
      return await apiClient.get<AuthResponse>('/auth/me');
    } catch {
      return null;
    }
  },
};

// ===========================
// Document Service
// ===========================

/**
 * 學習文件 / 資源服務：上傳（檔案、YouTube、分塊）、列表、刪除、考古題 markdown 取得。
 */
export const documentService = {
  async upload(req: UploadDocumentRequest): Promise<UploadDocumentResponse> {
    if (req.youtubeUrl) {
      return apiClient.post<UploadDocumentResponse>('/resources/youtube', {
        youtube_url: req.youtubeUrl,
        subject_id: req.subjectId,
      });
    }
    // File upload
    const formData = new FormData();
    if (req.file) formData.append('file', req.file);
    if (req.subjectId) formData.append('subject_id', req.subjectId);
    if (req.title) formData.append('filename', req.title);
    return apiClient.upload<UploadDocumentResponse>('/resources/upload-file', formData);
  },

  async list(): Promise<GetDocumentsResponse> {
    const raw = await apiClient.get<{ resources: Array<Record<string, unknown>> }>('/resources');
    const documents = (raw.resources || []).map((r): GetDocumentsResponse['documents'][0] => ({
      id: (r.id as string) || '',
      userId: '',
      subjectId: (r.subject_id as string) || '',
      sourceType: ((r.resource_type as string) || 'pdf').toUpperCase() as DocumentSourceType,
      title: (r.filename as string) || '',
      sourceUrl: (r.youtube_url as string) || '',
      mcpParsedTranscriptUrl: null,
      status: ((r.status as string) || '') as DocumentStatus,
      fileSizeBytes: ((r.file_size_mb as number) || 0) * 1024 * 1024,
      visionRequired: false,
      createdAt: (r.created_at as string) || new Date().toISOString(),
      errorMessage: (r.error_message as string | null) || null,
    }));
    return { documents, total: documents.length };
  },

  async getById(documentId: string): Promise<GetDocumentsResponse['documents'][0] | null> {
    try {
      return await apiClient.get(`/resources/${documentId}`);
    } catch {
      return null;
    }
  },

  async delete(documentId: string): Promise<void> {
    await apiClient.delete(`/resources/${documentId}`);
  },

  async getHistoricalMarkdown(historicalExamId: string): Promise<{ historical_exam_id: string; name: string; content: string; question_count: number }> {
    return apiClient.get(`/resources/historical/${historicalExamId}/markdown`);
  },

  async initChunkedUpload(filename: string, fileSize: number) {
    return apiClient.post<{ upload_id: string; chunk_size: number; total_chunks: number }>(
      '/resources/chunked/init',
      { filename, file_size: fileSize }
    );
  },

  async uploadChunk(uploadId: string, chunkIndex: number, chunk: Blob) {
    const formData = new FormData();
    formData.append('file', chunk);
    return apiClient.upload(`/resources/chunked/${uploadId}/chunk/${chunkIndex}`, formData);
  },

  async getChunkedUploadStatus(uploadId: string) {
    return apiClient.get(`/resources/chunked/${uploadId}/status`);
  },

  async mergeChunks(uploadId: string) {
    return apiClient.post(`/resources/chunked/${uploadId}/merge`);
  },
};

// ===========================
// Exam Service
// ===========================

/**
 * 模擬考試服務：建立 / 恢復考試、提交作答、取得結果。
 *
 * `create` 為兩階段流程：先 POST `/exams/config`，若回傳 `READY`（考古題模式）
 * 直接回傳，否則再呼叫 `/exams/{id}/generate` 觸發 AI 生題。
 */
export const examService = {
  async create(req: CreateExamRequest): Promise<CreateExamResponse> {
    // Step 1: Create exam config
    const configRes = await apiClient.post<{ exam_id: string }>('/exams/config', {
      document_ids: req.config?.selectedDocumentIds || [],
      node_ids: req.config?.selectedNodeIds || [],
      question_count: req.config?.questionCount || 10,
      difficulty: req.config?.difficulty || 2,
      question_types: req.config?.questionTypes,
      exam_mode: req.config?.examMode || 'hybrid',
    });

    const examId = (configRes as Record<string, unknown>).exam_id as string;
    const status = (configRes as Record<string, unknown>).status as string;

    // 考古題模式：config 已建好題目（READY），跳過 AI 生成
    if (status === 'READY') {
      return { exam: { id: examId }, exam_id: examId, examId } as unknown as CreateExamResponse;
    }

    // Step 2: AI 生成題目（hybrid 或 AI 模式）
    try {
      const genRes = await apiClient.post<Record<string, unknown>>(`/exams/${examId}/generate`);
      return {
        ...genRes,
        exam: { id: examId, ...(genRes.exam as Record<string, unknown> || {}) },
        exam_id: examId,
      } as unknown as CreateExamResponse;
    } catch {
      return { exam: { id: examId }, exam_id: examId, examId } as unknown as CreateExamResponse;
    }
  },

  async getExam(examId: string): Promise<CreateExamResponse> {
    const raw = await apiClient.get<Record<string, unknown>>(`/exams/${examId}/resume`);
    const rawQuestions = (raw.questions || []) as Array<Record<string, unknown>>;
    const rawExam = (raw.exam || {}) as Record<string, unknown>;
    return {
      exam: {
        id: (rawExam.id as string) || examId,
        title: (rawExam.title as string) || '模擬測驗',
        totalQuestions: (rawExam.total_questions as number) || rawQuestions.length,
        timeLimit: ((rawExam.duration_minutes as number) || 15) * 60,
      },
      questions: rawQuestions.map(q => ({
        id: (q.id as string) || '',
        examId,
        questionType: ((q.type as string) || 'single_choice').toUpperCase() as 'MULTIPLE_CHOICE',
        contentText: (q.content as string) || '',
        contentImageUrl: null,
        options: (q.options as Array<{ label: string; text: string }>) || [],
        correctAnswer: '',
        explanationMarkdown: '',
        citationChunkId: null,
        tags: [],
      })),
    } as unknown as CreateExamResponse;
  },

  async submit(req: SubmitExamRequest): Promise<SubmitExamResponse> {
    // Save each answer then submit
    for (const answer of req.answers) {
      await apiClient.post(`/exams/${req.examId}/answers`, {
        question_id: answer.questionId,
        user_choice: answer.userChoice,
      });
    }
    return apiClient.post<SubmitExamResponse>(`/exams/${req.examId}/submit`);
  },

  async getResults(examId: string): Promise<GetExamResultsResponse> {
    const raw = await apiClient.get<Record<string, unknown>>(`/exams/${examId}/result`);

    // Map backend flat response to frontend expected structure
    const score = Number(raw.score) || 0;
    const totalQuestions = (raw.total_questions as number) || 0;
    const correctCount = (raw.correct_count as number) || 0;

    return {
      exam: {
        id: (raw.exam_id as string) || examId,
        title: (raw.title as string) || '模擬測驗',
        score,
        totalQuestions,
        passingScore: Number(raw.passing_score) || 60,
        passStatus: (raw.pass_status as string) || (score >= 60 ? '通過' : '未通過'),
        timeSpent: (raw.time_spent_seconds as number) || 0,
      },
      questions: (raw.questions as GetExamResultsResponse['questions']) || [],
      userAnswers: (raw.user_answers as GetExamResultsResponse['userAnswers']) || Array.from({ length: totalQuestions }, (_, i) => ({
        questionId: `q_${i}`,
        userChoice: null,
        isCorrect: i < correctCount,
      })),
      domainAnalysis: (raw.domain_analysis as GetExamResultsResponse['domainAnalysis']) || [],
      aiSummary: (raw.ai_summary as string) || '',
    } as unknown as GetExamResultsResponse;
  },
};

// ===========================
// Review Service
// ===========================

/**
 * 錯題複習服務：錯題列表、AI 教練聊天、進階教練學習歷史。
 */
export const reviewService = {
  async getWrongQuestions(examId?: string, subjectId?: string): Promise<GetReviewQuestionsResponse> {
    const params = new URLSearchParams();
    if (examId) params.set('exam_id', examId);
    if (subjectId) params.set('subject_id', subjectId);
    const qs = params.toString();
    const raw = await apiClient.get<Record<string, unknown>>(`/wrong-answers${qs ? `?${qs}` : ''}`);

    // Map backend wrong_answers to frontend wrongQuestions
    const wrongAnswers = (raw.wrong_answers || raw.wrongQuestions || []) as Array<Record<string, unknown>>;
    return {
      examTitle: (raw.exam_title as string) || '錯題複習',
      wrongQuestions: wrongAnswers.map(wa => ({
        question: {
          id: (wa.question_id as string) || '',
          contentText: (wa.content as string) || '',
          content: (wa.content as string) || '',
          correctAnswer: (wa.correct_answer as string) || '',
          options: (wa.options as Array<{ label: string; text: string }>) || [],
          explanation: (wa.explanation as string) || '',
          explanationMarkdown: (wa.explanation as string) || '',
          subjectName: (wa.subject_name as string) || '',
          tags: [(wa.subject_name as string) || ''],
          citationChunkId: null,
          citationDocTitle: null,
          citationPage: null,
        },
        userAnswer: {
          userChoice: (wa.selected_answer as string) || '',
          isCorrect: false,
        },
      })),
    } as unknown as GetReviewQuestionsResponse;
  },

  async getChatHistory(questionId: string): Promise<ChatMessage[]> {
    try {
      const res = await apiClient.get<{ messages: ChatMessage[] }>(`/wrong-answers/questions/${questionId}/coach`);
      return res.messages || [];
    } catch {
      return [];
    }
  },

  async sendMessage(req: SendChatMessageRequest): Promise<SendChatMessageResponse> {
    return apiClient.post<SendChatMessageResponse>(
      `/wrong-answers/questions/${req.questionId}/coach`,
      { message: req.message },
    );
  },

  async getAdvancedCoach(subjectId?: string) {
    const params = subjectId ? `?subject_id=${subjectId}` : '';
    return apiClient.get(`/wrong-answers/advanced-coach${params}`);
  },

  async getLearningHistory(days = 30) {
    return apiClient.get(`/wrong-answers/advanced-coach/history?days=${days}`);
  },
};

// ===========================
// Dashboard Service
// ===========================

// ===========================
// Announcements (Public)
// ===========================

/**
 * 公告服務：取得目前 active 的公開公告（橫幅 / Modal）。
 */
export const announcementService = {
  async getActive(): Promise<{ announcements: { id: string; title: string; content: string; type: string; display_mode: string }[] }> {
    return apiClient.get('/announcements');
  },
};

// ===========================

/**
 * Dashboard 服務：每日任務、首頁總覽、複習日曆。
 */
export const dashboardService = {
  async get(subjectId?: string): Promise<GetDashboardResponse> {
    const params = subjectId ? `?subject_id=${subjectId}` : '';
    return apiClient.get<GetDashboardResponse>(`/dashboard${params}`);
  },

  async completeDailyQuest(req: CompleteDailyQuestRequest): Promise<void> {
    await apiClient.post(`/dashboard/quests/${req.questId}/complete`);
  },

  async getDailyQuests(): Promise<{ quests: Array<{ id: string; type: string; title: string; status: string; quest_type?: string; tooltip?: string }> }> {
    return apiClient.get('/dashboard/daily-quests');
  },

  async getReviewCalendar(subject?: string, month?: string): Promise<{ calendar: Array<{ date: string; count: number }>; subject: string | null; month: string | null }> {
    const qs = new URLSearchParams();
    if (subject) qs.set('subject', subject);
    if (month) qs.set('month', month);
    const q = qs.toString();
    return apiClient.get(`/dashboard/review-calendar${q ? '?' + q : ''}`);
  },
};

// ===========================
// Knowledge Service
// ===========================

/**
 * 知識節點下的單一學習鷹架（takeaway / elaborative / strategy）。
 */
export interface NodeScaffoldItem {
  /** Scaffold UUID */
  id: string;
  /** 鷹架類型 */
  type: 'takeaway' | 'elaborative' | 'strategy';
  chapter_heading: string | null;
  content: string;
  page_start: number | null;
  page_end: number | null;
  user_response: string | null;
  responded_at: string | null;
  reference_answer?: string | null;
}

/**
 * 取得知識節點下所有鷹架的回應結構。
 */
export interface NodeScaffoldsResponse {
  /** 節點 UUID */
  node_id: string;
  /** 該節點下的鷹架列表 */
  scaffolds: NodeScaffoldItem[];
}

/**
 * 知識圖譜服務：節點層級、節點細節、鷹架、資源摘要與反向工程。
 */
export const knowledgeService = {
  async getMap(subjectId?: string): Promise<Record<string, unknown>> {
    const path = subjectId
      ? `/knowledge-map/subjects/${subjectId}/nodes`
      : '/knowledge-map/layout';
    return apiClient.get<Record<string, unknown>>(path);
  },

  async getNodeDetail(nodeId: string): Promise<GetNodeDetailResponse> {
    return apiClient.get<GetNodeDetailResponse>(`/knowledge-map/nodes/${nodeId}`);
  },

  async getNodeScaffolds(nodeId: string): Promise<NodeScaffoldsResponse> {
    return apiClient.get<NodeScaffoldsResponse>(`/knowledge-map/nodes/${nodeId}/scaffolds`);
  },

  async getResourceScaffolds(resourceId: string): Promise<NodeScaffoldsResponse> {
    return apiClient.get<NodeScaffoldsResponse>(`/knowledge-map/resources/${resourceId}/scaffolds`);
  },

  async getResourceSummary(resourceId: string): Promise<{ title: string; content: string; node_count: number }> {
    return apiClient.get(`/knowledge-map/resources/${resourceId}/summary`);
  },

  async extractKnowledgeTree(subjectId: string): Promise<Record<string, unknown>> {
    return apiClient.post<Record<string, unknown>>(`/reverse-engineering/subjects/${subjectId}/extract`, {});
  },

  async getResourceChunks(resourceId: string): Promise<Record<string, unknown>> {
    return apiClient.get<Record<string, unknown>>(`/resources/${resourceId}/chunks`);
  },
};

// ===========================
// Account Service
// ===========================

/**
 * 帳號服務：個人資料 / 頭像、用量、成就、帳單與帳號刪除。
 */
export const accountService = {
  async updateProfile(req: UpdateProfileRequest): Promise<void> {
    await apiClient.patch('/dashboard/profile', {
      display_name: req.displayName,
      age: req.age,
      education: req.education,
      career: req.occupation,
      daily_study_minutes: req.dailyStudyMinutes,
      learning_style: req.learningStyle,
    });
  },

  async uploadAvatar(file: File): Promise<void> {
    const formData = new FormData();
    formData.append('avatar', file);
    await apiClient.upload('/dashboard/profile/avatar', formData);
  },

  async getUsage(): Promise<GetUserUsageResponse> {
    return apiClient.get<GetUserUsageResponse>('/dashboard/usage');
  },

  async getAchievements(): Promise<GetAchievementsResponse> {
    return apiClient.get<GetAchievementsResponse>('/dashboard/achievements');
  },

  async getBillingHistory(): Promise<GetBillingHistoryResponse> {
    return apiClient.get<GetBillingHistoryResponse>('/subscriptions/invoices');
  },

  async deleteAccount(): Promise<void> {
    await apiClient.delete('/auth/delete-account');
  },
};

// ===========================
// Subscription Service
// ===========================

/**
 * 訂閱方案服務：升級 / 取消、Trial 流程、FUP 檢查、退款與 Coupon 驗證。
 */
export const subscriptionService = {
  async upgrade(plan: string): Promise<void> {
    await apiClient.post('/subscriptions/upgrade', { plan });
  },

  async cancel(): Promise<void> {
    await apiClient.post('/subscriptions/cancel');
  },

  async startTrial() {
    return apiClient.post('/subscriptions/trial/start');
  },

  async getTrialStatus() {
    return apiClient.get('/subscriptions/trial/status');
  },

  async convertTrialToPaid() {
    return apiClient.post('/subscriptions/trial/convert');
  },

  async checkFup() {
    return apiClient.get('/subscriptions/fup/check');
  },

  async requestRefund(transactionId: string, amount: number, reason?: string) {
    return apiClient.post<{ refund_id: string; status: string }>(
      '/subscriptions/refund-request',
      { transaction_id: transactionId, amount, reason }
    );
  },

  async validateCoupon(code: string, plan: string, amount: number) {
    return apiClient.post<{ discount_amount: number; final_amount: number; code: string }>(
      '/subscriptions/coupons/validate',
      { code, plan, amount }
    );
  },
};

// ===========================
// Difficulty Progression Service
// ===========================

/**
 * 難度推進「下一步策略」的回應（後端可擴充任意欄位）。
 */
export interface NextStrategyResponse {
  /** 建議動作（例：advance / retry / switch_node） */
  action?: string;
  /** 下一個節點 UUID */
  next_node_id?: string;
  /** 目標難度等級 */
  target_difficulty?: string;
  /** 後端決策的人類可讀理由 */
  reason?: string;
  [key: string]: unknown;
}

/**
 * 難度自動推進服務：開始流程、查下一步策略、取得整條 trail。
 */
export const difficultyProgressionService = {
  async start(subjectId: string): Promise<{ message: string; status: string }> {
    return apiClient.post(`/difficulty-progression/subjects/${subjectId}/start`);
  },

  async nextStrategy(
    subjectId: string,
    params: {
      current_node_id: string;
      original_node_id?: string;
      consecutive_wrong?: number;
      consecutive_correct?: number;
    }
  ): Promise<NextStrategyResponse> {
    return apiClient.post(`/difficulty-progression/subjects/${subjectId}/next-strategy`, params);
  },

  async getTrail(subjectId: string): Promise<{ trail: Array<Record<string, unknown>> }> {
    return apiClient.get(`/difficulty-progression/subjects/${subjectId}/trail`);
  },
};

// ===========================
// Community Service
// ===========================

/**
 * 社群儀表板上的橫幅通知。
 */
export interface CommunityBanner {
  /** 橫幅樣式分類 */
  type: string;
  /** 顯示訊息 */
  message: string;
}

/**
 * 每週學習報告的單一週紀錄。
 */
export interface WeeklyReportItem {
  id: string;
  week_start: string;
  week_end: string;
  study_hours: number;
  exams_completed: number;
  questions_answered: number;
  progress_summary: string;
}

/**
 * 考後 AI 教練回饋。
 */
export interface ExamCoaching {
  /** 是否觸發教練介入 */
  coaching_triggered: boolean;
  /** 觸發的教練名稱 */
  coach_name?: string;
  /** 多語系或多段訊息 map */
  message?: Record<string, string>;
}

/**
 * 社群服務：社群橫幅、每週報告、考後教練。
 */
export const communityService = {
  async getDashboard(): Promise<{ banner: CommunityBanner | null }> {
    return apiClient.get('/community/dashboard');
  },
  async getWeeklyReports(): Promise<{ reports: WeeklyReportItem[] }> {
    return apiClient.get('/community/weekly-reports');
  },
  async getExamCoaching(): Promise<ExamCoaching> {
    return apiClient.get('/community/exam-results/coaching');
  },
};

// ===========================
// Learning Journey Service
// ===========================

/**
 * 待確認結果的學習旅程紀錄。
 */
export interface PendingJourneyItem {
  /** Journey UUID */
  id: string;
  /** 對應科目 ID */
  subject_id: string;
  /** 科目名稱 */
  subject_name: string;
  /** 應試日 ISO 日期 */
  exam_date: string | null;
  /** 放榜日 ISO 日期 */
  result_date: string | null;
  /** 結果狀態（passed / failed / null = 尚未填寫） */
  exam_result_status: string | null;
}

/**
 * 學習旅程服務：列出待確認、回填考試結果、再戰 / 放棄、更新放榜日。
 */
export const learningJourneyService = {
  async listPending(): Promise<{ items: PendingJourneyItem[] }> {
    return apiClient.get('/learning-journeys/pending');
  },

  async confirmResult(journeyId: string, status: 'passed' | 'failed'): Promise<Record<string, unknown>> {
    return apiClient.post(`/learning-journeys/${journeyId}/exam-result`, { status });
  },

  async retake(journeyId: string, examDate?: string, resultDate?: string): Promise<Record<string, unknown>> {
    return apiClient.post(`/learning-journeys/${journeyId}/retake`, {
      exam_date: examDate,
      result_date: resultDate,
    });
  },

  async quit(journeyId: string): Promise<Record<string, unknown>> {
    return apiClient.post(`/learning-journeys/${journeyId}/quit`);
  },

  async updateResultDate(journeyId: string, resultDate: string): Promise<Record<string, unknown>> {
    return apiClient.put(`/learning-journeys/${journeyId}/result-date`, { result_date: resultDate });
  },
};

// ===========================
// Anomaly Service (Admin)
// ===========================

/**
 * 系統異常單一筆紀錄（admin 監控用）。
 */
export interface AnomalyItem {
  /** 錯誤事件 ID */
  error_id: string;
  /** 錯誤分類 */
  error_type: string;
  /** 出現次數 */
  occurrence_count: number;
  /** 處理狀態 */
  status: string;
  /** 受影響範圍描述 */
  impact_scope: string | null;
  /** 指派處理人 ID */
  assigned_to: string | null;
  /** 首次出現時間 */
  first_seen_at: string | null;
  /** 最近出現時間 */
  last_seen_at: string | null;
  /** 是否已被分類 */
  classified: boolean;
}

/**
 * 異常管理服務（Admin）：列表、更新、維運任務 / 排程 / 維護模式。
 */
export const anomalyService = {
  async listAnomalies(): Promise<{ items: AnomalyItem[] }> {
    return apiClient.get('/admin/anomalies');
  },
  async updateAnomaly(errorId: string, status: string, assignedTo?: string): Promise<{ status: string; error_id: string }> {
    return apiClient.put(`/admin/anomalies/${errorId}`, { status, assigned_to: assignedTo });
  },
  async createMaintenanceTask(data: { name: string; priority: string; related_error?: string; estimated_hours?: number }): Promise<Record<string, unknown>> {
    return apiClient.post('/admin/maintenance-tasks', data);
  },
  async updateTaskStatus(taskId: string, status: string): Promise<Record<string, unknown>> {
    return apiClient.put(`/admin/maintenance-tasks/${taskId}/status`, { status });
  },
  async createMaintenanceSchedule(data: { name: string; starts_at: string; ends_at: string; notify_channels?: string; notify_targets?: string; notify_before?: string }): Promise<Record<string, unknown>> {
    return apiClient.post('/admin/maintenance-schedules', data);
  },
  async activateMaintenanceMode(reason: string, estimatedRecovery: string): Promise<Record<string, unknown>> {
    return apiClient.post('/admin/maintenance-mode', { reason, estimated_recovery: estimatedRecovery });
  },
};

// ===========================
// B2B Admin Service
// ===========================

/**
 * B2B 機構管理服務：學員管理、匯入、DPA、補救考試、機構級指標。
 *
 * 涵蓋三層：學員 / 班級（group）/ 機構（institution）。
 */
export const adminService = {
  async getStudentList(subjectId?: string): Promise<GetStudentListResponse> {
    const params = subjectId ? `?subject_id=${subjectId}` : '';
    return apiClient.get<GetStudentListResponse>(`/b2b/dashboard${params}`);
  },

  async importStudents(file: File, consentChecked = true, confirmSurcharge = false): Promise<ImportStudentsResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload<ImportStudentsResponse>(
      `/b2b/students/import?consent_checked=${consentChecked}&confirm_surcharge=${confirmSurcharge}`,
      formData
    );
  },

  async signDpa(signerName: string) {
    return apiClient.post('/b2b/dpa/sign', { signer_name: signerName });
  },

  async getDpa() {
    return apiClient.get('/b2b/dpa');
  },

  async removeStudent(studentId: string) {
    return apiClient.delete(`/b2b/students/${studentId}`);
  },

  async batchRemoveStudents(studentIds: string[]) {
    return apiClient.post('/b2b/students/batch-remove', { student_ids: studentIds });
  },

  async deleteGroup(groupId: string) {
    return apiClient.delete(`/b2b/groups/${groupId}`);
  },

  async getStudentReport(studentId: string) {
    return apiClient.get(`/b2b/students/${studentId}/report`);
  },

  async getStudentCompetency(studentId: string) {
    return apiClient.get(`/b2b/students/${studentId}/competency`);
  },

  async getAiSuggestions(studentId: string) {
    return apiClient.post(`/b2b/students/${studentId}/ai-suggestions`, {});
  },

  async getClassWeakness(groupId: string) {
    return apiClient.get(`/b2b/class/${groupId}/weakness`);
  },

  async generateRemediationExam(groupId: string, questionCount = 20) {
    return apiClient.post(`/b2b/exam/remediation/${groupId}`, { question_count: questionCount });
  },

  async getRemediationDefaults(studentId: string) {
    return apiClient.get(`/b2b/students/${studentId}/remediation-defaults`);
  },

  async createStudentRemediation(studentId: string, data: { question_count: number; competency_weights: { label: string; weight: number }[] }) {
    return apiClient.post(`/b2b/students/${studentId}/remediation-exam`, data);
  },

  // ── Institution-level (platform admin oversight) ──
  async getAdminDashboard() {
    return apiClient.get('/b2b/admin-dashboard');
  },
  async getInstitutionDpa(instId: string) {
    return apiClient.get(`/b2b/institutions/${instId}/dpa`);
  },
  async getInstitutionStudents(instId: string) {
    return apiClient.get(`/b2b/institutions/${instId}/students`);
  },
  async removeInstitutionStudent(instId: string, email: string) {
    return apiClient.delete(`/b2b/institutions/${instId}/students/${encodeURIComponent(email)}`);
  },
  async cancelInstitutionSubscription(instId: string) {
    return apiClient.post(`/b2b/institutions/${instId}/cancel-subscription`, {});
  },
  async getInstitutionErrorRanking(instId: string) {
    return apiClient.get(`/b2b/institutions/${instId}/error-ranking`);
  },
  async getInstitutionHealthKpi(instId: string) {
    return apiClient.get(`/b2b/institutions/${instId}/health-kpi`);
  },
  async getInstitutionEarlyWarnings(instId: string) {
    return apiClient.get(`/b2b/institutions/${instId}/early-warnings`);
  },
  async updateInstitutionWarningRules(instId: string, rules: unknown) {
    return apiClient.put(`/b2b/institutions/${instId}/warning-rules`, rules);
  },

  // ── Group-level ──
  async getGroupStudents(groupId: string) {
    return apiClient.get(`/b2b/groups/${groupId}/students`);
  },
  async assignGroupExam(groupId: string, data: unknown) {
    return apiClient.post(`/b2b/groups/${groupId}/assign-exam`, data);
  },
  async getGroupHeatmap(groupId: string) {
    return apiClient.get(`/b2b/groups/${groupId}/heatmap`);
  },
};

// ===========================
// Feedback Service (User)
// ===========================

/**
 * 使用者意見回饋服務：列出我送出的意見、查看詳情。
 */
export const feedbackService = {
  async listMyFeedbacks(): Promise<{ feedbacks: { feedback_id: string; type: string; subject: string; content: string; status: string; admin_reply: string; resolved_at: string | null; created_at: string | null }[]; count: number }> {
    return apiClient.get('/feedback');
  },

  async getFeedbackDetail(feedbackId: string): Promise<{ feedback_id: string; type: string; subject: string; content: string; status: string; admin_reply: string; resolved_at: string | null; created_at: string | null }> {
    return apiClient.get(`/feedback/${feedbackId}`);
  },
};

// ===========================
// Super Admin Service
// ===========================

/**
 * Super Admin 服務：使用者管理、系統設定、財務、內容審核、稽核日誌、儀表板等。
 *
 * 僅 `ADMIN` / `SUPER_ADMIN` role 能呼叫；後端會驗證權限。
 */
export const superAdminService = {
  async getUsers(params?: { search?: string; tier?: string; page?: number }): Promise<{ users: unknown[]; total: number }> {
    const qs = new URLSearchParams();
    if (params?.search) qs.set('keyword', params.search);
    if (params?.tier && params.tier !== 'All') qs.set('plan', params.tier);
    if (params?.page) qs.set('page', String(params.page));
    const q = qs.toString();
    return apiClient.get(`/admin/users${q ? `?${q}` : ''}`);
  },

  async getUserDetail(userId: string): Promise<Record<string, unknown>> {
    return apiClient.get(`/admin/users/${userId}`);
  },

  async exportUsersCSV(): Promise<Blob> {
    const token = (await import('./client')).getStoredToken();
    const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
    const res = await fetch(`${BASE_URL}/admin/users/export`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`Export failed: ${res.status}`);
    return res.blob();
  },

  async createUser(email: string, password: string): Promise<{ user_id: string; email: string }> {
    return apiClient.post('/admin/users', { email, password });
  },

  async suspendUser(userId: string, reason?: string): Promise<void> {
    await apiClient.post('/admin/users/suspend', { target_user_id: userId, reason });
  },

  async activateUser(userId: string): Promise<void> {
    await apiClient.post('/admin/users/activate', { target_user_id: userId });
  },

  async adjustRole(email: string, role: string): Promise<void> {
    await apiClient.post('/admin/users/adjust-role', { target_email: email, role });
  },

  async deleteUser(userId: string, confirmName: string): Promise<void> {
    await apiClient.post('/admin/users/delete', { target_user_id: userId, confirm_name: confirmName });
  },

  async notifyUser(userId: string, message: string): Promise<{ message: string }> {
    return apiClient.post(`/admin/users/${userId}/notify`, { message });
  },

  async getSettings(): Promise<Record<string, unknown>> {
    return apiClient.get('/admin/settings');
  },

  async getFeatureFlags(): Promise<{ flags: { id: string; name: string; description: string; enabled: boolean }[] }> {
    return apiClient.get('/admin/system-settings/feature-flags');
  },

  async getAdmins(): Promise<{ admins: { id: string; name: string; email: string; role: string; joined: string }[] }> {
    return apiClient.get('/admin/users?role=admin');
  },

  async getAnnouncements(): Promise<{ announcements: { id: string; title: string; content: string; display_mode: string; created_at: string }[] }> {
    return apiClient.get('/admin/system-settings/announcements');
  },

  async getPlanQuotas(): Promise<{ quotas: { label: string; key: string; free: number | string; pro: number | string; pro_plus: number | string; ultra: number | string }[] }> {
    const raw = await apiClient.get<{ quotas: { plan: string; monthly_uploads: number; monthly_exams: number; daily_ai_chats: number; monthly_vision_pages: number; max_file_size_mb: number }[] }>('/admin/system-settings/plan-quotas');
    if (!Array.isArray(raw?.quotas)) return { quotas: [] };
    // Transform: per-plan rows → per-parameter rows
    const planMap: Record<string, Record<string, number | string>> = {};
    for (const q of raw.quotas) {
      planMap[q.plan] = q as unknown as Record<string, number | string>;
    }
    const params = [
      { label: '每月上傳數', key: 'monthly_uploads' },
      { label: '每月考試數', key: 'monthly_exams' },
      { label: '每日 AI 對話數', key: 'daily_ai_chats' },
      { label: '每月 Vision 頁數', key: 'monthly_vision_pages' },
      { label: '最大檔案大小 (MB)', key: 'max_file_size_mb' },
    ];
    const quotas = params.map(p => ({
      label: p.label,
      key: p.key,
      free: planMap['FREE']?.[p.key] ?? '--',
      pro: planMap['PRO']?.[p.key] ?? '--',
      pro_plus: planMap['PRO_PLUS']?.[p.key] ?? '--',
      ultra: planMap['ULTRA']?.[p.key] ?? '--',
    }));
    return { quotas };
  },

  async getModelRouting(): Promise<Record<string, unknown>> {
    return apiClient.get('/admin/system-settings/model-routing');
  },

  async updateModelRouting(plan: string, taskType: string, model: string): Promise<void> {
    await apiClient.put(`/admin/system-settings/model-routing/${plan}/${taskType}`, { primary_model: model });
  },

  async updatePlanQuota(plan: string, quotas: Record<string, unknown>): Promise<void> {
    await apiClient.put(`/admin/system-settings/plan-quota/${plan}`, quotas);
  },

  async createAnnouncement(data: { title: string; content: string; display_mode: string; schedule_date?: string }): Promise<void> {
    await apiClient.post('/admin/system-settings/announcements', data);
  },

  async deactivateAnnouncement(id: string): Promise<void> {
    await apiClient.put(`/admin/system-settings/announcements/${id}/deactivate`, {});
  },

  async deleteAnnouncement(id: string): Promise<void> {
    await apiClient.delete(`/admin/system-settings/announcements/${id}`);
  },

  async updateFeatureFlag(flagId: string, enabled: boolean): Promise<void> {
    await apiClient.put(`/admin/system-settings/feature-flags/${flagId}`, { enabled });
  },

  async getFinanceOverview(): Promise<{ mrr: number; arpu: number; churn_rate: number; ltv: number; mrr_trend: string; arpu_trend: string; churn_trend: string; ltv_trend: string }> {
    const raw = await apiClient.get<Record<string, unknown>>('/admin/finance/overview');
    return {
      mrr: Number(raw.mrr || 0),
      arpu: Number(raw.arpu || 0),
      churn_rate: Number(raw.churn_rate || 0),
      ltv: Number(raw.ltv || 0),
      mrr_trend: (raw.mrr_trend as string) || '--',
      arpu_trend: (raw.arpu_trend as string) || '--',
      churn_trend: (raw.churn_trend as string) || '--',
      ltv_trend: (raw.ltv_trend as string) || '--',
    };
  },

  async getFinanceTransactions(): Promise<{ transactions: { id: string; user: string; amount: string; plan: string; status: string; time: string }[] }> {
    const raw = await apiClient.get<{ transactions: Array<Record<string, unknown>> }>('/admin/finance/transactions');
    return {
      transactions: (raw.transactions || []).map(t => ({
        id: String(t.transaction_id || t.id || ''),
        user: String(t.user_email || t.user_id || t.user || ''),
        amount: `NT$${Number(t.amount || 0).toLocaleString()}`,
        plan: String(t.target_plan || t.plan || ''),
        status: String(t.status || ''),
        time: String(t.created_at || t.time || ''),
      })),
    };
  },

  async getMrrTrend(): Promise<{ data: { name: string; new: number; expansion: number; churn: number }[] }> {
    const raw = await apiClient.get<{ trend?: Array<Record<string, unknown>>; data?: Array<Record<string, unknown>> }>('/admin/finance/mrr-trend');
    const items = raw.trend || raw.data || [];
    return {
      data: items.map(r => ({
        name: String(r.name || ''),
        new: Number(r.mrr || r.new || 0),
        expansion: Number(r.expansion || 0),
        churn: Number(r.churn || 0),
      })),
    };
  },

  async getSubscriptionDistribution(): Promise<{ distribution: { name: string; value: number; color: string }[] }> {
    const PLAN_COLORS: Record<string, string> = {
      FREE: '#94a3b8', PRO_199: '#10b981', PRO_PLUS_399: '#6366f1', ULTRA_1599: '#f59e0b', EDU: '#06b6d4',
    };
    const raw = await apiClient.get<{ distribution: Record<string, number> | Array<Record<string, unknown>> }>('/admin/finance/subscription-distribution');
    const dist = raw.distribution;
    // Backend returns dict { "FREE": 3, "ULTRA_1599": 3 }; frontend needs array
    if (dist && !Array.isArray(dist)) {
      return {
        distribution: Object.entries(dist)
          .filter(([, v]) => v > 0)
          .map(([name, value]) => ({
            name,
            value,
            color: PLAN_COLORS[name] || '#94a3b8',
          })),
      };
    }
    // Already array (future-proof)
    return { distribution: (dist as Array<{ name: string; value: number; color: string }>) || [] };
  },

  async listRefunds(status?: string): Promise<{ refunds: Array<{ refund_id: string; user_id: string; user_email?: string; transaction_id: string; amount: number; status: string; reason?: string; created_at?: string }> }> {
    const q = status ? `?status=${status}` : '';
    return apiClient.get(`/admin/finance/refunds${q}`);
  },

  async approveRefund(refundId: string): Promise<{ status: string }> {
    return apiClient.post(`/admin/finance/refunds/${refundId}/approve`);
  },

  async rejectRefund(refundId: string, reason: string): Promise<{ status: string }> {
    return apiClient.post(`/admin/finance/refunds/${refundId}/reject`, { reason });
  },

  async listCoupons(): Promise<{ coupons: Array<{ code: string; discount_type: string; discount_value: number; status: string; used_count?: number; max_uses?: number }> }> {
    return apiClient.get('/admin/finance/coupons');
  },

  async createCoupon(data: { code: string; discount_type: string; discount_value: number; applicable_plans?: string; max_uses?: number; max_uses_per_user?: number }): Promise<{ code: string; status: string }> {
    return apiClient.post('/admin/finance/coupons', data);
  },

  async getModerationQueue(): Promise<{ items: { id: string; user: string; type: string; content: string; reason: string; status: string; time: string }[] }> {
    return apiClient.get('/admin/moderation/queue');
  },

  async getModerationStats(): Promise<{ pending_reports: number; auto_flagged_today: number; cooled_users: number; false_positive_rate: string }> {
    return apiClient.get('/admin/moderation/stats');
  },

  async getAbuseMonitoring(): Promise<{ items: { id: string; user: string; metric: string; count: string; status: string; time: string }[] }> {
    return apiClient.get('/admin/moderation/abuse');
  },

  async getContentReviewQueue(): Promise<{ items: { id: number; type: string; content: string; reporter: string; status: 'pending' | 'resolved'; date: string }[] }> {
    return apiClient.get('/admin/moderation/content-review');
  },

  async approveContent(itemId: string): Promise<void> {
    await apiClient.post(`/admin/moderation/${itemId}/approve`);
  },

  async rejectContent(itemId: string): Promise<void> {
    await apiClient.post(`/admin/moderation/${itemId}/reject`);
  },

  async unlockCooldown(targetUserId: string): Promise<{ message: string }> {
    return apiClient.post(`/admin/moderation/ai-abuse/${targetUserId}/unlock`);
  },

  // --- Feedback Admin ---
  async getAdminFeedbacks(status?: string): Promise<{ feedbacks: { feedback_id: string; type: string; subject: string; content_preview: string; content: string; status: string; user_id: string; user_email: string; admin_reply: string; attachment_urls: string[]; created_at: string | null; resolved_at: string | null }[]; count: number }> {
    const params = status ? `?status=${status}` : '';
    return apiClient.get(`/feedback/admin/list${params}`);
  },

  async getAdminFeedbackStats(): Promise<{ total_count: number; pending_count: number; reviewing_count: number; resolved_count: number; top_category: string | null; avg_resolve_hours: number }> {
    return apiClient.get('/feedback/admin/stats');
  },

  async updateFeedback(feedbackId: string, data: { status: string; admin_reply?: string; close_reason?: string }): Promise<{ feedback_id: string; status: string; resolved_at: string | null }> {
    return apiClient.put(`/feedback/admin/${feedbackId}`, data);
  },

  async getAuditLogs(): Promise<{ logs: { id: string; timestamp: string; admin_id: string; admin_email: string; action: string; target_type: string; target_id: string; details: string; ip_address: string }[] }> {
    return apiClient.get('/admin/system-settings/audit-logs');
  },

  async getDashboardAlerts(): Promise<{ alerts: { id: number; type: string; message: string; time: string }[]; system_alerts: { severity: string; message: string; time: string }[] }> {
    return apiClient.get('/admin/dashboard/alerts');
  },

  async getSystemLoad(): Promise<{ cpu_percent: number; db_connections_percent: number; queue_depth_percent: number }> {
    return apiClient.get('/admin/dashboard/system-load');
  },

  async getDashboardCharts(): Promise<{ user_growth: { name: string; dau: number; mau: number }[]; ai_cost: { name: string; gemini: number; claude: number; gpt4: number; voyage: number }[] }> {
    return apiClient.get('/admin/dashboard/charts');
  },

  async getVersionInfo(): Promise<{
    backend_version: string;
    backend_commit: string;
    api_prefix: string;
    python_version: string;
    alembic_head: string;
    deployed_at: string;
    environment: string;
  }> {
    return apiClient.get('/admin/version');
  },
};

// ===========================
// Onboarding Service
// ===========================

/**
 * 使用者新手引導服務：科目目錄、提交引導完成。
 */
export const onboardingService = {
  async getSubjectCatalog(): Promise<GetSubjectCatalogResponse> {
    return apiClient.get<GetSubjectCatalogResponse>('/onboarding/subjects');
  },

  async submit(req: SubmitOnboardingRequest): Promise<SubmitOnboardingResponse> {
    return apiClient.post<SubmitOnboardingResponse>('/onboarding/complete', {
      display_name: req.displayName,
      subjects: req.subjects.map(s => ({
        subject_name: s.subjectName || s.subjectId,
        exam_date: s.examDate,
        self_assessed_level: s.selfAssessment,
      })),
      daily_study_minutes: req.dailyStudyMinutes,
      learning_preference: req.learningStyle,
    });
  },
};

// ===========================
// Subject Service
// ===========================

/**
 * 使用者科目服務：取得 / 新增 / 刪除使用者已選擇的考科。
 */
export const subjectService = {
  async getUserSubjects(): Promise<GetUserSubjectsResponse> {
    const raw = await apiClient.get<{
      subjects?: Array<{
        id?: string;
        name?: string;
        subject_name?: string;
        exam_date?: string;
        result_date?: string;
        self_assessed_level?: string;
      }>;
    }>('/onboarding/summary');
    const subjects = (raw.subjects || []).map((s, i) => ({
      id: s.id || `subject_${i}`,
      subjectId: s.id || `subject_${i}`,
      subjectName: s.subject_name || s.name || '',
      examDate: s.exam_date || '',
      resultDate: s.result_date || '',
      selfAssessment: (s.self_assessed_level || 'beginner') as 'beginner' | 'intermediate' | 'advanced',
      createdAt: new Date().toISOString(),
    }));
    return { subjects };
  },

  async addSubject(req: AddUserSubjectRequest): Promise<AddUserSubjectResponse> {
    return apiClient.post<AddUserSubjectResponse>('/subjects', {
      subject_name: req.subjectName || req.subjectId,
      exam_date: req.examDate,
      result_date: req.resultDate,
      self_assessed_level: req.selfAssessment,
    });
  },

  // PRD-033 US-01：自建考科列表
  async getMyCustomSubjects(): Promise<{
    subjects: Array<{ id: string; name: string; description?: string; category_id?: string; created_at?: string }>;
  }> {
    return apiClient.get('/subjects/mine');
  },

  async deleteSubject(subjectId: string): Promise<{ ok?: boolean }> {
    return apiClient.delete(`/subjects/${subjectId}`);
  },
};

// ── PRD-033 資源分享與預設綁定 ────────────────────────────────────────────

/**
 * 資源分享服務（PRD-033 US-03）：Ultra 用戶將資源分享給 EDU 機構。
 */
export const resourceShareService = {
  // US-03：Ultra 分享資源給 EDU
  async shareToInstitution(resourceId: string, targetInstitutionId: string) {
    return apiClient.post(`/resources/${resourceId}/share-to-institution`, {
      target_institution_id: targetInstitutionId,
    });
  },
  async revokeShare(resourceId: string) {
    return apiClient.delete(`/resources/${resourceId}/share`);
  },
};

/**
 * 平台預設資源綁定服務（PRD-033 US-04）：管理員為科目綁定 / 解除預設資源。
 */
export const adminDefaultResourceService = {
  // US-04：管理員綁定平台預設資源
  async bindDefault(subjectId: string, resourceId: string) {
    return apiClient.post(`/admin/subjects/${subjectId}/default-resources`, {
      resource_id: resourceId,
    });
  },
  async unbindDefault(subjectId: string, resourceId: string) {
    return apiClient.delete(`/admin/subjects/${subjectId}/default-resources/${resourceId}`);
  },
};

// ── Prompt Template Service ────────────────────────────────────────────────

/**
 * Prompt 模板列表項摘要。
 */
export interface PromptTemplateSummary {
  template_id: string;
  name: string;
  display_name: string;
  category: string;
  model: string;
  temperature: number;
  current_version: number;
  is_active: boolean;
}

/**
 * Prompt 模板詳細資料；繼承摘要欄位並加上 prompt 內容與配額限制。
 */
export interface PromptTemplateDetail extends PromptTemplateSummary {
  system_prompt: string;
  user_prompt: string;
  variables: Array<{ name: string; description: string; example: string }>;
  max_tokens: number;
  max_tokens_by_plan?: Record<string, number>;
  feature_refs?: string[];
  created_at?: string;
}

/**
 * Prompt 模板的歷史版本紀錄。
 */
export interface PromptTemplateVersion {
  version: number;
  model: string;
  system_prompt: string;
  user_prompt: string;
  temperature: number;
  change_note?: string;
  created_by?: string;
  created_at?: string;
}

/**
 * Prompt A/B 測試紀錄。
 */
export interface PromptAbTest {
  id: string;
  template_id: string;
  name: string;
  variant_a_version: number;
  traffic_split: number;
  status: 'running' | 'completed' | 'cancelled';
  winner?: string;
  metric_name?: string;
  started_at?: string;
  ended_at?: string;
}

/**
 * Prompt 模板管理服務（Admin）：CRUD、版本回溯、A/B 測試。
 */
export const promptTemplateService = {
  async listTemplates(category?: string): Promise<{ templates: PromptTemplateSummary[]; total: number }> {
    const q = category ? `?category=${category}` : '';
    return apiClient.get(`/admin/prompt-templates${q}`);
  },

  async getTemplate(templateId: string): Promise<PromptTemplateDetail> {
    return apiClient.get(`/admin/prompt-templates/${templateId}`);
  },

  async createTemplate(data: Partial<PromptTemplateDetail> & { change_note?: string }): Promise<{ template_id: string; current_version: number }> {
    return apiClient.post('/admin/prompt-templates', data);
  },

  async updateTemplate(templateId: string, data: Partial<PromptTemplateDetail> & { change_note?: string }): Promise<{ template_id: string; current_version: number }> {
    return apiClient.patch(`/admin/prompt-templates/${templateId}`, data);
  },

  async deactivateTemplate(templateId: string): Promise<{ template_id: string; is_active: boolean }> {
    return apiClient.delete(`/admin/prompt-templates/${templateId}`);
  },

  async listVersions(templateId: string): Promise<{ versions: PromptTemplateVersion[]; total: number }> {
    return apiClient.get(`/admin/prompt-templates/${templateId}/versions`);
  },

  async rollbackTemplate(templateId: string, version: number): Promise<{ template_id: string; current_version: number }> {
    return apiClient.post(`/admin/prompt-templates/${templateId}/rollback`, { version });
  },

  async createAbTest(templateId: string, data: {
    name: string;
    variant_b_system_prompt: string;
    variant_b_user_prompt: string;
    variant_b_temperature?: number;
    traffic_split?: number;
    metric_name?: string;
  }): Promise<{ ab_test_id: string; variant_a_version: number; status: string }> {
    return apiClient.post(`/admin/prompt-templates/${templateId}/ab-tests`, data);
  },

  async completeAbTest(testId: string, winner: 'A' | 'B'): Promise<{ ab_test_id: string; status: string; winner: string }> {
    return apiClient.patch(`/admin/prompt-templates/ab-tests/${testId}`, { action: 'complete', winner });
  },

  async cancelAbTest(testId: string): Promise<{ ab_test_id: string; status: string }> {
    return apiClient.patch(`/admin/prompt-templates/ab-tests/${testId}`, { action: 'cancel' });
  },

  async listAbTests(): Promise<{ ab_tests: PromptAbTest[]; total: number }> {
    return apiClient.get('/admin/prompt-templates/ab-tests');
  },
};

// ===========================
// Exam Import Service (Phase 3)
// ===========================

/**
 * 考古題匯入服務（Phase 3）：非同步任務送出、進度追蹤、儀表板統計與失敗分析。
 */
export const importService = {
  // --- Task Submission ---

  async submitAsync(data: {
    questionPdf: File;
    answerPdf: File;
    examCode: string;
    categoryCode: string;
    subjectCode: string;
    examName?: string;
    skipExisting?: boolean;
  }): Promise<{ task_id: string; status: string; message: string }> {
    const formData = new FormData();
    formData.append('question_pdf', data.questionPdf, data.questionPdf.name);
    formData.append('answer_pdf', data.answerPdf, data.answerPdf.name);
    formData.append('exam_code', data.examCode);
    formData.append('category_code', data.categoryCode);
    formData.append('subject_code', data.subjectCode);
    if (data.examName) {
      formData.append('exam_name', data.examName);
    }
    if (data.skipExisting !== undefined) {
      formData.append('skip_existing', String(data.skipExisting));
    }
    return apiClient.upload<{ task_id: string; status: string; message: string }>(
      '/exam-import/async',
      formData
    );
  },

  // --- Task Tracking ---

  async getTaskStatus(taskId: string): Promise<ImportTask | null> {
    try {
      const response = await apiClient.get<Record<string, unknown>>(
        `/exam-import/tasks/${taskId}`
      );
      return normalizeImportTask(response);
    } catch {
      return null;
    }
  },

  async listTasks(filters?: { status?: string; limit?: number }): Promise<ImportTask[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.limit) params.append('limit', String(filters.limit));

      const response = await apiClient.get<{ tasks: Array<Record<string, unknown>> }>(
        `/exam-import/tasks${params.size > 0 ? '?' + params.toString() : ''}`
      );
      return (response.tasks || []).map(normalizeImportTask);
    } catch {
      return [];
    }
  },

  async cancelTask(taskId: string): Promise<{ status: string; message: string }> {
    return apiClient.post(`/exam-import/tasks/${taskId}/cancel`, {});
  },

  // --- Monitoring Dashboard ---

  async getDashboardStats(): Promise<ImportDashboardStats | null> {
    try {
      return await apiClient.get<ImportDashboardStats>('/exam-import/dashboard/stats');
    } catch {
      return null;
    }
  },

  async getRecentJobs(limit: number = 20): Promise<RecentJob[]> {
    try {
      const response = await apiClient.get<{ recent_jobs: Array<Record<string, unknown>> }>(
        `/exam-import/dashboard/recent-jobs?limit=${limit}`
      );
      return (response.recent_jobs || []).map((job) => ({
        taskId: (job.task_id as string) || '',
        exam: (job.exam as string) || '',
        status: (job.status as ImportTaskStatus) || 'pending',
        progressPercent: ((job.progress_percent as number) || 0),
        questionsImported: ((job.questions_imported as number) || 0),
        totalQuestions: ((job.total_questions as number) || 0),
        createdAt: (job.created_at as string) || new Date().toISOString(),
        completedAt: (job.completed_at as string | null) || null,
        error: (job.error as string | null) || null,
      }));
    } catch {
      return [];
    }
  },

  async getFailedJobs(limit: number = 20): Promise<FailedJob[]> {
    try {
      const response = await apiClient.get<{ failed_jobs: Array<Record<string, unknown>> }>(
        `/exam-import/dashboard/failed-jobs?limit=${limit}`
      );
      return (response.failed_jobs || []).map((job) => ({
        taskId: (job.task_id as string) || '',
        exam: (job.exam as string) || '',
        errorMessage: (job.error_message as string | null) || null,
        retryCount: ((job.retry_count as number) || 0),
        failedAt: (job.failed_at as string) || new Date().toISOString(),
        canRetry: ((job.can_retry as boolean) || false),
      }));
    } catch {
      return [];
    }
  },

  async getStatusBreakdown(): Promise<StatusBreakdown | null> {
    try {
      return await apiClient.get<StatusBreakdown>('/exam-import/dashboard/status-breakdown');
    } catch {
      return null;
    }
  },

  async getPerformanceMetrics(days: number = 7): Promise<ImportPerformanceMetrics | null> {
    try {
      return await apiClient.get<ImportPerformanceMetrics>(
        `/exam-import/dashboard/performance-metrics?days=${days}`
      );
    } catch {
      return null;
    }
  },

  async getJobDetails(taskId: string): Promise<JobDetails | null> {
    try {
      return await apiClient.get<JobDetails>(`/exam-import/dashboard/job-details/${taskId}`);
    } catch {
      return null;
    }
  },
};

// --- Normalization Helper ---

function normalizeImportTask(data: Record<string, unknown>): ImportTask {
  return {
    id: (data.id as string) || '',
    taskId: (data.task_id as string) || '',
    userId: (data.user_id as string) || '',
    examCode: (data.exam_code as string) || '',
    categoryCode: (data.category_code as string) || '',
    subjectCode: (data.subject_code as string) || '',
    status: (data.status as any) || 'pending',
    progressPercent: ((data.progress_percent as number) || 0),
    questionsProcessed: ((data.questions_processed as number) || 0),
    questionsValid: ((data.questions_valid as number) || 0),
    questionsInvalid: ((data.questions_invalid as number) || 0),
    questionsImported: ((data.questions_imported as number) || 0),
    totalQuestions: ((data.total_questions as number) || 0),
    startedAt: (data.started_at as string | null) || null,
    completedAt: (data.completed_at as string | null) || null,
    createdAt: (data.created_at as string) || new Date().toISOString(),
    updatedAt: (data.updated_at as string) || new Date().toISOString(),
    errorMessage: (data.error_message as string | null) || null,
    validationErrors: (data.validation_errors as string[] | null) || null,
    importErrors: (data.import_errors as string[] | null) || null,
    requiresManualReview: ((data.requires_manual_review as boolean) || false),
    qualityGatesPassed: ((data.quality_gates_passed as boolean) || false),
    retryCount: ((data.retry_count as number) || 0),
  };
}
// ─── Resource Library Service ───────────────────────────────────────────────

/**
 * 學習庫中的單一資源（個人 / 機構 / 平台預設 / 分享）。
 */
export interface LibraryResource {
  resource_id: string;
  name: string;
  type: string;
  status: string;
  scope?: 'personal' | 'institution' | 'platform' | 'shared';
  badge?: 'personal' | 'institution' | 'official_default' | 'edu_shared';
  subject_id?: string | null;
  /** Spec 11 §鷹架生成子任務狀態 */
  scaffold_status?: 'ready' | 'pending' | 'failed' | 'none';
  /** Spec 11 §「系統應偵測檔案遺失並引導用戶重新上傳」 */
  needs_reupload?: boolean;
}

/**
 * 學習庫服務：列出 / 刪除 / 重新解析個人與分享資源。
 */
export const resourceLibraryService = {
  async list(opts?: { keyword?: string; subjectId?: string }): Promise<{ resources: LibraryResource[] }> {
    const params = new URLSearchParams();
    if (opts?.keyword) params.set('keyword', opts.keyword);
    if (opts?.subjectId) params.set('subject_id', opts.subjectId);
    const qs = params.toString();
    return apiClient.get(`/resource-library${qs ? `?${qs}` : ''}`);
  },
  async delete(resourceId: string): Promise<{ message: string }> {
    return apiClient.delete(`/resource-library/${resourceId}`);
  },
  async reparse(resourceId: string): Promise<{ message: string }> {
    return apiClient.post(`/resource-library/${resourceId}/reparse`, {});
  },
};

// ─── Retirement & Result Notification Service (super_admin) ────────────────

/**
 * 退役 / 結果通知服務（super_admin 排程觸發）。
 *
 * 涵蓋學習旅程的掃描、硬刪除、放榜通知與跨科推薦等批次任務。
 */
export const retirementService = {
  async scan() { return apiClient.post('/admin/retirement/scan', {}); },
  async hardDelete() { return apiClient.post('/admin/retirement/hard-delete', {}); },
  async postResultScan() { return apiClient.post('/admin/retirement/post-result', {}); },
  async recalculate() { return apiClient.post('/admin/subjects/recalculate', {}); },
  async notifyResultDay() { return apiClient.post('/admin/notifications/result-day', {}); },
  async notifyResultReminder() { return apiClient.post('/admin/notifications/result-reminder', {}); },
  async notifyResultDefault() { return apiClient.post('/admin/notifications/result-default', {}); },
  async crossRecommend() { return apiClient.post('/admin/notifications/cross-recommend', {}); },
};

// ─── Practice Service ───────────────────────────────────────────────────────

/**
 * 練習模式的單一題目（與正式考試題目欄位略異）。
 */
export interface PracticeQuestion {
  id: string;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  figure_urls?: string[];
  figure_description?: string | null;
  difficulty: string;
  type: string;
  // EPIC-035
  needs_answer?: boolean;
  answer_source?: string | null;
  confidence?: number | null;
  never_for_scoring?: boolean;
}

/**
 * 取得知識節點下練習題列表的回應結構。
 */
export interface PracticeQuestionsResponse {
  /** 節點 UUID */
  node_id: string;
  /** 題目陣列 */
  questions: PracticeQuestion[];
  /** 題目總數 */
  total: number;
}

/**
 * 提交練習作答後的即時回饋（含進度更新與向上傳播）。
 */
export interface PracticeSubmitResponse {
  ok: boolean;
  is_correct: boolean;
  correct_answer: string;
  selected_answer: string;
  explanation: string;
  question_id: string;
  mode: string;
  state_updated: boolean;
  progress: {
    node_id: string;
    new_progress: number;
    old_progress: number;
    status: string;
  } | null;
  propagation: Array<{
    node_id: string;
    new_progress: number;
    child_count: number;
  }>;
  // EPIC-035
  answer_source?: string | null;
  confidence?: number | null;
  never_for_scoring?: boolean;
}

/**
 * 練習服務：依知識節點取題並提交作答以更新進度。
 */
export const practiceService = {
  /** 查詢知識節點下的練習題列表 */
  async getNodeQuestions(nodeId: string): Promise<PracticeQuestionsResponse> {
    return apiClient.get(`/practice/nodes/${nodeId}/questions`);
  },

  /** 提交練習作答（即時回饋 + 知識圖譜進度更新） */
  async submitAnswer(questionId: string, selectedAnswer: string): Promise<PracticeSubmitResponse> {
    return apiClient.post('/practice/submit', {
      question_id: questionId,
      selected_answer: selectedAnswer,
    });
  },
};

// ===========================
// Feature 33 — Cost Monitor Service
// ===========================

import type {
  CostSummaryResponse,
  ProviderDetailResponse,
  GcpServicesResponse,
  TrendsResponse,
  UpdateBudgetRequest,
  GlobalScaleRequest,
  OverrideDisableRequest,
  BudgetUpdateResponse,
} from '@/types/cost-monitor';

/**
 * 成本監控服務（Feature 33）：AI provider 費用、GCP 服務費用、預算控制。
 */
export const costMonitorService = {
  async getSummary(): Promise<CostSummaryResponse> {
    return apiClient.get('/admin/cost/summary');
  },

  async getProviderDetail(provider: 'anthropic' | 'gemini' | 'voyage'): Promise<ProviderDetailResponse> {
    return apiClient.get(`/admin/cost/providers/${provider}`);
  },

  async getGcpServices(): Promise<GcpServicesResponse> {
    return apiClient.get('/admin/cost/gcp/services');
  },

  async getTrends(days = 30): Promise<TrendsResponse> {
    return apiClient.get(`/admin/cost/trends?days=${days}`);
  },

  async updateBudget(req: UpdateBudgetRequest): Promise<BudgetUpdateResponse> {
    return apiClient.put('/admin/cost/budget', req);
  },

  async globalScale(req: GlobalScaleRequest): Promise<BudgetUpdateResponse> {
    return apiClient.post('/admin/cost/budget/global-scale', req);
  },

  async overrideDisable(req: OverrideDisableRequest): Promise<BudgetUpdateResponse> {
    return apiClient.post('/admin/cost/budget/override-disable', req);
  },
};

// ===========================
// PRD-034 — Platform Subject Fork / Admin
// ===========================

/**
 * 平台科目版本資訊（PRD-034）。
 */
export interface PlatformSubjectVersionInfo {
  /** 平台科目 UUID */
  subject_id: string;
  /** 目前已發布版本號 */
  current_version: number;
  /** 最近一次發布時間（ISO） */
  published_at: string | null;
}

/**
 * 平台科目管理服務（PRD-034）：草稿更新、發布、回溯、版本查詢。
 */
export const platformSubjectAdminService = {
  async updateDraft(
    subjectId: string,
    resourceIds: string[],
  ): Promise<{ subject_id: string; resource_ids: string[] }> {
    return apiClient.put(`/admin/platform-subjects/${subjectId}/draft`, {
      resource_ids: resourceIds,
    });
  },

  async publish(
    subjectId: string,
  ): Promise<{ subject_id: string; version: number; published_at: string }> {
    return apiClient.post(`/admin/platform-subjects/${subjectId}/publish`, {});
  },

  async rollback(
    subjectId: string,
  ): Promise<{ subject_id: string; version: number; published_at: string | null }> {
    return apiClient.post(`/admin/platform-subjects/${subjectId}/rollback`, {});
  },

  async listVersions(subjectId: string): Promise<PlatformSubjectVersionInfo> {
    return apiClient.get(`/admin/platform-subjects/${subjectId}/versions`);
  },
};

/**
 * 科目 fork 服務：從平台科目分叉一份至使用者個人空間。
 */
export const subjectForkService = {
  async forkFromPlatform(platformSubjectId: string): Promise<{
    user_subject_id: string;
    subject_id: string;
    resources_copied: number;
    nodes_copied: number;
  }> {
    return apiClient.post(`/subjects/${platformSubjectId}/fork-from-platform`, {});
  },
};

// ===========================
// EPIC-035 Resource LLM Parse + Personal Bank + Scaffolds
// ===========================

import type {
  ParseJobResponse,
  ParseStatusResponse,
  ParsedResourceResponse,
  CandidateListResponse,
  ApproveCandidatesRequest,
  BlindAnswerResponse,
  InferenceJudgment,
} from '@/types/api';

/**
 * 資源 LLM 解析服務（EPIC-035）：觸發解析、查狀態、取得解析結果。
 */
export const resourceParseService = {
  async triggerParse(resourceId: string): Promise<ParseJobResponse> {
    return apiClient.post(`/resources/${resourceId}/parse`, {});
  },
  async getStatus(resourceId: string): Promise<ParseStatusResponse> {
    return apiClient.get(`/resources/${resourceId}/parse-status`);
  },
  async getParsed(resourceId: string): Promise<ParsedResourceResponse> {
    return apiClient.get(`/resources/${resourceId}/parsed`);
  },
};

/**
 * 題目候選服務（EPIC-035）：列出 LLM 抽取的候選題並批次核准 / 駁回。
 */
export const questionCandidateService = {
  async list(resourceId: string): Promise<CandidateListResponse> {
    return apiClient.get(`/resources/${resourceId}/question-candidates`);
  },
  async decide(
    resourceId: string,
    req: ApproveCandidatesRequest,
  ): Promise<{ approved: number; rejected: number }> {
    return apiClient.post(
      `/resources/${resourceId}/question-candidates/approve`,
      req,
    );
  },
};

/**
 * 學習鷹架回應服務：使用者對 takeaway / elaborative / strategy 鷹架的作答。
 */
export const scaffoldService = {
  async submitResponse(scaffoldId: string, content: string): Promise<{ status: string }> {
    return apiClient.post(`/resource-scaffolds/${scaffoldId}/response`, { content });
  },
};

/**
 * 盲答推理服務（EPIC-035）：未顯示選項前先讓使用者盲答，再判斷推理品質與寫筆記。
 */
export const blindInferenceService = {
  async submitBlindAnswer(
    questionId: string,
    answer: string,
  ): Promise<BlindAnswerResponse> {
    return apiClient.post(`/questions/${questionId}/blind-answer`, { answer });
  },
  async submitJudgment(
    questionId: string,
    judgment: InferenceJudgment,
  ): Promise<{ status: string; judgment: string }> {
    return apiClient.post(`/questions/${questionId}/inference-judgment`, { judgment });
  },
  async setConceptNote(questionId: string, note: string): Promise<{ status: string }> {
    return apiClient.post(`/questions/${questionId}/concept-note`, { note });
  },
};
