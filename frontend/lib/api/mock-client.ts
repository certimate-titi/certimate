/**
 * Mock API Client — 離線開發模式
 *
 * 啟用方式：在 .env.local 設定 NEXT_PUBLIC_API_MODE=mock
 *
 * 行為：
 * - GET  → 回傳空物件/陣列（依路徑推斷）
 * - POST → 回傳 { ok: true, id: "mock-uuid" }
 * - PUT/PATCH → 回傳 { ok: true }
 * - DELETE → 回傳 { ok: true }
 *
 * 可在 MOCK_OVERRIDES 中為特定路徑定義自訂回傳值。
 */

function uuidv4(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// ── 特定路徑的自訂 mock 回傳值 ────────────────────────────────────

const MOCK_USER = {
  id: 'mock-user-001',
  email: 'dev@certimate.local',
  display_name: 'Dev User',
  role: 'ADMIN',
  subscription_plan: 'ULTRA',
  subscription_status: 'ACTIVE',
  onboarding_completed: true,
  created_at: new Date().toISOString(),
};

const MOCK_OVERRIDES: Record<string, (path: string, body?: unknown) => unknown> = {
  // Auth
  'POST /auth/login': () => ({ token: 'mock-jwt-token', user: MOCK_USER }),
  'POST /auth/signup': () => ({ token: 'mock-jwt-token', user: MOCK_USER }),
  'GET /auth/me': () => MOCK_USER,
  'POST /auth/google-sso': () => ({ token: 'mock-jwt-token', user: MOCK_USER }),

  // Dashboard
  'GET /dashboard': () => ({
    streak_count: 5,
    daily_quests: [
      { id: '1', title: '完成 3 道練習題', progress: 2, target: 3, completed: false },
      { id: '2', title: '複習昨日錯題', progress: 1, target: 1, completed: true },
    ],
    recent_exams: [],
    achievements: [],
    weak_nodes: [],
  }),

  // Subjects
  'GET /subjects/catalog': () => ({
    categories: [
      {
        id: 'cat-finance', name: '金融證照',
        subjects: [
          { id: 'sub-001', name: '信託業務', question_count: 500 },
          { id: 'sub-002', name: '投資型商品', question_count: 380 },
        ],
      },
    ],
  }),
  'GET /subjects/user-subjects': () => ({
    subjects: [
      { id: 'sub-001', name: '信託��務', self_assessment: 'beginner' },
    ],
  }),

  // Knowledge Map
  'GET /knowledge-map/nodes': () => ({
    nodes: [
      { id: 'n1', name: '信託法規', mastery_rate: 0.3, color: 'red', children: [] },
      { id: 'n2', name: '信託業務', mastery_rate: 0.7, color: 'green', children: [] },
    ],
  }),

  // Announcements
  'GET /announcements/active': () => ({ announcements: [] }),

  // Prompt Templates (admin)
  'GET /prompt-templates': () => ({ templates: [], total: 0 }),
};

// ── Mock 路由匹配 ────────────────────────────────────────────────

function findOverride(method: string, path: string): ((path: string, body?: unknown) => unknown) | null {
  // 精確匹配
  const exactKey = `${method} ${path}`;
  if (MOCK_OVERRIDES[exactKey]) return MOCK_OVERRIDES[exactKey];

  // 前綴匹配（處理帶 ID 的路徑如 /users/123）
  for (const [key, handler] of Object.entries(MOCK_OVERRIDES)) {
    const [keyMethod, keyPath] = key.split(' ', 2);
    if (keyMethod === method && path.startsWith(keyPath)) {
      return handler;
    }
  }

  return null;
}

// ── 泛型回傳推斷 ──────────────────────────────────────────────────

function inferResponse(method: string, path: string): unknown {
  if (method === 'GET') {
    // 路徑含複數名詞 → 回傳陣列包裝
    const lastSegment = path.split('/').filter(Boolean).pop() || '';
    if (/s$/.test(lastSegment) && !/status$/.test(lastSegment)) {
      return { [lastSegment]: [], total: 0 };
    }
    return {};
  }
  if (method === 'POST') return { ok: true, id: uuidv4() };
  if (method === 'PUT' || method === 'PATCH') return { ok: true };
  if (method === 'DELETE') return { ok: true };
  return {};
}

// ── Mock delay（模擬網路延遲）────────────────────────────────────

const MOCK_DELAY_MS = 200;

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── 匯出 mock apiClient ─────────────────────────────────────────

export const mockApiClient = {
  async get<T>(path: string): Promise<T> {
    await delay(MOCK_DELAY_MS);
    const override = findOverride('GET', path);
    const result = override ? override(path) : inferResponse('GET', path);
    console.debug(`[MOCK] GET ${path}`, result);
    return result as T;
  },

  async post<T>(path: string, body?: unknown): Promise<T> {
    await delay(MOCK_DELAY_MS);
    const override = findOverride('POST', path);
    const result = override ? override(path, body) : inferResponse('POST', path);
    console.debug(`[MOCK] POST ${path}`, body, '→', result);
    return result as T;
  },

  async put<T>(path: string, body?: unknown): Promise<T> {
    await delay(MOCK_DELAY_MS);
    const override = findOverride('PUT', path);
    const result = override ? override(path, body) : inferResponse('PUT', path);
    console.debug(`[MOCK] PUT ${path}`, body, '→', result);
    return result as T;
  },

  async patch<T>(path: string, body?: unknown): Promise<T> {
    await delay(MOCK_DELAY_MS);
    const override = findOverride('PATCH', path);
    const result = override ? override(path, body) : inferResponse('PATCH', path);
    console.debug(`[MOCK] PATCH ${path}`, body, '→', result);
    return result as T;
  },

  async delete<T>(path: string): Promise<T> {
    await delay(MOCK_DELAY_MS);
    const override = findOverride('DELETE', path);
    const result = override ? override(path) : inferResponse('DELETE', path);
    console.debug(`[MOCK] DELETE ${path}`, '→', result);
    return result as T;
  },

  async upload<T>(path: string, _formData: FormData): Promise<T> {
    await delay(MOCK_DELAY_MS * 3);
    const result = { ok: true, id: uuidv4(), filename: 'mock-upload.pdf' };
    console.debug(`[MOCK] UPLOAD ${path}`, '→', result);
    return result as T;
  },
};
