/**
 * @file 路由 `/super-admin` — 平台管理 layout。
 *
 * Super Admin 子樹共用框架：左側導航（dashboard / users / finance /
 * audit-logs / settings 等）、頂部使用者列、權限守衛（非 ADMIN 會被導離）。
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  ShieldAlert,
  AlertTriangle,
  Settings,
  Menu,
  X,
  LogOut,
  Bell,
  Search,
  History,
  FileText,
  Upload,
  DollarSign,
  Zap,
  Wrench,
  GitMerge
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import TiTiLogo from '@/components/TiTiLogo';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '@/lib/auth-context';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const sidebarItems = [
  { name: '營運儀表板', href: '/super-admin/dashboard', icon: LayoutDashboard },
  { name: '用戶管理', href: '/super-admin/users', icon: Users },
  { name: '財務與訂閱', href: '/super-admin/finance', icon: CreditCard },
  { name: '內容與安全', href: '/super-admin/moderation', icon: ShieldAlert },
  { name: '考古題匯入', href: '/super-admin/exam-import', icon: Upload },
  { name: '異常維修', href: '/super-admin/anomaly', icon: AlertTriangle },
  { name: '系統設定', href: '/super-admin/settings', icon: Settings },
  { name: '審計日誌', href: '/super-admin/audit-logs', icon: History },
  { name: 'Prompt 模板', href: '/super-admin/prompt-templates', icon: FileText },
  { name: '成本監控', href: '/super-admin/cost-monitor', icon: DollarSign },
  { name: '放榜與退場', href: '/super-admin/retirement', icon: Zap },
  { name: '考綱逆向工程', href: '/super-admin/reverse-engineering', icon: Wrench },
  { name: '知識樹合併', href: '/super-admin/knowledge-merge', icon: GitMerge },
];

export default function SuperAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, isAuthenticated, isAdmin, signOut: authSignOut } = useAuth();
  const userEmail = user?.email ?? null;

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace('/login');
    } else if (!loading && isAuthenticated && !isAdmin) {
      router.replace('/dashboard');
    }
  }, [loading, isAuthenticated, isAdmin, router]);

  const handleLogout = async () => {
    try {
      await authSignOut();
      router.push('/login');
    } catch (error) {
      console.error('Logout failed', error);
    }
  };

  if (loading || !isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside 
        className={cn(
          "bg-slate-900 text-white transition-all duration-300 ease-in-out flex flex-col z-50",
          isSidebarOpen ? "w-64" : "w-20"
        )}
      >
        <nav className="flex-1 py-4 space-y-1 px-3">
          {sidebarItems.map((item) => {
            // 容忍 trailing slash（Next.js static export + Firebase rewrite 會帶 / 或不帶）
            // 並用 startsWith 容忍子路徑（例 /super-admin/users/abc 仍高亮 /super-admin/users）
            const normalizedPath = pathname?.replace(/\/$/, '') ?? '';
            const isActive =
              normalizedPath === item.href ||
              normalizedPath.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center px-3 py-3 rounded-xl transition-all group",
                  isActive 
                    ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" 
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon className={cn("h-5 w-5 shrink-0", isActive ? "text-white" : "group-hover:text-emerald-400")} />
                {isSidebarOpen && <span className="ml-3 font-medium">{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="w-full flex items-center px-3 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-white transition-all"
          >
            {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            {isSidebarOpen && <span className="ml-3 font-medium">收合選單</span>}
          </button>
          <button 
            onClick={handleLogout}
            className="w-full mt-2 flex items-center px-3 py-3 rounded-xl text-rose-400 hover:bg-rose-500/10 hover:text-rose-500 transition-all"
          >
            <LogOut className="h-5 w-5" />
            {isSidebarOpen && <span className="ml-3 font-medium">登出系統</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-40">
          <div className="flex items-center flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input 
                type="text" 
                placeholder="搜尋用戶、交易或日誌..." 
                className="w-full pl-10 pr-4 py-2 bg-slate-100 border-transparent focus:bg-white focus:border-emerald-500 rounded-lg text-sm transition-all outline-none"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-all">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-white"></span>
            </button>
            <div className="h-8 w-px bg-slate-200 mx-2"></div>
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-bold text-slate-900">Super Admin</p>
                <p className="text-xs text-slate-500">{userEmail || '未登入'}</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold border-2 border-white shadow-sm">
                {userEmail ? userEmail.charAt(0).toUpperCase() : 'SA'}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
