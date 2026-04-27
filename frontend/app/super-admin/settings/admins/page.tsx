/**
 * @file 路由 `/super-admin/settings/admins` — 管理員帳號管理頁。
 *
 * Super Admin 專屬：列出所有 ADMIN / SUPER_ADMIN，支援新增與移除。
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, MoreVertical } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { logAdminAction, AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';

/** TailwindCSS class 合併工具。 */
function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

/** 將後端回傳的管理員清單（可能為 `users` 或 `admins`）統一轉成顯示用結構。 */
function parseAdmins(res: unknown): { id: string; name: string; email: string; role: string; joined: string }[] {
  const raw = (res as { users?: unknown[]; admins?: unknown[] }).users || (res as { admins?: unknown[] }).admins || [];
  return (raw as Record<string, unknown>[]).map(u => ({
    id: String(u.id || ''),
    name: String(u.display_name || u.name || u.email || '--'),
    email: String(u.email || ''),
    role: String(u.role || 'Admin'),
    joined: String(u.created_at || u.joined || '--'),
  }));
}

export default function AdminsPage() {
  const [admins, setAdmins] = useState<{ id: string; name: string; email: string; role: string; joined: string }[]>([]);

  useEffect(() => {
    superAdminService.getAdmins().then(res => setAdmins(parseAdmins(res))).catch(() => {});
  }, []);

  const handleAdd = async () => {
    const email = prompt('請輸入新管理員的 Email:');
    if (!email) return;
    try {
      await superAdminService.adjustRole(email, 'admin');
      const res = await superAdminService.getAdmins();
      setAdmins(parseAdmins(res));
      await logAdminAction(AdminAction.CREATE_ADMIN, email, `新增了管理員帳號: ${email}`);
    } catch { alert('新增管理員失敗，請確認 Email 是否正確'); }
  };

  const handleDelete = async (id: string, email: string) => {
    if (!confirm(`確定要刪除管理員 ${email} 嗎？`)) return;
    try {
      await superAdminService.adjustRole(email, 'user');
      setAdmins(admins.filter(a => a.id !== id));
      await logAdminAction(AdminAction.DELETE_ADMIN, id, `刪除了管理員帳號: ${email}`);
    } catch { alert('刪除管理員失敗'); }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-slate-900">管理員帳號</h3>
        <button onClick={handleAdd} className="px-4 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all flex items-center gap-2">
          <Plus className="h-4 w-4" /> 新增管理員
        </button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-100">
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">管理員</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">權限</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">加入日期</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {admins.map((admin) => (
              <tr key={admin.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold text-xs">{admin.name.charAt(0)}</div>
                    <div>
                      <p className="text-sm font-bold text-slate-900">{admin.name}</p>
                      <p className="text-xs text-slate-500">{admin.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider", admin.role === 'Super Admin' ? "bg-rose-50 text-rose-600" : "bg-blue-50 text-blue-600")}>
                    {admin.role}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">{admin.joined}</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button className="p-2 text-slate-400 hover:text-slate-900 transition-all"><MoreVertical className="h-4 w-4" /></button>
                    <button onClick={() => handleDelete(admin.id, admin.email)} className="p-2 text-slate-400 hover:text-rose-500 transition-all"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
