'use client';

import React, { useState } from 'react';
import { Zap, Trash2, Award, Calculator, BellRing, Clock, RefreshCw, Sparkles, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { retirementService } from '@/lib/api/services';

type JobKey =
  | 'scan' | 'hardDelete' | 'postResultScan' | 'recalculate'
  | 'notifyResultDay' | 'notifyResultReminder' | 'notifyResultDefault' | 'crossRecommend';

interface JobDef {
  key: JobKey;
  title: string;
  description: string;
  icon: React.ElementType;
  color: string;
  section: 'retirement' | 'notification';
  confirm?: string;
}

const JOBS: JobDef[] = [
  { key: 'scan', title: '退場掃描', description: '掃描 ai_used_count 達閾值的 AI 題目標記 retired', icon: Zap, color: 'yellow', section: 'retirement' },
  { key: 'hardDelete', title: '硬刪除過期題', description: '移除退場超過保留期的題目', icon: Trash2, color: 'red', section: 'retirement', confirm: '確定執行硬刪除？此操作不可逆' },
  { key: 'postResultScan', title: '放榜後掃描', description: '放榜後標記題目 post_result 狀態', icon: Award, color: 'purple', section: 'retirement' },
  { key: 'recalculate', title: '重算可用題數', description: '重算各科目的 available_questions 統計', icon: Calculator, color: 'blue', section: 'retirement' },
  { key: 'notifyResultDay', title: '放榜日通知', description: '發送放榜當日通知給訂閱該科目的用戶', icon: BellRing, color: 'pink', section: 'notification' },
  { key: 'notifyResultReminder', title: '放榜提醒', description: '發送放榜前 N 天提醒', icon: Clock, color: 'indigo', section: 'notification' },
  { key: 'notifyResultDefault', title: '放榜違約補償', description: '處理已放榜但尚未填寫結果的用戶', icon: RefreshCw, color: 'orange', section: 'notification' },
  { key: 'crossRecommend', title: '跨科目推薦', description: '產生放榜後的跨科目推薦', icon: Sparkles, color: 'emerald', section: 'notification' },
];

type JobResult = { status: 'success' | 'error'; data?: any; message?: string; at: string };

export default function RetirementAdminPage() {
  const [running, setRunning] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, JobResult>>({});

  const handleRun = async (job: JobDef) => {
    if (job.confirm && !confirm(job.confirm)) return;
    setRunning((s) => ({ ...s, [job.key]: true }));
    try {
      const fn = (retirementService as any)[job.key];
      const data = await fn();
      setResults((s) => ({ ...s, [job.key]: { status: 'success', data, at: new Date().toISOString() } }));
    } catch (e: any) {
      setResults((s) => ({ ...s, [job.key]: { status: 'error', message: e?.message || '執行失敗', at: new Date().toISOString() } }));
    } finally {
      setRunning((s) => ({ ...s, [job.key]: false }));
    }
  };

  const renderJobCard = (job: JobDef) => {
    const Icon = job.icon;
    const isRunning = running[job.key];
    const r = results[job.key];
    return (
      <div key={job.key} className="bg-white border border-gray-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <div className={`w-10 h-10 rounded-lg bg-${job.color}-100 text-${job.color}-600 flex items-center justify-center flex-shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm text-gray-900">{job.title}</div>
            <div className="text-xs text-gray-500 mt-0.5">{job.description}</div>
            <button
              onClick={() => handleRun(job)}
              disabled={isRunning}
              className="mt-3 flex items-center gap-2 px-3 py-1.5 text-xs bg-gray-900 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
            >
              {isRunning ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
              執行
            </button>
            {r && (
              <div className={`mt-3 p-2 rounded text-xs ${r.status === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                <div className="flex items-center gap-1 mb-1">
                  {r.status === 'success' ? <CheckCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                  <span className="font-medium">{r.status === 'success' ? '成功' : '失敗'}</span>
                  <span className="text-gray-400 ml-auto">{new Date(r.at).toLocaleTimeString('zh-TW')}</span>
                </div>
                <pre className="whitespace-pre-wrap break-all text-[10px] max-h-32 overflow-auto">
                  {r.status === 'success' ? JSON.stringify(r.data, null, 2) : r.message}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">放榜 & 退場管理</h1>
        <p className="text-sm text-gray-500 mt-1">手動觸發 AI 題退場流程與放榜通知（通常由 cron 自動執行）</p>
      </div>

      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">AI 題退場</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {JOBS.filter((j) => j.section === 'retirement').map(renderJobCard)}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">放榜通知</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {JOBS.filter((j) => j.section === 'notification').map(renderJobCard)}
        </div>
      </section>
    </div>
  );
}
