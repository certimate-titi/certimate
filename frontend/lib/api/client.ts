const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

const TOKEN_KEY = 'certimate_jwt_token';
const REMEMBER_KEY = 'certimate_remember';

export function setRememberMe(val: boolean): void {
  localStorage.setItem(REMEMBER_KEY, String(val));
}

export function getRememberMe(): boolean {
  if (typeof window === 'undefined') return true;
  const v = localStorage.getItem(REMEMBER_KEY);
  return v === null ? true : v === 'true';
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (getRememberMe()) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
  }
}

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

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.text().catch(() => '');

    // 401 = token 過期或未登入 — 清除 token 並導向登入
    if (response.status === 401) {
      clearStoredToken();
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.href = '/login?expired=1';
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

export interface ApiClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body?: unknown): Promise<T>;
  put<T>(path: string, body?: unknown): Promise<T>;
  patch<T>(path: string, body?: unknown): Promise<T>;
  delete<T>(path: string): Promise<T>;
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

export const apiClient: ApiClient = process.env.NEXT_PUBLIC_API_MODE === 'mock'
  ? loadMockClient()
  : realApiClient;
