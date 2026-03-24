import type {
  User,
  UserUsageLog,
  Document,
  Exam,
  Question,
  UserAnswer,
  KnowledgeNode,
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
  AdminKPI,
  SystemAlert,
  PromoCode,
  FeatureFlag,
} from '@/types';
import type { GetNodeDetailResponse } from '@/types/api';

// ===========================
// Mock User & Usage
// ===========================

export const mockUser: User = {
  id: 'usr_001',
  email: 'simon@certimate.ai',
  displayName: 'Simon Chen',
  avatarUrl: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Simon',
  subscriptionTier: 'PRO_199',
  subscriptionStatus: 'ACTIVE',
  currentPeriodEnd: '2026-04-23T23:59:59Z',
  stripeCustomerId: 'cus_Pq7x12345678',
  onboardingCompleted: true,
  role: 'USER',
  createdAt: '2026-01-15T08:00:00Z',
};

export const mockUsage: UserUsageLog = {
  id: 'uul_001',
  userId: 'usr_001',
  billingCycleStart: '2026-03-23T00:00:00Z',
  claudeProQueriesCount: 45,
  visionOcrPagesCount: 12,
  youtubeMinutesParsed: 128,
  documentsUploadedCount: 8,
};

// ===========================
// Mock Documents (Expanded for Knowledge Base)
// ===========================

export const mockDocuments: Document[] = [
  {
    id: 'doc_001', userId: 'usr_001', subjectId: 'subj_pmp', sourceType: 'PDF',
    title: 'PMP 專案管理指南 第七版 (核心精華)',
    sourceUrl: 'gs://certimate/docs/pmp-guide-7th.pdf', mcpParsedTranscriptUrl: null,
    status: 'COMPLETED', fileSizeBytes: 15_200_000, visionRequired: false, createdAt: '2026-03-10T09:00:00Z',
  },
  {
    id: 'doc_002', userId: 'usr_001', subjectId: 'subj_pmp', sourceType: 'YOUTUBE_URL',
    title: '敏捷開發 Scrum 實戰工作坊',
    sourceUrl: 'https://www.youtube.com/watch?v=scrum-workshop', mcpParsedTranscriptUrl: 'gs://certimate/transcripts/scrum-workshop.txt',
    status: 'COMPLETED', fileSizeBytes: 0, visionRequired: false, createdAt: '2026-03-12T14:30:00Z',
  },
  {
    id: 'doc_003', userId: 'usr_001', subjectId: 'subj_aws_saa', sourceType: 'MARKDOWN',
    title: 'AWS SAA-C03 考前衝刺筆記',
    sourceUrl: 'gs://certimate/docs/aws-saa-notes.md', mcpParsedTranscriptUrl: null,
    status: 'COMPLETED', fileSizeBytes: 245_000, visionRequired: false, createdAt: '2026-03-15T11:00:00Z',
  },
  {
    id: 'doc_004', userId: 'usr_001', subjectId: 'subj_calculus', sourceType: 'IMAGE_MATH',
    title: '微積分二 - 泰勒級數手寫筆記',
    sourceUrl: 'gs://certimate/docs/calculus-taylor.png', mcpParsedTranscriptUrl: null,
    status: 'COMPLETED', fileSizeBytes: 3_400_000, visionRequired: true, createdAt: '2026-03-18T09:10:00Z',
  },
  {
    id: 'doc_005', userId: 'usr_001', subjectId: 'subj_pmp', sourceType: 'PDF',
    title: '利害關係人管理案例分析',
    sourceUrl: 'gs://certimate/docs/stakeholder-case.pdf', mcpParsedTranscriptUrl: null,
    status: 'PROCESSING', fileSizeBytes: 2_100_000, visionRequired: false, createdAt: '2026-03-23T10:00:00Z',
  },
  {
    id: 'doc_006', userId: 'usr_001', subjectId: 'subj_aws_saa', sourceType: 'PDF',
    title: 'AWS Well-Architected Framework',
    sourceUrl: 'gs://certimate/docs/aws-waf.pdf', mcpParsedTranscriptUrl: null,
    status: 'COMPLETED', fileSizeBytes: 12_500_000, visionRequired: false, createdAt: '2026-03-20T16:00:00Z',
  },
  {
    id: 'doc_007', userId: 'usr_001', subjectId: 'subj_toeic', sourceType: 'YOUTUBE_URL',
    title: '多益聽力高分技巧',
    sourceUrl: 'https://www.youtube.com/watch?v=toeic-listening', mcpParsedTranscriptUrl: 'gs://certimate/transcripts/toeic-listening.txt',
    status: 'FAILED', fileSizeBytes: 0, visionRequired: false, createdAt: '2026-03-22T08:00:00Z',
  },
];

// ===========================
// Mock Questions (50 Items)
// ===========================

const createMCQ = (id: string, text: string, options: string[], correct: string, explanation: string, tags: string[] = ['整合管理']): Question => ({
  id, examId: 'exam_001', questionType: 'MULTIPLE_CHOICE', contentText: text, contentImageUrl: null,
  options: options.map((t, i) => ({ label: String.fromCharCode(65 + i), text: t })),
  correctAnswer: correct, explanationMarkdown: explanation, citationChunkId: `chunk_${id}`, tags,
});

export const mockQuestions: Question[] = [
  // PMP - 整合管理
  createMCQ('q_01', '在專案管理中，哪個過程會產生「專案章程」？', ['發展專案管理計畫', '發展專案章程', '指導與管理專案工作', '監控專案工作'], 'B', '專案章程是「發展專案章程」過程的主要產出。', ['整合管理']),
  createMCQ('q_02', '變更請求獲得核准後，專案經理下一步應做什麼？', ['通知利害關係人', '更新專案管理計畫書', '執行變更', '計算成本增加'], 'B', '核准後應先更新計畫書（基準），再進行執行。', ['整合管理', '變更管理']),
  createMCQ('q_03', 'RACI 矩陣中，每個任務只能有一個人負責的是？', ['Responsible (負責者)', 'Accountable (當責者)', 'Consulted (諮詢者)', 'Informed (知會者)'], 'B', 'Accountable (A) 為最終負責人，只能有一位。', ['整合管理', '資源管理']),
  
  // PMP - 範圍管理
  createMCQ('q_04', 'WBS 的最底層分解為？', ['控制帳戶', '活動', '工作包 (Work Package)', '管理儲備'], 'C', 'WBS 底層是工作包，可進一步分解為活動。', ['範圍管理']),
  createMCQ('q_05', '「驗證範圍 (Validate Scope)」的主要目的是？', ['確保產品品質', '獲得客戶正式接受', '定義專案邊界', '控制範圍潛變'], 'B', '驗證範圍是讓客戶正式驗收已完成的交付物。', ['範圍管理']),

  // PMP - 時程管理
  createMCQ('q_06', '什麼是「關鍵路徑 (Critical Path)」？', ['最容易發生風險的路徑', '最耗費資源的路徑', '總時程最長的路徑', '緩衝時間最長的路徑'], 'C', '關鍵路徑決定了專案的最短完成時間，長度最長。', ['時程管理']),
  createMCQ('q_07', '「快速跟進 (Fast Tracking)」會導致什麼風險？', ['成本大幅增加', '資源閒置', '增加重工的風險', '時程變長'], 'C', '快速跟進是將順序任務並行，可能導致需要重做。', ['時程管理']),

  // PMP - 風險管理
  createMCQ('q_08', '對外包合約而言，「固定總價合約」將風險轉嫁給誰？', ['買方', '賣方', '政府', '保險公司'], 'B', '固定總價由賣方承擔超支風險。', ['風險管理', '採購管理']),
  createMCQ('q_09', '排除已知風險後，針對「未知風險」應使用？', ['應變儲備 (Contingency Reserve)', '管理儲備 (Management Reserve)', '活動成本估算', '風險登記冊'], 'B', '管理儲備用於未預見的風險。', ['風險管理']),

  // PMP - 敏捷開發
  createMCQ('q_10', 'Scrum 中，誰負責維護 Product Backlog 的優先順序？', ['Scrum Master', 'Product Owner', 'Developers', 'Stakeholders'], 'B', 'PO 負責產品價值最大化與 Backlog 管理。', ['敏捷', '範圍管理']),
  
  // 數學題型 - MATH_FORMULA
  {
    id: 'q_11', examId: 'exam_001', questionType: 'MATH_FORMULA',
    contentText: '請計算泰勒級數 $f(x) = e^x$ 在 $x=0$ 處展開的前三項。',
    contentImageUrl: null,
    options: [
      { label: 'A', text: '$1 + x + \\frac{x^2}{2}$' },
      { label: 'B', text: '$x + x^2 + x^3$' },
      { label: 'C', text: '$1 - x + \\frac{x^2}{2}$' },
      { label: 'D', text: '$1 + 2x + 3x^2$' },
    ],
    correctAnswer: 'A', explanationMarkdown: '$e^x = \\sum_{n=0}^{\\infty} \\frac{x^n}{n!} = 1 + x + \\frac{x^2}{2} + \\dots$', citationChunkId: 'chunk_math_01', tags: ['微積分'],
  },

  // 帶圖題目 - contentImageUrl
  {
    id: 'q_12', examId: 'exam_001', questionType: 'MULTIPLE_CHOICE',
    contentText: '根據下圖所示的網路邏輯圖，該專案的關鍵路徑時長為多長？',
    contentImageUrl: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?q=80&w=1000&auto=format&fit=crop',
    options: [
      { label: 'A', text: '12 天' },
      { label: 'B', text: '15 天' },
      { label: 'C', text: '18 天' },
      { label: 'D', text: '20 天' },
    ],
    correctAnswer: 'C', explanationMarkdown: '路徑 A-C-E 總長度為 18 天，為最長路徑。', citationChunkId: 'chunk_path_01', tags: ['時程管理'],
  },

  // 填空題型 - FILL_IN_BLANK
  {
    id: 'q_13', examId: 'exam_001', questionType: 'FILL_IN_BLANK',
    contentText: '在庫存管理中，EOQ 代表 _______ 訂購量。',
    contentImageUrl: null,
    options: [],
    correctAnswer: '經濟', explanationMarkdown: 'EOQ (Economic Order Quantity) 即經濟訂購量。', citationChunkId: 'chunk_eoq', tags: ['資源管理'],
  },
  
  ...Array.from({ length: 37 }).map((_, i) => {
    const idNum = i + 14;
    const subjects = ['整合管理', '範圍管理', '時程管理', '成本管理', '品質管理', '資源管理', '溝通管理', '風險管理', '採購管理', '利害關係人管理'];
    const tag = subjects[idNum % subjects.length];
    return createMCQ(
      `q_${idNum}`,
      `這是關於「${tag}」的模擬考題第 ${idNum} 題：在實際專案場景中，若遇到資源衝突，經理應首先查閱？`,
      ['資源管理計畫', '專案章程', '溝通矩陣', '風險登記冊'],
      'A',
      `對於${tag}中的資源分配問題，資源管理計畫書提供了指引。`,
      [tag]
    );
  })
];

// ===========================
// Mock Exam & Results
// ===========================

export const mockExams: Exam[] = [
  {
    id: 'exam_001', userId: 'usr_001', documentId: 'doc_001',
    title: 'PMP 2026 模擬考 (全真模擬)',
    examType: 'MOCK_EXAM', score: 78, totalQuestions: 50,
    timeLimit: 14400, // 4 hours
    createdAt: '2026-03-22T10:00:00Z',
  },
  {
    id: 'exam_aws_01', userId: 'usr_001', documentId: 'doc_aws_01',
    title: 'AWS SAA 核心架構測驗',
    examType: 'MOCK_EXAM', score: 65, totalQuestions: 30,
    timeLimit: 7200,
    createdAt: '2026-03-23T15:00:00Z',
  }
];

// 為了保持向後相容性，導出第一個作為 mockExam
export const mockExam = mockExams[0];

export const mockUserAnswers: UserAnswer[] = [
  // PMP 答案
  ...mockQuestions.filter(q => q.examId === 'exam_001').map((q, i) => {
    const isCorrect = Math.random() > 0.2;
    return {
      id: `ua_pmp_${String(i + 1).padStart(3, '0')}`,
      userId: 'usr_001', questionId: q.id, examId: 'exam_001',
      isCorrect,
      userChoice: isCorrect ? q.correctAnswer : (q.options.find(o => o.label !== q.correctAnswer)?.label || 'A'),
      ebbinghausNextReview: isCorrect ? null : '2026-03-24T09:00:00Z',
      ebbinghausMultiplier: isCorrect ? 2.5 : 1.0,
    };
  }),
  // AWS 答案 (模擬更多錯題以供測試)
  ...mockQuestions.filter(q => q.examId === 'exam_aws_01').map((q, i) => {
    const isCorrect = Math.random() > 0.6; // 較高錯誤率
    return {
      id: `ua_aws_${String(i + 1).padStart(3, '0')}`,
      userId: 'usr_001', questionId: q.id, examId: 'exam_aws_01',
      isCorrect,
      userChoice: isCorrect ? q.correctAnswer : (q.options.find(o => o.label !== q.correctAnswer)?.label || 'B'),
      ebbinghausNextReview: isCorrect ? null : '2026-03-25T10:00:00Z',
      ebbinghausMultiplier: isCorrect ? 2.0 : 1.0,
    };
  })
];

export const mockDomainAnalysis: DomainAnalysis[] = [
  { domain: '整合管理', correct: 12, total: 15, percentage: 80 },
  { domain: '範圍管理', correct: 8, total: 10, percentage: 80 },
  { domain: '時程管理', correct: 5, total: 8, percentage: 62 },
  { domain: '風險管理', correct: 4, total: 7, percentage: 57 },
  { domain: '其他', correct: 8, total: 10, percentage: 80 },
];

// ===========================
// Mock Knowledge Graph (Deepened for Soul)
// ===========================

export const mockKnowledgeNodes: KnowledgeNode[] = [
  {
    id: 'kn_pmp_root', documentId: 'doc_001', label: 'PMP 認證指南', parentId: null, depth: 0,
    citationChunkId: null, masteryLevel: 'partial',
    children: [
      {
        id: 'kn_pm_process', documentId: 'doc_001', label: '五大過程組', parentId: 'kn_pmp_root', depth: 1,
        citationChunkId: 'chunk_p01', masteryLevel: 'mastered',
        children: [
          {
            id: 'kn_pm_init', documentId: 'doc_001', label: '起始過程組', parentId: 'kn_pm_process', depth: 2, citationChunkId: 'chunk_p02', masteryLevel: 'mastered',
            children: [
              { id: 'kn_pm_init_01', documentId: 'doc_001', label: '發展專案章程', parentId: 'kn_pm_init', depth: 3, citationChunkId: 'chunk_p02_01', masteryLevel: 'mastered', children: [] },
              { id: 'kn_pm_init_02', documentId: 'doc_001', label: '辨識利害關係人', parentId: 'kn_pm_init', depth: 3, citationChunkId: 'chunk_p02_02', masteryLevel: 'mastered', children: [] },
            ],
          },
          {
            id: 'kn_pm_plan', documentId: 'doc_001', label: '規劃過程組', parentId: 'kn_pm_process', depth: 2, citationChunkId: 'chunk_p03', masteryLevel: 'partial',
            children: [
              { id: 'kn_pm_plan_01', documentId: 'doc_001', label: '發展專案管理計畫', parentId: 'kn_pm_plan', depth: 3, citationChunkId: 'chunk_p03_01', masteryLevel: 'partial', children: [] },
              { id: 'kn_pm_plan_scope', documentId: 'doc_001', label: '規劃範圍管理', parentId: 'kn_pm_plan', depth: 3, citationChunkId: 'chunk_p03_02', masteryLevel: 'mastered', children: [] },
            ],
          },
          { id: 'kn_pm_exec', documentId: 'doc_001', label: '執行過程組', parentId: 'kn_pm_process', depth: 2, citationChunkId: 'chunk_p04', masteryLevel: 'weak', children: [] },
        ],
      },
      {
        id: 'kn_pm_knowledge', documentId: 'doc_001', label: '十大知識領域', parentId: 'kn_pmp_root', depth: 1,
        citationChunkId: 'chunk_k01', masteryLevel: 'partial',
        children: [
          { id: 'kn_pm_int', documentId: 'doc_001', label: '整合管理', parentId: 'kn_pm_knowledge', depth: 2, citationChunkId: 'chunk_k02', masteryLevel: 'mastered', children: [] },
          { id: 'kn_pm_scope', documentId: 'doc_001', label: '範圍管理', parentId: 'kn_pm_knowledge', depth: 2, citationChunkId: 'chunk_k03', masteryLevel: 'mastered', children: [] },
          { id: 'kn_pm_risk', documentId: 'doc_001', label: '風險管理', parentId: 'kn_pm_knowledge', depth: 2, citationChunkId: 'chunk_k04', masteryLevel: 'weak', children: [] },
        ],
      },
    ],
  },
  {
    id: 'kn_aws_root', documentId: 'doc_003', label: 'AWS 雲端架構 (SAA)', parentId: null, depth: 0,
    citationChunkId: null, masteryLevel: 'partial',
    children: [
      {
        id: 'kn_aws_compute', documentId: 'doc_003', label: '運算服務 (Compute)', parentId: 'kn_aws_root', depth: 1,
        citationChunkId: 'chunk_aws_c01', masteryLevel: 'mastered',
        children: [
          { id: 'kn_aws_ec2', documentId: 'doc_003', label: 'EC2 執行個體', parentId: 'kn_aws_compute', depth: 2, citationChunkId: 'chunk_aws_c02', masteryLevel: 'mastered', children: [] },
          { id: 'kn_aws_lambda', documentId: 'doc_003', label: 'Lambda 無伺服器', parentId: 'kn_aws_compute', depth: 2, citationChunkId: 'chunk_aws_c03', masteryLevel: 'partial', children: [] },
        ],
      },
      {
        id: 'kn_aws_storage', documentId: 'doc_003', label: '儲存服務 (Storage)', parentId: 'kn_aws_root', depth: 1,
        citationChunkId: 'chunk_aws_s01', masteryLevel: 'partial',
        children: [
          { id: 'kn_aws_s3', documentId: 'doc_003', label: 'S3 儲存貯體', parentId: 'kn_aws_storage', depth: 2, citationChunkId: 'chunk_aws_s02', masteryLevel: 'mastered', children: [] },
          { id: 'kn_aws_ebs', documentId: 'doc_003', label: 'EBS 區塊儲存', parentId: 'kn_aws_storage', depth: 2, citationChunkId: 'chunk_aws_s03', masteryLevel: 'weak', children: [] },
        ],
      },
    ],
  },
];

// ===========================
// NEW: Mock Node Details (The Soul: Citations & Ground Truth)
// ===========================

export const mockNodeDetails: Record<string, GetNodeDetailResponse> = {
  'kn_pm_init_01': {
    node: mockKnowledgeNodes[0].children[0].children[0].children[0], // 發展專案章程
    citationText: `### 發展專案章程 (Develop Project Charter)
這是編寫一份正式批准專案並授權專案經理使用資源的過程。

**關鍵輸入：**
- 企業營運個案 (Business Case)
- 協議 (Agreements)
- 企業環境因素 (EEF)

**關鍵工具：**
- 專家判斷
- 資料蒐集 (腦力激盪、焦點小組)
- 會議

**主要產出：**
- **專案章程**：賦予專案法律地位的文件，包含高階層級的需求與里程碑。`,
    citationSource: {
      type: 'pdf',
      documentTitle: 'PMP 專案管理指南 第七版',
      page: 42,
      sourceUrl: 'gs://certimate/docs/pmp-guide-7th.pdf',
    },
  },
  'kn_pm_init_02': {
    node: mockKnowledgeNodes[0].children[0].children[0].children[1], // 辨識利害關係人
    citationText: `### 辨識利害關係人 (Identify Stakeholders)
辨識所有受專案影響的人員或組織，並記錄其參與度。

**關鍵工具：**
- **利害關係人分析**：評估利害關係人的權力與利益。
- **權力/利益矩陣 (Power/Interest Grid)**：將利害關係人分類以決定管理策略。`,
    citationSource: {
      type: 'pdf',
      documentTitle: 'PMP 專案管理指南 第七版',
      page: 85,
      sourceUrl: 'gs://certimate/docs/pmp-guide-7th.pdf',
    },
  },
  'kn_aws_lambda': {
    node: mockKnowledgeNodes[1].children[0].children[1], // Lambda
    citationText: `### AWS Lambda
AWS Lambda 是一項無伺服器、事件驅動的運算服務。

**核心特點：**
- **自動擴展**：根據請求流量自動增減執行個體。
- **按需付費**：僅在程式碼運行時計費。
- **支援語言**：Python, Node.js, Java, Go, Ruby 等。

**實際案例：**
- 回應 S3 的文件上傳事件，自動生成縮圖。
- 透過 API Gateway 觸發後端邏輯。`,
    citationSource: {
      type: 'pdf',
      documentTitle: 'AWS SAA-C03 考前衝刺筆記',
      page: 12,
      sourceUrl: 'gs://certimate/docs/aws-saa-notes.md',
    },
  },
};

// ===========================
// Mock Dashboard & Social
// ===========================

export const mockStreak: LearningStreak = {
  currentStreak: 15, longestStreak: 42, freezesRemaining: 2, freezesPerWeek: 1, lastActiveDate: '2026-03-23',
};

export const mockDailyQuests: DailyQuest[] = [
  { id: 'dq_01', description: '複習 10 題舊錯題', type: 'review', completed: true, xpReward: 50 },
  { id: 'dq_02', description: '探索「AWS IAM」知識節點', type: 'explore', completed: false, xpReward: 30 },
  { id: 'dq_03', description: '完成一份 20 題模擬考', type: 'quiz', completed: false, xpReward: 100 },
];

export const mockActivityItems: ActivityItem[] = [
  {
    id: 'act_01', type: 'error_review', title: '發現弱點領域', description: '你在「風險管理」的正確率低於 60%，建議進行專項訓練。',
    link: '/review', linkLabel: '立即強化',
  },
  {
    id: 'act_02', type: 'achievement', title: '獲得新成就：細節大師', description: '恭喜！你已連續 50 題未因計算錯誤丟分。',
    link: '/profile/achievements', linkLabel: '查看獎勵',
  },
];

export const mockReviewCalendar: ReviewCalendarDay[] = [
  { date: '2026-03-23', reviewCount: 15, topics: ['PMP 整合', 'AWS S3'] },
  { date: '2026-03-24', reviewCount: 8, topics: ['風險回應'] },
  { date: '2026-03-26', reviewCount: 22, topics: ['全科複習'] },
];

export const mockChatMessages: ChatMessage[] = [
  { id: 'msg_01', role: 'ai', content: '你好 Simon！我是你的 AI 助教。今天想針對 PMP 的哪個部分進行複習？', timestamp: '2026-03-23T09:00:00Z' },
  { id: 'msg_02', role: 'user', content: '我想了解「應變儲備」與「管理儲備」的差異。', timestamp: '2026-03-23T09:05:00Z' },
  {
    id: 'msg_03', role: 'ai', content: '好的。簡單來說：\n- **應變儲備**：處理「已知-未知」風險，包含在基準中。\n- **管理儲備**：處理「未知-未知」風險，不包含在基準中。',
    timestamp: '2026-03-23T09:05:10Z',
    citationSource: { type: 'pdf', label: 'PMBOK Guide 7th Edition, Page 168', page: 168 }
  },
  {
    id: 'msg_04', role: 'ai', content: '你覺得這兩者的核准權限有什麼不同？（這在考題中很常見哦！）',
    timestamp: '2026-03-23T09:06:00Z',
  },
];

// ===========================
// Mock Achievements & Milestones
// ===========================

export const mockAchievements: Achievement[] = [
  { id: 'ach_01', name: '首航', description: '完成第一次模擬考', iconEmoji: '🚀', unlockedAt: '2026-01-20T10:00:00Z' },
  { id: 'ach_02', name: '學富五車', description: '上傳超過 10 個文件', iconEmoji: '📚', unlockedAt: '2026-02-15T15:00:00Z' },
  { id: 'ach_03', name: '考神附體', description: '模擬考獲得 100 分', iconEmoji: '🎓', unlockedAt: null },
];

export const mockMilestones: GrowthMilestone[] = [
  { date: '2026-01-15', label: '加入 CertiMate', type: 'streak' },
  { date: '2026-02-01', label: '掌握「整合管理」領域', type: 'mastery' },
  { date: '2026-03-22', label: '完成 50 題全真考卷', type: 'exam' },
];

// ===========================
// Mock B2B / Admin / Catalog
// ===========================

export const mockStudents: Student[] = [
  {
    id: 'stu_01',
    name: '王小明',
    email: 'ming@corp.com',
    progress: 85,
    averageScore: 92,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-23T11:00:00Z',
    lastActiveLabel: '今天',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '風險管理', score: 88 },
      { label: '敏捷方法', score: 95 },
      { label: '時程估算', score: 72 },
    ],
  },
  {
    id: 'stu_02',
    name: '李大華',
    email: 'hua@corp.com',
    progress: 45,
    averageScore: 58,
    trend: 'down',
    status: 'needs_attention',
    lastActiveAt: '2026-03-20T15:00:00Z',
    lastActiveLabel: '3 天前',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '風險管理', score: 38 },
      { label: '敏捷方法', score: 61 },
      { label: '時程估算', score: 44 },
    ],
  },
  {
    id: 'stu_03',
    name: '張志誠',
    email: 'cheng@corp.com',
    progress: 98,
    averageScore: 96,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-23T09:30:00Z',
    lastActiveLabel: '今天',
    enrolledSubjectIds: ['subj_aws_saa'],
    competencies: [
      { label: '架構設計', score: 98 },
      { label: '網路安全', score: 92 },
      { label: '成本優化', score: 95 },
    ],
  },
  {
    id: 'stu_04',
    name: '陳美麗',
    email: 'mei@corp.com',
    progress: 12,
    averageScore: 35,
    trend: 'flat',
    status: 'inactive',
    lastActiveAt: '2026-03-10T08:00:00Z',
    lastActiveLabel: '2 週前',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '基礎概念', score: 40 },
      { label: '環境配置', score: 25 },
      { label: '範例實作', score: 10 },
    ],
  },
  {
    id: 'stu_05',
    name: '林書豪',
    email: 'jeremy@corp.com',
    progress: 60,
    averageScore: 75,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-22T22:00:00Z',
    lastActiveLabel: '昨天',
    enrolledSubjectIds: ['subj_pmp', 'subj_aws_saa'],
    competencies: [
      { label: '需求分析', score: 82 },
      { label: '利害關係人', score: 70 },
      { label: '品質管理', score: 65 },
    ],
  },
  {
    id: 'stu_06',
    name: '周杰倫',
    email: 'jay@corp.com',
    progress: 30,
    averageScore: 48,
    trend: 'down',
    status: 'needs_attention',
    lastActiveAt: '2026-03-18T14:00:00Z',
    lastActiveLabel: '5 天前',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '節奏控制', score: 30 },
      { label: '編碼邏輯', score: 55 },
      { label: '整合部署', score: 40 },
    ],
  },
  {
    id: 'stu_07',
    name: '蔡依林',
    email: 'jolin@corp.com',
    progress: 95,
    averageScore: 94,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-23T10:45:00Z',
    lastActiveLabel: '今天',
    enrolledSubjectIds: ['subj_aws_saa'],
    competencies: [
      { label: '全域視角', score: 96 },
      { label: '溝通管理', score: 98 },
      { label: '彈性開發', score: 90 },
    ],
  },
  {
    id: 'stu_08',
    name: '五月天',
    email: 'mayday@corp.com',
    progress: 72,
    averageScore: 81,
    trend: 'flat',
    status: 'active',
    lastActiveAt: '2026-03-21T16:20:00Z',
    lastActiveLabel: '2 天前',
    enrolledSubjectIds: ['subj_pmp', 'subj_aws_saa'],
    competencies: [
      { label: '團隊協作', score: 95 },
      { label: '持續整合', score: 78 },
      { label: '壓力測試', score: 62 },
    ],
  },
  {
    id: 'stu_09',
    name: '張惠妹',
    email: 'amei@corp.com',
    progress: 55,
    averageScore: 68,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-23T08:15:00Z',
    lastActiveLabel: '今天',
    enrolledSubjectIds: ['subj_aws_saa'],
    competencies: [
      { label: '異常處理', score: 85 },
      { label: '效能監控', score: 60 },
      { label: '日誌分析', score: 65 },
    ],
  },
  {
    id: 'stu_10',
    name: '吳青峰',
    email: 'greeny@corp.com',
    progress: 88,
    averageScore: 89,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-23T11:30:00Z',
    lastActiveLabel: '今天',
    enrolledSubjectIds: ['subj_pmp', 'subj_aws_saa'],
    competencies: [
      { label: '精確計算', score: 92 },
      { label: '邏輯推理', score: 88 },
      { label: '跨平台相容', score: 85 },
    ],
  },
  {
    id: 'stu_11',
    name: '蕭敬騰',
    email: 'jam@corp.com',
    progress: 25,
    averageScore: 42,
    trend: 'down',
    status: 'needs_attention',
    lastActiveAt: '2026-03-15T09:00:00Z',
    lastActiveLabel: '1 週前',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '穩定性', score: 35 },
      { label: '回復機制', score: 50 },
      { label: '組態管理', score: 30 },
    ],
  },
  {
    id: 'stu_12',
    name: '孫燕姿',
    email: 'stef@corp.com',
    progress: 78,
    averageScore: 85,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-22T13:40:00Z',
    lastActiveLabel: '昨天',
    enrolledSubjectIds: ['subj_aws_saa'],
    competencies: [
      { label: '並行處理', score: 88 },
      { label: '記憶體管理', score: 82 },
      { label: '緩存優化', score: 80 },
    ],
  },
  {
    id: 'stu_13',
    name: '田馥甄',
    email: 'hebe@corp.com',
    progress: 68,
    averageScore: 79,
    trend: 'flat',
    status: 'active',
    lastActiveAt: '2026-03-19T20:10:00Z',
    lastActiveLabel: '4 天前',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '模組化', score: 85 },
      { label: '抽象化設計', score: 75 },
      { label: '介面整合', score: 72 },
    ],
  },
  {
    id: 'stu_14',
    name: '林俊傑',
    email: 'jj@corp.com',
    progress: 92,
    averageScore: 90,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-23T11:55:00Z',
    lastActiveLabel: '今天',
    enrolledSubjectIds: ['subj_aws_saa'],
    competencies: [
      { label: '即時串流', score: 95 },
      { label: '大型架構', score: 88 },
      { label: '資料庫設計', score: 92 },
    ],
  },
  {
    id: 'stu_15',
    name: '梁靜茹',
    email: 'fish@corp.com',
    progress: 50,
    averageScore: 62,
    trend: 'up',
    status: 'active',
    lastActiveAt: '2026-03-22T15:30:00Z',
    lastActiveLabel: '昨天',
    enrolledSubjectIds: ['subj_pmp'],
    competencies: [
      { label: '穩定度', score: 65 },
      { label: '容錯性', score: 70 },
      { label: '自動化測試', score: 45 },
    ],
  },
];

export const mockSubjectCatalog: SubjectCatalogItem[] = [
  { id: 'subj_pmp', name: 'PMP', category: 'IT', description: '專案管理專業人士認證', isPopular: true },
  { id: 'subj_aws_saa', name: 'AWS SAA', category: 'IT', description: 'AWS 解決方案架構師 (助理級)', isPopular: true },
  { id: 'subj_calculus', name: '微積分 (二)', category: '其他', description: '大學微積分核心課程', isPopular: false },
  { id: 'subj_toeic', name: 'TOEIC', category: '語言', description: '多益英語測驗', isPopular: true },
  { id: 'subj_cfa_1', name: 'CFA Level I', category: '金融', description: '特許金融分析師一級過考', isPopular: false },
  { id: 'subj_nurse', name: '護理師執照', category: '醫療', description: '國考護理師備考資源', isPopular: false },
];

export const mockUserSubjects: UserSubject[] = [
  { id: 'us_001', subjectId: 'subj_pmp', subjectName: 'PMP', examDate: '2026-05-20', selfAssessment: 'intermediate', createdAt: '2026-01-15T08:00:00Z' },
  { id: 'us_002', subjectId: 'subj_aws_saa', subjectName: 'AWS SAA', examDate: '2026-06-15', selfAssessment: 'beginner', createdAt: '2026-03-01T08:00:00Z' },
];

// ===========================
// Management Mock Data
// ===========================

export const mockAdminKPIs: AdminKPI[] = [
  { label: 'MAU (月活躍用戶)', value: '1,245', change: '+12%', changeType: 'positive' },
  { label: 'MRR (月經常性收入)', value: '$12,450', change: '+5.4%', changeType: 'positive' },
  { label: '考卷完成總數', value: '45,892', change: '-2%', changeType: 'negative' },
];

export const mockSystemAlerts: SystemAlert[] = [
  { id: 'sa_01', severity: 'critical', message: 'Stripe Webhook 連線中斷，請立即檢查！', timestamp: '2026-03-23T22:00:00Z' },
  { id: 'sa_02', severity: 'warning', message: 'AWS Lambda 執行時間接近閾值 (85%)。', timestamp: '2026-03-23T21:30:00Z' },
];

export const mockPromoCodes: PromoCode[] = [
  {
    id: 'pc_01', code: 'SPRING2026', discountType: 'percentage', discountValue: 20,
    applicablePlans: ['PRO_199', 'PRO_PLUS_399'], maxUses: 100, currentUses: 45,
    validFrom: '2026-03-01T00:00:00Z', validUntil: '2026-04-30T23:59:59Z', isActive: true,
  },
];

export const mockFeatureFlags: FeatureFlag[] = [
  { id: 'ff_01', flagKey: 'next-gen-ocr', name: '次世代 OCR 解析', description: '啟用更強大的手寫公式辨識', isEnabled: true, rolloutPercentage: 10 },
  { id: 'ff_02', flagKey: 'social-study', name: '社群共讀模式', description: '允許用戶與好友即時比對考題', isEnabled: false, rolloutPercentage: 0 },
];

export const mockAdminSubjectStats: Record<string, {
  averageScore: number;
  scoreChange: number;
  topWeaknesses: { topic: string; errorRate: number }[];
}> = {
  subj_pmp: {
    averageScore: 78.5,
    scoreChange: 4.2,
    topWeaknesses: [
      { topic: '風險應對策略', errorRate: 65 },
      { topic: '實獲值管理 (EVM)', errorRate: 52 },
      { topic: '敏捷角色職責', errorRate: 40 },
    ],
  },
  subj_aws_saa: {
    averageScore: 72.0,
    scoreChange: -1.5,
    topWeaknesses: [
      { topic: 'VPC 網路架構', errorRate: 78 },
      { topic: 'IAM 權限最小化', errorRate: 45 },
      { topic: '多區域高可用設計', errorRate: 32 },
    ],
  },
};
