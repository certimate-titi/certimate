/**
 * @file 路由 `/schedule` — 動態大腦精力調度排程頁（Spec 09）。
 *
 * 顯示各備考科目的：
 * - 學習模式（Sprint / Standard / Mastery，依距考日自動推導）
 * - 今日推薦題數
 * - 下次複習時間
 * - 一鍵「開始今日複習」入口
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Calendar, Zap, BookOpen, Compass, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { scheduleService, type ScheduleRecommendation } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

const MODE_META: Record<string, { label: string; emoji: string; color: string; desc: string }> = {
  sprint: { label: 'Sprint 衝刺', emoji: '⚡', color: 'bg-rose-50 text-rose-700 border-rose-200', desc: '距考日 < 14 天，錯題與 AI 生題優先' },
  standard: { label: 'Standard 穩紮', emoji: '📚', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', desc: '距考日 1-6 月，SuperMemo-2 遺忘曲線排程' },
  mastery: { label: 'Mastery 廣讀', emoji: '🧭', color: 'bg-blue-50 text-blue-700 border-blue-200', desc: '距考日 > 6 月，隨機探索 + 盲區補強' },
};

export default function SchedulePage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [recs, setRecs] = useState<ScheduleRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    scheduleService.getRecommendations()
      .then((res) => setRecs(res.recommendations || []))
      .catch((e: unknown) => {
        const err = e as { message?: string };
        setError(err?.message || '載入排程失敗');
      })
      .finally(() => setLoading(false));
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-emerald-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center gap-2 mb-2">
        <Calendar className="w-6 h-6 text-emerald-500" />
        <h1 className="text-2xl font-bold text-slate-900">學習排程</h1>
      </div>
      <p className="text-sm text-slate-500 mb-6 leading-relaxed">
        系統依各科目「距考日天數」自動推導學習模式，並用 SuperMemo-2 遺忘曲線排程複習題目。
      </p>

      {error && (
        <div className="mb-4 flex items-start gap-2 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {recs.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-slate-200">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500 font-medium mb-2">尚無備考科目可排程</p>
          <p className="text-xs text-slate-400 mb-4">請先在 Onboarding 或會員中心新增至少一個備考科目</p>
          <Link href="/onboarding" className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-full font-medium text-sm hover:bg-emerald-600">
            前往新增科目 <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {recs.map((r) => {
            const meta = MODE_META[r.mode] || MODE_META.standard;
            const daysToExam = r.exam_date
              ? Math.ceil((new Date(r.exam_date).getTime() - Date.now()) / 86400_000)
              : null;
            return (
              <div key={r.subject_id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{r.subject_name}</h3>
                    {daysToExam !== null && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        距考日 <b className={daysToExam < 14 ? 'text-rose-600' : 'text-slate-700'}>{daysToExam} 天</b>
                      </p>
                    )}
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${meta.color}`}>
                    {meta.emoji} {meta.label}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-3 leading-relaxed">{meta.desc}</p>

                <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                  <div className="bg-slate-50 rounded p-2">
                    <div className="text-slate-400">待複習題數</div>
                    <div className="text-lg font-bold text-slate-900">{r.pending_questions}</div>
                  </div>
                  <div className="bg-slate-50 rounded p-2">
                    <div className="text-slate-400">推薦題數</div>
                    <div className="text-lg font-bold text-emerald-600">{r.recommended_count}</div>
                  </div>
                </div>

                {r.next_review_at && (
                  <p className="text-[11px] text-slate-400 mb-3">
                    下次複習：{new Date(r.next_review_at).toLocaleString('zh-TW')}
                  </p>
                )}

                <Link
                  href={`/exam/setup?subjectId=${r.subject_id}&from=schedule`}
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 text-white rounded-lg font-bold text-sm hover:bg-emerald-600 transition-colors"
                >
                  <Zap className="w-4 h-4" /> 開始今日複習
                </Link>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-6 text-xs text-slate-400 text-center flex items-center justify-center gap-2">
        <Compass className="w-3 h-3" />
        模式自動推導依考期天數計算（Sprint &lt; 14 天 / Standard 1-6 月 / Mastery &gt; 6 月）
      </div>
    </div>
  );
}
