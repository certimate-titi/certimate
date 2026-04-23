'use client';

import { useEffect, useMemo, useState, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, ChevronRight, Loader2, Activity, Sparkles } from 'lucide-react';
import { usePathParam } from '@/hooks/use-path-param';
import { canvasService, CanvasNode, CanvasTierResponse } from '@/lib/api/services';
import ForceGraph, { GraphNode } from '@/components/ForceGraph';
import { track } from '@/lib/analytics';

type Crumb = { id: string; name: string; depth: number };

export default function CanvasClient() {
  const subjectId = usePathParam(/\/subjects\/([^/]+)\/canvas/);
  const [tier, setTier] = useState<CanvasTierResponse | null>(null);
  const [breadcrumb, setBreadcrumb] = useState<Crumb[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadProgress, setLoadProgress] = useState(0);

  // Strategy E：骨架載入時推進預估進度條（以 2000ms 為基準，載入中停在 95%）
  useEffect(() => {
    if (!loading) { setLoadProgress(0); return; }
    const t0 = performance.now();
    const BASELINE_MS = 2000;
    const id = setInterval(() => {
      const elapsed = performance.now() - t0;
      const pct = Math.min(95, Math.round((elapsed / BASELINE_MS) * 100));
      setLoadProgress(pct);
    }, 80);
    return () => clearInterval(id);
  }, [loading]);

  const loadTier1 = useCallback(async () => {
    if (!subjectId) return;
    // Strategy F：若已有預取快取，立即套用避免 skeleton 閃爍
    const prefetched = canvasService.readPrefetchedTier1(subjectId);
    if (prefetched) {
      setTier(prefetched);
      setBreadcrumb([]);
      setSelectedId(null);
      track('canvas_view', { subject_id: subjectId, tier: 1, node_count: prefetched.nodes.length, load_ms: 0, prefetched: true });
      return;
    }
    setLoading(true);
    setError('');
    try {
      const t0 = performance.now();
      const res = await canvasService.getTier1(subjectId);
      track('canvas_view', { subject_id: subjectId, tier: 1, node_count: res.nodes.length, load_ms: Math.round(performance.now() - t0) });
      setTier(res);
      setBreadcrumb([]);
      setSelectedId(null);
    } catch (e) {
      setError((e as Error)?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [subjectId]);

  const loadChildren = useCallback(async (parentId: string, parentName: string, parentDepth: number) => {
    if (!subjectId) return;
    setLoading(true);
    setError('');
    try {
      const t0 = performance.now();
      const res = await canvasService.getChildren(subjectId, parentId);
      track('canvas_drill_down', { subject_id: subjectId, parent_id: parentId, tier: res.tier, node_count: res.nodes.length, load_ms: Math.round(performance.now() - t0) });
      setTier(res);
      setBreadcrumb((b) => [...b, { id: parentId, name: parentName, depth: parentDepth }]);
      setSelectedId(null);
    } catch (e) {
      setError((e as Error)?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [subjectId]);

  const jumpTo = useCallback(async (idx: number) => {
    if (idx === -1) { loadTier1(); return; }
    const target = breadcrumb[idx];
    if (!subjectId || !target) return;
    setLoading(true);
    setError('');
    try {
      const res = await canvasService.getChildren(subjectId, target.id);
      setTier(res);
      setBreadcrumb((b) => b.slice(0, idx + 1));
      setSelectedId(null);
    } catch (e) {
      setError((e as Error)?.message || '載入失敗');
    } finally {
      setLoading(false);
    }
  }, [subjectId, breadcrumb, loadTier1]);

  useEffect(() => { loadTier1(); }, [loadTier1]);

  // Auto-drill when ?focus=<node_id> is present in URL (from dashboard radar click)
  const [focusApplied, setFocusApplied] = useState(false);
  useEffect(() => {
    if (focusApplied || !tier || tier.tier !== 1) return;
    const params = new URLSearchParams(window.location.search);
    const focusId = params.get('focus');
    if (!focusId) { setFocusApplied(true); return; }
    const target = tier.nodes.find((n) => n.id === focusId);
    if (target?.has_children) {
      loadChildren(target.id, target.name, target.depth);
    }
    setFocusApplied(true);
  }, [tier, focusApplied, loadChildren]);

  const graphNodes: GraphNode[] = useMemo(() => {
    if (!tier) return [];
    return tier.nodes.map<GraphNode>((n) => ({
      id: n.id,
      name: n.name,
      depth: n.depth,
      progress: n.mastery_rate,
      color: n.mastery_color,
      parentId: tier.parent_id,
      status: n.mastery_color,
      availableQuestions: n.available_questions,
    }));
  }, [tier]);

  const selectedNode: CanvasNode | undefined = tier?.nodes.find((n) => n.id === selectedId);

  const handleNodeClick = (id: string) => {
    setSelectedId(id);
    const node = tier?.nodes.find((n) => n.id === id);
    if (!node || !node.has_children) return;
    loadChildren(id, node.name, node.depth);
  };

  // 建議優先補：mastery_rate < 40 且 available_questions > 0 的前 5 個
  const suggestions = useMemo(() => {
    if (!tier) return [];
    return [...tier.nodes]
      .filter((n) => n.mastery_rate < 40 && n.available_questions > 0)
      .sort((a, b) => a.mastery_rate - b.mastery_rate)
      .slice(0, 5);
  }, [tier]);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-4 flex items-center gap-2 text-xs text-slate-600">
          <Activity className="w-4 h-4 text-emerald-600" />
          <span className="font-mono">知識地圖 Canvas</span>
          <Link href="/account/resource-library" className="ml-auto flex items-center gap-1 text-slate-500 hover:text-slate-800">
            <ArrowLeft className="w-3 h-3" /> 回資源庫
          </Link>
        </div>

        <div className="flex items-center gap-2 mb-4 text-sm flex-wrap">
          <button onClick={() => jumpTo(-1)} className="flex items-center gap-1 text-emerald-700 hover:text-emerald-900">
            領域層
          </button>
          {breadcrumb.map((b, i) => (
            <span key={b.id} className="flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <button onClick={() => jumpTo(i)} className="text-emerald-700 hover:text-emerald-900">
                {b.name}
              </button>
            </span>
          ))}
          <span className="ml-auto text-xs text-slate-500">
            Tier {tier?.tier ?? '–'} · {tier?.nodes.length ?? 0} 節點
          </span>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-3 bg-white rounded-xl border border-slate-200 overflow-hidden relative min-h-[400px] md:min-h-[600px]">
            {loading && !tier && (
              <div className="absolute inset-0 p-8" aria-label="載入中骨架">
                <div className="relative w-full h-full">
                  {[
                    { top: '30%', left: '25%', size: 56 },
                    { top: '22%', left: '55%', size: 64 },
                    { top: '55%', left: '38%', size: 48 },
                    { top: '60%', left: '70%', size: 52 },
                    { top: '42%', left: '82%', size: 44 },
                    { top: '72%', left: '15%', size: 50 },
                  ].map((p, i) => (
                    <div
                      key={i}
                      className="absolute rounded-full bg-slate-200 animate-pulse"
                      style={{ top: p.top, left: p.left, width: p.size, height: p.size }}
                    />
                  ))}
                  <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-64 max-w-[80%] flex flex-col items-center gap-2 text-xs text-slate-500">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      {loadProgress < 95 ? '建構知識地圖...' : '仍在載入，馬上就好...'}
                    </div>
                    <div className="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 transition-[width] duration-150 ease-out"
                        style={{ width: `${loadProgress}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
            {loading && tier && (
              <div className="absolute top-3 right-3 z-10">
                <Loader2 className="w-4 h-4 text-emerald-500 animate-spin" />
              </div>
            )}
            {!loading && tier?.empty_reason && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 p-6 text-center">
                <Sparkles className="w-10 h-10 mb-3 opacity-40" />
                <p className="text-sm font-medium">
                  {tier.empty_reason === 'no_nodes_generated' && '此科目尚未產生知識節點'}
                  {tier.empty_reason === 'leaf_node' && '已到達葉節點，沒有更細分的子節點'}
                </p>
              </div>
            )}
            {!loading && !tier?.empty_reason && (
              <ForceGraph
                nodes={graphNodes}
                onNodeClick={handleNodeClick}
                selectedNodeId={selectedId}
                width={800}
                height={600}
              />
            )}
          </div>

          <div className="md:col-span-1 space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="text-sm font-semibold text-slate-700 mb-2">建議優先補</div>
              {suggestions.length === 0 ? (
                <div className="text-xs text-slate-400">沒有明顯弱點 👍</div>
              ) : (
                <ul className="space-y-2">
                  {suggestions.map((s) => (
                    <li key={s.id}>
                      <button
                        onClick={() => handleNodeClick(s.id)}
                        className="w-full text-left text-xs p-2 rounded hover:bg-red-50"
                      >
                        <div className="font-medium text-slate-800 truncate">{s.name}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5">
                          掌握 {s.mastery_rate}% · {s.available_questions} 題
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {selectedNode && (
              <div className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-700 mb-2">節點詳情</div>
                <div className="space-y-1 text-xs text-slate-600">
                  <div className="font-medium text-slate-900">{selectedNode.name}</div>
                  <div>掌握度 {selectedNode.mastery_rate}%</div>
                  <div>葉節點數 {selectedNode.leaf_count}</div>
                  <div>可用題數 {selectedNode.available_questions}</div>
                </div>
                {selectedNode.has_children && (
                  <div className="mt-2 text-[10px] text-emerald-600">↓ 再次點擊展開下一層</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
