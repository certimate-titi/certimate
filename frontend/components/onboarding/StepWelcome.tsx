'use client';

import { BrainCircuit } from 'lucide-react';
import { useOnboarding } from '@/lib/onboarding-context';

export default function StepWelcome() {
  const { formData, updateFormData } = useOnboarding();

  return (
    <div className="flex flex-col items-center text-center max-w-md mx-auto">
      {/* Welcome animation */}
      <div className="relative mb-8">
        <div className="w-24 h-24 bg-emerald-100 rounded-full flex items-center justify-center animate-[scale-in_0.6s_ease-out]">
          <BrainCircuit className="h-12 w-12 text-emerald-600" />
        </div>
        <div className="absolute inset-0 w-24 h-24 bg-emerald-200/50 rounded-full animate-ping" />
      </div>

      <h2 className="text-3xl font-bold text-slate-900 mb-3">
        歡迎加入 CertiMate！
      </h2>
      <p className="text-slate-500 mb-8">
        讓我們花不到 2 分鐘，為你打造專屬的學習計畫。
      </p>

      {/* Display name input */}
      <div className="w-full">
        <label htmlFor="displayName" className="block text-sm font-medium text-slate-700 text-left mb-2">
          你希望我們怎麼稱呼你？
        </label>
        <input
          id="displayName"
          type="text"
          value={formData.displayName}
          onChange={e => updateFormData({ displayName: e.target.value })}
          placeholder="輸入你的暱稱"
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
        <p className="text-xs text-slate-400 mt-2 text-left">
          可以直接跳過，之後隨時可以修改。
        </p>
      </div>
    </div>
  );
}
