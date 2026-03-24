'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { BrainCircuit, ArrowRight } from 'lucide-react';
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { auth } from '@/firebase';
import { useAuth } from '@/lib/auth-context';
import type { SubscriptionTier, UserRole } from '@/types';

const MOCK_ACCOUNTS: {
  label: string;
  email: string;
  displayName: string;
  tier: SubscriptionTier;
  role: UserRole;
  onboardingDone: boolean;
  badge: string;
  badgeColor: string;
}[] = [
  { label: 'user1 — 新用戶', email: 'user1@test.com', displayName: 'User1 新用戶', tier: 'FREE', role: 'USER', onboardingDone: false, badge: 'NEW', badgeColor: 'bg-slate-100 text-slate-600' },
  { label: 'user2 — PRO', email: 'user2@test.com', displayName: 'User2 PRO', tier: 'PRO_199', role: 'USER', onboardingDone: true, badge: 'PRO', badgeColor: 'bg-emerald-100 text-emerald-700' },
  { label: 'proplus — PRO PLUS', email: 'proplus@test.com', displayName: 'ProPlus 用戶', tier: 'PRO_PLUS_399', role: 'USER', onboardingDone: true, badge: 'PRO+', badgeColor: 'bg-yellow-100 text-yellow-700' },
  { label: 'ultra — 教育管理', email: 'ultra@test.com', displayName: 'Ultra 教育管理員', tier: 'ULTRA_1599', role: 'USER', onboardingDone: true, badge: 'ULTRA', badgeColor: 'bg-indigo-100 text-indigo-700' },
  { label: 'admin — 平台管理', email: 'admin@test.com', displayName: '平台管理者', tier: 'FREE', role: 'ADMIN', onboardingDone: true, badge: 'ADMIN', badgeColor: 'bg-rose-100 text-rose-700' },
];

export default function LoginPage() {
  const router = useRouter();
  const { onboardingCompleted, loginAsDemoUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleMockLogin = (account: typeof MOCK_ACCOUNTS[0]) => {
    loginAsDemoUser(
      { email: account.email, displayName: account.displayName, role: account.role },
      account.tier,
      account.onboardingDone,
    );
    router.push(account.onboardingDone ? '/dashboard' : '/onboarding');
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      router.push(onboardingCompleted ? '/dashboard' : '/onboarding');
    } catch (err: any) {
      console.error(err);
      setError(err.message || '登入失敗，請稍後再試。');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
            <BrainCircuit className="h-8 w-8 text-emerald-600" />
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900">歡迎回來</h2>
          <p className="mt-2 text-sm text-slate-600">
            登入以繼續你的學習旅程
          </p>
        </div>
        
        <form className="mt-8 space-y-6" action="#" method="POST">
          <div className="space-y-4">
            <div>
              <label htmlFor="email-address" className="sr-only">電子郵件</label>
              <input id="email-address" name="email" type="email" autoComplete="email" required className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm" placeholder="電子郵件" />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">密碼</label>
              <input id="password" name="password" type="password" autoComplete="current-password" required className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm" placeholder="密碼" />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-slate-300 rounded" />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-900">
                記住我
              </label>
            </div>

            <div className="text-sm">
              <Link href="/forgot-password" className="font-medium text-emerald-600 hover:text-emerald-500">
                忘記密碼？
              </Link>
            </div>
          </div>

          <div>
            <button type="submit" className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors">
              登入
            </button>
          </div>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-slate-500">
                或使用以下方式登入
              </span>
            </div>
          </div>

          <div className="mt-6">
            {error && (
              <div className="mb-4 p-3 bg-rose-50 text-rose-600 text-sm rounded-xl border border-rose-100">
                {error}
              </div>
            )}
            <button 
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center px-4 py-3 border border-slate-300 rounded-xl shadow-sm bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mr-2"></div>
              ) : (
                <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
              )}
              Google 登入
            </button>
          </div>
        </div>

        <p className="mt-8 text-center text-sm text-slate-600">
          還沒有帳號？{' '}
          <Link href="/signup" className="font-medium text-emerald-600 hover:text-emerald-500">
            免費註冊 <ArrowRight className="inline h-4 w-4" />
          </Link>
        </p>

        {/* Dev Quick Login */}
        <div className="mt-6 border-t border-dashed border-slate-200 pt-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3 text-center">
            🛠 開發快速登入（密碼：123）
          </p>
          <div className="grid grid-cols-2 gap-2">
            {MOCK_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                onClick={() => handleMockLogin(account)}
                className="flex items-center justify-between px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-left text-xs font-medium text-slate-700 transition-colors"
              >
                <span className="truncate mr-1">{account.label}</span>
                <span className={`shrink-0 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${account.badgeColor}`}>
                  {account.badge}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
