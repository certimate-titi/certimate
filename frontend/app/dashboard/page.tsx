/**
 * @file 路由 `/dashboard` — 使用者主控台首頁。
 *
 * 登入後的主入口；顯示歡迎語、備考模式徽章、連勝計數、4 核心指標卡、
 * 今日行動中心（3 CTA）、每日任務、待辦提醒、學習狀態、知識版圖進度。
 * 快速匯入資源已移至 /knowledge 的 UploadResourceModal。
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Clock, TrendingUp, BookOpen, AlertCircle, Sparkles, MessageSquare, FileText,
  Target, Map, Flame, Settings, BarChart2, ChevronDown, ChevronUp,
} from 'lucide-react';
import { dashboardService, subjectService, completionService } from '@/lib/api/services';
import ScheduleWeekCard from '@/components/ScheduleWeekCard';
import type { GetDashboardResponse, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import StreakCounter from '@/components/StreakCounter';
import DailyQuestCard from '@/components/DailyQuestCard';
import SubjectPickerModal from '@/components/SubjectPickerModal';
import AnnouncementBanner from '@/components/AnnouncementBanner';
import PendingJourneysBanner from '@/components/PendingJourneysBanner';
import DomainRadarChart from '@/components/DomainRadarChart';
import type { SelectedSubject } from '@/components/onboarding/SelectedSubjectCard';
import CompletionProgressBar from '@/components/completion/CompletionProgressBar';
import BadgeShelf from '@/components/completion/BadgeShelf';
import MarginalUtilityNudge from '@/components/completion/MarginalUtilityNudge';
import { calcCompletion, type CompletionNode } from '@/lib/completion-calc';
import type { SubjectCompletionResponse } from '@/types/api';

/** 依台灣時間 hour 決定問候語 */
function getGreeting(): string {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return '早安';
  if (h >= 12 && h < 18) return '午安';
  return '晚安';
}

/**
 * 使用者主控台首頁。
 *
 * 透過 `dashboardService` 載入儀表板資料；快速匯入資源入口已移至 /knowledge。
 */
export default function DashboardPage() {
  const { user, isAuthenticated, loading: authLoading, onboardingCompleted, isProPlus, isUltra, subscriptionTier } = useAuth();
  const router = useRouter();
  const [showModeTooltip, setShowModeTooltip] = useState(false);

  const [data, setData] = useState<GetDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Subject state
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [subjectsLoaded, setSubjectsLoaded] = useState(false);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');
  const [showAddSubject, setShowAddSubject] = useState(false);

  // Stage 1 — 待辦提醒摺疊
  const [todoExpanded, setTodoExpanded] = useState(false);
  const TODO_FOLD_LIMIT = 3;

  // #6 Completion Framework — 後端加權進度
  const [completion, setCompletion] = useState<SubjectCompletionResponse | null>(null);
  const [completionLoading, setCompletionLoading] = useState(false);
  // 'none'：無科目 / 'not_found'：API 404 / 'server_error'：API 5xx / null：正常
  const [completionError, setCompletionError] = useState<'none' | 'not_found' | 'server_error' | null>(null);

  const FAKE_UUID_RE = /^0{8}-0{4}-0{4}-0{4}-0{12}$/;

  const loadCompletion = useCallback((subjectId: string) => {
    // 守衛：無 subjectId 或假 UUID → 不發 API
    if (!subjectId || FAKE_UUID_RE.test(subjectId)) {
      setCompletion(null);
      setCompletionError('none');
      setCompletionLoading(false);
      return;
    }
    setCompletionLoading(true);
    setCompletionError(null);
    completionService
      .getCompletion(subjectId)
      .then((res) => { setCompletion(res); setCompletionError(null); })
      .catch((err: any) => {
        setCompletion(null);
        const status = err?.response?.status ?? err?.status;
        if (status === 404) setCompletionError('not_found');
        else if (status >= 500) setCompletionError('server_error');
        else setCompletionError(null); // 其他錯誤 fallback 到 mock
      })
      .finally(() => setCompletionLoading(false));
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !activeSubjectId) {
      setCompletion(null);
      setCompletionError(activeSubjectId ? null : 'none');
      return;
    }
    loadCompletion(activeSubjectId);
  }, [isAuthenticated, activeSubjectId, loadCompletion]);

  // T63 (Sprint 8 L30)：信心度校準趨勢（Feature 20）
  const [calibration, setCalibration] = useState<{
    calibration_rate: number;
    status: string;
    trend: Array<{ exam_id: string; submitted_at: string | null; calibration_rate: number }>;
    exam_count: number;
  } | null>(null);
  useEffect(() => {
    if (!isAuthenticated) return;
    dashboardService.getConfidenceCalibration().then(setCalibration).catch(() => setCalibration(null));
  }, [isAuthenticated]);

  // Onboarding guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (!onboardingCompleted) {
      router.replace('/onboarding');
    }
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load subjects
  useEffect(() => {
    if (authLoading || !isAuthenticated || !onboardingCompleted) return;
    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects || []);
      if (res.subjects && res.subjects.length > 0) {
        const saved = localStorage.getItem('certimate_active_subject_id');
        const match = saved && res.subjects.find((s: UserSubject) => s.id === saved);
        setActiveSubjectId(match ? saved : res.subjects[0].id);
      }
    }).catch(() => setSubjects([])).finally(() => setSubjectsLoaded(true));
  }, [authLoading, isAuthenticated, onboardingCompleted]);

  // Merge main dashboard response with quests + review-calendar endpoints.
  const loadDashboardData = useCallback(async (subjectId?: string) => {
    const [d, questsRes, calRes] = await Promise.all([
      dashboardService.get(subjectId),
      dashboardService.getDailyQuests().catch(() => ({ quests: [] })),
      dashboardService.getReviewCalendar().catch(() => ({ calendar: [], subject: null, month: null })),
    ]);
    const quests = (questsRes.quests || []).map((q: any) => ({
      id: q.id,
      type: (q.type as 'review' | 'explore' | 'quiz') || 'review',
      description: q.title,
      completed: q.status === 'completed',
      xpReward: 0,
      progress: typeof q.progress === 'number' ? q.progress : undefined,
      target: typeof q.target === 'number' ? q.target : undefined,
    }));
    const calendar = (calRes.calendar || []).map((c) => ({
      date: c.date,
      reviewCount: c.count,
      topics: [] as string[],
    }));
    return {
      ...d,
      dailyQuests: quests,
      reviewCalendar: calendar,
    };
  }, []);

  // Load dashboard data
  useEffect(() => {
    if (authLoading || !isAuthenticated) return;
    if (!onboardingCompleted || !activeSubjectId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    loadDashboardData(activeSubjectId)
      .then((merged) => { setData(merged); setLoading(false); })
      .catch(() => {
        setData({
          user: null as any,
          streak: { currentStreak: 0, longestStreak: 0, freezesRemaining: 0, freezesPerWeek: 0, lastActiveDate: new Date().toISOString() },
          dailyQuests: [],
          activityItems: [],
          reviewCalendar: [],
          stats: { overallAccuracy: 0, totalMocksCompleted: 0, totalQuestionsAnswered: 0, predictedPassRate: 0, examCountdown: null },
          domainStrengths: [],
        });
        setLoading(false);
      });
  }, [activeSubjectId, isAuthenticated, onboardingCompleted, loadDashboardData]);

  const handleAddSubject = useCallback(async (selected: SelectedSubject[]) => {
    const failures: string[] = [];
    for (const s of selected) {
      try {
        await subjectService.addSubject({
          subjectId: s.subjectId,
          subjectName: s.subjectName,
          examDate: s.examDate,
          resultDate: s.resultDate,
          selfAssessment: s.selfAssessment,
        });
      } catch (e: any) {
        const msg = e?.response?.data?.detail?.message || e?.response?.data?.message || e?.message || '未知錯誤';
        failures.push(`${s.subjectName}：${msg}`);
      }
    }
    try {
      const res = await subjectService.getUserSubjects();
      setSubjects(res.subjects);
      if (res.subjects.length > 0 && !activeSubjectId) {
        setActiveSubjectId(res.subjects[0].id);
      }
    } catch { /* silent */ }
    if (failures.length > 0) {
      alert(`部分科目新增失敗：\n\n${failures.join('\n')}`);
    }
    if (failures.length < selected.length) {
      setShowAddSubject(false);
    }
  }, [activeSubjectId]);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // 3d Layer: 載入態誤判防護 — 必須等 subjectsLoaded 為 true 才能判定「真空態」
  if (!subjectsLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // User logged in but hasn't picked a subject yet
  if (!activeSubjectId || subjects.length === 0) {
    return (
      <>
        <div className="min-h-screen flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white rounded-3xl shadow-sm border border-slate-200 p-8 text-center">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-xl font-bold text-slate-800 mb-2">歡迎使用 TiTi</h2>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed">
              你還沒有選擇備考科目。請先新增一個科目，我們會為你準備考古題題庫、
              知識心智圖與 AI 教練。
            </p>
            <button
              onClick={() => setShowAddSubject(true)}
              className="w-full bg-emerald-500 text-white py-3 rounded-full font-medium hover:bg-emerald-600 transition-colors"
            >
              開始選擇科目
            </button>
          </div>
        </div>
        {showAddSubject && (
          <SubjectPickerModal
            excludeSubjectIds={subjects.map(s => s.subjectId)}
            onConfirm={handleAddSubject}
            onClose={() => setShowAddSubject(false)}
          />
        )}
      </>
    );
  }

  if (loading || !data) {
    return (
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-6xl">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-slate-200 rounded w-48" />
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              <div className="h-48 bg-slate-200 rounded-3xl" />
              <div className="h-32 bg-slate-200 rounded-3xl" />
            </div>
            <div className="h-96 bg-slate-200 rounded-3xl" />
          </div>
        </div>
      </div>
    );
  }

  // ── 備考模式計算（與 backend schedule_service._calculate_mode 對齊）──
  const days = data.stats.examCountdown?.daysRemaining ?? null;
  const modeInfo = days !== null
    ? days <= 7
      ? { icon: '🚨', label: 'Final 最後衝刺', color: 'bg-red-50 text-red-700 border-red-200', desc: '距考 ≤ 7 天，純鞏固已遇過題目，停止探索新題。', strategy: '反覆刷錯題本與弱點節點，不再嘗試新內容。', weights: '過複習日 70% / 新錯題 10% / 弱點 20%' }
      : days <= 30
      ? { icon: '🔥', label: 'Sprint 衝刺', color: 'bg-rose-50 text-rose-700 border-rose-200', desc: '距考 8-30 天，重複錯題鞏固為主。', strategy: '重點加強曾答錯的高頻題目與未觸及的盲點。', weights: '過複習日 60% / 新錯題 15% / 弱點 20% / 隨機 5%' }
      : days <= 180
      ? { icon: '🏃', label: 'Standard 穩紮', color: 'bg-blue-50 text-blue-700 border-blue-200', desc: '1-6 月備考期，開拓與鞏固並行。', strategy: '兼顧新知識點探索與已有觀念的深化鞏固。', weights: '過複習日 40% / 新錯題 30% / 弱點 20% / 隨機 10%' }
      : { icon: '🌳', label: 'Mastery 廣讀', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', desc: '> 6 月長期備考，追求抗遺忘與跨域關聯。', strategy: '建立深層記憶與概念串聯，低壓穩步推進。', weights: '過複習日 25% / 新錯題 45% / 弱點 20% / 隨機 10%' }
    : null;

  // ── 待辦提醒分組 ──
  const allTodos = data.activityItems || [];
  const visibleTodos = todoExpanded ? allTodos : allTodos.slice(0, TODO_FOLD_LIMIT);
  const hiddenCount = allTodos.length - TODO_FOLD_LIMIT;

  return (
    <>
      {/* System Announcements */}
      <AnnouncementBanner />

      {/* Pending exam result confirmations */}
      <PendingJourneysBanner />

      {/* No-subject prompt */}
      {subjectsLoaded && subjects.length === 0 && isAuthenticated && onboardingCompleted && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-3">
          <div className="container mx-auto max-w-6xl flex items-center justify-between">
            <span className="text-sm text-amber-800">尚未建立備考科目，請先新增科目以開始學習</span>
            <button onClick={() => setShowAddSubject(true)} className="text-sm font-bold text-amber-700 hover:text-amber-900 underline">新增科目</button>
          </div>
        </div>
      )}

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-6xl">

        {/* ═══════════════════════════════════════════════════════════
            頂部 Section 1 — 歡迎語單行 header
            包含：問候語 + 連勝 + 備考模式徽章
            ═══════════════════════════════════════════════════════════ */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          {/* 左：問候語 + 模式徽章 */}
          <div className="flex flex-wrap items-center gap-2 min-w-0">
            <h1 className="text-[26px] font-bold text-slate-900 leading-tight">
              {getGreeting()}，{user?.displayName || '學習者'}！
            </h1>
            {modeInfo && (
              <div className="relative">
                <button
                  onClick={() => setShowModeTooltip(!showModeTooltip)}
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border cursor-pointer hover:shadow-sm transition-all ${modeInfo.color}`}
                >
                  {modeInfo.icon} {modeInfo.label}
                </button>
                {showModeTooltip && (
                  <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 p-4 z-30">
                    <h4 className="font-bold text-slate-900 text-sm mb-2">{modeInfo.icon} {modeInfo.label}</h4>
                    <p className="text-xs text-slate-600 mb-2">{modeInfo.desc}</p>
                    <p className="text-xs text-slate-500 mb-2"><strong>策略：</strong>{modeInfo.strategy}</p>
                    <div className="bg-slate-50 rounded-lg p-2">
                      <p className="text-[10px] text-slate-500 font-medium mb-1">配題權重</p>
                      <p className="text-xs text-slate-700">{modeInfo.weights}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          {/* 右：連勝計數 */}
          <div className="flex items-center gap-2 shrink-0" title={data.streak.freezeConsumedToday ? '休息也是學習的一部分，歡迎回來！' : undefined}>
            <StreakCounter streak={data.streak} />
            {data.streak.freezesRemaining > 0 && (
              <span className="text-xs text-blue-500 whitespace-nowrap">❄️ {data.streak.freezesRemaining}</span>
            )}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            頂部 Section 2 — 核心 4 指標卡（Grid 2x2 desktop / 1x4 mobile）
            主數字 36px extrabold；標籤 12px medium；語意色背景
            ═══════════════════════════════════════════════════════════ */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* 距考天數 — amber */}
          <div className="bg-amber-50 rounded-2xl p-5 shadow-sm border border-amber-100 text-center">
            <Clock className="h-5 w-5 text-amber-500 mx-auto mb-2" />
            <span className="block text-[36px] font-extrabold text-amber-700 leading-none mb-1">
              {data.stats.examCountdown?.daysRemaining ?? '--'}
            </span>
            <span className="text-xs font-medium text-amber-600">距離考試天數</span>
          </div>
          {/* 累積答題 — indigo */}
          <div className="bg-indigo-50 rounded-2xl p-5 shadow-sm border border-indigo-100 text-center">
            <BookOpen className="h-5 w-5 text-indigo-500 mx-auto mb-2" />
            <span className="block text-[36px] font-extrabold text-indigo-700 leading-none mb-1">
              {data.stats.totalQuestionsAnswered ?? 0}
            </span>
            <span className="text-xs font-medium text-indigo-600">累積答題數</span>
          </div>
          {/* 整體答對率 — emerald */}
          <div className="bg-emerald-50 rounded-2xl p-5 shadow-sm border border-emerald-100 text-center">
            <TrendingUp className="h-5 w-5 text-emerald-500 mx-auto mb-2" />
            <span className="block text-[36px] font-extrabold text-emerald-700 leading-none mb-1">
              {data.stats.overallAccuracy}%
            </span>
            <span className="text-xs font-medium text-emerald-600">整體答對率</span>
          </div>
          {/* 預測及格率 — purple */}
          <div className="bg-purple-50 rounded-2xl p-5 shadow-sm border border-purple-100 text-center">
            <Sparkles className="h-5 w-5 text-purple-500 mx-auto mb-2" />
            <span className="block text-[36px] font-extrabold text-purple-700 leading-none mb-1">
              {data.stats.predictedPassRate ?? '--'}%
            </span>
            <span className="text-xs font-medium text-purple-600">預測及格率</span>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            頂部 Section 3 — 今日行動中心
            副標：距考 N 天 | mode；3 個 CTA 卡片
            ═══════════════════════════════════════════════════════════ */}
        <section className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-3xl p-6 border border-emerald-100 shadow-sm mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[18px] font-bold text-slate-900">今日行動中心</h2>
            {days !== null && modeInfo && (
              <span className="text-xs font-bold text-slate-500">
                距考 {days} 天 | {modeInfo.label}
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* CTA 1 — 開始今日複習 */}
            <Link
              href="/practice"
              className="flex items-center gap-3 bg-white rounded-2xl p-4 border border-emerald-200 hover:border-emerald-400 hover:shadow-md transition-all group"
            >
              <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0 group-hover:bg-emerald-200 transition-colors">
                <Target className="h-5 w-5 text-emerald-600" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-900">開始今日複習</p>
                <p className="text-xs text-slate-500 truncate">AI 智慧配題 · 針對弱點加強</p>
              </div>
            </Link>
            {/* CTA 2 — 查看學習路徑 */}
            <Link
              href="/knowledge"
              className="flex items-center gap-3 bg-white rounded-2xl p-4 border border-indigo-200 hover:border-indigo-400 hover:shadow-md transition-all group"
            >
              <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 group-hover:bg-indigo-200 transition-colors">
                <Map className="h-5 w-5 text-indigo-600" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-900">查看學習路徑</p>
                <p className="text-xs text-slate-500 truncate">知識版圖 · 解鎖節點</p>
              </div>
            </Link>
            {/* CTA 3 — 複習錯題 */}
            <Link
              href="/review"
              className="flex items-center gap-3 bg-white rounded-2xl p-4 border border-rose-200 hover:border-rose-400 hover:shadow-md transition-all group"
            >
              <div className="h-10 w-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0 group-hover:bg-rose-200 transition-colors">
                <Flame className="h-5 w-5 text-rose-600" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-900">複習錯題</p>
                <p className="text-xs text-slate-500 truncate">錯題本 · 鞏固弱點</p>
              </div>
            </Link>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════
            中段 — 左欄 + 右欄 雙欄佈局
            ═══════════════════════════════════════════════════════════ */}
        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 items-start">

          {/* ── 左欄 ── */}
          <div className="lg:col-span-2 space-y-8">

            {/* 中段 Section 4 — 待辦提醒（摺疊：最多 3，超過顯查看全部） */}
            {allTodos.length > 0 && (
              <section>
                <h2 className="text-[18px] font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-indigo-500" /> 待辦提醒
                </h2>
                <div className="space-y-3">
                  {visibleTodos.map(item => {
                    const iconMap = {
                      error_review: TrendingUp,
                      incomplete_exam: BookOpen,
                      new_resource: FileText,
                      achievement: Sparkles,
                    };
                    const colorMap = {
                      error_review: 'bg-rose-100 text-rose-600',
                      incomplete_exam: 'bg-blue-100 text-blue-600',
                      new_resource: 'bg-emerald-100 text-emerald-600',
                      achievement: 'bg-amber-100 text-amber-600',
                    };
                    const Icon = iconMap[item.type];
                    const colorClass = colorMap[item.type];

                    return (
                      <div key={item.id} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 flex items-center justify-between hover:shadow-md transition-shadow cursor-pointer">
                        <div className="flex items-center gap-4">
                          <div className={`h-10 w-10 rounded-full flex items-center justify-center ${colorClass}`}>
                            <Icon className="h-5 w-5" />
                          </div>
                          <div>
                            <h4 className="font-medium text-slate-900">{item.title}</h4>
                            <p className="text-sm text-slate-500">{item.description}</p>
                          </div>
                        </div>
                        <Link href={item.link} className="text-sm font-medium text-emerald-600 hover:text-emerald-700 shrink-0">
                          {item.linkLabel} &rarr;
                        </Link>
                      </div>
                    );
                  })}
                </div>
                {/* 摺疊 / 展開按鈕 */}
                {allTodos.length > TODO_FOLD_LIMIT && (
                  <button
                    onClick={() => setTodoExpanded(prev => !prev)}
                    className="mt-3 flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-emerald-600 transition-colors"
                  >
                    {todoExpanded ? (
                      <><ChevronUp className="h-4 w-4" /> 收起</>
                    ) : (
                      <><ChevronDown className="h-4 w-4" /> 查看全部 {allTodos.length} 個</>
                    )}
                  </button>
                )}
              </section>
            )}

            {/* 中段 Section 5 — 每日任務 */}
            <section>
              <h2 className="text-[18px] font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-500" /> 每日任務
              </h2>
              <div className="space-y-2">
                {(data.dailyQuests || []).map(quest => (
                  <DailyQuestCard key={quest.id} quest={quest} />
                ))}
                {(data.dailyQuests || []).length === 0 && (
                  <p className="text-sm text-slate-400 py-3 text-center">今天已完成所有任務！</p>
                )}
              </div>
            </section>
          </div>

          {/* ── 右欄 ── */}
          <div className="space-y-8">
            {/* Schedule Week Card */}
            <ScheduleWeekCard isAuthenticated={isAuthenticated} />

            {/* 中段 Section 6 — 學習狀態（領域雷達圖 + 信心度趨勢） */}
            <section className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
              <h2 className="text-[18px] font-bold text-slate-900 mb-4">學習狀態</h2>

              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-500">整體答對率</span>
                  <span className="font-bold text-slate-900">{data.stats.overallAccuracy}%</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${data.stats.overallAccuracy}%` }} />
                </div>
              </div>

              <DomainRadarChart
                domains={data.domainStrengths}
                onDomainClick={activeSubjectId ? (_d, nodeId) => {
                  const qs = nodeId ? `?nodeId=${nodeId}` : '';
                  window.location.href = `/knowledge${qs}`;
                } : undefined}
              />

              {/* T63 (Sprint 8 L30) — 信心度校準趨勢（Feature 20） */}
              {calibration && calibration.exam_count > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-bold text-slate-800">信心度校準</h3>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      calibration.calibration_rate >= 0.8 ? 'bg-emerald-100 text-emerald-700' :
                      calibration.calibration_rate >= 0.5 ? 'bg-amber-100 text-amber-700' :
                      'bg-rose-100 text-rose-700'
                    }`}>
                      {calibration.status} {Math.round(calibration.calibration_rate * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">
                    最近 {calibration.exam_count} 場測驗中，「自信」答對率
                  </p>
                  {/* 簡易 sparkline：每場一根長條 */}
                  <div className="flex items-end gap-1 h-12">
                    {calibration.trend.slice().reverse().map((t, idx) => (
                      <div
                        key={t.exam_id}
                        className="flex-1 rounded-t transition-all"
                        style={{
                          height: `${Math.max(10, t.calibration_rate * 100)}%`,
                          backgroundColor:
                            t.calibration_rate >= 0.8 ? '#10b981' :
                            t.calibration_rate >= 0.5 ? '#f59e0b' :
                            '#f43f5e',
                          opacity: 0.4 + (idx / calibration.trend.length) * 0.6,
                        }}
                        title={`${Math.round(t.calibration_rate * 100)}%${t.submitted_at ? ' · ' + new Date(t.submitted_at).toLocaleDateString() : ''}`}
                      />
                    ))}
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>較舊</span>
                    <span>最近</span>
                  </div>
                </div>
              )}

              {activeSubjectId && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <Link
                    href="/knowledge"
                    className="flex items-center justify-center gap-1.5 text-xs text-emerald-600 hover:text-emerald-800 py-2 rounded-lg hover:bg-emerald-50 transition"
                  >
                    🗺️ 開啟知識地圖
                  </Link>
                </div>
              )}
            </section>

            {/* 中段 Section 7 — 知識版圖解鎖進度（#6 Completion Framework） */}
            {(() => {
              let percent: number;
              let sweetSpotReached: boolean;
              let showMarginalUtilityNudge: boolean;
              let unlockedBadges: string[];

              if (completion) {
                percent = completion.sweet_spot_progress;
                sweetSpotReached = percent >= 85;
                showMarginalUtilityNudge = completion.should_show_marginal_utility_nudge;
                unlockedBadges = completion.badges_unlocked;
              } else {
                const completionNodes: CompletionNode[] = (data.domainStrengths || []).map(
                  (d: { domain?: string; score?: number; name?: string }) => ({
                    id: d.domain || d.name || 'unknown',
                    subject_id: activeSubjectId,
                    mastery_rate: Math.round((d.score || 0) * 100),
                    frequency: 'medium' as const,
                  })
                );
                const result = calcCompletion(completionNodes);
                percent = result.percent;
                sweetSpotReached = result.sweetSpotReached;
                showMarginalUtilityNudge = result.showMarginalUtilityNudge;
                unlockedBadges = result.unlockedBadges;
              }

              return (
                <section className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-[18px] font-bold text-slate-900">知識版圖解鎖進度</h2>
                    <Link
                      href="/help/coverage-explained"
                      className="text-[11px] text-slate-500 hover:text-emerald-600 underline underline-offset-2"
                    >
                      為何不是 100%？
                    </Link>
                  </div>

                  {completionLoading && (
                    <div className="h-6 bg-slate-100 rounded animate-pulse mb-4" />
                  )}

                  {!completionLoading && completionError === 'server_error' && (
                    <div className="mb-4 p-4 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-center">
                      <p className="text-xs text-slate-500 mb-2">進度載入失敗，請稍後再試</p>
                      <button
                        onClick={() => loadCompletion(activeSubjectId)}
                        className="text-xs font-medium text-emerald-600 hover:text-emerald-800 underline"
                      >
                        重試
                      </button>
                    </div>
                  )}

                  {!completionLoading && completionError === 'not_found' && (
                    <div className="mb-4 p-4 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-center">
                      <p className="text-sm text-slate-600 mb-2">尚未找到此科目的進度資料</p>
                      <Link href="/account" className="text-xs font-semibold text-emerald-600 hover:text-emerald-800 underline">
                        前往帳號設定 →
                      </Link>
                    </div>
                  )}

                  {!completionLoading && completionError !== 'server_error' && completionError !== 'not_found' && (
                    <div className="mb-4">
                      <CompletionProgressBar
                        percent={percent}
                        sweetSpotReached={sweetSpotReached}
                        label={subjects.find(s => s.id === activeSubjectId)?.subjectName}
                      />
                    </div>
                  )}

                  {!completionLoading && !completionError && showMarginalUtilityNudge && (
                    <div className="mb-4">
                      <MarginalUtilityNudge percent={percent} show={showMarginalUtilityNudge} />
                    </div>
                  )}

                  {!completionLoading && !completionError && (
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <p className="text-xs text-slate-500 mb-3">里程碑徽章</p>
                      <BadgeShelf unlockedBadges={unlockedBadges as any} />
                    </div>
                  )}
                </section>
              );
            })()}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            底部 Section 8 — 文字連結區 + 幫助與反饋
            ═══════════════════════════════════════════════════════════ */}
        <div className="mt-8 pt-6 border-t border-slate-100">
          {/* 主要導航連結 */}
          <div className="flex justify-center items-center gap-6 flex-wrap mb-4">
            <Link
              href="/knowledge"
              className="text-sm font-bold text-slate-600 hover:text-emerald-600 flex items-center gap-1.5 transition-colors"
            >
              <Map className="h-4 w-4" /> 管理資源
            </Link>
            <span className="text-slate-200 text-sm">|</span>
            <Link
              href="/account/weekly-reports"
              className="text-sm font-bold text-slate-600 hover:text-emerald-600 flex items-center gap-1.5 transition-colors"
            >
              <BarChart2 className="h-4 w-4" /> 週報
            </Link>
            <span className="text-slate-200 text-sm">|</span>
            <Link
              href="/account"
              className="text-sm font-bold text-slate-600 hover:text-emerald-600 flex items-center gap-1.5 transition-colors"
            >
              <Settings className="h-4 w-4" /> 設定
            </Link>
          </div>
          {/* 幫助與反饋 */}
          <div className="flex justify-center items-center gap-4 flex-wrap">
            <Link href="/help/study-guide" className="text-xs text-slate-400 hover:text-emerald-600 flex items-center gap-1 underline underline-offset-2 transition-colors">
              <BookOpen className="h-3.5 w-3.5" /> 備考使用指南
            </Link>
            <span className="text-slate-200 text-xs">|</span>
            <Link href="/feedback" className="text-xs text-slate-400 hover:text-emerald-600 flex items-center gap-1 transition-colors">
              <MessageSquare className="h-3.5 w-3.5" /> 意見反饋
            </Link>
          </div>
        </div>
      </div>

      {/* Add Subject Modal */}
      {showAddSubject && (
        <SubjectPickerModal
          excludeSubjectIds={subjects.map(s => s.subjectId)}
          onConfirm={handleAddSubject}
          onClose={() => setShowAddSubject(false)}
        />
      )}
    </>
  );
}
