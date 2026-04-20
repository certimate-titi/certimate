'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, Search, RefreshCw, Trash2, RotateCw, Loader2, FileText, AlertTriangle, Share2 } from 'lucide-react';
import { resourceLibraryService, LibraryResource, resourceShareService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

const BADGE_META: Record<string, { label: string; cls: string }> = {
  official_default: { label: '官方預設', cls: 'bg-green-100 text-green-700' },
  edu_shared: { label: 'EDU 分享', cls: 'bg-blue-100 text-blue-700' },
  institution: { label: '機構', cls: 'bg-purple-100 text-purple-700' },
  personal: { label: '個人', cls: 'bg-slate-100 text-slate-600' },
};

const STATUS_COLORS: Record<string, string> = {
  ready: 'bg-green-100 text-green-700',
  completed: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  processing: 'bg-blue-100 text-blue-700',
  failed: 'bg-red-100 text-red-700',
};

export default function ResourceLibraryPage() {
  const { isUltra } = useAuth();
  const [items, setItems] = useState<LibraryResource[]>([]);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetch = useCallback(async (kw?: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await resourceLibraryService.list(kw);
      setItems(res.resources || []);
    } catch (e: any) {
      setError(e?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`確定要刪除「${name}」？`)) return;
    try {
      await resourceLibraryService.delete(id);
      fetch(keyword);
    } catch (e: any) {
      alert(`刪除失敗：${e?.message}`);
    }
  };

  const handleReparse = async (id: string) => {
    try {
      await resourceLibraryService.reparse(id);
      fetch(keyword);
    } catch (e: any) {
      alert(`重新解析失敗：${e?.message}`);
    }
  };

  // PRD-033 US-03: Ultra 分享給 EDU
  const handleShare = async (id: string, currentScope: string | undefined) => {
    if (currentScope === 'shared') {
      if (!confirm('確定撤回此資源對 EDU 的分享？')) return;
      try {
        await resourceShareService.revokeShare(id);
        fetch(keyword);
      } catch (e: any) {
        alert(`撤回失敗：${e?.message}`);
      }
      return;
    }
    const instId = prompt('請輸入目標 EDU 機構 ID（institution_id UUID）：');
    if (!instId) return;
    try {
      await resourceShareService.shareToInstitution(id, instId);
      fetch(keyword);
    } catch (e: any) {
      alert(`分享失敗：${e?.message}`);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/account" className="p-2 rounded-lg hover:bg-gray-100 text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">我的資源庫</h1>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetch(keyword)}
            placeholder="搜尋資源名稱..."
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          onClick={() => fetch(keyword)}
          className="flex items-center gap-1 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          重新整理
        </button>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>尚無資源</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">名稱</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">類型</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">歸屬</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">狀態</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((r) => (
                <tr key={r.resource_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{r.name}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">{r.type}</td>
                  <td className="px-4 py-3">
                    {(() => {
                      const meta = BADGE_META[r.badge || 'personal'] || BADGE_META.personal;
                      return (
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${meta.cls}`}>
                          {meta.label}
                        </span>
                      );
                    })()}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[r.status] || 'bg-gray-100 text-gray-600'}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleReparse(r.resource_id)}
                        disabled={r.status === 'pending' || r.status === 'processing'}
                        className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 px-2 py-1 rounded hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <RotateCw className="w-3 h-3" /> 重新解析
                      </button>
                      {isUltra && (r.scope === 'personal' || r.scope === 'shared') && (
                        <button
                          onClick={() => handleShare(r.resource_id, r.scope)}
                          className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${
                            r.scope === 'shared'
                              ? 'text-blue-600 hover:text-blue-800 hover:bg-blue-50'
                              : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'
                          }`}
                          title={r.scope === 'shared' ? '撤回分享' : '分享給 EDU'}
                        >
                          <Share2 className="w-3 h-3" /> {r.scope === 'shared' ? '撤回' : '分享'}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(r.resource_id, r.name)}
                        className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
                      >
                        <Trash2 className="w-3 h-3" /> 刪除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-400">
            共 {items.length} 筆
          </div>
        </div>
      )}
    </div>
  );
}
