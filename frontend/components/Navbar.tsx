/**
 * @file 全站主導覽列——含品牌標誌、主要連結、訂閱徽章、行動裝置選單與登入登出入口。
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { BookOpen, LayoutDashboard, BrainCircuit, PenTool, Dumbbell, User, Menu, X, LogOut, ShieldCheck, Building2, Calendar } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '@/lib/auth-context';
import TiTiLogo from '@/components/TiTiLogo';

/**
 * 全站 Navbar。
 *
 * 主連結固定為儀表板 / 學習庫 / 測驗 / 練習 / AI 教練；ULTRA 或 ADMIN 額外顯示「教育管理」，
 * ADMIN 另顯示「平台管理」入口；右側依訂閱方案顯示 Pro / Ultra / Admin 徽章；
 * < md 寬度顯示漢堡選單。
 */
export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated, user, signOut, isPro, isUltra, isAdmin } = useAuth();

  const navLinks = [
    { href: '/dashboard', label: '儀表板', icon: LayoutDashboard },
    { href: '/knowledge', label: '學習庫', icon: BookOpen },
    { href: '/exam/setup', label: '測驗', icon: PenTool },
    { href: '/practice', label: '練習', icon: Dumbbell },
    { href: '/schedule', label: '排程', icon: Calendar },
    { href: '/review', label: 'AI 教練', icon: BrainCircuit },
    // 教育管理：ULTRA tier 用戶；管理者帳號（ADMIN/SUPER_ADMIN）亦自動含
    ...(isUltra || isAdmin ? [{ href: '/edu-console', label: '教育管理', icon: Building2 }] : []),
    // 平台管理：ADMIN + SUPER_ADMIN 皆可（管理者帳號）
    ...(isAdmin ? [{ href: '/super-admin/dashboard', label: '平台管理', icon: ShieldCheck }] : []),
  ];

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <button
            className="md:hidden text-slate-600 hover:text-emerald-600 transition-colors"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <Link href="/" className="flex items-center gap-2">
            <TiTiLogo size={28} />
          </Link>
        </div>

        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors flex items-center gap-1"
            >
              <link.icon className="h-4 w-4" /> {link.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              {isAdmin && (
                <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 text-xs font-bold border border-rose-200">
                  Admin
                </span>
              )}
              {isUltra && !isAdmin && (
                <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-200">
                  Ultra
                </span>
              )}
              {isPro && !isUltra && !isAdmin && (
                <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  Pro
                </span>
              )}
              <Link href="/account" className="hidden sm:flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors">
                <div className="h-7 w-7 rounded-full bg-slate-200 flex items-center justify-center text-sm font-bold text-slate-600">
                  {user?.displayName?.charAt(0) || 'U'}
                </div>
                <span className="font-medium">{user?.displayName || '學習者'}</span>
              </Link>
              <button
                onClick={signOut}
                className="hidden sm:flex items-center gap-1 text-sm text-slate-400 hover:text-rose-500 transition-colors"
                title="登出"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </>
          ) : (
            <div className="hidden sm:flex items-center gap-4">
              <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                登入
              </Link>
              <Link href="/signup" className="rounded-full bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 transition-colors">
                免費註冊
              </Link>
            </div>
          )}
          <Link href="/account" className="sm:hidden text-slate-500 hover:text-slate-900">
            <User className="h-5 w-5" />
          </Link>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-slate-100 bg-white overflow-hidden"
          >
            <div className="flex flex-col p-4 space-y-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="flex items-center gap-3 text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors p-2 rounded-lg hover:bg-slate-50"
                  onClick={() => setIsOpen(false)}
                >
                  <link.icon className="h-5 w-5" /> {link.label}
                </Link>
              ))}
              <div className="pt-4 border-t border-slate-100 flex flex-col gap-3">
                {isAuthenticated ? (
                  <>
                    <Link
                      href="/account"
                      className="flex items-center gap-3 text-sm font-medium text-slate-600 p-2 rounded-lg hover:bg-slate-50"
                      onClick={() => setIsOpen(false)}
                    >
                      <User className="h-5 w-5" /> 帳號設定
                    </Link>
                    <button
                      onClick={() => { signOut(); setIsOpen(false); }}
                      className="flex items-center gap-3 text-sm font-medium text-rose-500 p-2 rounded-lg hover:bg-rose-50"
                    >
                      <LogOut className="h-5 w-5" /> 登出
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      className="text-center py-2 text-sm font-medium text-slate-600 hover:text-slate-900"
                      onClick={() => setIsOpen(false)}
                    >
                      登入
                    </Link>
                    <Link
                      href="/signup"
                      className="text-center rounded-full bg-emerald-500 py-2 text-sm font-medium text-white hover:bg-emerald-600 transition-colors"
                      onClick={() => setIsOpen(false)}
                    >
                      免費註冊
                    </Link>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
