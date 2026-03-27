'use client';

import React, { useState } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  FileText, 
  Image as ImageIcon, 
  MessageSquare, 
  User, 
  CheckCircle2, 
  XCircle,
  Clock,
  Activity,
  Zap,
  Filter,
  Search,
  MoreVertical,
  ArrowRight
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Mock Data
const moderationQueue = [
  { id: 'mod_1', user: '張小明', type: 'file', content: 'PMP_Exam_Dump_2026.pdf', reason: '異常大檔案 (150MB)', status: 'flagged', time: '10 分鐘前' },
  { id: 'mod_2', user: '李華', type: 'image', content: 'math_problem_01.png', reason: 'OCR 辨識失敗', status: 'pending', time: '25 分鐘前' },
  { id: 'mod_3', user: '王大同', type: 'chat', content: '如何破解系統限制？', reason: '關鍵字觸發 (破解)', status: 'flagged', time: '1 小時前' },
  { id: 'mod_4', user: '陳美玲', type: 'file', content: 'Notes.md', reason: '內容檢舉 (版權)', status: 'reported', time: '2 小時前' },
];

const abuseMonitoring = [
  { id: 'abs_1', user: 'usr_123', metric: '超綱問答轟炸', count: '15 次 / 10 分鐘', status: 'cooling', time: '即時' },
  { id: 'abs_2', user: 'usr_456', metric: 'Token 異常消耗', count: '2.5M / 1 小時', status: 'flagged', time: '5 分鐘前' },
  { id: 'abs_3', user: 'usr_789', metric: '高頻 API 呼叫', count: '500 次 / 1 分鐘', status: 'blocked', time: '15 分鐘前' },
];

const reportStats = [
  { label: '待處理檢舉', value: '12', color: 'rose' },
  { label: '今日自動標記', value: '45', color: 'amber' },
  { label: '已冷卻用戶', value: '8', color: 'indigo' },
  { label: '系統誤報率', value: '1.2%', color: 'emerald' },
];

const contentReviewQueue = [
  { id: 1, type: '使用者上傳', content: '疑似包含版權內容', reporter: '系統自動', status: 'pending' as const, date: '2026-03-26' },
  { id: 2, type: 'AI 對話', content: '偵測到超出範圍的提問', reporter: '系統自動', status: 'pending' as const, date: '2026-03-25' },
];

export default function ModerationPage() {
  const [activeTab, setActiveTab] = useState('queue');

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">內容與安全審核</h1>
          <p className="text-slate-500">防止平台濫用，維護內容品質與合規</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center gap-2">
            審核日誌
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {reportStats.map((stat) => (
          <div key={stat.label} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{stat.label}</p>
            <p className={cn(
              "text-2xl font-bold",
              stat.color === 'rose' && "text-rose-600",
              stat.color === 'amber' && "text-amber-600",
              stat.color === 'indigo' && "text-indigo-600",
              stat.color === 'emerald' && "text-emerald-600"
            )}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Content Review Queue */}
      <section className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="font-bold text-slate-900 flex items-center gap-2">
            <FileText className="h-5 w-5 text-indigo-500" /> 內容審查佇列
          </h2>
        </div>
        <div className="divide-y divide-slate-100">
          {contentReviewQueue.map((item) => (
            <div key={item.id} className="p-6 hover:bg-slate-50/50 transition-all">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={cn(
                      "text-xs font-bold px-2 py-1 rounded-lg",
                      item.type === '使用者上傳' ? "bg-blue-50 text-blue-600" : "bg-amber-50 text-amber-600"
                    )}>
                      {item.type}
                    </span>
                    <span className="text-xs font-bold px-2 py-1 rounded-lg bg-slate-100 text-slate-600">
                      {item.status === 'pending' ? '待審核' : item.status}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-slate-900 mb-1">{item.content}</p>
                  <p className="text-xs text-slate-500">
                    回報者：<span className="font-medium text-slate-700">{item.reporter}</span> &middot; {item.date}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button className="px-3 py-1.5 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" /> 通過
                  </button>
                  <button className="px-3 py-1.5 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center gap-1.5">
                    <XCircle className="h-3.5 w-3.5" /> 移除
                  </button>
                  <button className="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50 transition-all flex items-center gap-1.5">
                    <Search className="h-3.5 w-3.5" /> 查看詳情
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Moderation Queue */}
        <section className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
            <h2 className="font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-500" /> 待審核佇列
            </h2>
            <div className="flex gap-2">
              <button className="p-1.5 bg-slate-50 border-transparent hover:bg-slate-100 rounded-lg transition-all">
                <Filter className="h-4 w-4 text-slate-500" />
              </button>
            </div>
          </div>
          <div className="divide-y divide-slate-100">
            {moderationQueue.map((item) => (
              <div key={item.id} className="p-6 hover:bg-slate-50/50 transition-all group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "h-12 w-12 rounded-2xl flex items-center justify-center",
                      item.type === 'file' && "bg-blue-50 text-blue-600",
                      item.type === 'image' && "bg-emerald-50 text-emerald-600",
                      item.type === 'chat' && "bg-amber-50 text-amber-600"
                    )}>
                      {item.type === 'file' && <FileText className="h-6 w-6" />}
                      {item.type === 'image' && <ImageIcon className="h-6 w-6" />}
                      {item.type === 'chat' && <MessageSquare className="h-6 w-6" />}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">{item.content}</h3>
                      <p className="text-xs text-slate-500">由 <span className="font-bold text-slate-700">{item.user}</span> 上傳 • {item.time}</p>
                    </div>
                  </div>
                  <span className={cn(
                    "text-xs font-bold px-2 py-1 rounded-lg",
                    item.status === 'flagged' && "bg-rose-50 text-rose-600",
                    item.status === 'reported' && "bg-amber-50 text-amber-600",
                    item.status === 'pending' && "bg-slate-100 text-slate-600"
                  )}>
                    {item.status === 'flagged' && "系統標記"}
                    {item.status === 'reported' && "用戶檢舉"}
                    {item.status === 'pending' && "待處理"}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4">
                  <p className="text-sm text-slate-600 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    原因：<span className="font-medium text-slate-900">{item.reason}</span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2">
                    <ShieldCheck className="h-4 w-4" /> 通過審核
                  </button>
                  <button className="flex-1 py-2 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center justify-center gap-2">
                    <XCircle className="h-4 w-4" /> 刪除並警告
                  </button>
                  <button className="p-2 bg-slate-50 border border-slate-100 text-slate-400 hover:text-slate-900 rounded-xl transition-all">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full py-4 text-sm font-bold text-slate-500 hover:text-slate-900 bg-slate-50/50 transition-all border-t border-slate-100">
            查看所有佇列 &rarr;
          </button>
        </section>

        {/* AI Abuse Monitoring */}
        <div className="space-y-8">
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" /> AI 濫用監控
            </h2>
            <div className="space-y-4">
              {abuseMonitoring.map((abuse) => (
                <div key={abuse.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all group">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-slate-400" />
                      <span className="text-sm font-bold text-slate-900">{abuse.user}</span>
                    </div>
                    <span className={cn(
                      "text-[10px] font-bold px-1.5 py-0.5 rounded uppercase",
                      abuse.status === 'cooling' && "bg-amber-100 text-amber-600",
                      abuse.status === 'blocked' && "bg-rose-100 text-rose-600",
                      abuse.status === 'flagged' && "bg-blue-100 text-blue-600"
                    )}>
                      {abuse.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-1">{abuse.metric}</p>
                  <div className="flex justify-between items-end">
                    <p className="text-sm font-bold text-slate-900">{abuse.count}</p>
                    <button className="text-xs font-bold text-emerald-600 hover:text-emerald-700 transition-all">
                      查看日誌
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-6 py-3 text-sm font-bold text-slate-500 hover:text-slate-900 transition-all">
              查看所有異常 &rarr;
            </button>
          </section>

          {/* Quick Actions */}
          <section className="bg-slate-900 p-6 rounded-3xl shadow-xl shadow-slate-900/20">
            <h2 className="font-bold text-white mb-4">管理員快速操作</h2>
            <div className="space-y-2">
              <button className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all group">
                <span className="text-sm font-medium">發布全站公告</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-all" />
              </button>
              <button className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all group">
                <span className="text-sm font-medium">重置 AI 流量限制</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-all" />
              </button>
              <button className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all group">
                <span className="text-sm font-medium">清理系統暫存檔</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-all" />
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
