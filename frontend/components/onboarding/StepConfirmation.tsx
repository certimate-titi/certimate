'use client';

import { Pencil, Rocket } from 'lucide-react';
import { useOnboarding } from '@/lib/onboarding-context';

const assessmentLabels = {
  beginner: '初學者',
  intermediate: '有基礎',
  advanced: '進階複習',
};

const styleLabels = {
  drill: '大量刷題模式',
  concept: '觀念理解優先',
  hybrid: '混合模式',
};

export default function StepConfirmation() {
  const { formData, goToStep, submitOnboarding, submitting } = useOnboarding();

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="text-center mb-2">
        <h2 className="text-2xl font-bold text-slate-900">確認你的學習計畫</h2>
        <p className="text-sm text-slate-500 mt-1">檢查以下設定，準備好就出發！</p>
      </div>

      {/* Display name */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-slate-500">顯示名稱</span>
          <button onClick={() => goToStep(1)} className="text-emerald-600 hover:text-emerald-700">
            <Pencil className="h-3.5 w-3.5" />
          </button>
        </div>
        <p className="font-bold text-slate-900">{formData.displayName || '(未設定)'}</p>
      </div>

      {/* Subjects */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-500">備考科目 ({formData.subjects.length})</span>
          <button onClick={() => goToStep(2)} className="text-emerald-600 hover:text-emerald-700">
            <Pencil className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="space-y-2">
          {formData.subjects.map(s => (
            <div key={s.subjectId} className="flex items-center justify-between bg-slate-50 rounded-lg p-3">
              <div>
                <span className="font-bold text-sm text-slate-900">{s.subjectName}</span>
                <span className="ml-2 text-xs text-slate-500">{assessmentLabels[s.selfAssessment]}</span>
              </div>
              <span className="text-xs text-slate-500">{s.examDate}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Preferences */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-500">學習偏好</span>
          <button onClick={() => goToStep(3)} className="text-emerald-600 hover:text-emerald-700">
            <Pencil className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500">每日學習時間</span>
            <span className="font-medium text-slate-900">{formData.dailyStudyMinutes} 分鐘</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">學習方式</span>
            <span className="font-medium text-slate-900">{styleLabels[formData.learningStyle]}</span>
          </div>
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={submitOnboarding}
        disabled={submitting}
        className="w-full py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-lg transition-all shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {submitting ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            啟動中...
          </>
        ) : (
          <>
            <Rocket className="h-5 w-5" />
            開始我的學習旅程
          </>
        )}
      </button>
    </div>
  );
}
