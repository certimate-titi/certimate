/**
 * 前端埋點（PRD-046 US-07）
 *
 * 事件寫入 localStorage queue，定時批次 flush 到後端 /analytics/events。
 * 失敗時事件保留在 queue，下次再試；成功則清空已送出的部分。
 */

import { apiClient } from './api/client';

const QUEUE_KEY = 'certimate_analytics_queue';
const MAX_QUEUE_SIZE = 200;
const FLUSH_INTERVAL_MS = 30_000;
const FLUSH_BATCH_SIZE = 50;

/**
 * 前端埋點事件結構。
 */
export interface AnalyticsEvent {
  /** 事件名稱（snake_case 慣例） */
  name: string;
  /** 事件附帶屬性（任意 JSON-serializable 資料） */
  props?: Record<string, unknown>;
  /** 事件發生時間戳記（ms since epoch） */
  ts: number;
}

function readQueue(): AnalyticsEvent[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeQueue(events: AnalyticsEvent[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(events.slice(-MAX_QUEUE_SIZE)));
  } catch {
    /* quota — ignore */
  }
}

/**
 * 紀錄一筆埋點事件至本地 queue。
 *
 * 不立即送出；由 {@link startAnalyticsFlusher} 啟動的計時器或 {@link flushQueue} 批次傳送。
 * 開發模式會額外輸出 `console.debug`。
 *
 * @param name - 事件名稱
 * @param props - 任意附加屬性
 */
export function track(name: string, props?: Record<string, unknown>): void {
  const event: AnalyticsEvent = { name, props, ts: Date.now() };
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.debug('[analytics]', name, props);
  }
  writeQueue([...readQueue(), event]);
}

/**
 * 取得目前 localStorage 中尚未送出的埋點事件 snapshot。
 *
 * @returns queue 中所有事件；SSR / 解析失敗時回傳空陣列
 */
export function getQueue(): AnalyticsEvent[] {
  return readQueue();
}

/**
 * 清空本地埋點 queue。
 *
 * 通常用於測試或使用者登出時的資料清理。
 */
export function clearQueue(): void {
  if (typeof window !== 'undefined') localStorage.removeItem(QUEUE_KEY);
}

let flushing = false;

/**
 * 批次送出 queue 中的埋點事件至後端 `/analytics/events`。
 *
 * 一次最多送 {@link FLUSH_BATCH_SIZE} 筆；送出成功後從 queue 移除已送部分，
 * 失敗時保留全部事件供下次重試。函式具備防重入保護（`flushing` 旗標）。
 *
 * @returns 本次送出與剩餘的事件數量
 */
export async function flushQueue(): Promise<{ sent: number; remaining: number }> {
  if (typeof window === 'undefined' || flushing) return { sent: 0, remaining: 0 };
  const queue = readQueue();
  if (queue.length === 0) return { sent: 0, remaining: 0 };

  flushing = true;
  try {
    const batch = queue.slice(0, FLUSH_BATCH_SIZE);
    await apiClient.post('/analytics/events', { events: batch });
    const remaining = queue.slice(batch.length);
    writeQueue(remaining);
    return { sent: batch.length, remaining: remaining.length };
  } catch {
    return { sent: 0, remaining: queue.length };
  } finally {
    flushing = false;
  }
}

let timer: ReturnType<typeof setInterval> | null = null;

/**
 * 啟動定時 flush 計時器（每 {@link FLUSH_INTERVAL_MS} 毫秒呼叫 {@link flushQueue}）。
 *
 * 重複呼叫不會重複建立計時器；SSR 環境呼叫為 no-op。
 *
 * @returns 停止函式；呼叫即清除計時器
 */
export function startAnalyticsFlusher(): () => void {
  if (typeof window === 'undefined' || timer) return () => {};
  timer = setInterval(() => { void flushQueue(); }, FLUSH_INTERVAL_MS);
  return () => {
    if (timer) { clearInterval(timer); timer = null; }
  };
}
