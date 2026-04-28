/**
 * @file 路由 `/super-admin/settings` — 設定子樹 layout。
 *
 * 在 super-admin layout 內再嵌入一層側欄，列出 settings 各子頁
 * （AI 路由、Plans、Announcements、Flags、Admins、Version）。
 */
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Cpu,
  Zap,
  Bell,
  Flag,
  ShieldCheck,
  Server,
  ChevronRight,
  Key,
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const SETTINGS_TABS = [
  { id: 'ai', href: '/super-admin/settings', name: 'AI 模型路由', icon: Cpu },
  { id: 'api-keys', href: '/super-admin/settings/api-keys', name: 'API Keys', icon: Key },
  { id: 'plans', href: '/super-admin/settings/plans', name: '方案限額', icon: Zap },
  { id: 'announcements', href: '/super-admin/settings/announcements', name: '公告管理', icon: Bell },
  { id: 'flags', href: '/super-admin/settings/flags', name: 'Feature Flags', icon: Flag },
  { id: 'admins', href: '/super-admin/settings/admins', name: '管理員帳號', icon: ShieldCheck },
  { id: 'version', href: '/super-admin/settings/version', name: '版本資訊', icon: Server },
] as const;

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const getActiveTab = () => {
    // Exact match for root, otherwise match by prefix
    if (pathname === '/super-admin/settings') return 'ai';
    const match = SETTINGS_TABS.find(t => t.href !== '/super-admin/settings' && pathname.startsWith(t.href));
    return match?.id || 'ai';
  };

  const activeTab = getActiveTab();

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">系統設定</h1>
          <p className="text-slate-500">免改 code 即時調整系統行為參數與權限</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar Tabs */}
        <aside className="lg:w-64 shrink-0">
          <nav className="space-y-1">
            {SETTINGS_TABS.map((tab) => (
              <Link
                key={tab.id}
                href={tab.href}
                className={cn(
                  "w-full flex items-center px-4 py-3 rounded-xl transition-all group",
                  activeTab === tab.id
                    ? "bg-white text-emerald-600 shadow-sm border border-slate-200"
                    : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                <tab.icon className={cn("h-5 w-5 shrink-0", activeTab === tab.id ? "text-emerald-500" : "group-hover:text-slate-700")} />
                <span className="ml-3 font-medium text-sm">{tab.name}</span>
                {activeTab === tab.id && <ChevronRight className="ml-auto h-4 w-4" />}
              </Link>
            ))}
          </nav>
        </aside>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
