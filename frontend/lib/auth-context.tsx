'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { User, SubscriptionTier, SubscriptionStatus, UserRole } from '@/types';
import { apiClient, getStoredToken, setStoredToken, clearStoredToken } from '@/lib/api/client';
import { authService } from '@/lib/api/services';

/** Backend plan → frontend tier mapping */
const PLAN_TO_TIER: Record<string, SubscriptionTier> = {
  FREE: 'FREE',
  PRO: 'PRO_199',
  PRO_PLUS: 'PRO_PLUS_399',
  ULTRA: 'ULTRA_1599',
  EDU: 'EDU',
};

/** Backend role → frontend role mapping */
function mapRole(backendRole: string): UserRole {
  if (backendRole === 'ADMIN' || backendRole === 'SUPER_ADMIN') return 'ADMIN';
  if (backendRole === 'student') return 'STUDENT';
  return 'USER';
}

function mapTier(backendPlan: string): SubscriptionTier {
  return PLAN_TO_TIER[backendPlan] || 'FREE';
}

interface BackendLoginResponse {
  access_token: string;
  user: {
    email: string;
    subscription_plan: string;
    subscription_tier: string;
    role: string;
    status: string;
  };
  redirect_to: string;
  nav_items: { label: string; path: string }[];
}

interface BackendMeResponse {
  id: string;
  email: string;
  display_name: string;
  avatar_url: string;
  subscription_plan: string;
  subscription_tier: string;
  role: string;
  status: string;
  onboarding_completed: boolean;
  age?: number | null;
  education?: string | null;
  occupation?: string | null;
  daily_study_minutes?: number;
  learning_style?: string;
  nav_items: { label: string; path: string }[];
}

function mapStatus(backendStatus: string): SubscriptionStatus {
  if (backendStatus === 'trial') return 'TRIAL';
  if (backendStatus === 'cancelled' || backendStatus === 'canceled') return 'CANCELED';
  if (backendStatus === 'past_due') return 'PAST_DUE';
  return 'ACTIVE';
}

function backendMeToUser(me: BackendMeResponse): User {
  const tier = mapTier(me.subscription_plan);
  return {
    id: me.id,
    email: me.email,
    displayName: me.display_name || me.email.split('@')[0],
    avatarUrl: me.avatar_url || null,
    subscriptionTier: tier,
    subscriptionStatus: mapStatus(me.status),
    currentPeriodEnd: null,
    stripeCustomerId: null,
    onboardingCompleted: me.onboarding_completed,
    role: mapRole(me.role),
    createdAt: new Date().toISOString(),
    age: me.age ?? null,
    education: me.education ?? null,
    occupation: me.occupation ?? null,
    dailyStudyMinutes: me.daily_study_minutes ?? 30,
    learningStyle: (me.learning_style as User['learningStyle']) ?? 'hybrid',
  };
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isPro: boolean;
  isProPlus: boolean;
  isUltra: boolean;
  isAdmin: boolean;
  isStudent: boolean;
  isEdu: boolean;
  isTrial: boolean;
  subscriptionTier: SubscriptionTier;
  setSubscriptionTier: (tier: SubscriptionTier) => void;
  onboardingCompleted: boolean;
  setOnboardingCompleted: (completed: boolean) => void;
  loginWithCredentials: (email: string, password: string) => Promise<{ redirect_to: string }>;
  loginWithGoogle: (googleCredential: string) => Promise<{ redirect_to: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch current user from backend using stored JWT
  const fetchMe = useCallback(async (): Promise<User | null> => {
    const token = getStoredToken();
    if (!token) return null;
    try {
      const me = await apiClient.get<BackendMeResponse>('/auth/me');
      return backendMeToUser(me);
    } catch {
      clearStoredToken();
      return null;
    }
  }, []);

  // On mount: validate stored token
  useEffect(() => {
    fetchMe().then((u) => {
      setUser(u);
      setLoading(false);
    });
  }, [fetchMe]);

  // PRD-046 Canvas analytics flusher 於 2026-04-28 隨 Canvas 功能移除而移除

  const loginWithCredentials = useCallback(async (email: string, password: string) => {
    const res = await apiClient.post<BackendLoginResponse>('/auth/login', { email, password });
    setStoredToken(res.access_token);
    const me = await apiClient.get<BackendMeResponse>('/auth/me');
    const u = backendMeToUser(me);
    setUser(u);
    return { redirect_to: res.redirect_to };
  }, []);

  const loginWithGoogle = useCallback(async (googleCredential: string) => {
    // Google Identity Services returns a standard Google OAuth ID token.
    // Backend verifies via google.oauth2.id_token.verify_oauth2_token().
    const res = await authService.googleSSO(googleCredential);
    setStoredToken((res as any).access_token);
    const me = await apiClient.get<BackendMeResponse>('/auth/me');
    const u = backendMeToUser(me);
    setUser(u);
    return { redirect_to: (res as any).redirect_to || '/dashboard' };
  }, []);

  const signOut = useCallback(async () => {
    clearStoredToken();
    setUser(null);
    window.location.href = '/login';
  }, []);

  const setSubscriptionTier = useCallback((tier: SubscriptionTier) => {
    setUser((prev) => (prev ? { ...prev, subscriptionTier: tier } : null));
  }, []);

  const setOnboardingCompleted = useCallback((completed: boolean) => {
    setUser((prev) => (prev ? { ...prev, onboardingCompleted: completed } : null));
  }, []);

  const subscriptionTier = user?.subscriptionTier ?? 'FREE';
  const onboardingCompleted = user?.onboardingCompleted ?? false;

  const value: AuthContextValue = {
    user,
    loading,
    isAuthenticated: !!user,
    isPro: subscriptionTier === 'PRO_199' || subscriptionTier === 'PRO_PLUS_399' || subscriptionTier === 'ULTRA_1599',
    isProPlus: subscriptionTier === 'PRO_PLUS_399' || subscriptionTier === 'ULTRA_1599',
    isUltra: subscriptionTier === 'ULTRA_1599',
    isAdmin: user?.role === 'ADMIN',
    isStudent: user?.role === 'STUDENT',
    isEdu: subscriptionTier === 'EDU',
    isTrial: user?.subscriptionStatus === 'TRIAL',
    subscriptionTier,
    setSubscriptionTier,
    onboardingCompleted,
    setOnboardingCompleted,
    loginWithCredentials,
    loginWithGoogle,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
