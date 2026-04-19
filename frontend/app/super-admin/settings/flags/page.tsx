'use client';

import React, { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { logAdminAction, AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';

function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

export default function FlagsPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [featureFlags, setFeatureFlags] = useState<{ id: string; name: string; description: string; enabled: boolean }[]>([]);

  useEffect(() => {
    superAdminService.getFeatureFlags().then(res => {
      if (Array.isArray(res?.flags)) setFeatureFlags(res.flags);
    }).catch(() => {});
  }, []);

  const toggleFlag = (flagId: string) => {
    setFeatureFlags(prev => prev.map(f => f.id === flagId ? { ...f, enabled: !f.enabled } : f));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      for (const flag of featureFlags) {
        await superAdminService.updateFeatureFlag(flag.id, flag.enabled);
      }
      await logAdminAction(AdminAction.UPDATE_SETTINGS, 'flags', '更新了 Feature Flags 設定');
      alert('Feature Flags 已儲存');
    } catch { alert('儲存失敗'); }
    finally { setIsSaving(false); }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-slate-900">Feature Flags</h3>
        <button onClick={handleSave} disabled={isSaving} className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 disabled:opacity-50">
          {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          儲存設定
        </button>
      </div>
      <div className="space-y-4">
        {featureFlags.map((flag) => (
          <div key={flag.id} className="flex items-center justify-between p-6 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <p className="text-sm font-bold text-slate-900">{flag.name}</p>
                <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded uppercase", flag.enabled ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500")}>
                  {flag.enabled ? 'ON' : 'OFF'}
                </span>
              </div>
              <p className="text-xs text-slate-500 font-mono">{flag.id}</p>
              <p className="text-xs text-slate-500 mt-1">{flag.description}</p>
            </div>
            <button onClick={() => toggleFlag(flag.id)} className={cn("w-12 h-6 rounded-full transition-all relative cursor-pointer", flag.enabled ? "bg-emerald-500" : "bg-slate-300")}>
              <div className={cn("absolute top-1 w-4 h-4 bg-white rounded-full transition-all shadow-sm", flag.enabled ? "right-1" : "left-1")} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
