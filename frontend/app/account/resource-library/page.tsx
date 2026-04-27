/**
 * @file 路由 `/account/resource-library` — 個人學習資源庫頁。
 *
 * 顯示使用者擁有或被分享的學習資源（含官方預設、EDU 分享、機構、個人四類），
 * 提供搜尋、刪除、重新解析、分享等操作；同時輪詢 parse status 顯示處理進度。
 */
'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { ArrowLeft, Search, RefreshCw, Trash2, Loader2, FileText, AlertTriangle, Share2, CheckCircle2, BookOpenCheck } from 'lucide-react';
import { resourceLibraryService, LibraryResource, resourceShareService, resourceParseService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import { useIsEmbedded } from '@/lib/embed-context';
import type { ParseStatusResponse } from '@/types/api';

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

/**
 * 個人學習資源庫頁。
 *
 * 透過 `resourceLibraryService` 載入資源清單，並依狀態（pending/processing/ready/failed）
 * 顯示色彩標籤；支援嵌入模式（embed）以隱藏部分外層 chrome。
 */
export default function ResourceLibraryPage() {
  const embedded = useIsEmbedded();
  const { isUltra } = useAuth();
  const [items, setItems] = useState<LibraryResource[]>([]);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [parseStatus, setParseStatus] = useState<Record<string, ParseStatusResponse>>({});
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

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

  // EPIC-035: poll parse status for in-progress resources
  useEffect(() => {
    const active = items.filter((r) =>
      ['pending', 'processing', 'PENDING', 'CHUNKING', 'EXTRACTING', 'GENERATING'].includes(r.status),
    );
    if (active.length === 0) {
      if (pollTimer.current) { clearInterval(pollTimer.current); pollTimer.current = null; }
      return;
    }
    const poll = async () => {
      const updates: Record<string, ParseStatusResponse> = {};
      await Promise.all(
        active.map(async (r) => {
          try {
            updates[r.resource_id] = await resourceParseService.getStatus(r.resource_id);
          } catch { /* 404 when no job yet — ignore */ }
        }),
      );
      setParseStatus((prev) => ({ ...prev, ...updates }));
      const allDone = Object.values(updates).every(
        (s) => s.status === 'COMPLETED' || s.status === 'FAILED',
      );
      if (allDone && Object.keys(updates).length > 0) fetch(keyword);
    };
    poll();
    pollTimer.current = setInterval(poll, 3000);
    return () => {
      if (pollTimer.current) { clearInterval(pollTimer.current); pollTimer.current = null; }
    };
  }, [items, keyword, fetch]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`確定要刪除「${name}」？`)) return;
    try {
      await resourceLibraryService.delete(id);
      fetch(keyword);
    } catch (e: any) {
      alert(`刪除失敗：${e?.message}`);
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
      {!embedded && (
        <div className="flex items-center gap-3 mb-6">
          <Link href="/account" className="p-2 rounded-lg hover:bg-gray-100 text-gray-600">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-xl font-bold text-gray-900">我的資源庫</h1>
        </div>
      )}

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
                    {parseStatus[r.resource_id] && parseStatus[r.resource_id].status !== 'COMPLETED' && parseStatus[r.resource_id].status !== 'FAILED' && (
                      <div className="mt-1 flex items-center gap-1 text-xs text-blue-600">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {parseStatus[r.resource_id].status}
                      </div>
                    )}
                    {parseStatus[r.resource_id]?.status === 'FAILED' && (
                      <div className="mt-1 text-xs text-red-600" title={parseStatus[r.resource_id].failure_reason || ''}>
                        解析失敗
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/knowledge?resourceId=${r.resource_id}`}
                        className="flex items-center gap-1 text-xs text-teal-600 hover:text-teal-800 px-2 py-1 rounded hover:bg-teal-50"
                        title="於知識地圖檢視解析內容與學習鷹架"
                      >
                        <BookOpenCheck className="w-3 h-3" /> 解析內容
                      </Link>
                      <Link
                        href={`/resources/${r.resource_id}/candidates`}
                        className="flex items-center gap-1 text-xs text-amber-600 hover:text-amber-800 px-2 py-1 rounded hover:bg-amber-50"
                        title="確認抽取的題目"
                      >
                        <CheckCircle2 className="w-3 h-3" /> 題目確認
                      </Link>
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
