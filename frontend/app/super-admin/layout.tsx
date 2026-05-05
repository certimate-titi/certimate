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
  // 考綱逆向工程（F26）/ 知識樹合併（F29）— 已轉為後台自動觸發功能：
  //   - F26：考古題 ImportTask 完成時自動觸發 ReverseEngineeringService
  //   - F29：每次資源上傳完成時自動觸發 KnowledgeMergeService
  // Admin 不再需要手動入口；如需 monitoring/override 走後端 admin endpoints。
];

export default function SuperAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // desktop: 收合 / 展開（icon-only vs full）
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  // mobile: drawer 開關（< lg 用 overlay 形式）
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
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
      {/* Mobile drawer backdrop */}
      {isMobileDrawerOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/40 z-40"
          onClick={() => setIsMobileDrawerOpen(false)}
        />
      )}

      {/* Sidebar
          - mobile (< lg)：固定 overlay drawer，預設隱藏
          - desktop (≥ lg)：常駐 column，可在展開 (w-64) 與收合 (w-20) 之間切換 */}
      <aside
        className={cn(
          "bg-slate-900 text-white transition-all duration-300 ease-in-out flex flex-col z-50",
          // mobile drawer
          "fixed inset-y-0 left-0 w-64 lg:static",
          isMobileDrawerOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          // desktop width
          isSidebarOpen ? "lg:w-64" : "lg:w-20"
        )}
      >
        {/* Drawer 頂部品牌列（僅 mobile 顯示） */}
        <div className="lg:hidden flex items-center justify-between px-4 h-16 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-2">
            <TiTiLogo size={26} />
            <span className="font-bold text-sm">平台管理</span>
          </div>
          <button
            onClick={() => setIsMobileDrawerOpen(false)}
            className="p-2 text-slate-400 hover:text-white"
            aria-label="關閉選單"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 py-4 space-y-1 px-3 overflow-y-auto">
          {sidebarItems.map((item) => {
            // 容忍 trailing slash（Next.js static export + Firebase rewrite 會帶 / 或不帶）
            // 並用 startsWith 容忍子路徑
            const normalizedPath = pathname?.replace(/\/$/, '') ?? '';
            const isActive =
              normalizedPath === item.href ||
              normalizedPath.startsWith(item.href + '/');
            // mobile drawer 開啟時，永遠顯示 label；desktop 則依 isSidebarOpen
            const showLabel = isMobileDrawerOpen || isSidebarOpen;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileDrawerOpen(false)}
                className={cn(
                  "flex items-center px-3 py-3 rounded-xl transition-all group",
                  isActive
                    ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon className={cn("h-5 w-5 shrink-0", isActive ? "text-white" : "group-hover:text-emerald-400")} />
                {showLabel && <span className="ml-3 font-medium">{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800 shrink-0">
          {/* desktop 才顯示「收合 / 展開」（mobile 用右上 X 關閉） */}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="hidden lg:flex w-full items-center px-3 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-white transition-all"
          >
            {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            {isSidebarOpen && <span className="ml-3 font-medium">收合選單</span>}
          </button>
          <button
            onClick={handleLogout}
            className="w-full mt-2 flex items-center px-3 py-3 rounded-xl text-rose-400 hover:bg-rose-500/10 hover:text-rose-500 transition-all"
          >
            <LogOut className="h-5 w-5" />
            {(isMobileDrawerOpen || isSidebarOpen) && <span className="ml-3 font-medium">登出系統</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-3 sm:px-6 lg:px-8 sticky top-0 z-30 gap-2">
          {/* Mobile hamburger（lg 以上隱藏） */}
          <button
            onClick={() => setIsMobileDrawerOpen(true)}
            className="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg shrink-0"
            aria-label="開啟選單"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center flex-1 max-w-md min-w-0">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="搜尋用戶、交易或日誌..."
                className="w-full pl-10 pr-3 py-2 bg-slate-100 border-transparent focus:bg-white focus:border-emerald-500 rounded-lg text-sm transition-all outline-none"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 shrink-0">
            <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-all">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-white"></span>
            </button>
            <div className="hidden sm:block h-8 w-px bg-slate-200 mx-2"></div>
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="text-right hidden md:block">
                <p className="text-sm font-bold text-slate-900">Super Admin</p>
                <p className="text-xs text-slate-500 truncate max-w-[180px]">{userEmail || '未登入'}</p>
              </div>
              <div className="h-9 w-9 sm:h-10 sm:w-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold border-2 border-white shadow-sm">
                {userEmail ? userEmail.charAt(0).toUpperCase() : 'SA'}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-3 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
