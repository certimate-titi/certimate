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
    if (!svgRef.current || tags.length === 0) return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const tagMap = new Map(tags.map((t) => [t.normalized, t]));

    // Filter edges to only include tags that exist in tagMap
    const validEdges = edges.filter(
      (e) => tagMap.has(e.source) && tagMap.has(e.target)
    );

    // Node radius = proportional to count (min 10, max 36)
    // 修：當所有 tag count 相同（如全為 1），d3.scaleLinear domain 退化 → NaN，
    //     forceCollide radius NaN 導致節點全擠中心無排斥。改用固定中間值。
    const counts = tags.map((t) => t.count);
    const minCount = Math.min(...counts);
    const maxCount = Math.max(...counts);
    const radiusScale: (c: number) => number =
      minCount === maxCount
        ? () => 18
        : d3.scaleLinear().domain([minCount, maxCount]).range([10, 36]).clamp(true) as unknown as (c: number) => number;

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
        .distance((d: any) => Math.max(80 - (d.weight ?? 1) * 5, 40))
        .strength(0.8))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.1))
      .force('collision', d3.forceCollide().radius((d: any) => radiusScale(d.count) + 12));

    const container = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => container.attr('transform', event.transform));
    svg.call(zoom);
    svg.call(zoom.transform, d3.zoomIdentity);

    // Edges
    const link = container.append('g')
      .selectAll('line')
      .data(simEdges)
      .join('line')
      .attr('stroke', '#0ea5e9')
      .attr('stroke-opacity', (d: any) => Math.min(0.15 + (d.weight ?? 1) * 0.1, 0.7))
      .attr('stroke-width', (d: any) => Math.min(1 + (d.weight ?? 1) * 0.5, 4));

    // Edge weight labels
    container.append('g')
      .selectAll('text')
      .data(simEdges.filter((d: any) => (d.weight ?? 1) > 1))
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', '#94a3b8')
      .text((d: any) => d.weight);

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

    // Defs
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'tag-shadow');
    filter.append('feDropShadow')
      .attr('dx', 0).attr('dy', 1).attr('stdDeviation', 2)
      .attr('flood-color', '#00000015');

    // Node circles
    nodeGroup.append('circle')
      .attr('r', (d: any) => radiusScale(d.count))
      .attr('fill', (d: any) => activeTag === d.id ? '#0ea5e9' : '#e0f2fe')
      .attr('stroke', (d: any) => activeTag === d.id ? '#0284c7' : '#7dd3fc')
      .attr('stroke-width', (d: any) => activeTag === d.id ? 2.5 : 1.5)
      .attr('filter', 'url(#tag-shadow)');

    // Node labels
    nodeGroup.append('text')
      .text((d: any) => d.display.length > 10 ? d.display.slice(0, 10) + '…' : d.display)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', (d: any) => activeTag === d.id ? '#fff' : '#0369a1')
      .attr('font-size', (d: any) => `${Math.max(8, Math.min(12, radiusScale(d.count) * 0.55))}px`)
      .attr('font-weight', '600')
      .attr('pointer-events', 'none');

    // Count badge below
    nodeGroup.append('text')
      .text((d: any) => d.count)
      .attr('text-anchor', 'middle')
      .attr('dy', (d: any) => radiusScale(d.count) + 13)
      .attr('fill', '#64748b')
      .attr('font-size', '9px')
      .attr('pointer-events', 'none');

    // Edge weight label positions (tick updates)
    const edgeWeightLabels = container.selectAll('g:nth-of-type(2) text');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      edgeWeightLabels
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [tags, edges, dimensions, activeTag, onTagClick]);

  useEffect(() => {
    const cleanup = renderGraph();
    return cleanup;
  }, [renderGraph]);

  return (
    <div ref={containerRef} className="relative flex-1 h-full bg-slate-50 rounded-none overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
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
          <p className="font-bold text-sky-700 mb-1">{tooltip.tag.display}</p>
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
      {/* Legend */}
      {tags.length > 0 && (
        <div className="absolute bottom-3 left-3 bg-white/90 rounded-xl px-3 py-2 text-xs text-slate-500 border border-slate-200 shadow-sm">
          <p>節點大小 = 出現次數｜連線粗細 = 共現次數</p>
          <p className="text-[10px] text-slate-400 mt-0.5">點擊節點切換回 Timeline 篩選</p>
        </div>
      )}
    </div>
  );
}
