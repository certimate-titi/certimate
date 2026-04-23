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

export interface AnalyticsEvent {
  name: string;
  props?: Record<string, unknown>;
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

export function track(name: string, props?: Record<string, unknown>): void {
  const event: AnalyticsEvent = { name, props, ts: Date.now() };
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.debug('[analytics]', name, props);
  }
  writeQueue([...readQueue(), event]);
}

export function getQueue(): AnalyticsEvent[] {
  return readQueue();
}

export function clearQueue(): void {
  if (typeof window !== 'undefined') localStorage.removeItem(QUEUE_KEY);
}

let flushing = false;

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

export function startAnalyticsFlusher(): () => void {
  if (typeof window === 'undefined' || timer) return () => {};
  timer = setInterval(() => { void flushQueue(); }, FLUSH_INTERVAL_MS);
  return () => {
    if (timer) { clearInterval(timer); timer = null; }
  };
}
