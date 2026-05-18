/**
 * @file 路由 `/resources/[id]/candidates` — 題目候選審核客戶端元件。
 *
 * 由同目錄 `page.tsx`（generateStaticParams stub）載入；列出資源解析後
 * 抽取的候選題目（T2/T3 流程），讓使用者勾選確認以併入個人題庫。
 * 因應靜態匯出限制，從 `window.location.pathname` 解析 resource id。
 */
'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { questionCandidateService } from '@/lib/api/services';
import type { CandidateListResponse, QuestionCandidate } from '@/types/api';
import MathContent from '@/components/MathContent';

/** 從 `window.location.pathname` 解析 `/resources/{id}/candidates` 的 resource id。 */
function useResourceIdFromPath(): string {
  const [id, setId] = useState('');
  useEffect(() => {
    const m = window.location.pathname.match(/\/resources\/([^/]+)\/candidates/);
    if (m) setId(m[1]);
  }, []);
  return id;
}

export default function CandidateApprovalPage() {
  const resourceId = useResourceIdFromPath();

  const [data, setData] = useState<CandidateListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await questionCandidateService.list(resourceId);
      setData(res);
      setSelected(new Set());
    } catch (e: any) {
      setError(e?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [resourceId]);

  useEffect(() => { if (resourceId) fetch(); }, [resourceId, fetch]);

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const submit = async (approve: boolean) => {
    if (selected.size === 0) {
      alert('請先勾選至少一題');
      return;
    }
    setSubmitting(true);
    try {
      const res = await questionCandidateService.decide(resourceId, {
        candidate_ids: Array.from(selected),
        approve,
      });
      alert(`完成：核准 ${res.approved}、拒絕 ${res.rejected}`);
      fetch();
    } catch (e: any) {
      alert(`操作失敗：${e?.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const renderCandidate = (c: QuestionCandidate) => {
    const checked = selected.has(c.id);
    return (
      <div
        key={c.id}
        className={`border rounded-lg p-4 mb-3 cursor-pointer transition ${
          checked ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
        }`}
        onClick={() => toggle(c.id)}
      >
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={checked}
            onChange={() => toggle(c.id)}
            onClick={(e) => e.stopPropagation()}
            className="mt-1"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                c.tier === 'T2' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
              }`}>
                {c.tier}
              </span>
              {c.confidence !== null && (
                <span className="text-xs text-gray-500">
                  信心度 {(c.confidence * 100).toFixed(0)}%
                </span>
              )}
              {c.source_page !== null && (
                <span className="text-xs text-gray-400">來源：第 {c.source_page} 頁</span>
              )}
            </div>
            <div className="text-sm text-gray-900 mb-2">
              <MathContent>{c.question_text}</MathContent>
            </div>
            <ul className="text-xs text-gray-600 space-y-1 mb-2">
              {c.options.map((opt, i) => (
                <li key={i} className="flex gap-1">
                  <span className="font-mono shrink-0">{String.fromCharCode(65 + i)}.</span>
                  <MathContent>{opt}</MathContent>
                </li>
              ))}
            </ul>
            <p className="text-xs">
              <span className="text-gray-500">AI 推論答案：</span>
              {c.ai_inferred_answer ? (
                <span className="font-bold text-indigo-700">{c.ai_inferred_answer}</span>
              ) : (
                <span className="text-amber-600">無 — 需使用者盲推論作答</span>
              )}
            </p>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/knowledge" className="p-2 rounded-lg hover:bg-gray-100 text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">題目抽取確認</h1>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            已自動納入高信心題目（T1）：<span className="font-bold">{data.t1_count}</span> 題
          </div>

          {data.t2.length > 0 && (
            <section className="mb-6">
              <h2 className="font-semibold mb-3 text-amber-700">T2 中信心（需確認，{data.t2.length} 題）</h2>
              {data.t2.map(renderCandidate)}
            </section>
          )}

          {data.t3.length > 0 && (
            <section className="mb-6">
              <h2 className="font-semibold mb-3 text-red-700">T3 低信心（建議檢視後再納入，{data.t3.length} 題）</h2>
              {data.t3.map(renderCandidate)}
            </section>
          )}

          {data.t2.length === 0 && data.t3.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p>沒有待確認的題目候選</p>
            </div>
          )}

          {(data.t2.length > 0 || data.t3.length > 0) && (
            <div className="sticky bottom-4 flex justify-end gap-2 bg-white/90 backdrop-blur p-3 border border-gray-200 rounded-lg shadow">
              <span className="text-sm text-gray-500 self-center mr-auto">
                已選 {selected.size} 題
              </span>
              <button
                onClick={() => submit(false)}
                disabled={submitting || selected.size === 0}
                className="flex items-center gap-1 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                <XCircle className="w-4 h-4" /> 拒絕
              </button>
              <button
                onClick={() => submit(true)}
                disabled={submitting || selected.size === 0}
                className="flex items-center gap-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-40"
              >
                <CheckCircle2 className="w-4 h-4" /> 核准納入個人題庫
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
