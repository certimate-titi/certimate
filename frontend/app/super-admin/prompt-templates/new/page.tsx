/**
 * @file 路由 `/super-admin/prompt-templates/new` — 新增 Prompt 範本頁。
 *
 * Super Admin 專屬：建立新 prompt 範本（safety / knowledge / exam / teaching / emotion）；
 * 儲存後導向該範本的詳情頁。
 */
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Save, Loader2, AlertTriangle } from 'lucide-react';
import { promptTemplateService } from '@/lib/api/services';

const CATEGORIES = [
  { value: 'safety', label: '安全' },
  { value: 'knowledge', label: '知識' },
  { value: 'exam', label: '測驗' },
  { value: 'teaching', label: '教練' },
  { value: 'emotion', label: '情感' },
];

const MODELS = [
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'claude-3.5-sonnet',
  'claude-3.5-haiku',
  'gpt-4o',
  'gpt-4o-mini',
];

export default function NewPromptTemplatePage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const [templateId, setTemplateId] = useState('');
  const [name, setName] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [category, setCategory] = useState('teaching');
  const [model, setModel] = useState('gemini-2.5-flash');
  const [maxTokens, setMaxTokens] = useState(2048);
  const [temperature, setTemperature] = useState(0.5);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [userPrompt, setUserPrompt] = useState('{user_input}');
  const [changeNote, setChangeNote] = useState('初始版本');

  const canSubmit =
    templateId.trim() && name.trim() && displayName.trim() && systemPrompt.trim() && userPrompt.trim();

  const handleCreate = async () => {
    if (!canSubmit) {
      setErrorMsg('請填寫所有必填欄位');
      return;
    }
    setSaving(true);
    setErrorMsg('');
    try {
      const res = await promptTemplateService.createTemplate({
        template_id: templateId.trim(),
        name: name.trim(),
        display_name: displayName.trim(),
        category,
        model,
        max_tokens: maxTokens,
        temperature,
        system_prompt: systemPrompt,
        user_prompt: userPrompt,
        change_note: changeNote || undefined,
      });
      router.push(`/super-admin/prompt-templates/${res.template_id}`);
    } catch (e: any) {
      setErrorMsg(e?.message || '建立失敗');
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/super-admin/prompt-templates"
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">新增 Prompt 模板</h1>
      </div>

      {errorMsg && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" />
          {errorMsg}
          <button onClick={() => setErrorMsg('')} className="ml-auto text-red-400 hover:text-red-600">✕</button>
        </div>
      )}

      <div className="space-y-4 bg-white border border-gray-200 rounded-xl p-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Template ID *</label>
            <input
              type="text"
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              placeholder="e.g. knowledge_explainer"
              className="w-full p-2 text-sm font-mono border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <p className="text-xs text-gray-400 mt-1">唯一識別碼（英文小寫 + 底線）</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. knowledge.explainer"
              className="w-full p-2 text-sm font-mono border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Display Name *</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="e.g. 知識節點解說"
            className="w-full p-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">分類</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full p-2 text-sm border border-gray-200 rounded-lg bg-white"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">AI Model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full p-2 text-sm font-mono border border-gray-200 rounded-lg bg-white"
            >
              {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
            <input
              type="number"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              step={0.1}
              min={0}
              max={1}
              className="w-full p-2 text-sm border border-gray-200 rounded-lg"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
          <input
            type="number"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value))}
            min={128}
            max={32768}
            className="w-full p-2 text-sm border border-gray-200 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt *</label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={8}
            className="w-full p-3 text-sm font-mono border border-gray-200 rounded-lg resize-y"
            placeholder="你是..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">User Prompt *</label>
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            rows={4}
            className="w-full p-3 text-sm font-mono border border-gray-200 rounded-lg resize-y"
            placeholder="可使用 {variable} 變數"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">變更說明</label>
          <input
            type="text"
            value={changeNote}
            onChange={(e) => setChangeNote(e.target.value)}
            className="w-full p-2 text-sm border border-gray-200 rounded-lg"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Link
            href="/super-admin/prompt-templates"
            className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            取消
          </Link>
          <button
            onClick={handleCreate}
            disabled={saving || !canSubmit}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            建立模板
          </button>
        </div>
      </div>
    </div>
  );
}
