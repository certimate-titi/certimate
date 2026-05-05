/**
 * @file 路由 `/knowledge/wrong-answers` — 個人化錯題地圖（Feature 27）。
 *
 * 顯示當前科目知識節點的掌握度熱力圖（紅/橘/綠/灰），點擊節點展開錯題明細。
 */
'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, ChevronRight, ChevronDown, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { subjectService, wrongAnswerMapService, documentService, resourceParseService, type WrongAnswerMapNode } from '@/lib/api/services';
import type { UserSubject } from '@/types';
import SubjectSwitcher from '@/components/SubjectSwitcher';

const COLOR_CLASS: Record<string, string> = {
  green: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  orange: 'bg-amber-100 text-amber-800 border-amber-300',
  red: 'bg-rose-100 text-rose-800 border-rose-300',
  gray: 'bg-slate-100 text-slate-600 border-slate-300',
};

const COLOR_LABEL: Record<string, string> = {
  green: '已掌握',
  orange: '部分掌握',
  red: '需加強',
  gray: '未測',
};

export default function WrongAnswerHeatmapPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
      <Inner />
    </Suspense>
  );
}

function Inner() {
  const { isAuthenticated, loading: authLoading, onboardingCompleted } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSubjectId = typeof window !== 'undefined' ? (searchParams.get('subjectId') || localStorage.getItem('certimate_active_subject_id') || '') : '';

  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState(initialSubjectId);
  const [nodes, setNodes] = useState<WrongAnswerMapNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [wrongAnswers, setWrongAnswers] = useState<Record<string, Array<{ question_id: string; content: string; user_choice: string; correct_answer: string; answered_at: string }>>>({});
  const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null);

  // Layer 3：當 nodes 為空時，主動查 resource_parse_jobs 取得 FAILED 文件 failure_reason
  // 區分「真的沒錯題資料」vs「資源解析失敗導致無法產生知識節點與錯題」
  const [parseFailures, setParseFailures] = useState<Array<{name: string; reason: string}>>([]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (!onboardingCompleted) { router.replace('/onboarding'); return; }
    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects);
      if (!activeSubjectId && res.subjects.length > 0) {
        setActiveSubjectId(res.subjects[0].id);
      }
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router, activeSubjectId]);

  useEffect(() => {
    if (!activeSubjectId) return;
    setLoading(true);
    const subj = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = subj?.subjectId || activeSubjectId;
    wrongAnswerMapService.getMap(targetSubjectId)
      .then(res => setNodes(res.nodes || []))
      .catch(() => setNodes([]))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSubjectId]);

  // Layer 3：nodes 為空時查詢 parse job 失敗狀態
  useEffect(() => {
    if (loading || nodes.length > 0 || !activeSubjectId) {
      if (nodes.length > 0) setParseFailures([]);
      return;
    }
    documentService.list().then(async (res) => {
      const subjectFailedDocs = res.documents.filter(
        (d) => d.subjectId === activeSubjectId && d.status === 'FAILED'
      );
      const failures = await Promise.all(
        subjectFailedDocs.map(async (doc) => {
          try {
            const status = await resourceParseService.getStatus(doc.id);
            return { name: doc.title || '未命名資源', reason: status.failure_reason || '解析失敗（無詳細原因）' };
          } catch {
            return { name: doc.title || '未命名資源', reason: '解析失敗（查詢狀態失敗）' };
          }
        })
      );
      setParseFailures(failures);
    }).catch(() => setParseFailures([]));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, nodes.length, activeSubjectId]);

  const toggleNode = useCallback(async (nodeId: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId); else next.add(nodeId);
      return next;
    });
    if (!wrongAnswers[nodeId]) {
      setLoadingNodeId(nodeId);
      try {
        const res = await wrongAnswerMapService.getNodeWrongAnswers(nodeId);
        setWrongAnswers(prev => ({ ...prev, [nodeId]: res.wrong_answers || [] }));
      } catch {
        setWrongAnswers(prev => ({ ...prev, [nodeId]: [] }));
      } finally {
        setLoadingNodeId(null);
      }
    }
  }, [wrongAnswers]);

  const renderNode = (node: WrongAnswerMapNode, depth: number = 0): React.ReactNode => {
    const isExpanded = expanded.has(node.id);
    const colorClass = COLOR_CLASS[node.color] || COLOR_CLASS.gray;
    const wrongs = wrongAnswers[node.id];
    return (
      <div key={node.id} className="space-y-1" style={{ marginLeft: depth * 20 }}>
        <button
          onClick={() => toggleNode(node.id)}
          className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg border ${colorClass} hover:shadow-sm transition-shadow`}
          data-testid={`heatmap-node-${node.id}`}
        >
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <span className="font-medium flex-1">{node.name}</span>
          <span className="text-xs">{COLOR_LABEL[node.color]}</span>
          {node.wrong_count > 0 && (
            <span className="text-xs bg-white/70 px-2 py-0.5 rounded-full">錯 {node.wrong_count}</span>
          )}
          {node.mastery_rate != null && (
            <span className="text-xs">{Math.round(node.mastery_rate)}%</span>
          )}
        </button>
        {isExpanded && (
          <div className="ml-7 space-y-2">
            {loadingNodeId === node.id ? (
              <p className="text-xs text-slate-500 px-3">載入錯題中…</p>
            ) : wrongs && wrongs.length > 0 ? (
              <ul className="space-y-1">
                {wrongs.slice(0, 5).map(w => (
                  <li key={w.question_id} className="bg-rose-50 border border-rose-200 rounded-lg p-2 text-xs">
                    <p className="text-slate-800 line-clamp-2 mb-1">{w.content}</p>
                    <p className="text-slate-500">你選 <span className="text-rose-700 font-medium">{w.user_choice}</span> · 正解 <span className="text-emerald-700 font-medium">{w.correct_answer}</span></p>
                  </li>
                ))}
                {wrongs.length > 5 && (
                  <p className="text-xs text-slate-500 px-2">…另 {wrongs.length - 5} 題</p>
                )}
              </ul>
            ) : (
              <p className="text-xs text-slate-400 px-3">此節點目前無錯題記錄</p>
            )}
            {node.children && node.children.length > 0 && (
              <div className="space-y-1">
                {node.children.map(c => renderNode(c, depth + 1))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return <div className="flex items-center justify-center min-h-screen"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>;
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-3 sm:px-6 py-3 sm:py-4">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
          <div className="flex items-center gap-2 sm:gap-4 min-w-0">
            <Link href="/knowledge" className="p-2 rounded-lg hover:bg-slate-100 text-slate-600 shrink-0">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div className="flex-1 min-w-0">
              <h1 className="text-base sm:text-xl font-bold text-slate-900 truncate">個人錯題地圖</h1>
              <p className="text-[10px] sm:text-xs text-slate-500 hidden sm:block">紅 = 需加強、橘 = 部分掌握、綠 = 已掌握、灰 = 未測；點擊節點展開錯題明細</p>
              <p className="text-[10px] text-slate-500 sm:hidden">🔴需加強 🟠部分 🟢已掌握 ⚪未測</p>
            </div>
          </div>
          {subjects.length > 0 && (
            <div className="sm:ml-auto">
              <SubjectSwitcher
                subjects={subjects}
                activeSubjectId={activeSubjectId}
                onSwitch={(id) => { setActiveSubjectId(id); localStorage.setItem('certimate_active_subject_id', id); }}
                onAddSubject={() => router.push('/onboarding')}
                allowAdd={false}
                variant="compact"
              />
            </div>
          )}
        </div>
      </header>

      <main className="flex-1 overflow-y-auto py-8" data-testid="wrong-answer-heatmap">
        <div className="max-w-4xl mx-auto px-3 sm:px-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : nodes.length === 0 ? (
            <div className="text-center py-16">
              <AlertTriangle className="h-12 w-12 mx-auto text-slate-300 mb-3" />
              <p className="text-slate-600">尚無熱力圖資料</p>
              <p className="text-xs text-slate-400 mt-1">請先完成測驗，系統會根據作答記錄產生個人化錯題地圖</p>
              {parseFailures.length > 0 && (
                <div className="mt-4 mx-auto max-w-md text-left bg-rose-50 border border-rose-200 rounded-lg p-3">
                  <p className="text-xs font-semibold text-rose-700 mb-1">⚠️ 部分教材解析失敗，可能導致無法產生知識節點與錯題資料：</p>
                  <ul className="text-xs text-rose-600 space-y-1">
                    {parseFailures.slice(0, 3).map((f, i) => (
                      <li key={i}>• <span className="font-medium">{f.name}</span>：{f.reason}</li>
                    ))}
                    {parseFailures.length > 3 && (
                      <li className="italic">…另 {parseFailures.length - 3} 個（請至學習庫查看）</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {nodes.map(n => renderNode(n))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
