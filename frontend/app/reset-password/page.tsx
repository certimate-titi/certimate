'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { BrainCircuit, ArrowLeft, Lock, CheckCircle2, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api/client';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const isLongEnough = password.length >= 8;
  const isStrong = hasUpper && hasLower && hasNumber && isLongEnough;
  const passwordsMatch = password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isStrong || !passwordsMatch) return;

    setIsLoading(true);
    setError(null);

    try {
      await apiClient.post('/auth/reset-password', { token, password });
      setSuccess(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '重設失敗，請重試';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4">
        <div className="max-w-md w-full bg-white p-10 rounded-3xl shadow-xl border border-slate-100 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-rose-500 mx-auto" />
          <h2 className="text-xl font-bold text-slate-900">連結無效</h2>
          <p className="text-sm text-slate-600">缺少重設密碼的驗證資訊，請從信件中的連結進入。</p>
          <Link href="/forgot-password" className="inline-flex items-center gap-2 text-sm font-medium text-emerald-600 hover:text-emerald-500">
            <ArrowLeft className="h-4 w-4" /> 重新申請重設密碼
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
            <BrainCircuit className="h-8 w-8 text-emerald-600" />
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900">重設密碼</h2>
          <p className="mt-2 text-sm text-slate-600">請設定您的新密碼</p>
        </div>

        {success ? (
          <div className="text-center space-y-6">
            <div className="mx-auto h-16 w-16 bg-emerald-100 rounded-full flex items-center justify-center">
              <CheckCircle2 className="h-10 w-10 text-emerald-500" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">密碼已重設成功！</h3>
              <p className="text-sm text-slate-600">您現在可以使用新密碼登入。</p>
            </div>
            <button
              onClick={() => router.push('/login')}
              className="w-full py-3 px-4 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition-colors"
            >
              前往登入
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="new-password" className="block text-sm font-medium text-slate-700 mb-1">
                新密碼
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none rounded-xl block w-full pl-10 pr-10 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm"
                  placeholder="至少 8 個字元"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {password && (
                <div className="mt-2 space-y-1">
                  <div className={`text-xs flex items-center gap-1.5 ${isLongEnough ? 'text-emerald-600' : 'text-slate-400'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${isLongEnough ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    至少 8 個字元
                  </div>
                  <div className={`text-xs flex items-center gap-1.5 ${hasUpper ? 'text-emerald-600' : 'text-slate-400'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasUpper ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    包含大寫字母
                  </div>
                  <div className={`text-xs flex items-center gap-1.5 ${hasLower ? 'text-emerald-600' : 'text-slate-400'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasLower ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    包含小寫字母
                  </div>
                  <div className={`text-xs flex items-center gap-1.5 ${hasNumber ? 'text-emerald-600' : 'text-slate-400'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasNumber ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    包含數字
                  </div>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-slate-700 mb-1">
                確認密碼
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  id="confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="appearance-none rounded-xl block w-full pl-10 pr-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm"
                  placeholder="再次輸入新密碼"
                />
              </div>
              {confirmPassword && !passwordsMatch && (
                <p className="mt-1 text-xs text-rose-500">兩次輸入的密碼不一致</p>
              )}
            </div>

            {error && (
              <div className="p-3 bg-rose-50 text-rose-600 text-sm rounded-xl border border-rose-100">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !isStrong || !passwordsMatch}
              className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                '設定新密碼'
              )}
            </button>

            <div className="text-center">
              <Link href="/login" className="inline-flex items-center gap-2 text-sm font-medium text-emerald-600 hover:text-emerald-500">
                <ArrowLeft className="h-4 w-4" /> 返回登入頁
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ResetPasswordForm />
    </Suspense>
  );
}
