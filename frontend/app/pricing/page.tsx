'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, X, Sparkles, GraduationCap, Zap, Crown } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

const PLANS = [
  {
    id: 'FREE',
    name: '免費方案',
    price: 0,
    priceLabel: 'NT$0',
    period: '永久免費',
    icon: Zap,
    color: 'slate',
    features: [
      { text: '每日 3 次 AI 對話', included: true },
      { text: '每月 3 份文件上傳', included: true },
      { text: '每月 3 次自建測驗', included: true },
      { text: '知識心智圖', included: true },
      { text: '錯題複習', included: true },
      { text: '學習週報', included: false },
      { text: '進階 AI 教練', included: false },
      { text: 'Bloom 自訂比例', included: false },
      { text: '分片上傳', included: false },
    ],
  },
  {
    id: 'PRO_199',
    name: 'PRO 方案',
    price: 199,
    priceLabel: 'NT$199',
    period: '/月',
    icon: Sparkles,
    color: 'blue',
    popular: true,
    features: [
      { text: '每日 20 次 AI 對話', included: true },
      { text: '每月 15 份文件上傳', included: true },
      { text: '每月 10 次自建測驗', included: true },
      { text: '知識心智圖', included: true },
      { text: '錯題複習', included: true },
      { text: '學習週報', included: true },
      { text: '進階 AI 教練', included: false },
      { text: 'Bloom 自訂比例', included: false },
      { text: '分片上傳', included: false },
    ],
  },
  {
    id: 'PRO_PLUS_399',
    name: 'PRO+ 方案',
    price: 399,
    priceLabel: 'NT$399',
    period: '/月',
    icon: Crown,
    color: 'purple',
    features: [
      { text: '每日 50 次 AI 對話', included: true },
      { text: '每月 50 份文件上傳', included: true },
      { text: '每月 30 次自建測驗', included: true },
      { text: '知識心智圖', included: true },
      { text: '錯題複習', included: true },
      { text: '學習週報', included: true },
      { text: '進階 AI 教練', included: false },
      { text: 'Bloom 自訂比例', included: false },
      { text: '分片上傳', included: false },
    ],
  },
  {
    id: 'ULTRA_1599',
    name: 'ULTRA 方案',
    price: 1599,
    priceLabel: 'NT$1,599',
    period: '/月',
    icon: GraduationCap,
    color: 'amber',
    features: [
      { text: '無限 AI 對話 (FUP)', included: true },
      { text: '無限文件上傳', included: true },
      { text: '無限自建測驗', included: true },
      { text: '知識心智圖', included: true },
      { text: '錯題複習', included: true },
      { text: '學習週報', included: true },
      { text: '進階 AI 教練', included: true },
      { text: 'Bloom 自訂比例', included: true },
      { text: '分片上傳（500MB）', included: true },
      { text: 'B2B 機構管理後台', included: true },
      { text: 'EDU 學生帳號（30 名）', included: true },
      { text: '考古題優先召回', included: true },
    ],
  },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; btn: string }> = {
  slate: { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-900', btn: 'bg-slate-900 hover:bg-slate-800' },
  blue: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-900', btn: 'bg-blue-600 hover:bg-blue-700' },
  purple: { bg: 'bg-purple-50', border: 'border-purple-300', text: 'text-purple-900', btn: 'bg-purple-600 hover:bg-purple-700' },
  amber: { bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-900', btn: 'bg-amber-600 hover:bg-amber-700' },
};

export default function PricingPage() {
  const { isAuthenticated, subscriptionTier, isTrial } = useAuth();
  const router = useRouter();

  const handleSelect = (planId: string) => {
    if (!isAuthenticated) {
      router.push('/login?redirect=/pricing');
      return;
    }
    if (planId === subscriptionTier) return;
    // TODO: 接 ECPay 付款流程
    router.push(`/account?upgrade=${planId}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">選擇你的備考方案</h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            從免費開始，隨時升級。所有方案皆含核心學習功能。
          </p>
          {isTrial && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-amber-100 text-amber-800 rounded-full text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              您正在使用 14 天免費試用
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map((plan) => {
            const colors = COLOR_MAP[plan.color];
            const isCurrent = plan.id === subscriptionTier;
            const Icon = plan.icon;

            return (
              <div
                key={plan.id}
                className={`relative rounded-2xl border-2 p-6 ${colors.bg} ${
                  plan.popular ? 'border-blue-500 shadow-lg scale-105' : colors.border
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full">
                    最受歡迎
                  </div>
                )}

                <div className="flex items-center gap-2 mb-4">
                  <Icon className={`h-6 w-6 ${colors.text}`} />
                  <h3 className={`text-lg font-bold ${colors.text}`}>{plan.name}</h3>
                </div>

                <div className="mb-6">
                  <span className="text-3xl font-bold text-slate-900">{plan.priceLabel}</span>
                  <span className="text-slate-500 ml-1">{plan.period}</span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      {f.included ? (
                        <Check className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                      ) : (
                        <X className="h-4 w-4 text-slate-300 mt-0.5 shrink-0" />
                      )}
                      <span className={f.included ? 'text-slate-700' : 'text-slate-400'}>
                        {f.text}
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSelect(plan.id)}
                  disabled={isCurrent}
                  className={`w-full py-2.5 rounded-lg text-white font-medium transition ${
                    isCurrent ? 'bg-slate-300 cursor-not-allowed' : colors.btn
                  }`}
                >
                  {isCurrent ? '目前方案' : plan.price === 0 ? '開始使用' : '立即升級'}
                </button>
              </div>
            );
          })}
        </div>

        {/* EDU 說明區 */}
        <div className="mt-16 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-2xl p-8 border border-emerald-200">
          <div className="flex items-start gap-4">
            <GraduationCap className="h-10 w-10 text-emerald-600 shrink-0" />
            <div>
              <h3 className="text-xl font-bold text-emerald-900 mb-2">EDU 學生方案</h3>
              <p className="text-emerald-700 mb-4">
                ULTRA 方案用戶可透過機構管理後台為學生建立 EDU 帳號。
                每個 ULTRA 方案包含 30 個免費學生帳號，超過部分每人每月 NT$30。
              </p>
              <ul className="grid sm:grid-cols-2 gap-2 text-sm text-emerald-700">
                <li className="flex items-center gap-2"><Check className="h-4 w-4" /> 每日 5 次 AI 對話</li>
                <li className="flex items-center gap-2"><Check className="h-4 w-4" /> 無限指派測驗作答</li>
                <li className="flex items-center gap-2"><Check className="h-4 w-4" /> 知識心智圖瀏覽</li>
                <li className="flex items-center gap-2"><Check className="h-4 w-4" /> 錯題複習</li>
                <li className="flex items-center gap-2"><Check className="h-4 w-4" /> 學習週報</li>
                <li className="flex items-center gap-2"><X className="h-4 w-4 text-slate-400" /> 文件上傳 / 自建測驗</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 14 天試用 CTA */}
        {isAuthenticated && subscriptionTier === 'FREE' && (
          <div className="mt-8 text-center">
            <div className="inline-flex flex-col items-center gap-3 p-6 bg-amber-50 border border-amber-200 rounded-2xl">
              <Sparkles className="h-8 w-8 text-amber-500" />
              <h3 className="text-lg font-bold text-amber-900">免費體驗 14 天 ULTRA 功能</h3>
              <p className="text-sm text-amber-700">無需信用卡，到期自動恢復原方案</p>
              <button
                onClick={() => router.push('/account?trial=start')}
                className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-lg transition"
              >
                開始免費試用
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
