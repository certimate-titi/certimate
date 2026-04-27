/**
 * @file 路由 `/super-admin/audit-logs` — 平台稽核日誌頁。
 *
 * Super Admin 專屬：查詢管理操作稽核紀錄（admin action logs），
 * 支援搜尋、過濾、分頁、匯出 CSV。
 */
'use client';

import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter, 
  Download, 
  History,
  AlertCircle,
  Clock,
  User,
  Activity,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Settings,
  UserPlus,
  UserMinus,
  Zap
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface AuditLog {
  id: string;
  adminId: string;
  adminEmail: string;
  action: string;
  targetId: string;
  details: string;
  timestamp: Date | null;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAction, setSelectedAction] = useState('All');

  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 10;
  const [showDateFilter, setShowDateFilter] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  useEffect(() => {
    superAdminService.getAuditLogs().then(res => {
      if (!Array.isArray(res?.logs)) { setLoading(false); return; }
      const mapped: AuditLog[] = res.logs.map((log) => ({
        id: log.id || '',
        adminId: log.admin_id || '',
        adminEmail: log.admin_email || 'Unknown',
        action: log.action || '',
        targetId: log.target_id || '',
        details: typeof log.details === 'string' ? log.details : JSON.stringify(log.details || ''),
        timestamp: log.timestamp ? new Date(log.timestamp) : null,
      }));
      setLogs(mapped);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
      setError('載入日誌失敗，請稍後再試。');
    });
  }, []);

  const ACTION_LABELS: Record<string, { icon: typeof Activity; color: string; bg: string; border: string; label: string }> = {
    // 使用者管理
    [AdminAction.CREATE_ADMIN]:       { icon: UserPlus, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '新增管理員' },
    [AdminAction.EDIT_ADMIN]:         { icon: Settings, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100', label: '編輯管理員' },
    [AdminAction.DELETE_USER]:        { icon: UserMinus, color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-100', label: '刪除用戶' },
    [AdminAction.SUSPEND_USER]:       { icon: ShieldAlert, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', label: '停權用戶' },
    [AdminAction.ACTIVATE_USER]:      { icon: User, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '啟用用戶' },
    [AdminAction.ADJUST_ROLE]:        { icon: ShieldAlert, color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-100', label: '調整角色' },
    [AdminAction.NOTIFY_USER]:        { icon: Activity, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100', label: '通知用戶' },
    // 訂閱 & 財務
    [AdminAction.ADJUST_SUBSCRIPTION]:  { icon: Zap, color: 'text-indigo-600', bg: 'bg-indigo-50', border: 'border-indigo-100', label: '調整訂閱' },
    [AdminAction.SUBSCRIPTION_UPGRADE]: { icon: Zap, color: 'text-indigo-600', bg: 'bg-indigo-50', border: 'border-indigo-100', label: '訂閱升級' },
    [AdminAction.APPROVE_REFUND]:     { icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '核准退款' },
    [AdminAction.REJECT_REFUND]:      { icon: Activity, color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-100', label: '拒絕退款' },
    // 系統設定
    [AdminAction.UPDATE_SETTINGS]:    { icon: Settings, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100', label: '更新設定' },
    [AdminAction.UPDATE_MODEL_ROUTING]: { icon: Settings, color: 'text-cyan-600', bg: 'bg-cyan-50', border: 'border-cyan-100', label: '更新 AI 路由' },
    [AdminAction.RESET_AI_LIMITS]:    { icon: Activity, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', label: '重設 AI 限額' },
    [AdminAction.CLEAR_CACHE]:        { icon: Activity, color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-100', label: '清除快取' },
    // 成本監控
    [AdminAction.COST_MONITOR_VIEWED]:  { icon: Activity, color: 'text-slate-500', bg: 'bg-slate-50', border: 'border-slate-100', label: '查看成本監控' },
    [AdminAction.BUDGET_UPDATED]:     { icon: Zap, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', label: '更新預算' },
    [AdminAction.BUDGET_OVERRIDE]:    { icon: Zap, color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-100', label: '預算覆寫' },
    // 內容審核
    [AdminAction.RESOLVE_REPORT]:     { icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '處理檢舉' },
    [AdminAction.UNLOCK_COOLDOWN]:    { icon: Activity, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100', label: '解除冷卻' },
    [AdminAction.APPROVE_CONTENT]:    { icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '核准內容' },
    [AdminAction.REJECT_CONTENT]:     { icon: Activity, color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-100', label: '拒絕內容' },
    [AdminAction.UPDATE_FEEDBACK]:    { icon: Activity, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100', label: '更新反饋狀態' },
    [AdminAction.UPDATE_ANOMALY]:     { icon: ShieldAlert, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', label: '更新異常狀態' },
    // AI & Prompt
    [AdminAction.CREATE_PROMPT]:      { icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '建立 Prompt' },
    [AdminAction.UPDATE_PROMPT]:      { icon: Settings, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100', label: '更新 Prompt' },
    [AdminAction.DEACTIVATE_PROMPT]:  { icon: Activity, color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-100', label: '停用 Prompt' },
    [AdminAction.ROLLBACK_PROMPT]:    { icon: Activity, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', label: '回滾 Prompt' },
    [AdminAction.CREATE_AB_TEST]:     { icon: Zap, color: 'text-indigo-600', bg: 'bg-indigo-50', border: 'border-indigo-100', label: '建立 A/B 測試' },
    [AdminAction.COMPLETE_AB_TEST]:   { icon: Zap, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '完成 A/B 測試' },
    [AdminAction.FUP_SOFT_CAP]:       { icon: ShieldAlert, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', label: 'FUP 軟上限觸發' },
    // 知識庫
    [AdminAction.EXTRACT_KNOWLEDGE]:  { icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', label: '知識樹萃取' },
  };

  const getActionConfig = (action: string) => {
    return ACTION_LABELS[action] || { icon: Activity, color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-100', label: action };
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch =
      log.adminEmail.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.details.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.targetId.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesAction = selectedAction === 'All' || log.action === selectedAction;

    let matchesDate = true;
    if (dateFrom && log.timestamp) {
      matchesDate = log.timestamp >= new Date(dateFrom);
    }
    if (dateTo && log.timestamp && matchesDate) {
      const endDate = new Date(dateTo);
      endDate.setDate(endDate.getDate() + 1);
      matchesDate = log.timestamp < endDate;
    }

    return matchesSearch && matchesAction && matchesDate;
  });

  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
  const paginatedLogs = filteredLogs.slice((currentPage - 1) * logsPerPage, currentPage * logsPerPage);

  const handleExport = () => {
    if (filteredLogs.length === 0) return;
    
    const headers = ['時間', '操作者 Email', '操作者 ID', '動作', '目標 ID', '詳情'];
    const csvContent = [
      headers.join(','),
      ...filteredLogs.map(log => {
        const time = log.timestamp ? log.timestamp.toISOString() : '未知時間';
        const actionLabel = getActionConfig(log.action).label;
        // Escape quotes and wrap in quotes to handle commas in details
        const details = `"${log.details.replace(/"/g, '""')}"`;
        return `${time},${log.adminEmail},${log.adminId},${actionLabel},${log.targetId},${details}`;
      })
    ].join('\n');

    const blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <History className="h-6 w-6 text-emerald-500" />
            審計日誌
          </h1>
          <p className="text-slate-500 mt-1">追蹤並檢視所有管理員的操作紀錄，確保系統安全性與合規性。</p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button 
            onClick={handleExport}
            disabled={filteredLogs.length === 0}
            className="flex-1 sm:flex-none px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" /> 匯出日誌
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-rose-800">載入日誌失敗</h3>
            <p className="text-xs text-rose-600 mt-1 break-all">{error}</p>
          </div>
        </div>
      )}

      {/* Filters & Search */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col lg:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="搜尋 Email、操作詳情或目標 ID..." 
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-xl text-sm transition-all outline-none"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <select 
            className="bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-xl text-sm px-4 py-2 outline-none transition-all"
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
          >
            <option value="All">所有操作類型</option>
            {Object.values(AdminAction).map(action => (
              <option key={action} value={action}>{getActionConfig(action).label}</option>
            ))}
          </select>
          <button
            onClick={() => setShowDateFilter(!showDateFilter)}
            className={cn("px-4 py-2 bg-slate-50 border-transparent hover:bg-slate-100 rounded-xl text-sm font-medium transition-all flex items-center gap-2", showDateFilter && "bg-emerald-50 text-emerald-600")}
          >
            <Filter className="h-4 w-4" /> 進階篩選
          </button>
        </div>
      </div>

      {/* Date Filter Panel */}
      {showDateFilter && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1 space-y-1">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">開始日期</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setCurrentPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500"
            />
          </div>
          <div className="flex-1 space-y-1">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">結束日期</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setCurrentPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500"
            />
          </div>
          <button
            onClick={() => { setDateFrom(''); setDateTo(''); setCurrentPage(1); }}
            className="px-4 py-2 bg-slate-100 rounded-xl text-sm font-medium hover:bg-slate-200 transition-all"
          >
            清除日期
          </button>
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">時間</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">操作者</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">動作</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">目標 ID</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">詳情</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                      <p className="text-sm font-medium">載入日誌中...</p>
                    </div>
                  </td>
                </tr>
              ) : paginatedLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <History className="h-8 w-8 text-slate-300" />
                      <p className="text-sm font-medium">找不到符合條件的日誌</p>
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedLogs.map((log) => {
                  const config = getActionConfig(log.action);
                  const Icon = config.icon;
                  return (
                    <tr key={log.id} className="hover:bg-slate-50/50 transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2 text-sm text-slate-500">
                          <Clock className="h-4 w-4 shrink-0" />
                          {log.timestamp ? log.timestamp.toLocaleString('zh-TW', {
                            year: 'numeric', month: '2-digit', day: '2-digit',
                            hour: '2-digit', minute: '2-digit', second: '2-digit',
                            hour12: false
                          }) : '未知時間'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold text-xs border border-slate-200">
                            {log.adminEmail.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-900">{log.adminEmail}</p>
                            <p className="text-xs text-slate-500 font-mono">{log.adminId.slice(0, 8)}...</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-bold", config.bg, config.color, config.border)}>
                          <Icon className="h-3.5 w-3.5" />
                          {config.label}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-mono text-slate-600 bg-slate-100 px-2 py-1 rounded border border-slate-200">
                          {log.targetId}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-slate-700 max-w-md truncate" title={log.details}>
                          {log.details}
                        </p>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && filteredLogs.length > 0 && (
          <div className="px-6 py-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
            <p className="text-xs font-medium text-slate-500">
              顯示 {(currentPage - 1) * logsPerPage + 1} 到 {Math.min(currentPage * logsPerPage, filteredLogs.length)} 筆，共 {filteredLogs.length} 筆紀錄
            </p>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 text-slate-400 hover:text-slate-900 disabled:opacity-50 disabled:hover:text-slate-400"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum = i + 1;
                  if (totalPages > 5) {
                    if (currentPage > 3) {
                      pageNum = currentPage - 2 + i;
                    }
                    if (pageNum > totalPages) {
                      pageNum = totalPages - 4 + i;
                    }
                  }
                  return (
                    <button 
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={cn(
                        "w-8 h-8 text-xs font-bold rounded-lg transition-all",
                        currentPage === pageNum 
                          ? "bg-emerald-500 text-white" 
                          : "text-slate-600 hover:bg-slate-200"
                      )}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 text-slate-400 hover:text-slate-900 disabled:opacity-50 disabled:hover:text-slate-400"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
