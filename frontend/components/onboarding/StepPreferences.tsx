'use client';

import { useState } from 'react';
import { Zap, BookOpen, Sparkles } from 'lucide-react';
import { useOnboarding } from '@/lib/onboarding-context';
import type { LearningStyle } from '@/types';

const timeOptions = [
  { value: 15, label: '15 分鐘' },
  { value: 30, label: '30 分鐘' },
  { value: 60, label: '1 小時' },
  { value: -1, label: '自訂' },
];

const styleOptions: { value: LearningStyle; icon: typeof Zap; title: string; desc: string }[] = [
  { value: 'drill', icon: Zap, title: '大量刷題模式', desc: '以題目驅動，快速找出盲點' },
  { value: 'concept', icon: BookOpen, title: '觀念理解優先', desc: '先讀懂再做題，穩紮穩打' },
  { value: 'hybrid', icon: Sparkles, title: '混合模式', desc: '系統智慧搭配，兼顧理解與練習' },
];

export default function StepPreferences() {
  const { formData, updateFormData } = useOnboarding();
  const [showCustom, setShowCustom] = useState(
    !timeOptions.some(o => o.value === formData.dailyStudyMinutes)
  );

  const handleTimeSelect = (value: number) => {
    if (value === -1) {
      setShowCustom(true);
    } else {
      setShowCustom(false);
      updateFormData({ dailyStudyMinutes: value });
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-8">
      {/* Daily study time */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">每日可投入學習時間</h3>
        <p className="text-sm text-slate-500 mb-4">選擇適合你的學習節奏</p>

        <div className="flex gap-2 flex-wrap">
          {timeOptions.map(opt => (
            <button
              key={opt.value}
              onClick={() => handleTimeSelect(opt.value)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                (opt.value === -1 && showCustom) ||
                (!showCustom && opt.value === formData.dailyStudyMinutes)
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {showCustom && (
          <div className="mt-3 flex items-center gap-2">
            <input
              type="number"
              min={5}
              max={480}
              value={formData.dailyStudyMinutes}
              onChange={e => {
                const v = parseInt(e.target.value, 10);
                if (!isNaN(v)) updateFormData({ dailyStudyMinutes: Math.max(5, Math.min(480, v)) });
              }}
              className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
            <span className="text-sm text-slate-500">分鐘</span>
          </div>
        )}
      </div>

      {/* Learning style */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">偏好學習方式</h3>
        <p className="text-sm text-slate-500 mb-4">選一個最適合你的模式</p>

        <div className="space-y-3">
          {styleOptions.map(opt => {
            const Icon = opt.icon;
            const active = formData.learningStyle === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => updateFormData({ learningStyle: opt.value })}
                className={`w-full text-left flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                  active
                    ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                    : 'border-slate-200 hover:border-emerald-300'
                }`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                  active ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-500'
                }`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-bold text-sm text-slate-900">
                    {opt.title}
                    {opt.value === 'hybrid' && (
                      <span className="ml-2 text-[10px] font-medium bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">推薦</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{opt.desc}</p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <p className="text-xs text-slate-400 text-center">
        此步驟全為選填，你可以直接「下一步」採用預設值。
      </p>
    </div>
  );
}
