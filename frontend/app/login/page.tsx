'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useGoogleLogin } from '@react-oauth/google';
import TiTiLogo from '@/components/TiTiLogo';
import { useAuth } from '@/lib/auth-context';
import { setRememberMe as setRememberMePref } from '@/lib/api/client';

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

  // Google SSO via useGoogleLogin hook — opens Google consent popup,
  // returns an auth code that we exchange for an ID token on the backend.
  // Using implicit flow to get id_token directly.
  const googleLogin = useGoogleLogin({
    flow: 'implicit',
    onSuccess: async (tokenResponse) => {
      setIsLoading(true);
      setError(null);
      setRememberMePref(rememberMe);
      try {
        // Fetch user info from Google to get the ID token
        const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        const userInfo = await res.json();
        // Use the access_token for backend verification
        const { redirect_to } = await loginWithGoogle(tokenResponse.access_token);
        router.push(redirect_to || '/dashboard');
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Google 登入失敗';
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    onError: () => setError('Google 登入失敗'),
  });

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-sm w-full space-y-6 bg-white p-8 rounded-2xl shadow-lg border border-slate-100">
        {/* Logo + Title */}
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center mb-3">
            <TiTiLogo size={40} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">歡迎回來</h2>
          <p className="mt-1 text-sm text-slate-500">
            登入以繼續你的學習旅程
          </p>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 text-rose-600 text-sm rounded-xl border border-rose-100">
            {error}
          </div>
        )}

        {/* Email + Password form */}
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <input
              id="email-address"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-shadow"
              placeholder="電子郵件"
            />
          </div>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 pr-10 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-shadow"
              placeholder="密碼"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
              <input type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="h-3.5 w-3.5 rounded border-slate-300 text-slate-900 focus:ring-slate-900" />
              記住我
            </label>
            <Link href="/forgot-password" className="text-slate-500 hover:text-slate-900 transition-colors">
              忘記密碼？
            </Link>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors disabled:opacity-50 flex items-center justify-center"
          >
            {isLoading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />}
            以 Email 繼續
          </button>
        </form>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200" /></div>
          <div className="relative flex justify-center"><span className="px-3 bg-white text-xs text-slate-400 uppercase tracking-wider">或</span></div>
        </div>

        {/* Google SSO — Notion-style custom button */}
        <button
          type="button"
          onClick={() => googleLogin()}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-200 transition-all disabled:opacity-50"
        >
          <svg className="h-4.5 w-4.5" viewBox="0 0 24 24" width="18" height="18">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
          以 Google 繼續
        </button>

        {/* Sign up link */}
        <p className="text-center text-sm text-slate-500">
          還沒有帳號？{' '}
          <Link href="/signup" className="font-medium text-slate-900 hover:underline">
            免費註冊 <ArrowRight className="inline h-3.5 w-3.5" />
          </Link>
        </p>
      </div>
    </div>
  );
}
