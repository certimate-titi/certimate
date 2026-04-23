/**
 * 前端埋點 stub（PRD-046 US-07）
 *
 * 極簡版本：事件丟 localStorage queue，後續可批次 flush 到後端。
 * MVP 階段只有 console 輸出 + 持久化，等後端 /analytics/events 上線再接。
 */

const QUEUE_KEY = 'certimate_analytics_queue';
const MAX_QUEUE_SIZE = 200;

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
