'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, Loader2, Lightbulb, MessageSquare, Target, AlertTriangle, Check } from 'lucide-react';
import { resourceParseService, scaffoldService } from '@/lib/api/services';
import type { ParsedResourceResponse, Scaffold, ScaffoldType } from '@/types/api';

const SCAFFOLD_META: Record<ScaffoldType, { label: string; icon: any; cls: string }> = {
  takeaway: { label: '重點摘要', icon: Lightbulb, cls: 'bg-yellow-50 border-yellow-200 text-yellow-900' },
  elaborative: { label: '延伸思考', icon: MessageSquare, cls: 'bg-indigo-50 border-indigo-200 text-indigo-900' },
  strategy: { label: '學習策略', icon: Target, cls: 'bg-emerald-50 border-emerald-200 text-emerald-900' },
};

function ScaffoldCard({ s, onSubmitted }: { s: Scaffold; onSubmitted: () => void }) {
  const meta = SCAFFOLD_META[s.type];
  const Icon = meta.icon;
  const [response, setResponse] = useState(s.user_response || '');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!response.trim()) return;
    setSubmitting(true);
    try {
      await scaffoldService.submitResponse(s.id, response);
      onSubmitted();
    } catch (e: any) {
      alert(`儲存失敗：${e?.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={`border rounded-lg p-4 mb-3 ${meta.cls}`}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wide">{meta.label}</span>
            {s.chapter_heading && (
              <span className="text-xs opacity-70">· {s.chapter_heading}</span>
            )}
          </div>
          <p className="text-sm whitespace-pre-wrap mb-3">{s.content}</p>

          {s.type === 'elaborative' && (
            <div className="mt-3">
              <textarea
                value={response}
                onChange={(e) => setResponse(e.target.value)}
                rows={3}
                placeholder="用自己的話說明你的想法..."
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <div className="flex items-center gap-2 mt-2">
                <button
                  onClick={submit}
                  disabled={submitting || !response.trim() || response === s.user_response}
                  className="flex items-center gap-1 px-3 py-1 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-40"
                >
                  <Check className="w-3 h-3" />
                  {s.user_response ? '更新回應' : '送出回應'}
                </button>
                {s.user_response && (
                  <span className="text-xs text-gray-500">已記錄於 {s.user_response.length} 字</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function useResourceIdFromPath(): string {
  const [id, setId] = useState('');
  useEffect(() => {
    const m = window.location.pathname.match(/\/resources\/([^/]+)\/parsed/);
    if (m) setId(m[1]);
  }, []);
  return id;
}

export default function ParsedResourcePage() {
  const resourceId = useResourceIdFromPath();

  const [data, setData] = useState<ParsedResourceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetch = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await resourceParseService.getParsed(resourceId);
      setData(res);
    } catch (e: any) {
      setError(e?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [resourceId]);

  useEffect(() => { if (resourceId) fetch(); }, [resourceId, fetch]);

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
        <Link href="/account/resource-library" className="p-2 rounded-lg hover:bg-gray-100 text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">資源解析內容</h1>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600">
            <span className="mr-3">類型：<span className="font-mono">{data.detected_content_type || '—'}</span></span>
            <span>信任度：<span className="font-mono">{data.trust_level || '—'}</span></span>
          </div>

          <section className="mb-8">
            <h2 className="font-semibold mb-3 text-gray-800">學習鷹架 Layer A</h2>
            {data.scaffolds.length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-8">此資源尚無學習鷹架</div>
            ) : (
              data.scaffolds.map((s) => <ScaffoldCard key={s.id} s={s} onSubmitted={fetch} />)
            )}
          </section>

          {data.parsed_markdown && (
            <section>
              <h2 className="font-semibold mb-3 text-gray-800">解析全文</h2>
              <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-[60vh] overflow-y-auto font-sans">
                {data.parsed_markdown}
              </pre>
            </section>
          )}
        </>
      )}
    </div>
  );
}
