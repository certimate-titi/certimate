'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { onAuthStateChanged, signOut as firebaseSignOut, type User as FirebaseUser } from 'firebase/auth';
import { auth } from '@/firebase';
import type { User, SubscriptionTier, UserRole } from '@/types';

interface DemoUserInfo {
  email: string;
  displayName: string;
  role: UserRole;
}

interface AuthContextValue {
  firebaseUser: FirebaseUser | null;
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isPro: boolean;
  isProPlus: boolean;
  isUltra: boolean;
  isAdmin: boolean;
  subscriptionTier: SubscriptionTier;
  setSubscriptionTier: (tier: SubscriptionTier) => void;
  onboardingCompleted: boolean;
  setOnboardingCompleted: (completed: boolean) => void;
  loginAsDemoUser: (info: DemoUserInfo, tier: SubscriptionTier, onboardingDone: boolean) => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TIER_STORAGE_KEY = 'certimate_demo_tier';
const ONBOARDING_STORAGE_KEY = 'certimate_onboarding_completed';
const DEMO_USER_KEY = 'certimate_demo_user';

const ls = {
  get: (key: string) => (typeof window !== 'undefined' ? window.localStorage?.getItem(key) : null),
  set: (key: string, val: string) => { if (typeof window !== 'undefined') window.localStorage?.setItem(key, val); },
  remove: (key: string) => { if (typeof window !== 'undefined') window.localStorage?.removeItem(key); },
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [subscriptionTier, setTierState] = useState<SubscriptionTier>('FREE');
  const [onboardingCompleted, setOnboardingCompletedState] = useState(false);
  const [demoUser, setDemoUserState] = useState<DemoUserInfo | null>(null);

  // Load saved state from localStorage
  useEffect(() => {
    const savedTier = ls.get(TIER_STORAGE_KEY) as SubscriptionTier | null;
    if (savedTier === 'FREE' || savedTier === 'PRO_199' || savedTier === 'PRO_PLUS_399' || savedTier === 'ULTRA_1599') {
      setTierState(savedTier);
    }
    if (ls.get(ONBOARDING_STORAGE_KEY) === 'true') {
      setOnboardingCompletedState(true);
    }
    const savedDemo = ls.get(DEMO_USER_KEY);
    if (savedDemo) {
      try { setDemoUserState(JSON.parse(savedDemo)); } catch { /* ignore */ }
    }
  }, []);

  const setSubscriptionTier = useCallback((tier: SubscriptionTier) => {
    setTierState(tier);
    ls.set(TIER_STORAGE_KEY, tier);
  }, []);

  const setOnboardingCompleted = useCallback((completed: boolean) => {
    setOnboardingCompletedState(completed);
    ls.set(ONBOARDING_STORAGE_KEY, String(completed));
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (fbUser) => {
      setFirebaseUser(fbUser);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const user: User | null = firebaseUser
    ? {
        id: firebaseUser.uid,
        email: firebaseUser.email ?? '',
        displayName: firebaseUser.displayName ?? '學習者',
        avatarUrl: firebaseUser.photoURL,
        subscriptionTier,
        subscriptionStatus: 'ACTIVE',
        currentPeriodEnd: null,
        stripeCustomerId: null,
        onboardingCompleted,
        role: 'USER',
        createdAt: firebaseUser.metadata.creationTime ?? new Date().toISOString(),
      }
    : demoUser
    ? {
        id: `demo_${demoUser.email}`,
        email: demoUser.email,
        displayName: demoUser.displayName,
        avatarUrl: null,
        subscriptionTier,
        subscriptionStatus: 'ACTIVE',
        currentPeriodEnd: null,
        stripeCustomerId: null,
        onboardingCompleted,
        role: demoUser.role,
        createdAt: new Date().toISOString(),
      }
    : null;

  const loginAsDemoUser = useCallback((info: DemoUserInfo, tier: SubscriptionTier, onboardingDone: boolean) => {
    setDemoUserState(info);
    setTierState(tier);
    setOnboardingCompletedState(onboardingDone);
    ls.set(DEMO_USER_KEY, JSON.stringify(info));
    ls.set(TIER_STORAGE_KEY, tier);
    ls.set(ONBOARDING_STORAGE_KEY, String(onboardingDone));
  }, []);

  const signOut = useCallback(async () => {
    if (firebaseUser) await firebaseSignOut(auth);
    setDemoUserState(null);
    setTierState('FREE');
    setOnboardingCompletedState(false);
    ls.remove(DEMO_USER_KEY);
    ls.remove(TIER_STORAGE_KEY);
    ls.remove(ONBOARDING_STORAGE_KEY);
  }, [firebaseUser]);

  const value: AuthContextValue = {
    firebaseUser,
    user,
    loading,
    isAuthenticated: !!firebaseUser || !!demoUser,
    isPro: subscriptionTier === 'PRO_199' || subscriptionTier === 'PRO_PLUS_399' || subscriptionTier === 'ULTRA_1599',
    isProPlus: subscriptionTier === 'PRO_PLUS_399' || subscriptionTier === 'ULTRA_1599',
    isUltra: subscriptionTier === 'ULTRA_1599',
    isAdmin: user?.role === 'ADMIN',
    subscriptionTier,
    setSubscriptionTier,
    onboardingCompleted,
    setOnboardingCompleted,
    loginAsDemoUser,
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
