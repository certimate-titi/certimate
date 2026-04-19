'use client';

import React, { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';
import { logAdminAction, AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';

export default function PlansPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [planQuotas, setPlanQuotas] = useState<{ label: string; key: string; free: number | string; pro: number | string; pro_plus: number | string; ultra: number | string }[]>([]);

  useEffect(() => {
    superAdminService.getPlanQuotas().then(res => {
      if (res.quotas?.length) setPlanQuotas(res.quotas);
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const planUpdates: Record<string, Record<string, number>> = { FREE: {}, PRO: {}, PRO_PLUS: {}, ULTRA: {} };
      for (const row of planQuotas) {
        planUpdates['FREE'][row.key] = Number(row.free) || 0;
        planUpdates['PRO'][row.key] = Number(row.pro) || 0;
        planUpdates['PRO_PLUS'][row.key] = Number(row.pro_plus) || 0;
        planUpdates['ULTRA'][row.key] = Number(row.ultra) || 0;
      }
      for (const [plan, updates] of Object.entries(planUpdates)) {
        await superAdminService.updatePlanQuota(plan, updates);
      }
      await logAdminAction(AdminAction.UPDATE_SETTINGS, 'plans', '更新了方案限額設定');
      alert('方案限額已儲存');
    } catch {
      alert('儲存失敗，請稍後再試');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-slate-900">方案限額調整</h3>
        <button onClick={handleSave} disabled={isSaving} className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 disabled:opacity-50">
          {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          儲存設定
        </button>
      </div>
      {planQuotas.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm">尚無方案限額設定，請先於資料庫建立 plan_quotas 資料</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">參數</th>
                <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">FREE</th>
                <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">PRO</th>
                <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">PRO_PLUS</th>
                <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">ULTRA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {planQuotas.map((row) => (
                <tr key={row.key}>
                  <td className="py-4 text-sm font-medium text-slate-700">{row.label}</td>
                  {(['free', 'pro', 'pro_plus', 'ultra'] as const).map(plan => (
                    <td key={plan} className="py-4">
                      <input type="number" value={row[plan]} onChange={e => setPlanQuotas(prev => prev.map(r => r.key === row.key ? { ...r, [plan]: e.target.value } : r))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
