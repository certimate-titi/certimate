'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  Search, 
  Filter, 
  MoreVertical, 
  UserPlus, 
  Download, 
  Mail, 
  ShieldCheck, 
  ShieldAlert, 
  Trash2,
  ChevronLeft,
  ChevronRight,
  Eye
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { logAdminAction, AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function UserManagementPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTier, setSelectedTier] = useState('All');
  const [users, setUsers] = useState<{ id: string; name: string; email: string; tier: string; status: string; lastLogin: string; joined: string; tokens: string }[]>([]);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const usersPerPage = 10;

  React.useEffect(() => {
    superAdminService.getUsers({ search: searchTerm, tier: selectedTier }).then((res) => {
      const mapped = (res.users || []).map((u: unknown) => {
        const rec = u as Record<string, unknown>;
        return {
          id: (rec.id as string) || '',
          name: (rec.display_name as string) || (rec.name as string) || (rec.email as string) || '--',
          email: (rec.email as string) || '',
          tier: (rec.plan as string) || (rec.tier as string) || 'FREE',
          status: (rec.status as string) || 'active',
          lastLogin: (rec.last_login_at as string) || (rec.lastLogin as string) || '--',
          joined: (rec.created_at as string) || (rec.joined as string) || '--',
          tokens: (rec.tokens as string) || '--',
        };
      });
      setUsers(mapped);
    }).catch(() => {});
  }, [searchTerm, selectedTier]);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">用戶管理</h1>
          <p className="text-slate-500">管理所有用戶的完整生命週期與權限</p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button
            onClick={async () => {
              try {
                const blob = await superAdminService.exportUsersCSV();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'users-export.csv';
                a.click();
                URL.revokeObjectURL(url);
              } catch { alert('匯出失敗，請稍後再試'); }
            }}
            className="flex-1 sm:flex-none px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
          >
            <Download className="h-4 w-4" /> 匯出 CSV
          </button>
          <button
            onClick={async () => {
              const email = prompt('請輸入新用戶的 Email:');
              if (!email) return;
              const password = prompt('請設定密碼（至少 8 碼）:');
              if (!password || password.length < 8) { alert('密碼至少 8 碼'); return; }
              try {
                await superAdminService.createUser(email, password);
                await logAdminAction(AdminAction.CREATE_ADMIN, email, `新增用戶: ${email}`);
                alert('用戶已建立');
                window.location.reload();
              } catch { alert('新增失敗，可能 Email 已被註冊或權限不足'); }
            }}
            className="flex-1 sm:flex-none px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
          >
            <UserPlus className="h-4 w-4" /> 新增用戶
          </button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col lg:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="搜尋 Email、姓名或 User ID..." 
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-xl text-sm transition-all outline-none"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <select 
            className="bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-xl text-sm px-4 py-2 outline-none transition-all"
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value)}
          >
            <option value="All">所有方案</option>
            <option value="Free">Free</option>
            <option value="Pro">Pro</option>
            <option value="Ultra">Ultra</option>
          </select>
          <button
            onClick={() => setShowFilterPanel(!showFilterPanel)}
            className={cn("px-4 py-2 bg-slate-50 border-transparent hover:bg-slate-100 rounded-xl text-sm font-medium transition-all flex items-center gap-2", showFilterPanel && "bg-emerald-50 text-emerald-600")}
          >
            <Filter className="h-4 w-4" /> 進階篩選
          </button>
        </div>
      </div>

      {/* User Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">用戶資訊</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">方案</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">狀態</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Token 消耗</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">最後活躍</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">註冊日期</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.slice((currentPage - 1) * usersPerPage, currentPage * usersPerPage).map((user) => (
                <tr key={user.id} className="hover:bg-slate-50/50 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold border border-slate-200">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900">{user.name}</p>
                        <p className="text-xs text-slate-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "text-xs font-bold px-2 py-1 rounded-lg",
                      user.tier === 'Ultra' && "bg-indigo-50 text-indigo-600",
                      user.tier === 'Pro' && "bg-emerald-50 text-emerald-600",
                      user.tier === 'Free' && "bg-slate-100 text-slate-600"
                    )}>
                      {user.tier}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        "h-2 w-2 rounded-full",
                        user.status === 'active' && "bg-emerald-500",
                        user.status === 'suspended' && "bg-rose-500",
                        user.status === 'cooling' && "bg-amber-500"
                      )}></div>
                      <span className="text-xs font-medium text-slate-700">
                        {user.status === 'active' && "正常"}
                        {user.status === 'suspended' && "已停權"}
                        {user.status === 'cooling' && "冷卻中"}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-slate-700">
                    {user.tokens}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {user.lastLogin && user.lastLogin !== '--'
                      ? new Date(user.lastLogin).toLocaleDateString('zh-TW')
                      : '--'}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {user.joined && user.joined !== '--'
                      ? new Date(user.joined).toLocaleDateString('zh-TW')
                      : '--'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link 
                        href={`/super-admin/users/${user.id}`}
                        className="p-2 text-slate-400 hover:text-emerald-500 hover:bg-emerald-50 rounded-lg transition-all"
                        title="查看詳情"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                      <button
                        onClick={async () => {
                          const msg = prompt(`發送通知給 ${user.name}：`);
                          if (!msg) return;
                          try {
                            const { apiClient } = await import('@/lib/api/client');
                            await apiClient.post(`/admin/users/${user.id}/notify`, { message: msg });
                            alert('通知已發送');
                          } catch { alert('發送失敗'); }
                        }}
                        className="p-2 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-all"
                        title="發送通知"
                      >
                        <Mail className="h-4 w-4" />
                      </button>
                      <button
                        onClick={async () => {
                          const reason = prompt(`請輸入停權用戶 ${user.name} 的原因：`);
                          if (!reason) return;
                          try {
                            await superAdminService.suspendUser(user.id, reason);
                            await logAdminAction(AdminAction.SUSPEND_USER, user.id, `停權了用戶: ${user.email}`);
                            setUsers(prev => prev.map(u => u.id === user.id ? { ...u, status: 'suspended' } : u));
                          } catch { alert('停權失敗'); }
                        }}
                        className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all"
                        title="停權帳號"
                      >
                        <ShieldAlert className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {users.length > 0 && (() => {
          const totalPages = Math.ceil(users.length / usersPerPage);
          return (
            <div className="px-6 py-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
              <p className="text-xs font-medium text-slate-500">
                顯示 {(currentPage - 1) * usersPerPage + 1} 到 {Math.min(currentPage * usersPerPage, users.length)} 筆，共 {users.length} 筆用戶
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-2 text-slate-400 hover:text-slate-900 disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum = i + 1;
                    if (totalPages > 5 && currentPage > 3) {
                      pageNum = currentPage - 2 + i;
                    }
                    if (pageNum > totalPages) pageNum = totalPages - 4 + i;
                    if (pageNum < 1) pageNum = i + 1;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={cn(
                          "w-8 h-8 text-xs font-bold rounded-lg transition-all",
                          currentPage === pageNum ? "bg-emerald-500 text-white" : "text-slate-500 hover:bg-slate-200"
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
                  className="p-2 text-slate-400 hover:text-slate-900 disabled:opacity-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
