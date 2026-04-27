/**
 * @file 路由 `/onboarding` — 新手引導流程頁。
 *
 * 四步驟（Welcome → SubjectPicker → Preferences → Confirmation），
 * 由 `OnboardingProvider` 管理狀態；草稿存於 `localStorage.certimate_onboarding_draft`。
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { OnboardingProvider, useOnboarding } from '@/lib/onboarding-context';
import OnboardingProgress from '@/components/onboarding/OnboardingProgress';
import StepWelcome from '@/components/onboarding/StepWelcome';
import SubjectPicker from '@/components/onboarding/SubjectPicker';
import StepPreferences from '@/components/onboarding/StepPreferences';
import StepConfirmation from '@/components/onboarding/StepConfirmation';

function OnboardingContent() {
  const { currentStep, formData, goNext, goBack, updateFormData } = useOnboarding();
  const [validationError, setValidationError] = useState('');

  const handleNext = () => {
    const ok = goNext();
    if (!ok && currentStep === 2) {
      setValidationError('請至少選擇一個備考科目');
    } else {
      setValidationError('');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Progress bar */}
      <div className="bg-white border-b border-slate-200 py-6 px-4">
        <OnboardingProgress currentStep={currentStep} />
      </div>

      {/* Step content */}
      <div className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        {currentStep === 1 && <StepWelcome />}
        {currentStep === 2 && (
          <div>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-slate-900">選擇你的備考科目</h2>
              <p className="text-sm text-slate-500 mt-1">支援同時備考多個科目，每科獨立追蹤</p>
            </div>
            <SubjectPicker
              mode="onboarding"
              initialSelected={formData.subjects}
              onConfirm={subjects => updateFormData({ subjects })}
            />
            {validationError && (
              <p className="text-sm text-rose-500 text-center mt-4">{validationError}</p>
            )}
          </div>
        )}
        {currentStep === 3 && <StepPreferences />}
        {currentStep === 4 && <StepConfirmation />}
      </div>

      {/* Navigation buttons */}
      {currentStep < 4 && (
        <div className="bg-white border-t border-slate-200 py-4 px-4">
          <div className="container mx-auto max-w-4xl flex justify-between">
            <button
              onClick={goBack}
              disabled={currentStep === 1}
              className="flex items-center gap-1 px-6 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" /> 上一步
            </button>
            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold transition-colors"
            >
              下一步 <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OnboardingPage() {
  const { isAuthenticated, loading, onboardingCompleted } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (onboardingCompleted) {
      router.replace('/dashboard');
    }
  }, [loading, isAuthenticated, onboardingCompleted, router]);

  if (loading || !isAuthenticated || onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <OnboardingProvider>
      <OnboardingContent />
    </OnboardingProvider>
  );
}
