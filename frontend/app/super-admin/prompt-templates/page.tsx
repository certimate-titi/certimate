'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  FileText,
  Plus,
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronRight,
  Tag,
  Zap,
} from 'lucide-react';
import { promptTemplateService, PromptTemplateSummary } from '@/lib/api/services';

const CATEGORIES = ['all', 'safety', 'knowledge', 'exam', 'teaching', 'emotion'];

const CATEGORY_LABELS: Record<string, string> = {
  all: '全部',
  safety: '安全',
  knowledge: '知識',
  exam: '測驗',
  teaching: '教練',
  emotion: '情感',
};

const CATEGORY_COLORS: Record<string, string> = {
  safety: 'bg-red-100 text-red-700',
  knowledge: 'bg-blue-100 text-blue-700',
  exam: 'bg-yellow-100 text-yellow-700',
  teaching: 'bg-green-100 text-green-700',
  emotion: 'bg-purple-100 text-purple-700',
};

export default function PromptTemplatesPage() {
  const [templates, setTemplates] = useState<PromptTemplateSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await promptTemplateService.listTemplates(
        selectedCategory !== 'all' ? selectedCategory : undefined
      );
      setTemplates(res.templates || []);
    } catch (e: any) {
      setError(e?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const filteredTemplates = templates.filter((t) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.template_id.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q) ||
      t.display_name.toLowerCase().includes(q)
    );
  });

  const handleDeactivate = async (templateId: string, name: string) => {
    if (!confirm(`確定要停用模板「${name}」嗎？`)) return;
    try {
      await promptTemplateService.deactivateTemplate(templateId);
      fetchTemplates();
    } catch (e: any) {
      alert(`停用失敗：${e?.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Prompt 模板管理</h1>
            <p className="text-sm text-gray-500">管理 AI 服務使用的 Prompt 模板（super_admin 限定）</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchTemplates}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            重新整理
          </button>
          <Link
            href="/super-admin/prompt-templates/new"
            className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" />
            新增模板
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜尋模板..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Category filter */}
        <div className="flex items-center gap-1">
          <Filter className="w-4 h-4 text-gray-400 mr-1" />
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                selectedCategory === cat
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : error ? (
        <div className="text-center py-20 text-red-500">{error}</div>
      ) : filteredTemplates.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>尚無 Prompt 模板</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">ID / 名稱</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">分類</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">模型</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">版本</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">狀態</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredTemplates.map((t) => (
                <tr key={t.template_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded">
                        {t.template_id}
                      </span>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{t.display_name}</div>
                        <div className="text-xs text-gray-400">{t.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${CATEGORY_COLORS[t.category] || 'bg-gray-100 text-gray-600'}`}>
                      <Tag className="w-3 h-3" />
                      {CATEGORY_LABELS[t.category] || t.category}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <Zap className="w-3.5 h-3.5" />
                      <span className="font-mono text-xs">{t.model}</span>
                    </div>
                    <div className="text-xs text-gray-400">T={t.temperature}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-gray-900">v{t.current_version}</span>
                  </td>
                  <td className="px-4 py-3">
                    {t.is_active ? (
                      <span className="flex items-center gap-1 text-xs text-green-700">
                        <CheckCircle className="w-3.5 h-3.5" /> 啟用
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <XCircle className="w-3.5 h-3.5" /> 停用
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/super-admin/prompt-templates/${t.template_id}`}
                        className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 px-2 py-1 rounded hover:bg-indigo-50"
                      >
                        編輯 <ChevronRight className="w-3 h-3" />
                      </Link>
                      {t.is_active && (
                        <button
                          onClick={() => handleDeactivate(t.template_id, t.display_name)}
                          className="text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
                        >
                          停用
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-400">
            共 {filteredTemplates.length} 個模板
          </div>
        </div>
      )}
    </div>
  );
}
