'use client';

import { useState } from 'react';
import { Pencil, Rocket } from 'lucide-react';
import { useOnboarding } from '@/lib/onboarding-context';
import { getModeBadge } from './SelectedSubjectCard';

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
  const [showLaunchAnimation, setShowLaunchAnimation] = useState(false);

  const handleLaunch = async () => {
    await submitOnboarding();
    setShowLaunchAnimation(true);
    // The redirect happens after the animation (1.5s) — see onboarding-context
  };

  if (showLaunchAnimation) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white">
        <div className="flex flex-col items-center launch-celebration">
          <span className="text-7xl mb-4">&#127881;</span>
          <p className="text-2xl font-bold text-slate-900">準備就緒！</p>
          <p className="text-sm text-slate-500 mt-2">正在啟動你的學習旅程...</p>
        </div>
        <style jsx>{`
          .launch-celebration {
            animation: launchScaleFade 1.5s ease-out forwards;
          }
          @keyframes launchScaleFade {
            0% {
              opacity: 0;
              transform: scale(0.5);
            }
            30% {
              opacity: 1;
              transform: scale(1.1);
            }
            50% {
              transform: scale(1);
            }
            80% {
              opacity: 1;
              transform: scale(1);
            }
            100% {
              opacity: 0;
              transform: scale(1.2);
            }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="text-center mb-2">
        <h2 className="text-2xl font-bold text-slate-900">確認你的學習計畫</h2>
        <p className="text-sm text-slate-500 mt-1">檢查以下設定，準備好就出發！</p>
      </div>

      {/* Personal info */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-500">個人資訊</span>
          <button
            onClick={() => goToStep(1)}
            className="flex items-center gap-1 text-xs font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            <Pencil className="h-3 w-3" />
            編輯
          </button>
        </div>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500">顯示名稱</span>
            <span className="font-medium text-slate-900">{formData.displayName || '(未設定)'}</span>
          </div>
          {formData.age && (
            <div className="flex justify-between">
              <span className="text-slate-500">年齡</span>
              <span className="font-medium text-slate-900">{formData.age} 歲</span>
            </div>
          )}
          {formData.education && (
            <div className="flex justify-between">
              <span className="text-slate-500">最高學歷</span>
              <span className="font-medium text-slate-900">{formData.education}</span>
            </div>
          )}
          {formData.occupation && (
            <div className="flex justify-between">
              <span className="text-slate-500">職業 / 領域</span>
              <span className="font-medium text-slate-900">{formData.occupation}</span>
            </div>
          )}
        </div>
      </div>

      {/* Subjects */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-500">備考科目 ({formData.subjects.length})</span>
          <button
            onClick={() => goToStep(2)}
            className="flex items-center gap-1 text-xs font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            <Pencil className="h-3 w-3" />
            編輯
          </button>
        </div>
        <div className="space-y-2">
          {formData.subjects.map(s => {
            const badge = getModeBadge(s.examDate);
            return (
              <div key={s.subjectId} className="flex items-center justify-between bg-slate-50 rounded-lg p-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-sm text-slate-900">{s.subjectName}</span>
                  <span className="text-xs text-slate-500">{assessmentLabels[s.selfAssessment]}</span>
                  {badge && (
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${badge.className}`}>
                      {badge.label}
                    </span>
                  )}
                </div>
                <span className="text-xs text-slate-500 shrink-0 ml-2">{s.examDate}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Preferences */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-500">學習偏好</span>
          <button
            onClick={() => goToStep(3)}
            className="flex items-center gap-1 text-xs font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            <Pencil className="h-3 w-3" />
            編輯
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
        onClick={handleLaunch}
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
