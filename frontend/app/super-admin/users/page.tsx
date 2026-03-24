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

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Mock Data
const users = [
  { id: 'usr_1', name: '張小明', email: 'ming@example.com', tier: 'Ultra', status: 'active', lastLogin: '2026-03-18 14:30', joined: '2026-01-15', tokens: '125k' },
  { id: 'usr_2', name: '李華', email: 'hua@example.com', tier: 'Pro', status: 'active', lastLogin: '2026-03-18 10:15', joined: '2026-02-10', tokens: '45k' },
  { id: 'usr_3', name: '王大同', email: 'datong@example.com', tier: 'Free', status: 'suspended', lastLogin: '2026-03-15 09:00', joined: '2026-03-01', tokens: '2k' },
  { id: 'usr_4', name: '陳美玲', email: 'meiling@example.com', tier: 'Ultra', status: 'active', lastLogin: '2026-03-18 15:45', joined: '2025-12-20', tokens: '210k' },
  { id: 'usr_5', name: '林志豪', email: 'zhihao@example.com', tier: 'Pro', status: 'cooling', lastLogin: '2026-03-17 22:30', joined: '2026-02-25', tokens: '88k' },
  { id: 'usr_6', name: '趙敏', email: 'zhaomin@example.com', tier: 'Free', status: 'active', lastLogin: '2026-03-18 08:20', joined: '2026-03-10', tokens: '5k' },
  { id: 'usr_7', name: '孫悟空', email: 'wukong@example.com', tier: 'Ultra', status: 'active', lastLogin: '2026-03-18 12:00', joined: '2026-01-05', tokens: '350k' },
  { id: 'usr_8', name: '唐三藏', email: 'sanzang@example.com', tier: 'Pro', status: 'active', lastLogin: '2026-03-18 11:30', joined: '2026-02-15', tokens: '12k' },
];

export default function UserManagementPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTier, setSelectedTier] = useState('All');

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">用戶管理</h1>
          <p className="text-slate-500">管理所有用戶的完整生命週期與權限</p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button className="flex-1 sm:flex-none px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center justify-center gap-2">
            <Download className="h-4 w-4" /> 匯出 CSV
          </button>
          <button 
            onClick={async () => {
              const email = prompt('請輸入新管理員 Email:');
              if (email) {
                await logAdminAction(AdminAction.CREATE_ADMIN, 'new', `嘗試新增管理員: ${email}`);
                alert('已記錄新增請求');
              }
            }}
            className="flex-1 sm:flex-none px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
          >
            <UserPlus className="h-4 w-4" /> 新增管理員
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
          <button className="px-4 py-2 bg-slate-50 border-transparent hover:bg-slate-100 rounded-xl text-sm font-medium transition-all flex items-center gap-2">
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
              {users.map((user) => (
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
                    {user.lastLogin}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {user.joined}
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
                      <button className="p-2 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-all" title="發送通知">
                        <Mail className="h-4 w-4" />
                      </button>
                      <button 
                        onClick={async () => {
                          if (confirm(`確定要停權用戶 ${user.name} 嗎？`)) {
                            await logAdminAction(AdminAction.SUSPEND_USER, user.id, `停權了用戶: ${user.email}`);
                            alert('用戶已停權並記錄日誌');
                          }
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
        <div className="px-6 py-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
          <p className="text-xs font-medium text-slate-500">顯示 1 到 8 筆，共 1,240 筆用戶</p>
          <div className="flex items-center gap-2">
            <button className="p-2 text-slate-400 hover:text-slate-900 disabled:opacity-50" disabled>
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-1">
              {[1, 2, 3, '...', 12].map((page, i) => (
                <button 
                  key={i}
                  className={cn(
                    "w-8 h-8 text-xs font-bold rounded-lg transition-all",
                    page === 1 ? "bg-emerald-500 text-white" : "text-slate-500 hover:bg-slate-200"
                  )}
                >
                  {page}
                </button>
              ))}
            </div>
            <button className="p-2 text-slate-400 hover:text-slate-900">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
