'use client';

/**
 * @file 路由 `/today/reviews` — SM-2 鷹架複習面板（Sprint 7 T53）。
 *
 * UX：
 * - 列出今日該複習的鷹架（next_review_at <= now）
 * - 每一條卡片：
 *   - 章節標題 + content preview
 *   - 點擊「現在複習」→ 跳到 reading 頁該章節，自動高亮對應 RetrievalCard
 *   - 顯示 SM-2 metadata：interval_days / repetitions / 下次間隔預測
 *
 * 教學原理：Spaced Repetition + Active Recall
 *   今日該複習的東西現在不複習，明天會更困難（遺忘曲線）
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, BookOpen, AlertTriangle, Lightbulb, Brain, XCircle } from 'lucide-react';

import { useAuth } from '@/lib/auth-context';
import { documentService, resourceParseService } from '@/lib/api/services';

interface DueReviewItem {
  schedule_id: string;
  scaffold_id: string;
  chapter_heading: string | null;
  type: string;
  content_preview: string;
  resource_id: string;
  resource_name: string;
  next_review_at: string;
  interval_days: number;
  repetitions: number;
}

const TYPE_META: Record<string, { Icon: typeof BookOpen; label: string; color: string }> = {
  takeaway: { Icon: BookOpen, label: '重點', color: 'text-emerald-600 bg-emerald-50' },
  pitfall: { Icon: AlertTriangle, label: '迷思', color: 'text-rose-600 bg-rose-50' },
  advance_organizer: { Icon: Lightbulb, label: '讀前定錨', color: 'text-violet-600 bg-violet-50' },
  elaborative: { Icon: Brain, label: '思考題', color: 'text-indigo-600 bg-indigo-50' },
};

export default function TodayReviewsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<DueReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Layer 3：空態時主動查 resource_parse_jobs 確認是否為解析失敗
  const [parseJobFailures, setParseJobFailures] = useState<Array<{ title: string; reason: string }>>([]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    void loadDue();
  }, [authLoading, isAuthenticated, router]);

  const loadDue = async () => {
    setLoading(true);
    try {
      const { apiClient } = await import('@/lib/api/client');
      const r = await apiClient.get('/scaffold-reviews/due?limit=50') as {
        total: number;
        items: DueReviewItem[];
      };
      setItems(r.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  // Layer 3：items 載入後若為空，主動查 FAILED 資源確認是否為解析失敗
  useEffect(() => {
    if (loading) return;
    if (items.length > 0) { setParseJobFailures([]); return; }

    documentService.list().then(async (res) => {
      const failedDocs = (res.documents || []).filter(
        (d: { status?: string }) => d.status === 'FAILED'
      );
      if (failedDocs.length === 0) { setParseJobFailures([]); return; }
      const failures = await Promise.all(
        failedDocs.slice(0, 3).map(async (doc: { id: string; title?: string }) => {
          try {
            const status = await resourceParseService.getStatus(doc.id);
            return { title: doc.title || '未命名資源', reason: status.failure_reason || '解析失敗（無詳細原因）' };
          } catch {
            return { title: doc.title || '未命名資源', reason: '解析失敗（查詢狀態失敗）' };
          }
        })
      );
      setParseJobFailures(failures);
    }).catch(() => { /* 查詢失敗時靜默 */ });
  }, [items, loading]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link href="/today" className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900">
          <ArrowLeft className="w-4 h-4" /> 今日
        </Link>
        <div className="text-sm font-medium text-slate-700">SM-2 鷹架複習</div>
        <div className="ml-auto text-xs text-slate-500">{items.length} 個到期</div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">
        {items.length === 0 ? (
          <div className="space-y-4">
            {parseJobFailures.length > 0 && (
              <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4" data-testid="reviews-empty-parse-failures">
                <div className="flex items-start gap-2 mb-2">
                  <XCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                  <p className="text-sm font-medium text-rose-700">
                    部分資源解析失敗，可能導致鷹架未生成
                  </p>
                </div>
                <ul className="ml-7 space-y-1">
                  {parseJobFailures.map((f, i) => (
                    <li key={i} className="text-xs text-rose-600">
                      <span className="font-medium">{f.title}</span>：{f.reason}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/account/resource-library"
                  className="inline-block ml-7 mt-2 text-xs text-rose-600 underline hover:text-rose-800"
                >
                  前往學習庫重新解析 →
                </Link>
              </div>
            )}
            <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center">
              <div className="text-3xl mb-3">✨</div>
              <h2 className="text-lg font-bold text-slate-800 mb-2">今日無到期複習</h2>
              <p className="text-sm text-slate-500 mb-4">
                繼續閱讀新章節 + 點「我已揭曉」自評，未來會自動安排複習時間。
              </p>
              <Link
                href="/today"
                className="inline-block px-4 py-2 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white text-sm"
              >
                回今日首頁
              </Link>
            </div>
          </div>
        ) : (
          <>
            <p className="text-xs text-slate-500 mb-4">
              📚 依 SM-2 spaced repetition 演算法計算的個人化複習清單。現在複習效果最好（遺忘曲線）。
            </p>
            <div className="space-y-3">
              {items.map((item) => {
                const meta = TYPE_META[item.type] || TYPE_META.takeaway;
                const Icon = meta.Icon;
                return (
                  <article
                    key={item.schedule_id}
                    className="bg-white rounded-2xl border border-slate-200 p-4 hover:border-emerald-300 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`shrink-0 w-10 h-10 rounded-xl ${meta.color} flex items-center justify-center`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-slate-500">{meta.label}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                            連對 {item.repetitions} 次 · 下次 {item.interval_days}d
                          </span>
                        </div>
                        {item.chapter_heading && (
                          <p className="text-xs text-slate-500 mb-1 truncate">
                            {item.chapter_heading} · {item.resource_name}
                          </p>
                        )}
                        <p className="text-sm text-slate-700 line-clamp-2 mb-3">
                          {item.content_preview}
                        </p>
                        <Link
                          href={`/library/read/reading?docId=${item.resource_id}`}
                          className="inline-block px-3 py-1.5 rounded-full bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-medium border border-emerald-200"
                        >
                          現在複習 →
                        </Link>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
            <p className="text-xs text-slate-400 mt-6 text-center">
              💡 複習完點 RetrievalCard 自評（沒想到 / 想到一半 / 完全想到），SM-2 會自動排下次間隔。
            </p>
          </>
        )}
      </main>
    </div>
  );
}
