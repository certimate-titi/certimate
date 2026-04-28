/**
 * @file 路由 `/account/weekly-reports` — 我的歷史週報列表（Spec 14）。
 *
 * 列出使用者所有自動生成的週學習報告，含學習時數、完成測驗、答題數、
 * AI 整理的進度摘要。可手動觸發產生本週報告（cron 失誤時手動補）。
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, FileText, Loader2, RefreshCw, Calendar, BookOpen, Clock, ListChecks } from 'lucide-react';
import { communityService, type WeeklyReportItem as WeeklyReport } from '@/lib/api/services';

export default function WeeklyReportsPage() {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await communityService.getWeeklyReports();
      setReports(res.reports || []);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg(`載入失敗：${err?.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, []);

  const handleGenerate = async () => {
    if (!confirm('手動觸發產生本週報告？\n\n通常每週日凌晨自動產生，僅在 cron 失誤或測試時手動補。')) return;
    setGenerating(true);
    setMsg(null);
    try {
      const res = await communityService.generateWeeklyReport();
      setMsg(`✅ ${res.message}`);
      fetch();
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg(`❌ ${err?.message || '產生失敗'}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <Link href="/account" className="p-2 rounded-lg hover:bg-gray-100 text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <FileText className="w-6 h-6 text-emerald-500" />
        <h1 className="text-2xl font-bold text-slate-900">我的歷史週報</h1>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="ml-auto flex items-center gap-1 px-3 py-1.5 text-xs border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-50"
        >
          {generating ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
          產生本週報告
        </button>
      </div>
      <p className="text-sm text-slate-500 mb-6 leading-relaxed ml-11">
        系統每週日凌晨自動為活躍用戶生成 AI 進度摘要，含學習時數、完成測驗、答題量。
      </p>

      {msg && (
        <div className="mb-4 px-3 py-2 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700">
          {msg}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500 font-medium mb-1">尚無週報</p>
          <p className="text-xs text-slate-400">
            活躍用戶（每週至少做 1 份測驗）會在週日自動收到報告。
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <div key={r.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-sm transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  {r.week_start.slice(5, 10)} – {r.week_end.slice(5, 10)}
                </h3>
                <span className="text-[10px] text-slate-400">
                  {new Date(r.week_start).getFullYear()} 第 {Math.ceil((new Date(r.week_start).getTime() - new Date(new Date(r.week_start).getFullYear(), 0, 1).getTime()) / 86400_000 / 7)} 週
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="bg-emerald-50 rounded p-2 text-center">
                  <Clock className="w-3 h-3 text-emerald-600 mx-auto mb-1" />
                  <div className="text-lg font-bold text-emerald-700">{r.study_hours.toFixed(1)}</div>
                  <div className="text-[10px] text-emerald-600">學習時數</div>
                </div>
                <div className="bg-blue-50 rounded p-2 text-center">
                  <BookOpen className="w-3 h-3 text-blue-600 mx-auto mb-1" />
                  <div className="text-lg font-bold text-blue-700">{r.exams_completed}</div>
                  <div className="text-[10px] text-blue-600">完成測驗</div>
                </div>
                <div className="bg-amber-50 rounded p-2 text-center">
                  <ListChecks className="w-3 h-3 text-amber-600 mx-auto mb-1" />
                  <div className="text-lg font-bold text-amber-700">{r.questions_answered}</div>
                  <div className="text-[10px] text-amber-600">答題數</div>
                </div>
              </div>
              {r.progress_summary && (
                <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-line bg-slate-50 rounded p-3">
                  {r.progress_summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
