/**
 * @file 路由 `/knowledge/mindmap` — 全螢幕知識地圖頁。
 *
 * 以 ForceGraph + MindMapTree 兩種視圖呈現整個科目的知識結構；
 * 透過 query string `subjectId` 切換科目。
 */
'use client';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Network, ArrowLeft, X, BookOpen, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import { knowledgeService, subjectService, documentService, resourceParseService } from '@/lib/api/services';
import type { GetNodeDetailResponse } from '@/types/api';
import type { KnowledgeNode, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import MindMapTree, { type MindMapNode } from '@/components/MindMapTree';
import ForceGraph, { type GraphNode } from '@/components/ForceGraph';

/**
 * 全螢幕知識地圖頁外層（Suspense 包裝以滿足 `useSearchParams` 需求）。
 */
export default function FullMindMapPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>}>
      <FullMindMapPageInner />
    </Suspense>
  );
}

function FullMindMapPageInner() {
  const { isAuthenticated, loading: authLoading, onboardingCompleted } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSubjectId = searchParams.get('subjectId') || localStorage.getItem('certimate_active_subject_id') || '';

  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState(initialSubjectId);
  const [mindMapNodes, setMindMapNodes] = useState<MindMapNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'tree' | 'force'>('force');
  // Layer 3：mindMapNodes 為空時主動查 resource_parse_jobs，區分「尚未上傳」vs「parse job 失敗」
  const [parseJobFailures, setParseJobFailures] = useState<Array<{ title: string; reason: string }>>([]);
  // L62：節點詳情面板
  const [nodeDetail, setNodeDetail] = useState<GetNodeDetailResponse | null>(null);
  const [loadingNodeDetail, setLoadingNodeDetail] = useState(false);

  // Flatten MindMapNode tree → GraphNode[] for ForceGraph
  const graphNodes: GraphNode[] = (() => {
    const flat: GraphNode[] = [];
    const flatten = (nodes: MindMapNode[]) => {
      for (const n of nodes) {
        flat.push({
          id: n.id, name: n.name, depth: n.depth,
          progress: n.mastery_rate || 0,
          color: n.mastery_color || 'gray',
          parentId: n.parent_id,
          status: n.status || 'UNSEEN',
          availableQuestions: 0,
        });
        if (n.children) flatten(n.children);
      }
    };
    flatten(mindMapNodes);
    return flat;
  })();

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
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    knowledgeService.getMap(targetSubjectId).then((mapRes: Record<string, unknown>) => {
      setMindMapNodes((mapRes.nodes || []) as unknown as MindMapNode[]);
      setLoading(false);
    }).catch(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSubjectId]);

  // Layer 3：mindMapNodes 為空時觸發查詢，區分「尚未上傳」vs「parse job 失敗」
  useEffect(() => {
    if (loading || mindMapNodes.length > 0 || !activeSubjectId) {
      setParseJobFailures([]);
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
            return { title: doc.title || '未命名資源', reason: status.failure_reason || '解析失敗（無詳細原因）' };
          } catch {
            return { title: doc.title || '未命名資源', reason: '解析失敗（查詢狀態失敗）' };
          }
        })
      );
      setParseJobFailures(failures);
    }).catch(() => setParseJobFailures([]));
  }, [loading, mindMapNodes.length, activeSubjectId]);

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    // L62：載入節點詳情至側邊面板
    setNodeDetail(null);
    setLoadingNodeDetail(true);
    knowledgeService.getNodeDetail(nodeId)
      .then(detail => {
        setNodeDetail(detail);
      })
      .catch(() => setNodeDetail(null))
      .finally(() => setLoadingNodeDetail(false));
  };

  const closeNodeDetail = () => {
    setSelectedNodeId(null);
    setNodeDetail(null);
  };

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <>
      {subjects.length > 0 && (
        <SubjectSwitcher
          subjects={subjects}
          activeSubjectId={activeSubjectId}
          onSwitch={(id) => { setActiveSubjectId(id); localStorage.setItem('certimate_active_subject_id', id); }}
          onAddSubject={() => router.push('/onboarding')}
          allowAdd={false}
        />
      )}
      <div className="flex-1 flex flex-col h-[calc(100vh-64px-48px)] overflow-hidden bg-white">
        <header className="border-b border-slate-200 px-6 py-3 flex items-center gap-4 shrink-0">
          <button onClick={() => router.push('/knowledge')} className="text-slate-400 hover:text-slate-600">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-emerald-500" />
            <h1 className="text-lg font-bold text-slate-900">完整知識心智圖</h1>
          </div>
          <div className="ml-auto flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> 精熟 (&ge;80%)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> 部分 (60-79%)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" /> 需加強 (&lt;60%)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300" /> 未測驗</span>
          </div>
        </header>

        {/* View Mode Toggle */}
        <div className="px-6 pt-4 flex items-center gap-2">
          <div className="flex bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('force')}
              className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                viewMode === 'force' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >🌐 動態圖譜</button>
            <button
              onClick={() => setViewMode('tree')}
              className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                viewMode === 'tree' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >📋 列表模式</button>
          </div>
          <span className="text-xs text-slate-400">{graphNodes.length} 個知識節點</span>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : mindMapNodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-400 px-6">
              <div className="text-center max-w-md">
                <Network className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                <p>尚無知識圖譜節點</p>
                {parseJobFailures.length > 0 ? (
                  <div className="mt-4 text-left bg-rose-50 border border-rose-200 rounded-lg p-3">
                    <p className="text-xs font-semibold text-rose-700 mb-1">⚠️ 偵測到 {parseJobFailures.length} 個資源解析失敗，導致無法生成知識圖譜：</p>
                    <ul className="text-xs text-rose-600 space-y-1">
                      {parseJobFailures.slice(0, 3).map((f, i) => (
                        <li key={i}>• <span className="font-medium">{f.title}</span>：{f.reason}</li>
                      ))}
                      {parseJobFailures.length > 3 && (
                        <li className="italic">…另 {parseJobFailures.length - 3} 個（請至學習庫查看）</li>
                      )}
                    </ul>
                  </div>
                ) : (
                  <p className="text-xs mt-1">上傳教材後系統會自動生成</p>
                )}
              </div>
            </div>
          ) : viewMode === 'force' ? (
            <ForceGraph
              nodes={graphNodes}
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedNodeId}
              width={900}
              height={600}
            />
          ) : (
            <MindMapTree
              nodes={mindMapNodes}
              selectedNodeId={selectedNodeId}
              onNodeClick={handleNodeClick}
            />
          )}
        </div>
      </div>

      {/* L62: 節點詳情側邊面板（點擊節點後顯示） */}
      {selectedNodeId && (
        <aside
          data-testid="mindmap-node-detail-panel"
          className="fixed right-0 top-0 h-full w-96 bg-white border-l border-slate-200 shadow-xl z-40 flex flex-col"
        >
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <h3 className="font-bold text-slate-900">節點詳情</h3>
            <button onClick={closeNodeDetail} aria-label="關閉節點詳情" className="p-1 text-slate-500 hover:text-slate-900">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {loadingNodeDetail ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : nodeDetail ? (
              <>
                <div>
                  <h4 className="text-base font-bold text-slate-900">{nodeDetail.node.label || '未命名節點'}</h4>
                  {nodeDetail.citationSource && (
                    <p className="text-xs text-slate-500 mt-1">
                      來源：{nodeDetail.citationSource.documentTitle}
                      {nodeDetail.citationSource.page != null && ` · 第 ${nodeDetail.citationSource.page} 頁`}
                    </p>
                  )}
                </div>
                {nodeDetail.citationText && (
                  <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                    <p className="text-xs font-medium text-slate-600 mb-1">節點摘要</p>
                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{nodeDetail.citationText.slice(0, 400)}</p>
                  </div>
                )}
                <div className="space-y-2">
                  <Link
                    href={`/practice?nodeId=${selectedNodeId}`}
                    className="flex items-center gap-2 px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium"
                  >
                    <BookOpen className="h-4 w-4" />
                    開始練習此節點
                  </Link>
                  <Link
                    href={`/knowledge?subjectId=${activeSubjectId}&nodeId=${selectedNodeId}`}
                    className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 text-sm font-medium"
                  >
                    <BarChart3 className="h-4 w-4" />
                    在學習庫查看詳情
                  </Link>
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-500 text-center py-8">無法載入節點詳情</p>
            )}
          </div>
        </aside>
      )}
    </>
  );
}
