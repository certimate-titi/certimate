'use client';

import React, { useState, useEffect } from 'react';
import { Info, Save, RefreshCw } from 'lucide-react';
import { logAdminAction, AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';

export default function AiRoutingPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [aiRouting, setAiRouting] = useState({
    freeBasic: 'gemini-1.5-flash', freeFallback: 'llama-3-8b',
    proBasic: 'claude-3.5-sonnet', proFallback: 'gpt-4o',
  });

  useEffect(() => {
    superAdminService.getModelRouting().then(res => {
      const routings = (res as Record<string, unknown>).routings;
      if (Array.isArray(routings)) {
        const map: Record<string, Record<string, string>> = {};
        for (const r of routings as { plan: string; task_type: string; primary_model: string; fallback_model: string }[]) {
          if (!map[r.plan]) map[r.plan] = {};
          map[r.plan][r.task_type] = r.primary_model;
          map[r.plan][r.task_type + '_fallback'] = r.fallback_model || '';
        }
        setAiRouting(prev => ({
          freeBasic: map['FREE']?.['basic'] || prev.freeBasic,
          freeFallback: map['FREE']?.['basic_fallback'] || prev.freeFallback,
          proBasic: map['PRO']?.['advanced'] || prev.proBasic,
          proFallback: map['PRO']?.['advanced_fallback'] || prev.proFallback,
        }));
      }
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await superAdminService.updateModelRouting('FREE', 'basic', aiRouting.freeBasic);
      await superAdminService.updateModelRouting('FREE', 'fallback', aiRouting.freeFallback);
      await superAdminService.updateModelRouting('PRO', 'advanced', aiRouting.proBasic);
      await superAdminService.updateModelRouting('PRO', 'fallback', aiRouting.proFallback);
      await logAdminAction(AdminAction.UPDATE_SETTINGS, 'ai', '更新了 AI 模型路由 的系統設定');
      alert('AI 模型路由設定已儲存');
    } catch {
      alert('儲存失敗，請稍後再試');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-slate-900">AI 模型路由</h3>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 disabled:opacity-50"
        >
          {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          儲存設定
        </button>
      </div>

      <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-2xl border border-blue-100">
        <Info className="h-5 w-5 text-blue-500 shrink-0" />
        <p className="text-sm text-blue-700">AI 模型路由設定將即時影響所有用戶的請求處理路徑。</p>
      </div>

      <div className="grid gap-8">
        <section>
          <h3 className="text-lg font-bold text-slate-900 mb-4">Free 用戶路由</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">基本任務模型</label>
              <select value={aiRouting.freeBasic} onChange={e => setAiRouting(p => ({ ...p, freeBasic: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                <option>gemini-1.5-flash</option>
                <option>llama-3-8b</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">備援模型 (Fallback)</label>
              <select value={aiRouting.freeFallback} onChange={e => setAiRouting(p => ({ ...p, freeFallback: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                <option>llama-3-8b</option>
                <option>gemini-1.5-flash</option>
              </select>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-lg font-bold text-slate-900 mb-4">Pro / Ultra 用戶路由</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">進階任務模型</label>
              <select value={aiRouting.proBasic} onChange={e => setAiRouting(p => ({ ...p, proBasic: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                <option>claude-3.5-sonnet</option>
                <option>gpt-4o</option>
                <option>gemini-1.5-pro</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">備援模型 (Fallback)</label>
              <select value={aiRouting.proFallback} onChange={e => setAiRouting(p => ({ ...p, proFallback: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                <option>gpt-4o</option>
                <option>claude-3.5-sonnet</option>
              </select>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-lg font-bold text-slate-900 mb-4">Fallback 觸發條件</h3>
          <p className="text-sm text-slate-500">
            Timeout 和重試次數目前由後端 <code className="px-1.5 py-0.5 bg-slate-100 rounded text-xs">LLMService</code> 控制（預設 timeout 30s / 重試 2 次），
            未來可透過環境變數 <code className="px-1.5 py-0.5 bg-slate-100 rounded text-xs">LLM_TIMEOUT_SECONDS</code> 調整。
          </p>
        </section>
      </div>
    </div>
  );
}
