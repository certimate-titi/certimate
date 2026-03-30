'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, XCircle, ArrowRight, Loader2 } from 'lucide-react';
import TiTiLogo from '@/components/TiTiLogo';
import { authService } from '@/lib/api/services';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('驗證連結無效');
      return;
    }

    authService.verifyEmail(token)
      .then((res) => {
        setStatus('success');
        setMessage(res.message || '帳號驗證成功！');
      })
      .catch((err) => {
        setStatus('error');
        try {
          const parsed = JSON.parse(err.message.replace(/^API Error \d+: /, ''));
          setMessage(parsed.detail || '驗證連結無效或已過期');
        } catch {
          setMessage('驗證連結無效或已過期');
        }
      });
  }, [token]);

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4">
      <div className="max-w-md w-full bg-white p-10 rounded-3xl shadow-xl border border-slate-100 text-center">
        <div className="mx-auto flex items-center justify-center mb-6">
          <TiTiLogo size={48} />
        </div>

        {status === 'loading' && (
          <>
            <Loader2 className="mx-auto h-12 w-12 text-emerald-500 animate-spin mb-4" />
            <h2 className="text-xl font-bold text-slate-900 mb-2">正在驗證您的帳號...</h2>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="mx-auto w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="h-8 w-8 text-emerald-500" />
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 mb-2">驗證成功！</h2>
            <p className="text-sm text-slate-600 mb-8">{message}</p>
            <Link
              href="/login"
              className="inline-flex items-center justify-center w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold rounded-xl transition-colors"
            >
              前往登入 <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="mx-auto w-16 h-16 bg-rose-50 rounded-full flex items-center justify-center mb-4">
              <XCircle className="h-8 w-8 text-rose-500" />
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 mb-2">驗證失敗</h2>
            <p className="text-sm text-slate-600 mb-8">{message}</p>
            <Link
              href="/signup"
              className="inline-flex items-center justify-center w-full py-3 px-4 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              重新註冊
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
