'use client';

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import type { OnboardingFormData, SelfAssessmentLevel, LearningStyle } from '@/types';
import { onboardingService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

const DRAFT_STORAGE_KEY = 'certimate_onboarding_draft';

interface OnboardingState {
  currentStep: 1 | 2 | 3 | 4;
  formData: OnboardingFormData;
  submitting: boolean;
}

type OnboardingAction =
  | { type: 'GO_TO_STEP'; step: 1 | 2 | 3 | 4 }
  | { type: 'UPDATE_FORM'; payload: Partial<OnboardingFormData> }
  | { type: 'SET_SUBMITTING'; value: boolean }
  | { type: 'RESTORE'; state: OnboardingState };

const defaultFormData: OnboardingFormData = {
  displayName: '',
  subjects: [],
  dailyStudyMinutes: 30,
  learningStyle: 'hybrid',
};

function reducer(state: OnboardingState, action: OnboardingAction): OnboardingState {
  switch (action.type) {
    case 'GO_TO_STEP':
      return { ...state, currentStep: action.step };
    case 'UPDATE_FORM':
      return { ...state, formData: { ...state.formData, ...action.payload } };
    case 'SET_SUBMITTING':
      return { ...state, submitting: action.value };
    case 'RESTORE':
      return action.state;
    default:
      return state;
  }
}

interface OnboardingContextValue {
  currentStep: 1 | 2 | 3 | 4;
  formData: OnboardingFormData;
  submitting: boolean;
  goNext: () => boolean;
  goBack: () => void;
  goToStep: (step: 1 | 2 | 3 | 4) => void;
  updateFormData: (data: Partial<OnboardingFormData>) => void;
  submitOnboarding: () => Promise<void>;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { setOnboardingCompleted, user } = useAuth();

  const initialState: OnboardingState = {
    currentStep: 1,
    formData: {
      ...defaultFormData,
      displayName: user?.email?.split('@')[0] ?? '',
    },
    submitting: false,
  };

  const [state, dispatch] = useReducer(reducer, initialState);

  // Restore draft from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(DRAFT_STORAGE_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved) as OnboardingState;
          parsed.submitting = false;
          dispatch({ type: 'RESTORE', state: parsed });
        } catch {
          // ignore invalid JSON
        }
      } else if (user?.email) {
        dispatch({
          type: 'UPDATE_FORM',
          payload: { displayName: user.email.split('@')[0] },
        });
      }
    }
  }, [user?.email]);

  // Persist draft to localStorage on changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(state));
    }
  }, [state]);

  const goNext = useCallback((): boolean => {
    // Validate Step 2: at least 1 subject
    if (state.currentStep === 2 && state.formData.subjects.length === 0) {
      return false;
    }
    if (state.currentStep < 4) {
      dispatch({ type: 'GO_TO_STEP', step: (state.currentStep + 1) as 1 | 2 | 3 | 4 });
      return true;
    }
    return false;
  }, [state.currentStep, state.formData.subjects.length]);

  const goBack = useCallback(() => {
    if (state.currentStep > 1) {
      dispatch({ type: 'GO_TO_STEP', step: (state.currentStep - 1) as 1 | 2 | 3 | 4 });
    }
  }, [state.currentStep]);

  const goToStep = useCallback((step: 1 | 2 | 3 | 4) => {
    dispatch({ type: 'GO_TO_STEP', step });
  }, []);

  const updateFormData = useCallback((data: Partial<OnboardingFormData>) => {
    dispatch({ type: 'UPDATE_FORM', payload: data });
  }, []);

  const submitOnboarding = useCallback(async () => {
    dispatch({ type: 'SET_SUBMITTING', value: true });
    try {
      await onboardingService.submit({
        displayName: state.formData.displayName,
        age: state.formData.age,
        education: state.formData.education,
        occupation: state.formData.occupation,
        subjects: state.formData.subjects.map(s => ({
          subjectId: s.subjectId,
          examDate: s.examDate,
          selfAssessment: s.selfAssessment,
        })),
        dailyStudyMinutes: state.formData.dailyStudyMinutes,
        learningStyle: state.formData.learningStyle,
      });
      setOnboardingCompleted(true);
      if (typeof window !== 'undefined') {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
      }
      // Delay redirect to allow the launch celebration animation to play (~1.5s)
      setTimeout(() => {
        router.push('/dashboard');
      }, 1500);
    } finally {
      dispatch({ type: 'SET_SUBMITTING', value: false });
    }
  }, [state.formData, setOnboardingCompleted, router]);

  const value: OnboardingContextValue = {
    currentStep: state.currentStep,
    formData: state.formData,
    submitting: state.submitting,
    goNext,
    goBack,
    goToStep,
    updateFormData,
    submitOnboarding,
  };

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding(): OnboardingContextValue {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}
