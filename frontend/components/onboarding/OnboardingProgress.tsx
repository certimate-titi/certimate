'use client';

import { Check } from 'lucide-react';

interface OnboardingProgressProps {
  currentStep: 1 | 2 | 3 | 4;
}

const steps = [
  { label: '歡迎' },
  { label: '選擇科目' },
  { label: '學習偏好' },
  { label: '確認啟動' },
];

export default function OnboardingProgress({ currentStep }: OnboardingProgressProps) {
  return (
    <div className="flex items-center justify-center gap-0">
      {steps.map((step, i) => {
        const stepNum = (i + 1) as 1 | 2 | 3 | 4;
        const isCompleted = stepNum < currentStep;
        const isCurrent = stepNum === currentStep;

        return (
          <div key={i} className="flex items-center">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all
                  ${isCompleted ? 'bg-emerald-500 text-white' : ''}
                  ${isCurrent ? 'bg-emerald-500 text-white ring-4 ring-emerald-100' : ''}
                  ${!isCompleted && !isCurrent ? 'bg-slate-200 text-slate-400' : ''}
                `}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : stepNum}
              </div>
              <span
                className={`text-xs mt-1.5 font-medium ${
                  isCurrent ? 'text-emerald-600' : isCompleted ? 'text-slate-500' : 'text-slate-400'
                }`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line */}
            {i < steps.length - 1 && (
              <div
                className={`w-12 sm:w-20 h-0.5 mx-1 mb-5 ${
                  stepNum < currentStep ? 'bg-emerald-500' : 'bg-slate-200'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
