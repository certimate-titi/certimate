'use client';

import { useState } from 'react';
import Link from 'next/link';
import { BrainCircuit, ArrowLeft, Mail, CheckCircle2 } from 'lucide-react';
import { sendPasswordResetEmail } from 'firebase/auth';
import { auth } from '@/firebase';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      await sendPasswordResetEmail(auth, email.trim());
      setSent(true);
    } catch (err: any) {
      console.error(err);
      if (err.code === 'auth/user-not-found') {
        setError('找不到此電子郵件對應的帳號。');
      } else if (err.code === 'auth/invalid-email') {
        setError('請輸入有效的電子郵件地址。');
      } else {
        setError('發送失敗，請稍後再試。');
      }
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
          <h2 className="text-3xl font-extrabold text-slate-900">忘記密碼</h2>
          <p className="mt-2 text-sm text-slate-600">
            輸入你的電子郵件，我們將發送重設密碼的連結給你。
          </p>
        </div>

        {sent ? (
          <div className="text-center space-y-6">
            <div className="mx-auto h-16 w-16 bg-emerald-100 rounded-full flex items-center justify-center">
              <CheckCircle2 className="h-10 w-10 text-emerald-500" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">重設信件已寄出！</h3>
              <p className="text-sm text-slate-600">
                請檢查 <span className="font-medium text-slate-900">{email}</span> 的收件匣，點擊信中的連結來重設密碼。
              </p>
            </div>
            <p className="text-xs text-slate-400">
              沒有收到？請檢查垃圾郵件匣，或稍待幾分鐘後再試。
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-sm font-medium text-emerald-600 hover:text-emerald-500"
            >
              <ArrowLeft className="h-4 w-4" /> 返回登入頁
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 space-y-6">
            <div>
              <label htmlFor="reset-email" className="block text-sm font-medium text-slate-700 mb-1">
                電子郵件
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  id="reset-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none rounded-xl block w-full pl-10 pr-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 text-rose-600 text-sm rounded-xl border border-rose-100">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !email.trim()}
              className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                '發送重設連結'
              )}
            </button>

            <div className="text-center">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 text-sm font-medium text-emerald-600 hover:text-emerald-500"
              >
                <ArrowLeft className="h-4 w-4" /> 返回登入頁
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
