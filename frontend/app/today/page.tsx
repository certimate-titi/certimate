'use client';

/**
 * @file 路由 `/today` — 今日學習首頁（Sprint 3 T30）。
 *
 * 對應 ux-redesign-plan.md「Activity-First, Not View-First」原則：
 * 登入後使用者真正想看的是「現在該學什麼」，不是「儀表板數字報表」。
 *
 * Sprint 3 範圍策略：
 * - 不直接覆蓋既有 /dashboard（避免破壞既有 onboarding redirect）
 * - 新增獨立 /today 路由作為「新版學習首頁」
 * - 用戶可手動切換、CEO Q1 拍板後再決定 /dashboard → /today redirect
 *
 * 三件事內容：
 * 1. 繼續讀（上次中斷的章節）
 * 2. 複習（待複習錯題清單）
 * 3. Sprint 模擬測驗（依距考天數計算建議）
 *
 * Sprint 3 簡化版：每件事都是 Link 卡片，計算邏輯先用 dashboard endpoint 既有資料
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, BookOpen, Repeat, Target, Zap } from 'lucide-react';

import { useAuth } from '@/lib/auth-context';
// dashboardService removed in T42; using /dashboard/today via apiClient

interface TodaySnapshot {
  // 上次讀的資源（從 dashboard 取）
  resume?: { resourceId: string; chapterAnchor?: string; resourceName: string; subjectId?: string } | null;
  reviewCount: number;
  examDaysLeft: number | null;
  streak: number;
}

export default function TodayPage() {
  const { isAuthenticated, loading: authLoading, user } = useAuth();
  const router = useRouter();
  const [snapshot, setSnapshot] = useState<TodaySnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    void loadSnapshot();
  }, [authLoading, isAuthenticated, router]);

  const loadSnapshot = async () => {
    setLoading(true);
    try {
      // P4 (Sprint 5 T42)：改用 /dashboard/today 專屬 endpoint
      const t = await (await import('@/lib/api/client')).apiClient.get('/dashboard/today') as {
        greeting?: string;
        streak_days?: number;
        days_to_exam?: number | null;
        review_count?: number;
        resume?: { resource_id: string; resource_name: string; subject_id: string | null } | null;
      };
      setSnapshot({
        resume: t.resume
          ? { resourceId: t.resume.resource_id, resourceName: t.resume.resource_name, subjectId: t.resume.subject_id ?? undefined }
          : null,
        reviewCount: t.review_count ?? 0,
        examDaysLeft: t.days_to_exam ?? null,
        streak: t.streak_days ?? 0,
      });
    } catch {
      // /today endpoint 失敗 → 仍渲染基本卡片但無資料
      setSnapshot({ resume: null, reviewCount: 0, examDaysLeft: null, streak: 0 });
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 6) return '夜深了';
    if (h < 12) return '早安';
    if (h < 18) return '午安';
    return '晚安';
  })();

  const totalMinutes = (snapshot?.resume ? 20 : 0) + (snapshot?.reviewCount ? 10 : 0) + 30;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero */}
      <section className="bg-gradient-to-br from-emerald-50 to-white px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            {greeting}{user?.displayName ? `，${user.displayName}` : ''} 👋
          </h1>
          <p className="text-sm text-slate-600 flex flex-wrap items-center gap-3">
            {snapshot?.examDaysLeft !== null && snapshot?.examDaysLeft !== undefined && (
              <span className="inline-flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-emerald-600" />
                距下次考試 <strong className="text-slate-800">{snapshot.examDaysLeft}</strong> 天
              </span>
            )}
            {snapshot?.streak !== undefined && snapshot.streak > 0 && (
              <span className="inline-flex items-center gap-1">
                🔥 連續 <strong className="text-slate-800">{snapshot.streak}</strong> 天
              </span>
            )}
          </p>
        </div>
      </section>

      {/* Today's 3 things */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        <header className="mb-4">
          <h2 className="text-lg font-bold text-slate-900 mb-1">🎯 今日 3 件事（{totalMinutes} 分鐘）</h2>
          <p className="text-xs text-slate-500">完成可大幅提升保留率（spaced practice + retrieval）</p>
        </header>

        <div className="space-y-3">
          {/* 1. Resume */}
          {snapshot?.resume ? (
            <Link
              href={`/library/read/reading?docId=${snapshot.resume.resourceId}${snapshot.resume.subjectId ? `&subjectId=${snapshot.resume.subjectId}` : ''}`}
              className="group block bg-white rounded-2xl border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all p-4"
            >
              <div className="flex items-start gap-3">
                <div className="shrink-0 w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-emerald-600 mb-0.5">⓵ 繼續讀 · 約 20 分</p>
                  <h3 className="text-sm font-medium text-slate-900 mb-1 line-clamp-1">
                    {snapshot.resume.resourceName || '上次的章節'}
                  </h3>
                  <p className="text-xs text-slate-500">點擊接續上次中斷處</p>
                </div>
                <ArrowRight className="shrink-0 w-4 h-4 text-slate-400 group-hover:text-emerald-600 mt-3" />
              </div>
            </Link>
          ) : (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-4">
              <div className="flex items-start gap-3">
                <div className="shrink-0 w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-slate-400" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-slate-400 mb-0.5">⓵ 繼續讀</p>
                  <p className="text-sm text-slate-500">尚未開始閱讀任何資源</p>
                  <Link
                    href="/knowledge"
                    className="text-xs text-emerald-600 hover:underline mt-1 inline-block"
                  >
                    去學習庫上傳資源 →
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* 2. Review */}
          {snapshot && snapshot.reviewCount > 0 ? (
            <Link
              href="/knowledge/wrong-answers"
              className="group block bg-white rounded-2xl border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all p-4"
            >
              <div className="flex items-start gap-3">
                <div className="shrink-0 w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center">
                  <Repeat className="w-5 h-5 text-amber-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-amber-600 mb-0.5">⓶ 複習錯題 · 約 10 分</p>
                  <h3 className="text-sm font-medium text-slate-900 mb-1">
                    {snapshot.reviewCount} 題待複習
                  </h3>
                  <p className="text-xs text-slate-500">遺忘曲線提醒，現在複習效果最好</p>
                </div>
                <ArrowRight className="shrink-0 w-4 h-4 text-slate-400 group-hover:text-amber-600 mt-3" />
              </div>
            </Link>
          ) : (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-4">
              <div className="flex items-start gap-3">
                <div className="shrink-0 w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center">
                  <Repeat className="w-5 h-5 text-slate-400" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-slate-400 mb-0.5">⓶ 複習錯題</p>
                  <p className="text-sm text-slate-500">目前沒有待複習的題目，繼續累積吧</p>
                </div>
              </div>
            </div>
          )}

          {/* 3. Sprint mock exam */}
          <Link
            href="/exam/setup"
            className="group block bg-white rounded-2xl border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all p-4"
          >
            <div className="flex items-start gap-3">
              <div className="shrink-0 w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center">
                <Zap className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold text-indigo-600 mb-0.5">⓷ Sprint 模擬測驗 · 約 30 分</p>
                <h3 className="text-sm font-medium text-slate-900 mb-1">
                  {snapshot?.examDaysLeft && snapshot.examDaysLeft <= 14
                    ? `距考試 ${snapshot.examDaysLeft} 天，建議安排今日測驗`
                    : '保持節奏，每週至少 1 次模擬'}
                </h3>
                <p className="text-xs text-slate-500">testing effect — 練習比再讀有效</p>
              </div>
              <ArrowRight className="shrink-0 w-4 h-4 text-slate-400 group-hover:text-indigo-600 mt-3" />
            </div>
          </Link>
        </div>

        {/* Quick links */}
        <footer className="mt-8 pt-6 border-t border-slate-200">
          <p className="text-xs text-slate-400 mb-2">其他工具</p>
          <div className="flex flex-wrap gap-2">
            <Link href="/dashboard" className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-slate-300">📊 完整儀表板</Link>
            <Link href="/knowledge" className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-slate-300">🗺️ 知識圖譜</Link>
            <Link href="/practice" className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-slate-300">📝 自由練習</Link>
            <Link href="/account" className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-slate-300">⚙️ 帳號設定</Link>
          </div>
        </footer>
      </main>
    </div>
  );
}
