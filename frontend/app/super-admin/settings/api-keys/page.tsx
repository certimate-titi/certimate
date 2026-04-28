/**
 * @file 路由 `/super-admin/settings/api-keys` — API Key 健康監控與管理頁。
 *
 * Spec 12c §API Keys：4 把 LLM key 卡片，每張：狀態徽章 / last_4 / 上次檢查
 * / 測試按鈕 / 重設輸入。Super Admin 專屬。
 */
'use client';

import React, { useEffect, useState } from 'react';
import { Key, CheckCircle2, XCircle, Loader2, RefreshCw, Save, AlertCircle } from 'lucide-react';
import { superAdminService, type ApiKeyStatus } from '@/lib/api/services';

const PROVIDER_LABEL: Record<string, string> = {
  anthropic: 'Anthropic Claude',
  gemini: 'Google Gemini',
  voyage: 'Voyage AI Embedding',
  openai: 'OpenAI',
};

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [msgs, setMsgs] = useState<Record<string, { ok: boolean; text: string }>>({});

  const fetchAll = async () => {
    setLoading(true);
    try {
      const res = await superAdminService.getApiKeyStatus();
      setKeys(res.keys || []);
    } catch (e: unknown) {
      const err = e as { message?: string };
      alert(`載入失敗：${err?.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleTest = async (provider: string) => {
    setBusy(`test:${provider}`);
    setMsgs((m) => ({ ...m, [provider]: { ok: false, text: '測試中…' } }));
    try {
      const res = await superAdminService.testApiKey(provider);
      setMsgs((m) => ({
        ...m,
        [provider]: {
          ok: res.healthy,
          text: res.healthy ? '✅ 連線成功' : `❌ ${res.last_failure_reason || '失敗'}`,
        },
      }));
      fetchAll();
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsgs((m) => ({ ...m, [provider]: { ok: false, text: `❌ ${err?.message}` } }));
    } finally {
      setBusy(null);
    }
  };

  const handleSave = async (provider: string) => {
    const k = (inputs[provider] || '').trim();
    if (!k) {
      setMsgs((m) => ({ ...m, [provider]: { ok: false, text: '請輸入新 key' } }));
      return;
    }
    if (!confirm(`確定寫入 ${provider} 新 API key？\n\n系統會：\n1. 先 ping 測試新 key\n2. 通過後寫入 Secret Manager（雲端）\n3. 記錄 audit log（只記 last_4）`)) return;
    setBusy(`save:${provider}`);
    try {
      const res = await superAdminService.updateApiKey(provider, k);
      setMsgs((m) => ({ ...m, [provider]: { ok: true, text: `✅ ${res.message}` } }));
      setInputs((x) => ({ ...x, [provider]: '' }));
      fetchAll();
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsgs((m) => ({ ...m, [provider]: { ok: false, text: `❌ ${err?.message}` } }));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Key className="w-5 h-5 text-indigo-500" />
        <h2 className="text-lg font-bold text-gray-900">API Keys 健康監控與管理</h2>
        <button onClick={fetchAll} className="ml-auto flex items-center gap-1 text-xs px-2 py-1 border rounded hover:bg-gray-50">
          <RefreshCw className="w-3 h-3" /> 重新整理
        </button>
      </div>
      <div className="text-xs text-gray-500 mb-4">
        Spec 12c §API Keys：監控 4 把 LLM API key 健康狀態。失效時系統自動寄信通知 SUPER_ADMIN。
        重設時會先 ping 驗證新 key，通過後寫入 Secret Manager（雲端）。
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {keys.map((k) => {
            const healthBadge =
              k.healthy === true ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-medium">
                  <CheckCircle2 className="w-3 h-3" /> healthy
                </span>
              ) : k.healthy === false ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 text-xs font-medium">
                  <XCircle className="w-3 h-3" /> unhealthy
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs font-medium">
                  <AlertCircle className="w-3 h-3" /> 未測試
                </span>
              );
            const msg = msgs[k.provider];
            return (
              <div key={k.provider} className={`bg-white border rounded-xl p-4 ${k.healthy === false ? 'border-rose-300' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{PROVIDER_LABEL[k.provider] || k.provider}</h3>
                  {healthBadge}
                </div>
                <div className="text-xs text-gray-600 space-y-1 mb-3">
                  <div>後 4 碼: <span className="font-mono">{k.configured ? `…${k.last_4}` : '（未設定）'}</span></div>
                  <div>上次檢查: {k.last_check_at ? new Date(k.last_check_at).toLocaleString('zh-TW') : '—'}</div>
                  {k.last_failure_reason && (
                    <div className="text-rose-600">失敗原因：<span className="font-mono">{k.last_failure_reason.slice(0, 80)}</span></div>
                  )}
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <button
                    onClick={() => handleTest(k.provider)}
                    disabled={busy === `test:${k.provider}`}
                    className="flex items-center gap-1 px-3 py-1 text-xs bg-indigo-500 text-white rounded hover:bg-indigo-600 disabled:opacity-50"
                  >
                    {busy === `test:${k.provider}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                    測試
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="password"
                    placeholder="輸入新 API key…"
                    value={inputs[k.provider] || ''}
                    onChange={(e) => setInputs((x) => ({ ...x, [k.provider]: e.target.value }))}
                    className="flex-1 px-2 py-1 border border-gray-200 rounded text-xs font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <button
                    onClick={() => handleSave(k.provider)}
                    disabled={busy === `save:${k.provider}` || !inputs[k.provider]}
                    className="flex items-center gap-1 px-3 py-1 text-xs bg-emerald-500 text-white rounded hover:bg-emerald-600 disabled:opacity-50"
                  >
                    {busy === `save:${k.provider}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                    儲存
                  </button>
                </div>
                {msg && (
                  <div className={`mt-2 text-xs ${msg.ok ? 'text-emerald-600' : 'text-rose-600'}`}>{msg.text}</div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
