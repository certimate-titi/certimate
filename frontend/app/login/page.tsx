'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, Eye, EyeOff } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import TiTiLogo from '@/components/TiTiLogo';
import { useAuth } from '@/lib/auth-context';
import { setRememberMe as setRememberMePref } from '@/lib/api/client';

const SUPER_ADMIN_ACCOUNT = {
  label: 'Super Admin',
  email: 'admin@certimate.com',
  password: 'admin123',
  badge: 'SA',
  badgeColor: 'bg-rose-100 text-rose-700',
};

export default function LoginPage() {
  const router = useRouter();
  const { loginWithCredentials, loginWithGoogle } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const doLogin = async (loginEmail: string, loginPassword: string) => {
    setIsLoading(true);
    setError(null);
    setRememberMePref(rememberMe);
    try {
      const { redirect_to } = await loginWithCredentials(loginEmail, loginPassword);
      router.push(redirect_to || '/dashboard');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '登入失敗';
      // Try to extract detail from backend error
      try {
        const parsed = JSON.parse(message.replace(/^API Error \d+: /, ''));
        setError(parsed.detail || '帳號或密碼錯誤');
      } catch {
        setError('帳號或密碼錯誤');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await doLogin(email, password);
  };

  const handleSuperAdminLogin = () => {
    doLogin(SUPER_ADMIN_ACCOUNT.email, SUPER_ADMIN_ACCOUNT.password);
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center mb-4">
            <TiTiLogo size={48} />
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900">歡迎回來</h2>
          <p className="mt-2 text-sm text-slate-600">
            登入以繼續你的學習旅程
          </p>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 text-rose-600 text-sm rounded-xl border border-rose-100">
            {error}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email-address" className="sr-only">電子郵件</label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm"
                placeholder="電子郵件"
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="sr-only">密碼</label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-xl relative block w-full px-4 py-3 pr-12 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm"
                placeholder="密碼"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input id="remember-me" name="remember-me" type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-slate-300 rounded" />
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
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              ) : null}
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

          <div className="mt-6 flex justify-center">
            <GoogleLogin
              onSuccess={async (credentialResponse) => {
                if (!credentialResponse.credential) {
                  setError('Google 登入失敗：未取得憑證');
                  return;
                }
                setIsLoading(true);
                setError(null);
                setRememberMePref(rememberMe);
                try {
                  const { redirect_to } = await loginWithGoogle(credentialResponse.credential);
                  router.push(redirect_to || '/dashboard');
                } catch (err: unknown) {
                  const msg = err instanceof Error ? err.message : 'Google 登入失敗';
                  setError(msg);
                } finally {
                  setIsLoading(false);
                }
              }}
              onError={() => setError('Google 登入失敗')}
              width="400"
              text="signin_with"
              shape="pill"
              logo_alignment="center"
            />
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
            🛠 開發快速登入
          </p>
          <button
            onClick={handleSuperAdminLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-left text-xs font-medium text-slate-700 transition-colors disabled:opacity-50"
          >
            <span className="truncate mr-1">{SUPER_ADMIN_ACCOUNT.label}</span>
            <span className={`shrink-0 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${SUPER_ADMIN_ACCOUNT.badgeColor}`}>
              {SUPER_ADMIN_ACCOUNT.badge}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
