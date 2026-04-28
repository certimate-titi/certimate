/**
 * @file ScheduleWeekCard — 儀表板「學習排程」雙層卡 Widget（Spec 09 cross-ref）。
 *
 * 上半：各科目今日排程（模式 badge、距考日、待複習數、推薦數、開始按鈕）。
 * 下半：本週 7 日橫條，每格顯示待複習熱度（由 next_review_at 前端聚合計算）。
 * 右上角「前往完整」Link → /schedule。
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Calendar, ArrowRight, Zap, BookOpen, AlertCircle, Loader2 } from 'lucide-react';
import { scheduleService, type ScheduleRecommendation } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

/** 模式 meta（與 /schedule/page.tsx 共用定義，不另開 shared util 以避免跨層衝突）。 */
const MODE_META: Record<string, { label: string; emoji: string; color: string }> = {
  sprint:   { label: 'Sprint',   emoji: '⚡', color: 'bg-rose-50 text-rose-700 border-rose-200' },
  standard: { label: 'Standard', emoji: '📚', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  mastery:  { label: 'Mastery',  emoji: '🧭', color: 'bg-blue-50 text-blue-700 border-blue-200' },
};

/** 今日起 7 天標籤（今 / 明 / 星期X）。 */
function buildWeekLabels(): { date: Date; label: string }[] {
  const result: { date: Date; label: string }[] = [];
  const dayNames = ['日', '一', '二', '三', '四', '五', '六'];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now);
    d.setDate(now.getDate() + i);
    const label = i === 0 ? '今' : i === 1 ? '明' : `${dayNames[d.getDay()]}`;
    result.push({ date: d, label });
  }
  return result;
}

/**
 * 前端聚合 7 日熱度。
 * 規則：next_review_at 落在該天 → +pending_questions；null → 均勻散 7 天。
 */
function buildWeekHeatmap(
  subjects: ScheduleRecommendation[],
  weekDays: { date: Date; label: string }[],
): number[] {
  const counts = new Array<number>(7).fill(0);
  for (const s of subjects) {
    if (s.next_review_at) {
      const reviewDate = new Date(s.next_review_at);
      for (let i = 0; i < 7; i++) {
        const d = weekDays[i].date;
        if (
          reviewDate.getFullYear() === d.getFullYear() &&
          reviewDate.getMonth() === d.getMonth() &&
          reviewDate.getDate() === d.getDate()
        ) {
          counts[i] += s.pending_questions;
          break;
        }
      }
    } else {
      // 均勻散到 7 天
      const perDay = Math.ceil(s.pending_questions / 7);
      for (let i = 0; i < 7; i++) {
        counts[i] += perDay;
      }
    }
  }
  return counts;
}

/** 根據題數回傳熱度色階 class。 */
function heatColor(count: number, max: number): string {
  if (count === 0 || max === 0) return 'bg-slate-100';
  const ratio = count / max;
  if (ratio < 0.25) return 'bg-emerald-100';
  if (ratio < 0.5)  return 'bg-emerald-200';
  if (ratio < 0.75) return 'bg-emerald-400';
  return 'bg-emerald-600';
}

/** 熱度文字顏色（深色背景用白字）。 */
function heatTextColor(count: number, max: number): string {
  if (count === 0 || max === 0) return 'text-slate-400';
  const ratio = count / max;
  return ratio >= 0.75 ? 'text-white' : 'text-slate-700';
}

/**
 * ScheduleWeekCard 元件 props。
 * isAuthenticated 由 DashboardPage 傳入，避免元件內重複監聽 auth 狀態。
 */
export interface ScheduleWeekCardProps {
  /** 外部傳入 auth 狀態，已驗證才呼叫 API。 */
  isAuthenticated: boolean;
}

/**
 * 儀表板「學習排程」雙層卡。
 *
 * 上半顯示各科目今日排程卡，下半顯示本週 7 日熱度橫條。
 */
export default function ScheduleWeekCard({ isAuthenticated }: ScheduleWeekCardProps) {
  const [subjects, setSubjects] = useState<ScheduleRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const weekDays = buildWeekLabels();

  useEffect(() => {
    if (!isAuthenticated) return;
    scheduleService.getRecommendations()
      .then((res) => setSubjects(res.subjects || []))
      .catch((e: unknown) => {
        const err = e as { message?: string };
        setError(err?.message || '載入排程失敗');
      })
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const heatmap = buildWeekHeatmap(subjects, weekDays);
  const maxHeat = Math.max(...heatmap, 1);

  return (
    <section className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-emerald-500" />
          學習排程
        </h2>
        <Link
          href="/schedule"
          className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-800 font-medium transition-colors"
        >
          前往完整 <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="flex items-start gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs mb-4">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && subjects.length === 0 && (
        <div className="text-center py-6">
          <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-xs text-slate-500 mb-3">尚無備考科目排程</p>
          <Link
            href="/schedule"
            className="text-xs font-medium text-emerald-600 hover:text-emerald-800 underline"
          >
            前往設定
          </Link>
        </div>
      )}

      {/* Subject Cards */}
      {!loading && !error && subjects.length > 0 && (
        <div className="space-y-3 mb-5">
          {subjects.map((s) => {
            const meta = MODE_META[s.mode] || MODE_META.standard;
            const daysToExam = s.exam_date
              ? Math.ceil((new Date(s.exam_date).getTime() - Date.now()) / 86_400_000)
              : null;
            const examUrgent = daysToExam !== null && daysToExam < 14;

            return (
              <div
                key={s.subject_id}
                className="border border-slate-100 rounded-xl p-3 hover:border-slate-200 transition-colors"
              >
                {/* Row 1: Subject name + mode badge */}
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-slate-900 truncate">{s.subject_name}</p>
                    {daysToExam !== null && (
                      <p className="text-[11px] mt-0.5">
                        距考日{' '}
                        <span className={examUrgent ? 'text-rose-600 font-bold' : 'text-slate-500'}>
                          {daysToExam} 天
                        </span>
                      </p>
                    )}
                  </div>
                  <span className={`shrink-0 px-1.5 py-0.5 rounded-full text-[10px] font-medium border ${meta.color}`}>
                    {meta.emoji} {meta.label}
                  </span>
                </div>

                {/* Row 2: Stats + CTA */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-3 text-[11px] text-slate-500">
                    <span>
                      待複習 <b className="text-slate-800">{s.pending_questions}</b>
                    </span>
                    <span>
                      推薦 <b className="text-emerald-600">{s.recommended_count}</b>
                    </span>
                  </div>
                  <Link
                    href={`/exam/setup?subjectId=${s.subject_id}&from=schedule`}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-emerald-500 text-white rounded-lg text-[11px] font-bold hover:bg-emerald-600 transition-colors shrink-0"
                  >
                    <Zap className="w-3 h-3" /> 開始今日複習
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 7-Day Heatmap */}
      {!loading && (
        <>
          <div className="border-t border-slate-100 pt-4">
            <p className="text-[11px] font-bold text-slate-500 mb-2 uppercase tracking-wide">本週節奏</p>
            <div className="grid grid-cols-7 gap-1">
              {weekDays.map((day, i) => {
                const count = heatmap[i];
                const isToday = i === 0;
                return (
                  <div key={i} className="flex flex-col items-center gap-1">
                    {/* Day cell */}
                    <div
                      className={`
                        w-full aspect-square rounded-lg flex flex-col items-center justify-center text-center
                        ${heatColor(count, maxHeat)}
                        ${isToday ? 'ring-2 ring-emerald-400 ring-offset-1' : ''}
                      `}
                      title={count > 0 ? `${count} 題待複習` : '無待複習'}
                    >
                      <span className={`text-[10px] font-bold leading-none ${heatTextColor(count, maxHeat)}`}>
                        {day.label}
                      </span>
                      {count > 0 && (
                        <span className={`text-[9px] leading-none mt-0.5 ${heatTextColor(count, maxHeat)}`}>
                          {count}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-end gap-1 mt-2">
              <span className="text-[9px] text-slate-400">少</span>
              {['bg-slate-100', 'bg-emerald-100', 'bg-emerald-200', 'bg-emerald-400', 'bg-emerald-600'].map((c, i) => (
                <div key={i} className={`w-3 h-3 rounded-sm ${c}`} />
              ))}
              <span className="text-[9px] text-slate-400">多</span>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
