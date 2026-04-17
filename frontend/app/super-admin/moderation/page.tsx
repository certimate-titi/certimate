'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
  ArrowRight,
  Mail,
  Send,
  Eye
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

import { superAdminService } from '@/lib/api/services';

export default function ModerationPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('queue');
  const [queueFilter, setQueueFilter] = useState('all');
  const [moderationQueue, setModerationQueue] = useState<{ id: string; user: string; type: string; content: string; reason: string; status: string; time: string }[]>([]);
  const [abuseMonitoring, setAbuseMonitoring] = useState<{ id: string; user: string; metric: string; count: string; status: string; time: string }[]>([]);
  const [contentReviewQueue, setContentReviewQueue] = useState<{ id: number; type: string; content: string; reporter: string; status: 'pending' | 'resolved'; date: string }[]>([]);
  const [detailModal, setDetailModal] = useState<{ type: string; content: string; user?: string; reason?: string; date?: string; reporter?: string; id?: string | number; source: 'content' | 'queue' } | null>(null);

  // Feedback state
  type FeedbackItem = { feedback_id: string; type: string; subject: string; content_preview: string; content: string; status: string; user_id: string; user_email: string; admin_reply: string; attachment_urls: string[]; created_at: string | null; resolved_at: string | null };
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [feedbackFilter, setFeedbackFilter] = useState('');
  const [feedbackStats, setFeedbackStats] = useState<{ total_count: number; pending_count: number; reviewing_count: number; resolved_count: number; top_category: string | null; avg_resolve_hours: number } | null>(null);
  const [feedbackModal, setFeedbackModal] = useState<FeedbackItem | null>(null);
  const [adminReply, setAdminReply] = useState('');
  const [feedbackUpdating, setFeedbackUpdating] = useState(false);

  const loadFeedbacks = (status?: string) => {
    superAdminService.getAdminFeedbacks(status || undefined).then(res => {
      if (Array.isArray(res?.feedbacks)) setFeedbacks(res.feedbacks);
    }).catch(() => {});
  };

  const [reportStats, setReportStats] = useState([
    { label: '待處理檢舉', value: '--', color: 'rose' },
    { label: '今日自動標記', value: '--', color: 'amber' },
    { label: '已冷卻用戶', value: '--', color: 'indigo' },
    { label: '系統誤報率', value: '--', color: 'emerald' },
  ]);

  useEffect(() => {
    superAdminService.getModerationStats().then(stats => {
      setReportStats([
        { label: '待處理檢舉', value: String(stats.pending_reports ?? 0), color: 'rose' },
        { label: '今日自動標記', value: String(stats.auto_flagged_today ?? 0), color: 'amber' },
        { label: '已冷卻用戶', value: String(stats.cooled_users ?? 0), color: 'indigo' },
        { label: '系統誤報率', value: stats.false_positive_rate ?? '--', color: 'emerald' },
      ]);
    }).catch(() => {});
    superAdminService.getModerationQueue().then(res => {
      if (Array.isArray(res?.items)) setModerationQueue(res.items);
    }).catch(() => {});
    superAdminService.getAbuseMonitoring().then(res => {
      if (Array.isArray(res?.items)) setAbuseMonitoring(res.items);
    }).catch(() => {});
    superAdminService.getContentReviewQueue().then(res => {
      if (Array.isArray(res?.items)) setContentReviewQueue(res.items);
    }).catch(() => {});
    loadFeedbacks();
    superAdminService.getAdminFeedbackStats().then(stats => {
      setFeedbackStats(stats);
    }).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">內容與安全審核</h1>
          <p className="text-slate-500">防止平台濫用，維護內容品質與合規</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push('/super-admin/audit-logs')}
            className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center gap-2"
          >
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
                  <button
                    onClick={async () => {
                      try {
                        await superAdminService.approveContent(String(item.id));
                        setContentReviewQueue(prev => prev.filter(i => i.id !== item.id));
                      } catch { alert('操作失敗'); }
                    }}
                    className="px-3 py-1.5 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" /> 通過
                  </button>
                  <button
                    onClick={async () => {
                      if (!confirm('確定要移除此內容嗎？')) return;
                      try {
                        await superAdminService.rejectContent(String(item.id));
                        setContentReviewQueue(prev => prev.filter(i => i.id !== item.id));
                      } catch { alert('操作失敗'); }
                    }}
                    className="px-3 py-1.5 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center gap-1.5"
                  >
                    <XCircle className="h-3.5 w-3.5" /> 移除
                  </button>
                  <button
                    onClick={() => setDetailModal({ type: item.type, content: item.content, reporter: item.reporter, date: item.date, id: item.id, source: 'content' })}
                    className="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50 transition-all flex items-center gap-1.5"
                  >
                    <Search className="h-3.5 w-3.5" /> 查看詳情
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Feedback Management */}
      <section className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
          <h2 className="font-bold text-slate-900 flex items-center gap-2">
            <Mail className="h-5 w-5 text-emerald-500" /> 用戶反饋管理
          </h2>
          <div className="flex items-center gap-3">
            {feedbackStats && (
              <div className="hidden sm:flex items-center gap-3 text-xs">
                <span className="px-2 py-1 rounded-lg bg-amber-50 text-amber-600 font-bold">待處理 {feedbackStats.pending_count}</span>
                <span className="px-2 py-1 rounded-lg bg-blue-50 text-blue-600 font-bold">處理中 {feedbackStats.reviewing_count}</span>
                <span className="px-2 py-1 rounded-lg bg-emerald-50 text-emerald-600 font-bold">已解決 {feedbackStats.resolved_count}</span>
              </div>
            )}
            <select
              value={feedbackFilter}
              onChange={(e) => { setFeedbackFilter(e.target.value); loadFeedbacks(e.target.value); }}
              className="bg-slate-50 border-transparent rounded-lg text-xs px-3 py-1.5 outline-none"
            >
              <option value="">全部</option>
              <option value="PENDING">待處理</option>
              <option value="REVIEWING">處理中</option>
              <option value="RESOLVED">已解決</option>
            </select>
          </div>
        </div>
        {feedbacks.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">暫無反饋紀錄</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {feedbacks.map((fb) => (
              <div key={fb.feedback_id} className="p-5 hover:bg-slate-50/50 transition-all">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-mono font-bold text-slate-400">{fb.feedback_id}</span>
                      <span className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded-lg uppercase",
                        fb.type === 'BUG' && "bg-rose-50 text-rose-600",
                        fb.type === 'FEATURE_REQUEST' && "bg-blue-50 text-blue-600",
                        fb.type === 'CONTENT_ERROR' && "bg-amber-50 text-amber-600",
                        fb.type === 'OTHER' && "bg-slate-100 text-slate-600",
                        !['BUG','FEATURE_REQUEST','CONTENT_ERROR','OTHER'].includes(fb.type) && "bg-slate-100 text-slate-600"
                      )}>
                        {fb.type === 'BUG' ? '錯誤回報' : fb.type === 'FEATURE_REQUEST' ? '功能建議' : fb.type === 'CONTENT_ERROR' ? '內容勘誤' : fb.type === 'OTHER' || fb.type === 'other' ? '其他' : fb.type}
                      </span>
                      <span className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded-lg",
                        fb.status === 'PENDING' && "bg-amber-50 text-amber-600",
                        fb.status === 'REVIEWING' && "bg-blue-50 text-blue-600",
                        fb.status === 'RESOLVED' && "bg-emerald-50 text-emerald-600"
                      )}>
                        {fb.status === 'PENDING' ? '待處理' : fb.status === 'REVIEWING' ? '處理中' : fb.status === 'RESOLVED' ? '已解決' : fb.status}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-slate-900 mb-0.5">{fb.subject}</p>
                    <p className="text-xs text-slate-500">
                      {fb.user_email} &middot; {fb.created_at ? new Date(fb.created_at).toLocaleString('zh-TW') : '--'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {fb.status === 'PENDING' && (
                      <button
                        onClick={async () => {
                          try {
                            await superAdminService.updateFeedback(fb.feedback_id, { status: 'REVIEWING' });
                            loadFeedbacks(feedbackFilter || undefined);
                            superAdminService.getAdminFeedbackStats().then(setFeedbackStats).catch(() => {});
                          } catch { alert('操作失敗'); }
                        }}
                        className="px-3 py-1.5 bg-blue-500 text-white rounded-xl text-xs font-bold hover:bg-blue-600 transition-all shadow-lg shadow-blue-500/20 flex items-center gap-1.5"
                      >
                        <Eye className="h-3.5 w-3.5" /> 開始處理
                      </button>
                    )}
                    <button
                      onClick={() => { setFeedbackModal(fb); setAdminReply(fb.admin_reply || ''); }}
                      className="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50 transition-all flex items-center gap-1.5"
                    >
                      <Search className="h-3.5 w-3.5" /> 詳情
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Feedback Detail Modal */}
      {feedbackModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setFeedbackModal(null)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-900">反饋詳情 — {feedbackModal.feedback_id}</h3>
              <span className={cn(
                "text-xs font-bold px-2 py-1 rounded-lg",
                feedbackModal.status === 'PENDING' && "bg-amber-50 text-amber-600",
                feedbackModal.status === 'REVIEWING' && "bg-blue-50 text-blue-600",
                feedbackModal.status === 'RESOLVED' && "bg-emerald-50 text-emerald-600"
              )}>
                {feedbackModal.status === 'PENDING' ? '待處理' : feedbackModal.status === 'REVIEWING' ? '處理中' : '已解決'}
              </span>
            </div>
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">類型</span>
                <span className="font-bold text-slate-900">
                  {feedbackModal.type === 'BUG' ? '錯誤回報' : feedbackModal.type === 'FEATURE_REQUEST' ? '功能建議' : feedbackModal.type === 'CONTENT_ERROR' ? '內容勘誤' : feedbackModal.type === 'OTHER' || feedbackModal.type === 'other' ? '其他' : feedbackModal.type}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">主旨</span>
                <span className="font-bold text-slate-900">{feedbackModal.subject}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">提交者</span>
                <span className="font-bold text-slate-900">{feedbackModal.user_email}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">時間</span>
                <span className="text-slate-900">{feedbackModal.created_at ? new Date(feedbackModal.created_at).toLocaleString('zh-TW') : '--'}</span>
              </div>
              <div className="text-sm">
                <span className="text-slate-500 block mb-1">內容</span>
                <p className="font-medium text-slate-900 bg-slate-50 p-3 rounded-xl border border-slate-100 whitespace-pre-wrap">{feedbackModal.content}</p>
              </div>
              {feedbackModal.attachment_urls?.length > 0 && (
                <div className="text-sm">
                  <span className="text-slate-500 block mb-1">附件 ({feedbackModal.attachment_urls.length} 張)</span>
                  <div className="grid grid-cols-2 gap-2">
                    {feedbackModal.attachment_urls.map((url, i) => (
                      <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="block rounded-xl overflow-hidden border border-slate-200 hover:border-emerald-400 transition-all">
                        <img src={url} alt={`附件 ${i + 1}`} className="w-full h-32 object-cover" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
              {feedbackModal.status !== 'RESOLVED' && (
                <div className="text-sm">
                  <span className="text-slate-500 block mb-1">管理員回覆</span>
                  <textarea
                    value={adminReply}
                    onChange={(e) => setAdminReply(e.target.value)}
                    placeholder="輸入回覆內容..."
                    rows={3}
                    className="w-full p-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 resize-none"
                  />
                </div>
              )}
              {feedbackModal.admin_reply && feedbackModal.status === 'RESOLVED' && (
                <div className="text-sm">
                  <span className="text-slate-500 block mb-1">管理員回覆</span>
                  <p className="font-medium text-slate-900 bg-emerald-50 p-3 rounded-xl border border-emerald-100 whitespace-pre-wrap">{feedbackModal.admin_reply}</p>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              {feedbackModal.status !== 'RESOLVED' && (
                <button
                  disabled={feedbackUpdating}
                  onClick={async () => {
                    setFeedbackUpdating(true);
                    try {
                      await superAdminService.updateFeedback(feedbackModal.feedback_id, {
                        status: 'RESOLVED',
                        admin_reply: adminReply || undefined,
                      });
                      setFeedbackModal(null);
                      loadFeedbacks(feedbackFilter || undefined);
                      superAdminService.getAdminFeedbackStats().then(setFeedbackStats).catch(() => {});
                    } catch { alert('操作失敗'); }
                    setFeedbackUpdating(false);
                  }}
                  className="flex-1 py-2.5 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" /> {adminReply ? '回覆並解決' : '標記已解決'}
                </button>
              )}
              {feedbackModal.status === 'PENDING' && (
                <button
                  disabled={feedbackUpdating}
                  onClick={async () => {
                    setFeedbackUpdating(true);
                    try {
                      await superAdminService.updateFeedback(feedbackModal.feedback_id, { status: 'REVIEWING' });
                      setFeedbackModal(null);
                      loadFeedbacks(feedbackFilter || undefined);
                      superAdminService.getAdminFeedbackStats().then(setFeedbackStats).catch(() => {});
                    } catch { alert('操作失敗'); }
                    setFeedbackUpdating(false);
                  }}
                  className="flex-1 py-2.5 bg-blue-500 text-white rounded-xl text-xs font-bold hover:bg-blue-600 transition-all shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Eye className="h-4 w-4" /> 開始處理
                </button>
              )}
              <button
                onClick={() => setFeedbackModal(null)}
                className="py-2.5 px-4 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50 transition-all"
              >
                關閉
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Moderation Queue */}
        <section className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
            <h2 className="font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-500" /> 待審核佇列
            </h2>
            <div className="flex gap-2">
              <select
                value={queueFilter}
                onChange={(e) => setQueueFilter(e.target.value)}
                className="bg-slate-50 border-transparent rounded-lg text-xs px-3 py-1.5 outline-none"
              >
                <option value="all">全部</option>
                <option value="flagged">系統標記</option>
                <option value="reported">用戶檢舉</option>
                <option value="pending">待處理</option>
              </select>
            </div>
          </div>
          <div className="divide-y divide-slate-100">
            {moderationQueue.filter(item => queueFilter === 'all' || item.status === queueFilter).map((item) => (
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
                  <button
                    onClick={async () => {
                      try {
                        await superAdminService.approveContent(item.id);
                        setModerationQueue(prev => prev.filter(i => i.id !== item.id));
                      } catch { alert('操作失敗'); }
                    }}
                    className="flex-1 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
                  >
                    <ShieldCheck className="h-4 w-4" /> 通過審核
                  </button>
                  <button
                    onClick={async () => {
                      if (!confirm('確定要刪除此內容並警告用戶嗎？')) return;
                      try {
                        await superAdminService.rejectContent(item.id);
                        setModerationQueue(prev => prev.filter(i => i.id !== item.id));
                      } catch { alert('操作失敗'); }
                    }}
                    className="flex-1 py-2 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center justify-center gap-2"
                  >
                    <XCircle className="h-4 w-4" /> 刪除並警告
                  </button>
                  <button
                    onClick={() => setDetailModal({ type: item.type, content: item.content, user: item.user, reason: item.reason, date: item.time, id: item.id, source: 'queue' })}
                    className="p-2 bg-slate-50 border border-slate-100 text-slate-400 hover:text-slate-900 rounded-xl transition-all"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setQueueFilter('all')}
            className="w-full py-4 text-sm font-bold text-slate-500 hover:text-slate-900 bg-slate-50/50 transition-all border-t border-slate-100"
          >
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
                    <button
                      onClick={() => router.push('/super-admin/audit-logs')}
                      className="text-xs font-bold text-emerald-600 hover:text-emerald-700 transition-all"
                    >
                      查看日誌
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => router.push('/super-admin/audit-logs')}
              className="w-full mt-6 py-3 text-sm font-bold text-slate-500 hover:text-slate-900 transition-all"
            >
              查看所有異常 &rarr;
            </button>
          </section>

          {/* Quick Actions */}
          <section className="bg-slate-900 p-6 rounded-3xl shadow-xl shadow-slate-900/20">
            <h2 className="font-bold text-white mb-4">管理員快速操作</h2>
            <div className="space-y-2">
              <button
                onClick={() => router.push('/super-admin/settings')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all group"
              >
                <span className="text-sm font-medium">發布全站公告</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-all" />
              </button>
              <button
                onClick={async () => {
                  if (!confirm('確定要重置所有用戶的 AI 流量限制嗎？')) return;
                  try {
                    const { apiClient } = await import('@/lib/api/client');
                    await apiClient.post('/admin/system-settings/reset-ai-limits');
                    alert('AI 流量限制已重置');
                  } catch { alert('重置失敗，請稍後再試'); }
                }}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all group"
              >
                <span className="text-sm font-medium">重置 AI 流量限制</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-all" />
              </button>
              <button
                onClick={async () => {
                  if (!confirm('確定要清理系統暫存檔嗎？')) return;
                  try {
                    const { apiClient } = await import('@/lib/api/client');
                    await apiClient.post('/admin/system-settings/clear-cache');
                    alert('系統暫存檔已清理');
                  } catch { alert('清理失敗，請稍後再試'); }
                }}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all group"
              >
                <span className="text-sm font-medium">清理系統暫存檔</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-all" />
              </button>
            </div>
          </section>
        </div>
      </div>
      {/* Detail Modal */}
      {detailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setDetailModal(null)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 mb-4">
              {detailModal.source === 'content' ? '檢舉詳情' : '審核項目詳情'}
            </h3>
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">類型</span>
                <span className={cn(
                  "text-xs font-bold px-2 py-1 rounded-lg",
                  detailModal.type === '使用者上傳' ? "bg-blue-50 text-blue-600" : "bg-amber-50 text-amber-600"
                )}>
                  {detailModal.type}
                </span>
              </div>
              <div className="text-sm">
                <span className="text-slate-500 block mb-1">內容</span>
                <p className="font-medium text-slate-900 bg-slate-50 p-3 rounded-xl border border-slate-100">{detailModal.content}</p>
              </div>
              {detailModal.user && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">用戶</span>
                  <span className="font-bold text-slate-900">{detailModal.user}</span>
                </div>
              )}
              {detailModal.reason && (
                <div className="text-sm">
                  <span className="text-slate-500 block mb-1">原因</span>
                  <p className="font-medium text-slate-900 bg-amber-50 p-3 rounded-xl border border-amber-100 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                    {detailModal.reason}
                  </p>
                </div>
              )}
              {detailModal.reporter && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">回報者</span>
                  <span className="font-bold text-slate-900">{detailModal.reporter}</span>
                </div>
              )}
              {detailModal.date && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">{detailModal.source === 'content' ? '日期' : '時間'}</span>
                  <span className="text-slate-900">{detailModal.date}</span>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  try {
                    await superAdminService.approveContent(String(detailModal.id));
                    if (detailModal.source === 'content') {
                      setContentReviewQueue(prev => prev.filter(i => String(i.id) !== String(detailModal.id)));
                    } else {
                      setModerationQueue(prev => prev.filter(i => i.id !== String(detailModal.id)));
                    }
                    setDetailModal(null);
                  } catch { alert('操作失敗'); }
                }}
                className="flex-1 py-2.5 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="h-4 w-4" /> 通過
              </button>
              <button
                onClick={async () => {
                  if (!confirm('確定要移除此內容嗎？')) return;
                  try {
                    await superAdminService.rejectContent(String(detailModal.id));
                    if (detailModal.source === 'content') {
                      setContentReviewQueue(prev => prev.filter(i => String(i.id) !== String(detailModal.id)));
                    } else {
                      setModerationQueue(prev => prev.filter(i => i.id !== String(detailModal.id)));
                    }
                    setDetailModal(null);
                  } catch { alert('操作失敗'); }
                }}
                className="flex-1 py-2.5 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center justify-center gap-2"
              >
                <XCircle className="h-4 w-4" /> 移除
              </button>
              <button
                onClick={() => setDetailModal(null)}
                className="py-2.5 px-4 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50 transition-all"
              >
                關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
