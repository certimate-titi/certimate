/**
 * useReadingPageState — 章節閱讀頁狀態 hook（Sprint 1 T05）
 *
 * 為新路由 /library/[stub]/reading 而建。封裝：
 * - 從 URL 解析 docId / subjectId / chapter
 * - parse_status 輪詢（解析中時每 5s 重抓 markdown，一旦 SUCCESS 即停）
 * - markdown / 鷹架資料載入
 * - 章節目錄建構（從 markdown 提取 H2/H3）
 *
 * 不改 frontend/app/knowledge/page.tsx 既有狀態 — 這是 NEW route 專用 hook，
 * 避免破壞既有功能（per CTO 自檢策略：漸進式重構）。
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { resourceParseService } from '@/lib/api/services';

export type ParseStatus = 'queued' | 'parsing' | 'success' | 'failed' | null;

export interface ChapterEntry {
  /** 章節標題（去 markdown 標記後純文字）*/
  heading: string;
  /** Heading level — 2 = H2, 3 = H3 */
  level: 2 | 3;
  /** Anchor id（slug from heading） */
  anchorId: string;
  /** 在 markdown 中的字元偏移 */
  offset: number;
}

export interface ScaffoldEntry {
  id: string;
  chapter_heading: string | null;
  type: 'takeaway' | 'elaborative' | 'strategy';
  content: string;
  retrieval_prompt: string | null;
  template_code: string | null;
  user_response: string | null;
}

export interface ReadingPageState {
  /** Resource UUID 從 URL 解析 */
  resourceId: string;
  /** Subject UUID 從 URL 解析（可空）*/
  subjectId: string;
  /** 當前章節 anchor（用 query string ?chapter= 控制）*/
  currentChapter: string;
  /** 後端解析狀態 */
  parseStatus: ParseStatus;
  /** 解析失敗原因（若 parse_status=failed）*/
  parseFailureReason: string | null;
  /** Markdown 全文 */
  markdown: string;
  /** 章節目錄（從 markdown H2/H3 提取）*/
  chapters: ChapterEntry[];
  /** 學習鷹架資料 */
  scaffolds: ScaffoldEntry[];
  /** 載入中 */
  loading: boolean;
  /** 錯誤訊息 */
  error: string | null;
  /** 手動重抓 */
  refetch: () => Promise<void>;
}

const POLL_INTERVAL_MS = 5000;
const MAX_POLL_DURATION_MS = 5 * 60 * 1000; // 5 分鐘輪詢上限

/**
 * 從 markdown 提取 H2/H3 章節目錄。
 *
 * 不靠 markdown parser（避免重依賴），只用簡單 regex。
 */
function extractChapters(markdown: string): ChapterEntry[] {
  const out: ChapterEntry[] = [];
  const lines = markdown.split('\n');
  let offset = 0;
  let counter = 0;
  for (const line of lines) {
    const m = /^(##|###)\s+(.+?)\s*$/.exec(line);
    if (m) {
      const level = m[1].length === 2 ? 2 : 3;
      const heading = m[2].replace(/[*_`]/g, '').trim();
      if (heading) {
        const anchorId = `ch-${counter++}-${heading.toLowerCase().replace(/\s+/g, '-').replace(/[^\p{L}\p{N}-]/gu, '').slice(0, 40)}`;
        out.push({ heading, level: level as 2 | 3, anchorId, offset });
      }
    }
    offset += line.length + 1;
  }
  return out;
}

/**
 * 從 URL pathname / search 解析 reading 頁參數。
 *
 * 因為靜態匯出 + Firebase rewrite 限制（見 CLAUDE.md），不能用 useParams()。
 * 必須從 window.location 直接 regex 解析。
 */
function parseUrlParams(): { resourceId: string; subjectId: string; chapter: string } {
  if (typeof window === 'undefined') return { resourceId: '', subjectId: '', chapter: '' };
  const params = new URLSearchParams(window.location.search);
  return {
    resourceId: params.get('docId') ?? '',
    subjectId: params.get('subjectId') ?? '',
    chapter: params.get('chapter') ?? '',
  };
}

export function useReadingPageState(): ReadingPageState {
  const [{ resourceId, subjectId, chapter }, setUrlParams] = useState(parseUrlParams);
  const [parseStatus, setParseStatus] = useState<ParseStatus>(null);
  const [parseFailureReason, setParseFailureReason] = useState<string | null>(null);
  const [markdown, setMarkdown] = useState<string>('');
  const [scaffolds, setScaffolds] = useState<ScaffoldEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollStartRef = useRef<number>(0);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Re-parse URL on history change（user navigates away and back）
  useEffect(() => {
    const handler = () => setUrlParams(parseUrlParams());
    window.addEventListener('popstate', handler);
    return () => window.removeEventListener('popstate', handler);
  }, []);

  const fetchMarkdownAndStatus = useCallback(async () => {
    if (!resourceId) return;
    try {
      const md = await resourceParseService.getMarkdown(resourceId) as {
        markdown?: string;
        parse_status?: ParseStatus;
        parse_failure_reason?: string | null;
      };
      setMarkdown(md.markdown ?? '');
      setParseStatus(md.parse_status ?? null);
      setParseFailureReason(md.parse_failure_reason ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'markdown 讀取失敗');
    }
  }, [resourceId]);

  const fetchScaffolds = useCallback(async () => {
    if (!resourceId) return;
    try {
      const parsed = await resourceParseService.getParsed(resourceId) as unknown as {
        scaffolds?: ScaffoldEntry[];
      };
      setScaffolds(parsed.scaffolds ?? []);
    } catch {
      // FREE plan 或解析未完成時 /parsed 可能 403/404，不致命
      setScaffolds([]);
    }
  }, [resourceId]);

  // Initial load
  useEffect(() => {
    if (!resourceId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    Promise.all([fetchMarkdownAndStatus(), fetchScaffolds()]).finally(() => {
      setLoading(false);
    });
  }, [resourceId, fetchMarkdownAndStatus, fetchScaffolds]);

  // Poll while parse_status is queued/parsing
  useEffect(() => {
    if (!resourceId) return;
    if (parseStatus !== 'queued' && parseStatus !== 'parsing') {
      // 完成 / 失敗 / 無 job 都停輪詢
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      return;
    }
    if (pollStartRef.current === 0) pollStartRef.current = Date.now();
    if (Date.now() - pollStartRef.current > MAX_POLL_DURATION_MS) return;

    pollTimerRef.current = setTimeout(() => {
      void fetchMarkdownAndStatus();
      void fetchScaffolds();
    }, POLL_INTERVAL_MS);

    return () => {
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [resourceId, parseStatus, fetchMarkdownAndStatus, fetchScaffolds]);

  const chapters = useMemo(() => extractChapters(markdown), [markdown]);

  const refetch = useCallback(async () => {
    pollStartRef.current = 0;
    setLoading(true);
    await Promise.all([fetchMarkdownAndStatus(), fetchScaffolds()]);
    setLoading(false);
  }, [fetchMarkdownAndStatus, fetchScaffolds]);

  return {
    resourceId,
    subjectId,
    currentChapter: chapter,
    parseStatus,
    parseFailureReason,
    markdown,
    chapters,
    scaffolds,
    loading,
    error,
    refetch,
  };
}
