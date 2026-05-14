'use client';

/**
 * @file NotesTagGraph.tsx
 *
 * 標籤圖譜元件：
 *  - Nodes = 使用者筆記中的 unique hashtags（從 listTags 取得）
 *  - Edges = 共現次數（同一篇筆記有多個 #tag → 兩兩之間邊權重 +1）
 *  - Node size = tag 出現次數（count）
 *  - 點擊 node → onTagClick callback（觸發 timeline tag filter + 切回 timeline view）
 *  - 共現計算：client-side（100 筆以內規模 OK）
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { userTagService, userNoteService } from '@/lib/api/services';
import type { AggregatedTag } from '@/types/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface TagNode {
  id: string;        // normalized tag
  display: string;   // display tag (e.g. #深度學習)
  count: number;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface TagEdge {
  source: string | TagNode;
  target: string | TagNode;
  weight: number;
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface NotesTagGraphProps {
  subjectId: string | null;
  activeTag: string | null;
  onTagClick: (normalized: string) => void;
}

// ─── Hashtag extractor ────────────────────────────────────────────────────────

function extractHashtags(content: string): string[] {
  const matches = content.match(/#[\w一-鿿㐀-䶿]+/g) ?? [];
  // Normalize: lowercase, strip leading #
  return [...new Set(matches.map((t) => t.slice(1).toLowerCase()))];
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function NotesTagGraph({ subjectId, activeTag, onTagClick }: NotesTagGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tags, setTags] = useState<AggregatedTag[]>([]);
  const [edges, setEdges] = useState<{ source: string; target: string; weight: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; tag: AggregatedTag } | null>(null);
  const [dimensions, setDimensions] = useState({ width: 700, height: 500 });

  // Measure container
  useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDimensions({
          width: entry.contentRect.width || 700,
          height: Math.max(entry.contentRect.height, 400) || 500,
        });
      }
    });
    obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  // Fetch tags (aggregate 3 sources) + notes for co-occurrence edges
  useEffect(() => {
    if (!subjectId) {
      setTags([]);
      setEdges([]);
      return;
    }
    setLoading(true);

    // aggregate endpoint 提供 3 sources 合併的 tag list
    // user-notes list 仍用於計算共現邊（只有 note 有自由文字 hashtag）
    Promise.allSettled([
      userTagService.aggregate({ subject_id: subjectId, limit: 100 }),
      userNoteService.list({ subject_id: subjectId, limit: 100 }),
    ]).then(([tagRes, noteRes]) => {
      const tagItems = tagRes.status === 'fulfilled' ? tagRes.value.items : [];
      setTags(tagItems);

      if (noteRes.status === 'fulfilled') {
        // Build co-occurrence map from notes content
        const coMap: Record<string, number> = {};
        noteRes.value.items.forEach((note) => {
          const noteTags = extractHashtags(note.content);
          for (let i = 0; i < noteTags.length; i++) {
            for (let j = i + 1; j < noteTags.length; j++) {
              const key = [noteTags[i], noteTags[j]].sort().join('|');
              coMap[key] = (coMap[key] ?? 0) + 1;
            }
          }
        });
        const edgeList = Object.entries(coMap).map(([key, weight]) => {
          const [source, target] = key.split('|');
          return { source, target, weight };
        });
        setEdges(edgeList);
      }
    }).finally(() => setLoading(false));
  }, [subjectId]);

  // D3 force graph
  const renderGraph = useCallback(() => {
    if (!svgRef.current) return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    // 永遠先清 SVG（即便 tags 為空也要清掉前一個 subject 的殘留圖）
    svg.selectAll('*').remove();
    if (tags.length === 0) return;

    const tagMap = new Map(tags.map((t) => [t.normalized, t]));

    // Filter edges to only include tags that exist in tagMap
    const validEdges = edges.filter(
      (e) => tagMap.has(e.source) && tagMap.has(e.target)
    );

    // Node radius — Obsidian 風格小節點（4-12px）
    const counts = tags.map((t) => t.count);
    const minCount = Math.min(...counts);
    const maxCount = Math.max(...counts);
    const radiusScale: (c: number) => number =
      minCount === maxCount
        ? () => 6
        : d3.scaleLinear().domain([minCount, maxCount]).range([4, 12]).clamp(true) as unknown as (c: number) => number;

    // 鄰居索引：mouseenter 時用來找該節點 1-hop 鄰居以套高亮
    const neighborMap = new Map<string, Set<string>>();
    for (const e of validEdges) {
      if (!neighborMap.has(e.source)) neighborMap.set(e.source, new Set());
      if (!neighborMap.has(e.target)) neighborMap.set(e.target, new Set());
      neighborMap.get(e.source)!.add(e.target);
      neighborMap.get(e.target)!.add(e.source);
    }

    const simNodes: TagNode[] = tags.map((t) => ({
      id: t.normalized,
      display: t.display,
      count: t.count,
      x: width / 2 + (Math.random() - 0.5) * 200,
      y: height / 2 + (Math.random() - 0.5) * 200,
    }));

    const simEdges = validEdges.map((e) => ({ ...e }));

    const simulation = d3.forceSimulation(simNodes as any)
      .force('link', d3.forceLink(simEdges as any)
        .id((d: any) => d.id)
        .distance((d: any) => Math.max(60 - (d.weight ?? 1) * 4, 30))
        .strength(0.6))
      .force('charge', d3.forceManyBody().strength(-80))
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.08))
      .force('collision', d3.forceCollide().radius((d: any) => radiusScale(d.count) + 6));

    const container = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => container.attr('transform', event.transform));
    svg.call(zoom);
    svg.call(zoom.transform, d3.zoomIdentity);

    // High-count threshold：top 30% 視為「常用 tag」，顯示 emerald；其餘 slate-400
    const sortedCounts = [...counts].sort((a, b) => b - a);
    const top30Idx = Math.max(1, Math.floor(sortedCounts.length * 0.3));
    const highCountThreshold = sortedCounts[top30Idx - 1] ?? 0;
    const baseFillForNode = (id: string) => {
      const c = tagMap.get(id)?.count ?? 0;
      return c >= highCountThreshold ? '#10b981' : '#9ca3af'; // emerald-500 / slate-400
    };

    // Edges — Obsidian 風格：預設極淡灰，hover/active 相關邊變紫
    const link = container.append('g')
      .selectAll('line')
      .data(simEdges)
      .join('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-opacity', (d: any) => Math.min(0.35 + (d.weight ?? 1) * 0.05, 0.6))
      .attr('stroke-width', (d: any) => Math.min(0.8 + (d.weight ?? 1) * 0.4, 3))
      .style('transition', 'stroke 150ms ease, stroke-opacity 150ms ease');

    // Edge weight 不再以數字顯示；共現次數已由 link stroke-width 編碼
    // Node groups
    const nodeGroup = container.append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .style('cursor', 'pointer')
      .on('click', (_event, d: any) => onTagClick(d.id))
      .on('mouseenter', (event, d: any) => {
        const rect = svgRef.current!.getBoundingClientRect();
        const tag = tagMap.get(d.id);
        if (tag) {
          setTooltip({ x: event.clientX - rect.left, y: event.clientY - rect.top - 10, tag });
        }
      })
      .on('mouseleave', () => setTooltip(null))
      .call(
        d3.drag<SVGGElement, any>()
          .on('start', (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }) as any
      );

    // Node circles — Obsidian 風格
    // 預設：emerald（高頻）/ slate-400（一般）
    // active（已點擊持續）：飽和紫 + ring
    // 非鄰居 dim 由 hover handler 動態套，初始皆「正常」色
    nodeGroup.append('circle')
      .attr('r', (d: any) => radiusScale(d.count) + (activeTag === d.id ? 2 : 0))
      .attr('fill', (d: any) => activeTag === d.id ? '#8b5cf6' : baseFillForNode(d.id))
      .attr('stroke', (d: any) => activeTag === d.id ? '#c4b5fd' : 'none')
      .attr('stroke-width', (d: any) => activeTag === d.id ? 1.5 : 0)
      .style('transition', 'fill 150ms ease, r 150ms ease');

    // Node labels — Obsidian 風格：預設不顯示，只在 active 或 hover 時可見
    nodeGroup.append('text')
      .attr('class', 'tag-label')
      .text((d: any) => d.display.length > 12 ? d.display.slice(0, 12) + '…' : d.display)
      .attr('text-anchor', 'middle')
      .attr('dy', (d: any) => radiusScale(d.count) + 12)
      .attr('fill', '#334155')
      .attr('font-size', '10px')
      .attr('font-weight', '500')
      .attr('pointer-events', 'none')
      .style('opacity', (d: any) => activeTag === d.id ? 1 : 0)
      .style('transition', 'opacity 120ms ease');

    // Hover：紫色高亮該節點 + 鄰居白 + 非鄰居 dim + edges 變紫
    nodeGroup
      .on('mouseenter.highlight', function (_event, d: any) {
        const hoveredId = d.id;
        const hovNeighbors = neighborMap.get(hoveredId) ?? new Set<string>();

        // Nodes：hover 紫 / 鄰居深色 / 其他 dim 淺灰
        nodeGroup.select<SVGCircleElement>('circle')
          .attr('fill', (nd: any) => {
            if (nd.id === hoveredId) return '#8b5cf6';
            if (hovNeighbors.has(nd.id)) return '#334155';  // slate-700 強對比
            return '#e2e8f0';                                // slate-200 淡化
          });

        // 顯示 hover 節點 label
        d3.select(this).select<SVGTextElement>('.tag-label').style('opacity', 1);

        // Edges：hover 相關紫亮，其他淡化
        link
          .attr('stroke', (ed: any) => {
            const s = typeof ed.source === 'string' ? ed.source : ed.source.id;
            const t = typeof ed.target === 'string' ? ed.target : ed.target.id;
            return s === hoveredId || t === hoveredId ? '#8b5cf6' : '#e2e8f0';
          })
          .attr('stroke-opacity', (ed: any) => {
            const s = typeof ed.source === 'string' ? ed.source : ed.source.id;
            const t = typeof ed.target === 'string' ? ed.target : ed.target.id;
            return s === hoveredId || t === hoveredId ? 0.85 : 0.3;
          });
      })
      .on('mouseleave.highlight', function (_event, d: any) {
        // 還原預設：node 顏色按 baseFill / active；edges 全部回 slate-400
        nodeGroup.select<SVGCircleElement>('circle')
          .attr('fill', (nd: any) => activeTag === nd.id ? '#8b5cf6' : baseFillForNode(nd.id));

        link
          .attr('stroke', '#94a3b8')
          .attr('stroke-opacity', (ed: any) => Math.min(0.35 + (ed.weight ?? 1) * 0.05, 0.6));

        if (activeTag !== d.id) {
          d3.select(this).select<SVGTextElement>('.tag-label').style('opacity', 0);
        }
      });

    // Tick handler updates DOM positions from datum.
    const updateDom = () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    };

    // Tick handler 註冊讓 d3 timer + drag 互動可用。但因 React StrictMode + Suspense
    // 環境實測 'tick' event 可能在 cleanup 前只觸發 1-2 次（rAF 鏈被 cancel）→ DOM
    // transform 永遠 null。
    //
    // 防線：mount 時同步跑 200 ticks 強制 converge 並立即 updateDom，把最終位置寫進
    // DOM。即使後續 cleanup 取消 d3 timer，DOM 已有完整佈局。forceLink id→node
    // 解析在 simulation 創建時已完成，sync tick 不會撞 PR #109 的 crash。
    simulation.on('tick', updateDom);
    for (let i = 0; i < 200; i++) simulation.tick();
    updateDom();

    // 重啟 d3 timer 讓拖曳互動能再觸發 tick → updateDom（即便 alpha 已降，drag
    // start 會 alphaTarget(0.3).restart() 拉起 timer）。
    simulation.alpha(0.05).restart();

    return () => { simulation.stop(); };
  }, [tags, edges, dimensions, activeTag, onTagClick]);

  useEffect(() => {
    const cleanup = renderGraph();
    return cleanup;
  }, [renderGraph]);

  return (
    <div ref={containerRef} className="relative flex-1 h-full bg-white rounded-none overflow-hidden">
      {/* 首頁同款 24px 灰格底紋 */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      {!loading && tags.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-4">
          <span className="text-4xl">🏷️</span>
          <p className="text-sm text-slate-500 font-medium">尚無標籤</p>
          <p className="text-xs text-slate-400">在自由筆記中輸入 #標籤 即可建立標籤圖譜</p>
        </div>
      )}
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
        viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
      />
      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute bg-white text-slate-800 px-3 py-2 rounded-lg text-xs shadow-lg pointer-events-none z-10 border border-slate-200 min-w-[160px]"
          style={{ left: tooltip.x, top: tooltip.y, transform: 'translate(-50%, -100%)' }}
        >
          <p className="font-bold text-emerald-700 mb-1">{tooltip.tag.display}</p>
          <p className="text-slate-500 mb-1.5">共 {tooltip.tag.count} 次 · 點擊篩選</p>
          <div className="border-t border-slate-100 pt-1.5 space-y-0.5">
            <p className="text-[10px] text-slate-400 font-medium">來源分佈</p>
            <div className="flex flex-col gap-0.5 text-[10px]">
              {tooltip.tag.sources.note > 0 && (
                <span className="text-emerald-600">📝 筆記：{tooltip.tag.sources.note}</span>
              )}
              {tooltip.tag.sources.annotation > 0 && (
                <span className="text-violet-600">✨ AI 標記：{tooltip.tag.sources.annotation}</span>
              )}
              {tooltip.tag.sources.scaffold > 0 && (
                <span className="text-amber-600">🦅 鷹架深讀：{tooltip.tag.sources.scaffold}</span>
              )}
            </div>
          </div>
        </div>
      )}
      {/* Legend — Obsidian 風格深色 */}
      {tags.length > 0 && (
        <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm rounded-xl px-3 py-2 text-xs text-slate-600 border border-slate-200 shadow-sm">
          <p>節點大小 = 出現次數｜連線粗細 = 共現次數</p>
          <p className="text-[10px] text-slate-400 mt-0.5">hover 顯示標籤 · 點擊節點篩選 Timeline</p>
        </div>
      )}
    </div>
  );
}
