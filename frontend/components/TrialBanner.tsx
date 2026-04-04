'use client';

import { useEffect, useState } from 'react';
import { Sparkles, Clock } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api/client';

interface TrialStatus {
  is_trial: boolean;
  remaining_days: number;
  trial_end: string | null;
}

export function TrialBanner() {
  const { isTrial, isAuthenticated } = useAuth();
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !isTrial) return;
    apiClient.get<TrialStatus>('/subscriptions/trial/status').then(setTrialStatus).catch(() => {});
  }, [isAuthenticated, isTrial]);

  if (!isTrial || !trialStatus?.is_trial) return null;

  const days = trialStatus.remaining_days;
  const urgent = days <= 3;

  return (
    <div className={`px-4 py-2 text-center text-sm font-medium ${
      urgent ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
    }`}>
      <div className="flex items-center justify-center gap-2">
        {urgent ? <Clock className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
        <span>
          ULTRA 免費試用剩餘 {days} 天
          {urgent && ' — 立即升級以保留所有功能'}
        </span>
        <a href="/pricing" className="underline ml-2 font-bold">
          查看方案
        </a>
      </div>
    </div>
  );
}
