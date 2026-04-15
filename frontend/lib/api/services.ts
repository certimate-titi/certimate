/**
 * API Service Layer
 *
 * All service functions call the real backend API via apiClient.
 * The function signatures are the API contract.
 */

import { apiClient } from './client';

import type { DocumentSourceType, DocumentStatus } from '@/types/models';
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

export const authService = {
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

export const announcementService = {
  async getActive(): Promise<{ announcements: { id: string; title: string; content: string; type: string; display_mode: string }[] }> {
    return apiClient.get('/announcements');
  },
};

// ===========================

export const dashboardService = {
  async get(subjectId?: string): Promise<GetDashboardResponse> {
    const params = subjectId ? `?subject_id=${subjectId}` : '';
    return apiClient.get<GetDashboardResponse>(`/dashboard${params}`);
  },

  async completeDailyQuest(req: CompleteDailyQuestRequest): Promise<void> {
    await apiClient.post(`/dashboard/quests/${req.questId}/complete`);
  },
};

// ===========================
// Knowledge Service
// ===========================

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
};

// ===========================
// B2B Admin Service
// ===========================

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
};

// ===========================
// Super Admin Service
// ===========================

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
    return apiClient.get('/admin/finance/overview');
  },

  async getFinanceTransactions(): Promise<{ transactions: { id: string; user: string; amount: string; plan: string; status: string; time: string }[] }> {
    return apiClient.get('/admin/finance/transactions');
  },

  async getMrrTrend(): Promise<{ data: { name: string; new: number; expansion: number; churn: number }[] }> {
    return apiClient.get('/admin/finance/mrr-trend');
  },

  async getSubscriptionDistribution(): Promise<{ distribution: { name: string; value: number; color: string }[] }> {
    return apiClient.get('/admin/finance/subscription-distribution');
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
};

// ── Prompt Template Service ────────────────────────────────────────────────

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

export interface PromptTemplateDetail extends PromptTemplateSummary {
  system_prompt: string;
  user_prompt: string;
  variables: Array<{ name: string; description: string; example: string }>;
  max_tokens: number;
  max_tokens_by_plan?: Record<string, number>;
  feature_refs?: string[];
  created_at?: string;
}

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

// ─── Practice Service ───────────────────────────────────────────────────────

export interface PracticeQuestion {
  id: string;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  difficulty: string;
  type: string;
}

export interface PracticeQuestionsResponse {
  node_id: string;
  questions: PracticeQuestion[];
  total: number;
}

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
}

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
