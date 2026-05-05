/**
 * @file 路由 `/super-admin/prompt-templates/[templateId]` — Prompt 範本詳情客戶端元件。
 *
 * 由同目錄 `page.tsx`（generateStaticParams stub）載入；編輯單一 prompt 範本，
 * 支援版本切換、Save / Rollback 與 inline diff。
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Save,
  RotateCcw,
  GitBranch,
  Clock,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle,
  AlertTriangle,
  FlaskConical,
} from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import {
  promptTemplateService,
  PromptTemplateDetail,
  PromptTemplateVersion,
  PromptAbTest,
} from '@/lib/api/services';

const AVAILABLE_MODELS = [
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
  { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3.5-haiku', label: 'Claude 3.5 Haiku' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
] as const;

/**
 * 從 window.location.pathname 解析真實 templateId。
 * 靜態匯出 + Firebase rewrite 下 useParams() 只會讀到 stub 字面值「detail」，
 * 必須走 pathname regex 拿到真 ID。
 */
function useTemplateIdFromPath(): string {
  const [id, setId] = useState('');
  useEffect(() => {
    const m = window.location.pathname.match(/\/super-admin\/prompt-templates\/([^/]+)/);
    if (m && m[1] && m[1] !== 'detail') setId(m[1]);
  }, []);
  return id;
}

export default function PromptTemplateDetailPage() {
  const router = useRouter();
  const templateId = useTemplateIdFromPath();
  const { loading: authLoading, isAuthenticated, isSuperAdmin } = useAuth();
  // SUPER_ADMIN-only：高等設定（Prompt 模板）
  useEffect(() => {
    if (!authLoading && isAuthenticated && !isSuperAdmin) {
      router.replace('/super-admin/dashboard');
    }
  }, [authLoading, isAuthenticated, isSuperAdmin, router]);

  const [template, setTemplate] = useState<PromptTemplateDetail | null>(null);
  const [versions, setVersions] = useState<PromptTemplateVersion[]>([]);
  const [abTests, setAbTests] = useState<PromptAbTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'edit' | 'versions' | 'ab-test'>('edit');
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Edit form state
  const [systemPrompt, setSystemPrompt] = useState('');
  const [userPrompt, setUserPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.5);
  const [model, setModel] = useState('gemini-2.5-flash');
  const [changeNote, setChangeNote] = useState('');

  // A/B test form
  const [abName, setAbName] = useState('');
  const [abVariantB, setAbVariantB] = useState('');
  const [abUserPromptB, setAbUserPromptB] = useState('');
  const [abTempB, setAbTempB] = useState(0.5);
  const [abSplit, setAbSplit] = useState(30);
  const [abMetric, setAbMetric] = useState('accuracy');

  const fetchAll = useCallback(async () => {
    if (!templateId) return;  // 等 pathname regex 解析完畢
    setLoading(true);
    try {
      const [tpl, ver] = await Promise.all([
        promptTemplateService.getTemplate(templateId),
        promptTemplateService.listVersions(templateId),
      ]);
      setTemplate(tpl);
      setVersions(ver.versions || []);
      setSystemPrompt(tpl.system_prompt);
      setUserPrompt(tpl.user_prompt);
      setTemperature(tpl.temperature);
      setModel(tpl.model || 'gemini-2.5-flash');

      const ab = await promptTemplateService.listAbTests();
      setAbTests(ab.ab_tests.filter((t) => t.template_id === (tpl as any).id || true));
    } catch (e: any) {
      setErrorMsg(e?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [templateId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleSave = async () => {
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      await promptTemplateService.updateTemplate(templateId, {
        system_prompt: systemPrompt,
        user_prompt: userPrompt,
        temperature,
        model,
        change_note: changeNote || undefined,
      });
      setSuccessMsg('已成功更新並建立新版本');
      setChangeNote('');
      fetchAll();
    } catch (e: any) {
      setErrorMsg(e?.message || '儲存失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleRollback = async (version: number) => {
    if (!confirm(`確定要回滾至 v${version}？這將建立一個新版本。`)) return;
    try {
      await promptTemplateService.rollbackTemplate(templateId, version);
      setSuccessMsg(`已回滾至 v${version}，新版本已建立`);
      fetchAll();
    } catch (e: any) {
      setErrorMsg(e?.message || '回滾失敗');
    }
  };

  const handleCreateAbTest = async () => {
    if (!abName || !abVariantB || !abUserPromptB) {
      setErrorMsg('請填寫測試名稱、Variant B system_prompt 和 user_prompt');
      return;
    }
    try {
      await promptTemplateService.createAbTest(templateId, {
        name: abName,
        variant_b_system_prompt: abVariantB,
        variant_b_user_prompt: abUserPromptB,
        variant_b_temperature: abTempB,
        traffic_split: abSplit,
        metric_name: abMetric,
      });
      setSuccessMsg('A/B 測試已建立');
      setAbName('');
      setAbVariantB('');
      setAbUserPromptB('{user_input}');
      fetchAll();
    } catch (e: any) {
      setErrorMsg(e?.message || '建立 A/B 測試失敗');
    }
  };

  const handleAbAction = async (testId: string, action: 'A' | 'B' | 'cancel') => {
    if (action === 'cancel') {
      if (!confirm('確定要取消此 A/B 測試？')) return;
      await promptTemplateService.cancelAbTest(testId);
    } else {
      if (!confirm(`確定選擇 Variant ${action} 為勝者？`)) return;
      await promptTemplateService.completeAbTest(testId, action);
    }
    fetchAll();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (!template) {
    return (
      <div className="p-6 text-center text-red-500">
        模板 {templateId} 不存在
      </div>
    );
  }

  const TABS = [
    { id: 'edit', label: '編輯 Prompt', icon: Save },
    { id: 'versions', label: `版本歷史 (${versions.length})`, icon: Clock },
    { id: 'ab-test', label: 'A/B 測試', icon: FlaskConical },
  ] as const;

  if (authLoading || !isAuthenticated || !isSuperAdmin) {
    return (
      <div className="p-8 text-slate-500 text-sm">
        {authLoading ? '載入中⋯' : '需要 SUPER_ADMIN 權限。'}
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/super-admin/prompt-templates"
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm bg-gray-100 px-2 py-0.5 rounded">
              {template.template_id}
            </span>
            <h1 className="text-xl font-bold text-gray-900">{template.display_name}</h1>
            <span className="text-sm text-gray-400">({template.name})</span>
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
              v{template.current_version}
            </span>
            {!template.is_active && (
              <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">
                已停用
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
            <span>分類：{template.category}</span>
            <span>模型：{template.model}</span>
            <span>溫度：{template.temperature}</span>
            <span>max_tokens：{template.max_tokens}</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      {successMsg && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          <CheckCircle className="w-4 h-4" />
          {successMsg}
        </div>
      )}
      {errorMsg && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" />
          {errorMsg}
          <button onClick={() => setErrorMsg('')} className="ml-auto text-red-400 hover:text-red-600">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === id
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* ── Edit Tab ── */}
      {activeTab === 'edit' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt
            </label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={10}
              className="w-full p-3 text-sm font-mono border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
              placeholder="System Prompt..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User Prompt
            </label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              rows={5}
              className="w-full p-3 text-sm font-mono border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
              placeholder="User Prompt（可使用 {variable} 變數）..."
            />
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AI Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full p-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                {AVAILABLE_MODELS.map(m => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature
              </label>
              <input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                step={0.1}
                min={0}
                max={1}
                className="w-full p-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                變更說明（選填）
              </label>
              <input
                type="text"
                value={changeNote}
                onChange={(e) => setChangeNote(e.target.value)}
                placeholder="e.g. 調整語氣..."
                className="w-full p-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              儲存並遞增版本
            </button>
          </div>
        </div>
      )}

      {/* ── Version History Tab ── */}
      {activeTab === 'versions' && (
        <div className="space-y-3">
          {versions.length === 0 ? (
            <div className="text-center py-10 text-gray-400">尚無版本歷史</div>
          ) : (
            versions.map((v) => (
              <div
                key={v.version}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-indigo-600">
                      v{v.version}
                    </span>
                    {v.version === template.current_version && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                        當前版本
                      </span>
                    )}
                    {v.change_note && (
                      <span className="text-xs text-gray-500">{v.change_note}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {v.created_at && (
                      <span className="text-xs text-gray-400">
                        {new Date(v.created_at).toLocaleString('zh-TW')}
                      </span>
                    )}
                    {v.version !== template.current_version && (
                      <button
                        onClick={() => handleRollback(v.version)}
                        className="flex items-center gap-1 text-xs text-orange-600 hover:text-orange-800 px-2 py-1 rounded hover:bg-orange-50"
                      >
                        <RotateCcw className="w-3 h-3" />
                        回滾至此版本
                      </button>
                    )}
                  </div>
                </div>
                <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded font-mono truncate">
                  {v.system_prompt?.slice(0, 150)}
                  {v.system_prompt?.length > 150 ? '...' : ''}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── A/B Test Tab ── */}
      {activeTab === 'ab-test' && (
        <div className="space-y-6">
          {/* Running A/B Tests */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">進行中的 A/B 測試</h3>
            {abTests.filter((t) => t.status === 'running').length === 0 ? (
              <div className="text-sm text-gray-400 py-4 text-center">無進行中的 A/B 測試</div>
            ) : (
              abTests
                .filter((t) => t.status === 'running')
                .map((ab) => (
                  <div
                    key={ab.id}
                    className="border border-blue-200 bg-blue-50 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="font-medium text-sm text-blue-900">{ab.name}</span>
                        <span className="ml-2 text-xs text-blue-600">
                          Variant B 流量：{ab.traffic_split}%
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAbAction(ab.id, 'A')}
                          className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full"
                        >
                          選 A 為勝者
                        </button>
                        <button
                          onClick={() => handleAbAction(ab.id, 'B')}
                          className="text-xs px-3 py-1 bg-indigo-100 hover:bg-indigo-200 text-indigo-700 rounded-full"
                        >
                          選 B 為勝者
                        </button>
                        <button
                          onClick={() => handleAbAction(ab.id, 'cancel')}
                          className="text-xs px-3 py-1 bg-red-100 hover:bg-red-200 text-red-600 rounded-full"
                        >
                          取消測試
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-blue-700">
                      對照組：v{ab.variant_a_version} / 指標：{ab.metric_name || '—'}
                    </div>
                  </div>
                ))
            )}
          </div>

          {/* Create New A/B Test */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <FlaskConical className="w-4 h-4" />
              建立新 A/B 測試
            </h3>
            <div className="space-y-3">
              <input
                type="text"
                value={abName}
                onChange={(e) => setAbName(e.target.value)}
                placeholder="測試名稱 e.g. 語氣對比測試"
                className="w-full p-2 text-sm border border-gray-200 rounded-lg"
              />
              <div>
                <label className="block text-xs text-gray-500 mb-1">Variant B System Prompt</label>
                <textarea
                  value={abVariantB}
                  onChange={(e) => setAbVariantB(e.target.value)}
                  rows={5}
                  className="w-full p-2 text-sm font-mono border border-gray-200 rounded-lg"
                  placeholder="Variant B 的 system prompt..."
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Variant B User Prompt</label>
                <textarea
                  value={abUserPromptB}
                  onChange={(e) => setAbUserPromptB(e.target.value)}
                  rows={2}
                  className="w-full p-2 text-sm font-mono border border-gray-200 rounded-lg"
                  placeholder="{user_input}"
                />
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">Variant B Temperature</label>
                  <input
                    type="number"
                    value={abTempB}
                    onChange={(e) => setAbTempB(parseFloat(e.target.value))}
                    step={0.1} min={0} max={1}
                    className="w-full p-2 text-sm border border-gray-200 rounded-lg"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">Variant B 流量 %</label>
                  <input
                    type="number"
                    value={abSplit}
                    onChange={(e) => setAbSplit(parseInt(e.target.value))}
                    min={1} max={99}
                    className="w-full p-2 text-sm border border-gray-200 rounded-lg"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">追蹤指標</label>
                  <select
                    value={abMetric}
                    onChange={(e) => setAbMetric(e.target.value)}
                    className="w-full p-2 text-sm border border-gray-200 rounded-lg"
                  >
                    <option value="accuracy">accuracy</option>
                    <option value="satisfaction">satisfaction</option>
                    <option value="cost">cost</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  onClick={handleCreateAbTest}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
                >
                  <FlaskConical className="w-4 h-4" />
                  建立 A/B 測試
                </button>
              </div>
            </div>
          </div>

          {/* Past A/B Tests */}
          {abTests.filter((t) => t.status !== 'running').length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">歷史 A/B 測試</h3>
              <div className="space-y-2">
                {abTests
                  .filter((t) => t.status !== 'running')
                  .map((ab) => (
                    <div
                      key={ab.id}
                      className="border border-gray-200 rounded-lg p-3 text-sm text-gray-600"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{ab.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          ab.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                        }`}>
                          {ab.status === 'completed' ? `完成 • 勝者 ${ab.winner}` : '已取消'}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
