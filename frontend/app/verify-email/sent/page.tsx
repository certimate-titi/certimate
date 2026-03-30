'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Mail, ArrowRight, RefreshCw, Loader2 } from 'lucide-react';
import TiTiLogo from '@/components/TiTiLogo';
import { authService } from '@/lib/api/services';

function SentContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const [cooldown, setCooldown] = useState(0);
  const [resent, setResent] = useState(false);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const handleResend = async () => {
    if (cooldown > 0 || !email) return;
    setCooldown(60);
    setResent(false);
    try {
      await authService.resendVerification(email);
      setResent(true);
    } catch {
      // silent fail
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4">
      <div className="max-w-md w-full bg-white p-10 rounded-3xl shadow-xl border border-slate-100 text-center">
        <div className="mx-auto flex items-center justify-center mb-4">
          <TiTiLogo size={48} />
        </div>

        <div className="mx-auto w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mb-6">
          <Mail className="h-8 w-8 text-emerald-500" />
        </div>

        <h2 className="text-2xl font-extrabold text-slate-900 mb-2">請查收驗證信</h2>
        <p className="text-sm text-slate-600 mb-1">我們已寄送驗證信至：</p>
        <p className="text-sm font-bold text-slate-900 mb-6">{email || '您的信箱'}</p>

        <p className="text-sm text-slate-500 mb-8">
          請點擊信中的連結完成帳號驗證。<br />
          驗證連結將於 24 小時後失效。
        </p>

        {resent && (
          <div className="p-3 bg-emerald-50 text-emerald-700 text-sm rounded-xl border border-emerald-100 mb-4">
            驗證信已重新寄出！
          </div>
        )}

        <button
          onClick={handleResend}
          disabled={cooldown > 0}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mb-4"
        >
          <RefreshCw className="h-4 w-4" />
          {cooldown > 0 ? `重寄驗證信 (${cooldown}s)` : '重寄驗證信'}
        </button>

        <Link
          href="/login"
          className="inline-flex items-center text-sm font-medium text-emerald-600 hover:text-emerald-500"
        >
          前往登入 <ArrowRight className="ml-1 h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

export default function VerifyEmailSentPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
      </div>
    }>
      <SentContent />
    </Suspense>
  );
}
