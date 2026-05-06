/**
 * 前端 HTTP API client 與 JWT token 儲存工具。
 *
 * - 自動為每個請求注入 `Authorization: Bearer <token>`
 * - 401 時清除 token 並導向 `/login?expired=1`
 * - 透過 `NEXT_PUBLIC_API_MODE=mock` 切換到離線 mock client
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

const TOKEN_KEY = 'certimate_jwt_token';
const REMEMBER_KEY = 'certimate_remember';

/**
 * 設定「Remember Me」偏好。
 *
 * 影響後續 {@link setStoredToken} 寫入 `localStorage`（true）或 `sessionStorage`（false）。
 *
 * @param val - 是否記住登入
 */
export function setRememberMe(val: boolean): void {
  localStorage.setItem(REMEMBER_KEY, String(val));
}

/**
 * 取得目前的「Remember Me」偏好。
 *
 * @returns 預設 true；SSR 環境同樣回傳 true
 */
export function getRememberMe(): boolean {
  if (typeof window === 'undefined') return true;
  const v = localStorage.getItem(REMEMBER_KEY);
  return v === null ? true : v === 'true';
}

/**
 * 讀取目前的 JWT token。
 *
 * 優先從 `localStorage` 取（Remember Me 啟用），找不到則退回 `sessionStorage`。
 *
 * @returns Token 字串；未登入或 SSR 時回傳 null
 */
export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

/**
 * 寫入 JWT token 至瀏覽器 storage。
 *
 * 依 {@link getRememberMe} 決定使用 `localStorage` 或 `sessionStorage`。
 *
 * @param token - JWT 字串
 */
export function setStoredToken(token: string): void {
  if (getRememberMe()) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
  }
}

/**
 * 清除兩種 storage 中的 JWT token（登出 / token 過期時呼叫）。
 */
export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const token = getStoredToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

/**
 * 在考試頁時被踢登入應保留答題進度（localStorage 已由 exam workspace 寫入）。
 * 回傳「目標登入頁 URL」含 next 參數讓登入後可回到原頁。
 */
function buildLoginRedirect(): string {
  if (typeof window === 'undefined') return '/login?expired=1';
  const path = window.location.pathname + window.location.search;
  // 考試頁特殊：完整保留 query 讓登入後可帶回 examId
  if (path.startsWith('/exam/workspace')) {
    return `/login?expired=1&next=${encodeURIComponent(path)}`;
  }
  return '/login?expired=1';
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.text().catch(() => '');

    // 401 = token 過期或未登入 — 清除 token 並導向登入
    if (response.status === 401) {
      clearStoredToken();
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.href = buildLoginRedirect();
      }
      throw new Error('登入已過期，請重新登入');
    }

    // 解析後端錯誤訊息
    let message = response.statusText;
    try {
      const parsed = JSON.parse(errorBody);
      message = parsed?.detail?.message || parsed?.detail || parsed?.message || message;
    } catch {
      message = errorBody || message;
    }

    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

/**
 * 靜默 refresh token —— 在 token 還有效但快過期時呼叫。
 * 失敗（如 token 已過期）回傳 false，呼叫端應走正常 401 流程。
 */
let _refreshInflight: Promise<boolean> | null = null;
export async function refreshTokenSilently(): Promise<boolean> {
  if (_refreshInflight) return _refreshInflight;
  const tok = getStoredToken();
  if (!tok) return false;
  _refreshInflight = (async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const r = await fetch(`${baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tok}`, 'Content-Type': 'application/json' },
      });
      if (!r.ok) return false;
      const data = await r.json() as { access_token?: string };
      if (!data.access_token) return false;
      setStoredToken(data.access_token);
      return true;
    } catch {
      return false;
    } finally {
      _refreshInflight = null;
    }
  })();
  return _refreshInflight;
}

/**
 * 啟動 token 自動延期：每 30 分鐘呼叫一次 /auth/refresh。
 * 由 AuthProvider 在初次登入後啟動，登出時清除。
 */
let _refreshTimer: ReturnType<typeof setInterval> | null = null;
export function startTokenAutoRefresh() {
  if (typeof window === 'undefined') return;
  if (_refreshTimer) return; // 已啟動
  // 30 分鐘間隔（JWT 8h TTL 內滑動續期，遠早於過期）
  _refreshTimer = setInterval(() => {
    void refreshTokenSilently();
  }, 30 * 60 * 1000);
}

export function stopTokenAutoRefresh() {
  if (_refreshTimer) {
    clearInterval(_refreshTimer);
    _refreshTimer = null;
  }
}

async function fetchWithRetry(url: string, init: RequestInit, retries = 2): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    try {
      const resp = await fetch(url, init);
      return resp;
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`[API] fetch failed (attempt ${i + 1}/${retries + 1}): ${init.method || 'GET'} ${url}`, err);
      }
      if (i === retries) throw err;
      await new Promise(r => setTimeout(r, 1000 * (i + 1)));
    }
  }
  throw new Error('Failed to fetch');
}

// ── API Client Interface ───────────────────────────────────────────

/**
 * HTTP API client 介面。
 *
 * 真實 / Mock 兩種實作（`realApiClient` 與 `mockApiClient`）都實作此介面，
 * 供 {@link apiClient} 在執行時依環境變數切換。
 */
export interface ApiClient {
  /** 發 GET 請求並解析為型別 T */
  get<T>(path: string): Promise<T>;
  /** 發 POST 請求；body 會 JSON.stringify */
  post<T>(path: string, body?: unknown): Promise<T>;
  /** 發 PUT 請求 */
  put<T>(path: string, body?: unknown): Promise<T>;
  /** 發 PATCH 請求 */
  patch<T>(path: string, body?: unknown): Promise<T>;
  /** 發 DELETE 請求 */
  delete<T>(path: string): Promise<T>;
  /** 以 multipart/form-data 上傳檔案；不可手動設 Content-Type */
  upload<T>(path: string, formData: FormData): Promise<T>;
}

// ── Real API Client ────────────────────────────────────────────────

const realApiClient: ApiClient = {
  async get<T>(path: string): Promise<T> {
    const headers = getAuthHeaders();
    const response = await fetchWithRetry(`${BASE_URL}${path}`, { headers });
    return handleResponse<T>(response);
  },

  async post<T>(path: string, body?: unknown): Promise<T> {
    const headers = getAuthHeaders();
    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  async put<T>(path: string, body?: unknown): Promise<T> {
    const headers = getAuthHeaders();
    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      method: 'PUT',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  async patch<T>(path: string, body?: unknown): Promise<T> {
    const headers = getAuthHeaders();
    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      method: 'PATCH',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  async delete<T>(path: string): Promise<T> {
    const headers = getAuthHeaders();
    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse<T>(response);
  },

  async upload<T>(path: string, formData: FormData): Promise<T> {
    const headers: Record<string, string> = {};
    const token = getStoredToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    // Don't set Content-Type — browser sets it with boundary for multipart
    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return handleResponse<T>(response);
  },
};

// ── Mock 模式切換 ──────────────────────────────────────────────────
// .env.local 設定 NEXT_PUBLIC_API_MODE=mock 啟用離線開發模式
// 離線時前端可完整運作，不需後端 API

function loadMockClient(): ApiClient {
  // Dynamic import 避免 production build 包含 mock 程式碼
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  return require('./mock-client').mockApiClient as ApiClient;
}

/**
 * 全域共用的 API client 實例。
 *
 * 依 `NEXT_PUBLIC_API_MODE` 環境變數動態切換：
 * - `'mock'` → 載入 `./mock-client` 的 `mockApiClient`
 * - 其他 → 使用呼叫真實後端的 `realApiClient`
 */
export const apiClient: ApiClient = process.env.NEXT_PUBLIC_API_MODE === 'mock'
  ? loadMockClient()
  : realApiClient;
