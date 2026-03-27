'use client';

import { BrainCircuit } from 'lucide-react';
import { useOnboarding } from '@/lib/onboarding-context';

const educationOptions = [
  '國中',
  '高中·高職',
  '專科',
  '大學',
  '碩士',
  '博士',
  '其他',
];

const ageOptions = Array.from({ length: 56 }, (_, i) => i + 15); // 15–70

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
      <p className="text-slate-500 mb-2">
        讓我們花不到 2 分鐘，為你打造專屬的學習計畫。
      </p>
      <p className="text-sm text-emerald-600 mb-8">
        填寫個人資訊有助於 AI 教練提供更適合您的學習建議
      </p>

      <div className="w-full space-y-5">
        {/* Display name input */}
        <div>
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

        {/* Age select */}
        <div>
          <label htmlFor="age" className="block text-sm font-medium text-slate-700 text-left mb-2">
            年齡
            <span className="ml-1 text-xs text-slate-400 font-normal">(選填)</span>
          </label>
          <select
            id="age"
            value={formData.age ?? ''}
            onChange={e => {
              const val = e.target.value;
              updateFormData({ age: val ? Number(val) : undefined });
            }}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
          >
            <option value="">請選擇年齡</option>
            {ageOptions.map(age => (
              <option key={age} value={age}>{age} 歲</option>
            ))}
          </select>
        </div>

        {/* Education select */}
        <div>
          <label htmlFor="education" className="block text-sm font-medium text-slate-700 text-left mb-2">
            最高學歷
            <span className="ml-1 text-xs text-slate-400 font-normal">(選填)</span>
          </label>
          <select
            id="education"
            value={formData.education ?? ''}
            onChange={e => {
              const val = e.target.value;
              updateFormData({ education: val || undefined });
            }}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
          >
            <option value="">請選擇學歷</option>
            {educationOptions.map(edu => (
              <option key={edu} value={edu}>{edu}</option>
            ))}
          </select>
        </div>

        {/* Occupation input */}
        <div>
          <label htmlFor="occupation" className="block text-sm font-medium text-slate-700 text-left mb-2">
            職業 / 領域
            <span className="ml-1 text-xs text-slate-400 font-normal">(選填)</span>
          </label>
          <input
            id="occupation"
            type="text"
            value={formData.occupation ?? ''}
            onChange={e => {
              const val = e.target.value;
              updateFormData({ occupation: val || undefined });
            }}
            placeholder="例如：軟體工程師、會計師、學生"
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
      </div>
    </div>
  );
}
