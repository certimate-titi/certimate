/**
 * Playwright route-based API mock for E2E tests.
 * Intercepts all /api/v1/** requests and returns mock responses.
 *
 * Usage: call `installApiMock(page)` before each test.
 */
import type { Page, Route } from '@playwright/test';
import { findUser, findUserByToken, EXAMS, SUBJECT_CATALOG, type MockUser } from './data';

// ─── Helpers ────────────────────────────────────────────────────────────────

async function json(route: Route, body: unknown, status = 200): Promise<true> {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
  return true;
}

async function error(route: Route, status: number, detail: string): Promise<true> {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify({ detail }),
  });
  return true;
}

function extractBearer(route: Route): string | null {
  const auth = route.request().headers()['authorization'] ?? '';
  return auth.startsWith('Bearer ') ? auth.slice(7) : null;
}

function currentUser(route: Route): MockUser | undefined {
  const token = extractBearer(route);
  return token ? findUserByToken(token) : undefined;
}

function makeToken(user: MockUser): string {
  // Generate a fake JWT with 3 dot-separated base64url segments
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).replace(/=+$/, '');
  const payload = btoa(JSON.stringify({ sub: user.id, email: user.email })).replace(/=+$/, '');
  const signature = btoa(`mock-sig-${user.id}`).replace(/=+$/, '');
  return `${header}.${payload}.${signature}`;
}

/** Track feedback submissions for rate-limiting mock */
const recentFeedbackSubjects = new Set<string>();

function makeLoginResponse(user: MockUser) {
  const redirectTo = user.onboarding_completed ? '/dashboard' : '/onboarding';
  const navItems: { label: string; path: string }[] = [];
  if (user.subscription_plan === 'ULTRA') {
    navItems.push({ label: '教育管理', path: '/edu-console' });
  }
  if (user.role === 'ADMIN') {
    navItems.push({ label: '平台管理', path: '/super-admin/dashboard' });
  }
  return {
    access_token: makeToken(user),
    user: {
      email: user.email,
      subscription_plan: user.subscription_plan,
      subscription_tier: user.subscription_plan,
      role: user.role,
      status: user.status,
    },
    redirect_to: redirectTo,
    nav_items: navItems,
  };
}

function makeMeResponse(user: MockUser) {
  const navItems: { label: string; path: string }[] = [];
  if (user.subscription_plan === 'ULTRA') {
    navItems.push({ label: '教育管理', path: '/edu-console' });
  }
  if (user.role === 'ADMIN') {
    navItems.push({ label: '平台管理', path: '/super-admin/dashboard' });
  }
  return {
    id: user.id,
    email: user.email,
    display_name: user.display_name,
    avatar_url: '',
    subscription_plan: user.subscription_plan,
    subscription_tier: user.subscription_plan,
    role: user.role,
    status: user.status,
    onboarding_completed: user.onboarding_completed,
    age: null,
    education: null,
    occupation: null,
    daily_study_minutes: 30,
    learning_style: 'hybrid',
    nav_items: navItems,
  };
}

// ─── Route Handlers ─────────────────────────────────────────────────────────

/** Return true if the route was handled (fulfilled), false/undefined to skip to next handler */
type Handler = (route: Route, method: string, path: string) => Promise<boolean | void> | boolean | void;

const handlers: Handler[] = [
  // ── Auth ──────────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/auth/login') return;
    const body = route.request().postDataJSON();
    const { email, password } = body ?? {};

    // Email format validation
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return error(route, 400, '電子郵件格式無效');
    }

    const user = findUser(email);
    if (!user || (user.password !== '*' && user.password !== password)) {
      return error(route, 401, '帳號或密碼錯誤');
    }
    if (user.status === '待驗證') {
      return error(route, 403, '帳號尚未驗證，請查收啟用信件');
    }

    return json(route, makeLoginResponse(user));
  },

  async (route, method, path) => {
    if (method !== 'GET' || path !== '/auth/me') return;
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    return json(route, makeMeResponse(user));
  },

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/auth/register') return;
    const body = route.request().postDataJSON();
    const { email, password, agreed_to_terms } = body ?? {};

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return error(route, 400, '電子郵件格式無效');
    }
    if (!agreed_to_terms) {
      return error(route, 400, '請閱讀並同意服務條款與隱私權政策');
    }
    if (!password || password.length < 8 || !/[A-Z]/.test(password) || !/[0-9]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
      return error(route, 400, '密碼強度不足');
    }
    if (findUser(email)) {
      return error(route, 409, '此電子郵件已被註冊');
    }

    return json(route, {
      message: '註冊成功',
      user: { email, subscription_plan: 'FREE', status: '待驗證' },
    }, 201);
  },

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/auth/verify-email') return;
    const body = route.request().postDataJSON();
    if (!body?.token || body.token.includes('invalid')) {
      return error(route, 400, '驗證連結無效或已過期');
    }
    return json(route, { message: '驗證成功', status: '已啟用' });
  },

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/auth/resend-verification') return;
    return json(route, { message: '驗證信已寄出' });
  },

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/auth/forgot-password') return;
    return json(route, { message: '密碼重設信已寄出', expires_in: 3600 });
  },

  async (route, method, path) => {
    if (method !== 'DELETE' || path !== '/auth/delete-account') return;
    return json(route, { message: '帳號已刪除' });
  },

  // ── Exams ─────────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/exams/config') return;
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    const body = route.request().postDataJSON();
    const config = body?.config ?? body ?? {};
    const nodeIds: string[] = config.selectedNodeIds ?? config.selected_node_ids ?? [];
    const count: number = config.questionCount ?? config.question_count ?? 0;

    if (nodeIds.length === 0) {
      return error(route, 400, '請至少選擇一個知識範圍');
    }

    // Node-specific question counts matching Feature 04 Background
    const nodeQuestionCounts: Record<string, number> = { '1': 20, '2': 20, '3': 20, '4': 20, '5': 60, '6': 100, '7': 100 };
    const available = nodeIds.reduce((sum, id) => sum + (nodeQuestionCounts[id] ?? 50), 0);
    if (count > available) {
      return error(route, 400, `所選範圍最多可出 ${available} 題，請調整題數`);
    }

    // Plan limits
    const plan = user.subscription_plan;
    if (plan === 'FREE' && count > 10) {
      return error(route, 400, 'FREE 方案每次測驗最多 10 題，升級 PRO 最多可出 50 題');
    }
    if (plan === 'PRO' && count > 50) {
      return error(route, 400, 'PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上');
    }

    const examId = 100 + Math.floor(Math.random() * 900);
    return json(route, { exam_id: examId, status: 'PENDING' }, 201);
  },

  async (route, method, path) => {
    const match = path.match(/^\/exams\/(\d+)\/generate$/);
    if (method !== 'POST' || !match) return;
    return json(route, { status: 'READY', question_count: 20 });
  },

  async (route, method, path) => {
    const match = path.match(/^\/exams\/(\d+)\/resume$/);
    if (method !== 'GET' || !match) return;
    const examId = parseInt(match[1]);
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    const exam = EXAMS.find((e) => e.id === examId);
    if (!exam) return error(route, 404, '測驗不存在');
    if (exam.owner_email !== user.email) {
      return error(route, 403, '無存取此測驗的權限');
    }
    if (exam.status === 'SUBMITTED') {
      return error(route, 400, '測驗已提交，無法重新開始');
    }

    const questions = Array.from({ length: exam.question_count }, (_, i) => ({
      id: `q${examId * 100 + i + 1}`,
      type: 'single_choice',
      content: `題目 ${i + 1}`,
      options: [
        { label: 'A', text: `選項 A` },
        { label: 'B', text: `選項 B` },
        { label: 'C', text: `選項 C` },
        { label: 'D', text: `選項 D` },
      ],
    }));

    return json(route, {
      id: examId,
      status: exam.status === 'READY' ? 'IN_PROGRESS' : exam.status,
      time_limit_minutes: 60,
      questions,
      answers: {},
    });
  },

  async (route, method, path) => {
    const match = path.match(/^\/exams\/(\d+)\/answers$/);
    if (method !== 'POST' || !match) return;
    return json(route, { message: 'saved' });
  },

  async (route, method, path) => {
    const match = path.match(/^\/exams\/(\d+)\/submit$/);
    if (method !== 'POST' || !match) return;
    return json(route, { status: 'SUBMITTED' });
  },

  async (route, method, path) => {
    const match = path.match(/^\/exams\/(\d+)\/result$/);
    if (method !== 'GET' || !match) return;
    const examId = parseInt(match[1]);
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    const exam = EXAMS.find((e) => e.id === examId);
    if (!exam) return error(route, 404, '測驗不存在');
    if (exam.owner_email !== user.email) {
      return error(route, 403, '無存取此測驗結果的權限');
    }
    if (exam.status !== 'SUBMITTED') {
      return error(route, 400, '測驗尚未提交，無法查看結果');
    }

    return json(route, {
      exam_id: examId,
      score: 75,
      total_questions: exam.question_count,
      correct_count: 15,
      pass_threshold: 70,
      passed: true,
      time_spent_seconds: 1800,
      submitted_at: new Date().toISOString(),
      node_analysis: [
        { node_name: 'EC2 運算', correct_rate: 0.9, color: '綠色', question_count: 5 },
        { node_name: 'IAM 身分', correct_rate: 0.4, color: '紅色', question_count: 5 },
        { node_name: 'VPC 網路', correct_rate: 0.5, color: '紅色', question_count: 5 },
        { node_name: 'S3 儲存', correct_rate: 0.8, color: '綠色', question_count: 5 },
      ],
    });
  },

  // ── Resources ─────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'GET' || path !== '/resources') return;
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    return json(route, {
      resources: [
        { id: 1, subject_id: 'subj_pmp', resource_type: 'pdf', filename: 'PMP_Guide.pdf', status: 'COMPLETED', file_size_mb: 2.5, created_at: '2026-03-01' },
        { id: 2, subject_id: 'subj_aws', resource_type: 'youtube', filename: '', youtube_url: 'https://youtube.com/watch?v=abc', status: 'COMPLETED', file_size_mb: 0, created_at: '2026-03-02' },
        { id: 3, subject_id: 'subj_pmp', resource_type: 'pdf', filename: 'PMP_Practice.pdf', status: 'PROCESSING', file_size_mb: 1.2, created_at: '2026-03-03' },
      ],
    });
  },

  async (route, method, path) => {
    const match = path.match(/^\/resources\/(\d+)$/);
    if (!match) return;
    const resourceId = parseInt(match[1]);
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');

    // Resource ownership check: resources 1-3 belong to alice
    const ownerMap: Record<number, string> = { 1: 'alice@example.com', 2: 'alice@example.com', 3: 'alice@example.com', 4: 'bob@example.com' };
    if (ownerMap[resourceId] && ownerMap[resourceId] !== user.email) {
      return error(route, 403, '無存取此資源的權限');
    }

    if (method === 'DELETE') {
      return json(route, { message: '已刪除' });
    }
    if (method === 'GET') {
      return json(route, { id: resourceId, subject_id: 'subj_pmp', resource_type: 'pdf', filename: 'doc.pdf', status: 'COMPLETED' });
    }
  },

  // ── Onboarding ────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'GET' || path !== '/onboarding/subjects') return;
    // Frontend expects { subjects: SubjectCatalogItem[] } with flat array
    return json(route, {
      subjects: [
        { id: '1', name: '信託業業務人員', category: '金融', description: '信託業務相關證照', isPopular: true },
        { id: '2', name: '投信投顧業務人員', category: '金融', description: '投信投顧業務證照', isPopular: false },
        { id: '3', name: '期貨分析師', category: '金融', description: '期貨市場分析證照', isPopular: true },
        { id: '4', name: 'CFA Level 1', category: '金融', description: 'CFA 特許金融分析師一級', isPopular: true },
        { id: '10', name: 'AWS SAA', category: 'IT', description: 'AWS Solutions Architect Associate', isPopular: true },
        { id: '11', name: 'Azure AZ-900', category: 'IT', description: 'Microsoft Azure Fundamentals', isPopular: false },
        { id: '12', name: 'CCNA', category: 'IT', description: 'Cisco Certified Network Associate', isPopular: false },
        { id: '5', name: 'PMP', category: 'IT', description: 'Project Management Professional', isPopular: true },
        { id: '6', name: 'AI 應用規劃師', category: 'IT', description: 'iPAS AI 應用規劃師', isPopular: false },
        { id: '7', name: '不動產經紀人', category: '其他', description: '不動產經紀業務證照', isPopular: false },
        { id: '8', name: '證券商業務員', category: '金融', description: '證券商業務人員證照', isPopular: true },
        { id: '9', name: '期貨商業務員', category: '金融', description: '期貨商業務人員證照', isPopular: false },
      ],
    });
  },

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/onboarding/complete') return;
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    const body = route.request().postDataJSON();
    const subjects = body?.subjects || [];
    if (subjects.length === 0) return error(route, 400, '請至少選擇一個備考科目');
    return json(route, { message: '引導完成', redirect_to: '/dashboard' });
  },

  async (route, method, path) => {
    if (method !== 'GET' || path !== '/onboarding/summary') return;
    const user = currentUser(route);
    return json(route, { subjects: [], user_id: user?.id ?? '0' });
  },

  // ── Dashboard ─────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'GET' || path !== '/dashboard') return;
    return json(route, {
      streak_days: 7,
      total_study_minutes: 1200,
      exams_completed: 15,
      daily_quests: [],
      achievements: [],
      growth_timeline: [],
      recent_exams: [],
      pomodoro_stats: { weekly_count: 12, weekly_minutes: 300 },
    });
  },

  // ── Knowledge Map ─────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (path.startsWith('/knowledge-map')) {
      if (method !== 'GET') return;
      return json(route, {
        nodes: [
          { id: 'n1', name: 'EC2 運算', color: 'green', mastery: 0.9 },
          { id: 'n2', name: 'IAM 身分', color: 'red', mastery: 0.3 },
          { id: 'n3', name: 'S3 儲存', color: 'yellow', mastery: 0.6 },
        ],
        edges: [],
      });
    }
  },

  // ── Feedback ──────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (path === '/feedback' && method === 'POST') {
      const user = currentUser(route);
      if (!user) return error(route, 401, '未授權，請先登入');
      const body = route.request().postDataJSON();
      if (!body?.subject || !body?.content || !body?.type) return error(route, 400, '必要欄位未填寫');
      if (body.subject && body.subject.length > 100) return error(route, 400, '主旨不得超過 100 個字元');
      if (body.content && body.content.length > 2000) return error(route, 400, '內容不得超過 2000 個字元');
      // Rate-limit: same user + same subject within short window
      const key = `${user.email}:${body.subject}`;
      if (recentFeedbackSubjects.has(key)) return error(route, 429, '您已於近期提交過相同主題的反饋，請稍後再試');
      recentFeedbackSubjects.add(key);
      return json(route, { id: 'fb_1', message: '已收到您的意見' }, 201);
    }
    if (path === '/feedback' && method === 'GET') {
      const user = currentUser(route);
      if (!user) return error(route, 401, '未授權');
      return json(route, { feedbacks: [] });
    }
  },

  async (route, method, path) => {
    if (path === '/admin/feedback' && method === 'GET') {
      const user = currentUser(route);
      if (!user) return error(route, 401, '未授權');
      if (user.role !== 'ADMIN') return error(route, 403, '權限不足');
      return json(route, { feedbacks: [] });
    }
  },

  // ── Settings: Pomodoro ─────────────────────────────────────────────────────

  async (route, method, path) => {
    if (path !== '/settings/pomodoro' || method !== 'PUT') return;
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    const body = route.request().postDataJSON();
    const focus = body?.focus_minutes;
    if (focus !== undefined && (focus < 15 || focus > 60)) {
      return error(route, 400, '專注時長需介於 15 至 60 分鐘');
    }
    return json(route, { message: '設定已儲存' });
  },

  // ── Admin: Question Import ────────────────────────────────────────────────

  async (route, method, path) => {
    if (path !== '/admin/questions/import' || method !== 'POST') return;
    const user = currentUser(route);
    if (!user) return error(route, 401, '未授權');
    if (user.role !== 'ADMIN') return error(route, 403, '權限不足');
    const body = route.request().postDataJSON();
    const questions = body?.questions || [];
    // Validate: check for missing correct_answer
    for (let i = 0; i < questions.length; i++) {
      if (!questions[i].correct_answer) {
        return error(route, 400, `第 ${i + 1} 題缺少必填欄位：correct_answer`);
      }
    }
    return json(route, { imported: questions.length }, 201);
  },

  // ── Wrong Answers / Review ────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'GET' || !path.startsWith('/wrong-answers')) return;
    return json(route, { wrong_answers: [] });
  },

  // ── Announcements ─────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'GET' || path !== '/announcements') return;
    return json(route, { announcements: [] });
  },

  // ── Admin endpoints ───────────────────────────────────────────────────────

  async (route, method, path) => {
    if (!path.startsWith('/admin/')) return;
    const user = currentUser(route);
    if (!user || user.role !== 'ADMIN') {
      return error(route, 403, '僅管理員可存取');
    }
    // Generic admin response
    return json(route, { data: [], total: 0 });
  },

  // ── Subjects ──────────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (method !== 'POST' || path !== '/subjects') return;
    return json(route, { id: 100, message: '已新增科目' }, 201);
  },

  // ── Subscriptions ─────────────────────────────────────────────────────────

  async (route, method, path) => {
    if (!path.startsWith('/subscriptions')) return;
    if (method === 'POST') return json(route, { message: 'OK' });
    if (method === 'GET') return json(route, { invoices: [] });
  },
];

// ─── Install ────────────────────────────────────────────────────────────────

export async function installApiMock(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();
    const path = url.pathname.replace(/^.*\/api\/v1/, '');

    for (const handler of handlers) {
      const handled = await handler(route, method, path);
      if (handled) return; // route was fulfilled
    }

    // No handler matched — return 404
    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({ detail: `Mock: No handler for ${method} ${path}` }),
    });
  });
}
