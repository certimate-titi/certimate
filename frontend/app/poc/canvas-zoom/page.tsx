'use client';

import { useMemo, useState, useEffect, useRef } from 'react';
import { generateMockNodes, masteryToStatus, masteryToColor, CanvasNode } from './mock-data';
import ForceGraph, { GraphNode } from '@/components/ForceGraph';
import { ArrowLeft, ChevronRight, Activity } from 'lucide-react';

type TierContext = {
  level: 1 | 2 | 3;
  parentId: string | null;
  breadcrumb: { id: string; name: string }[];
};

export default function CanvasZoomPOCPage() {
  const allNodes = useMemo(() => generateMockNodes(), []);
  const [ctx, setCtx] = useState<TierContext>({ level: 1, parentId: null, breadcrumb: [] });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [perf, setPerf] = useState<{ renderMs: number; switchMs: number; nodeCount: number }>({
    renderMs: 0,
    switchMs: 0,
    nodeCount: 0,
  });
  const lastSwitchStart = useRef<number>(0);

  const visibleNodes: GraphNode[] = useMemo(() => {
    const t0 = performance.now();
    let filtered: CanvasNode[];
    if (ctx.level === 1) {
      filtered = allNodes.filter((n) => n.tier === 1);
    } else {
      filtered = allNodes.filter((n) => n.parentId === ctx.parentId);
    }
    const mapped = filtered.map<GraphNode>((n) => ({
      id: n.id,
      name: n.name,
      depth: n.tier - 1,
      progress: Math.round(n.mastery * 100),
      color: masteryToColor(n.mastery),
      parentId: n.parentId,
      status: masteryToStatus(n.mastery),
      availableQuestions: n.questionCount,
    }));
    const renderMs = performance.now() - t0;
    setTimeout(() => {
      const switchMs = lastSwitchStart.current ? performance.now() - lastSwitchStart.current : 0;
      setPerf({ renderMs, switchMs, nodeCount: mapped.length });
    }, 0);
    return mapped;
  }, [ctx, allNodes]);

  const handleNodeClick = (id: string) => {
    setSelectedId(id);
    const node = allNodes.find((n) => n.id === id);
    if (!node || node.tier === 3) return;
    lastSwitchStart.current = performance.now();
    setCtx({
      level: (node.tier + 1) as 1 | 2 | 3,
      parentId: id,
      breadcrumb: [...ctx.breadcrumb, { id, name: node.name }],
    });
  };

  const handleBreadcrumb = (idx: number) => {
    lastSwitchStart.current = performance.now();
    if (idx === -1) {
      setCtx({ level: 1, parentId: null, breadcrumb: [] });
      return;
    }
    const newBreadcrumb = ctx.breadcrumb.slice(0, idx + 1);
    const parent = newBreadcrumb[newBreadcrumb.length - 1];
    const parentNode = allNodes.find((n) => n.id === parent.id);
    if (!parentNode) return;
    setCtx({
      level: (parentNode.tier + 1) as 1 | 2 | 3,
      parentId: parent.id,
      breadcrumb: newBreadcrumb,
    });
  };

  const selectedNode = allNodes.find((n) => n.id === selectedId);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-4 flex items-center gap-2 text-xs text-slate-600">
          <Activity className="w-4 h-4 text-emerald-600" />
          <span className="font-mono">POC-canvas-zoom</span>
          <span className="text-slate-400">· 驗證 D3 ForceGraph 三層 Zoom</span>
        </div>

        <div className="flex items-center gap-2 mb-4 text-sm">
          <button
            onClick={() => handleBreadcrumb(-1)}
            className="flex items-center gap-1 text-emerald-600 hover:text-emerald-800"
          >
            <ArrowLeft className="w-4 h-4" />
            領域層 (L1)
          </button>
          {ctx.breadcrumb.map((b, i) => (
            <span key={b.id} className="flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <button
                onClick={() => handleBreadcrumb(i)}
                className="text-emerald-600 hover:text-emerald-800"
              >
                {b.name}
              </button>
            </span>
          ))}
          <span className="ml-auto text-xs text-slate-500">
            當前：Tier {ctx.level} · 節點數 {perf.nodeCount}
          </span>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="col-span-3 bg-white rounded-lg border border-slate-200 overflow-hidden">
            <ForceGraph
              nodes={visibleNodes}
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedId}
              width={800}
              height={600}
            />
          </div>

          <div className="col-span-1 space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <div className="text-xs font-medium text-slate-700 mb-2">📊 效能指標</div>
              <div className="space-y-1 text-xs font-mono text-slate-600">
                <div>Render ms: {perf.renderMs.toFixed(2)}</div>
                <div>Switch ms: {perf.switchMs.toFixed(2)}</div>
                <div>Nodes: {perf.nodeCount}</div>
                <div>Total: {allNodes.length}</div>
              </div>
              <div className="mt-3 text-[10px] text-slate-500">
                目標：Switch &lt;500ms、FPS &gt;30
              </div>
            </div>

            {selectedNode && (
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <div className="text-xs font-medium text-slate-700 mb-2">節點詳情</div>
                <div className="space-y-1 text-xs text-slate-600">
                  <div>名稱：{selectedNode.name}</div>
                  <div>Tier：{selectedNode.tier}</div>
                  <div>掌握度：{(selectedNode.mastery * 100).toFixed(0)}%</div>
                  <div>題數：{selectedNode.questionCount}</div>
                  <div>錯題：{selectedNode.wrongAnswerCount}</div>
                </div>
                {selectedNode.tier < 3 && (
                  <div className="mt-2 text-[10px] text-emerald-600">
                    ↓ 點擊節點展開下一層
                  </div>
                )}
              </div>
            )}

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-[11px] text-amber-800">
              <div className="font-medium mb-1">⚠️ POC 說明</div>
              <ul className="list-disc pl-4 space-y-0.5">
                <li>192 假節點（6×4×8）</li>
                <li>單擊節點 → 進下一層</li>
                <li>Breadcrumb 返回上層</li>
                <li>不入主線，僅驗證</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
