'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';

export interface GraphNode {
  id: string;
  name: string;
  depth: number;
  progress: number; // 0-100
  color: string;
  parentId: string | null;
  status: string;
  availableQuestions: number;
}

interface ForceGraphProps {
  nodes: GraphNode[];
  onNodeClick: (nodeId: string) => void;
  selectedNodeId?: string | null;
  width?: number;
  height?: number;
}

// TiTi 品牌色系（淺色背景版）
const STATUS_COLORS: Record<string, string> = {
  green: '#10b981',   // emerald-500
  yellow: '#f59e0b',  // amber-500
  red: '#ef4444',     // red-500
  gray: '#cbd5e1',    // slate-300
};

const NODE_BG = '#ffffff';
const NODE_STROKE_DEFAULT = '#e2e8f0';  // slate-200
const LINK_COLOR = '#10b98130';         // emerald-500 with opacity
const TEXT_COLOR = '#334155';           // slate-700
const LABEL_COLOR = '#64748b';          // slate-500
const SELECTED_RING = '#10b981';        // emerald-500

/**
 * Obsidian-style force-directed knowledge graph.
 *
 * Features:
 * - 力導向佈局（drag to reposition）
 * - 節點大小 = depth（根最大，葉最小）
 * - 節點顏色 = mastery progress（green/yellow/red/gray）
 * - 進度環（arc around node）
 * - 連線 = parent-child 關係
 * - Zoom + Pan
 */
export default function ForceGraph({
  nodes,
  onNodeClick,
  selectedNodeId,
  width = 800,
  height = 600,
}: ForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number; y: number; node: GraphNode;
  } | null>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Build links from parent-child
    const links: { source: string; target: string }[] = [];
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    for (const node of nodes) {
      if (node.parentId && nodeMap.has(node.parentId)) {
        links.push({ source: node.parentId, target: node.id });
      }
    }

    // D3 force simulation data
    const simNodes = nodes.map(n => ({
      ...n,
      x: width / 2 + (Math.random() - 0.5) * 200,
      y: height / 2 + (Math.random() - 0.5) * 200,
    }));

    const simLinks = links.map(l => ({ ...l }));

    // Force simulation — tight clustering around parent nodes
    const simulation = d3.forceSimulation(simNodes as any)
      .force('link', d3.forceLink(simLinks as any).id((d: any) => d.id)
        .distance((d: any) => d.source.depth === 0 ? 60 : 40)  // 根→章短，章→節更短
        .strength(1.5))  // 強連結力讓子節點靠攏
      .force('charge', d3.forceManyBody()
        .strength((d: any) => d.depth === 0 ? -300 : -80))  // 根節點互斥強，子節點弱
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.1))
      .force('collision', d3.forceCollide().radius((d: any) => getRadius(d.depth) + 8))
      .force('x', d3.forceX(width / 2).strength(0.05))   // 輕微向心力
      .force('y', d3.forceY(height / 2).strength(0.05));

    // Container with zoom
    const container = svg.append('g');
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => container.attr('transform', event.transform));
    svg.call(zoom);
    // Reset transform when nodes change — 避免切層後節點被前次 pan/zoom 推出 viewport
    svg.call(zoom.transform, d3.zoomIdentity);

    // Links
    const link = container.append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', '#10b981')
      .attr('stroke-width', 1.2)
      .attr('stroke-opacity', 0.25);

    // Node groups
    const nodeGroup = container.append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .style('cursor', 'pointer')
      .on('click', (_event, d: any) => onNodeClick(d.id))
      .on('mouseenter', (event, d: any) => {
        const rect = svgRef.current!.getBoundingClientRect();
        setTooltip({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top - 10,
          node: d,
        });
      })
      .on('mouseleave', () => setTooltip(null))
      .call(drag(simulation) as any);

    // Drop shadow for depth
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'node-shadow');
    filter.append('feDropShadow')
      .attr('dx', 0).attr('dy', 1).attr('stdDeviation', 2)
      .attr('flood-color', '#00000015');

    // Selection glow filter — soft emerald halo via blur + flood
    const glowFilter = defs.append('filter')
      .attr('id', 'node-glow')
      .attr('x', '-50%').attr('y', '-50%')
      .attr('width', '200%').attr('height', '200%');
    glowFilter.append('feGaussianBlur')
      .attr('stdDeviation', '4').attr('result', 'blur');
    glowFilter.append('feFlood')
      .attr('flood-color', SELECTED_RING).attr('flood-opacity', '0.6');
    glowFilter.append('feComposite')
      .attr('in2', 'blur').attr('operator', 'in').attr('result', 'glow');
    const glowMerge = glowFilter.append('feMerge');
    glowMerge.append('feMergeNode').attr('in', 'glow');
    glowMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Selection halo — soft glow circle behind the node, leaves mastery ring untouched
    nodeGroup.filter((d: any) => d.id === selectedNodeId)
      .insert('circle', ':first-child')
      .attr('r', (d: any) => getRadius(d.depth))
      .attr('fill', NODE_BG)
      .attr('filter', 'url(#node-glow)');

    // Background circle — stroke always = mastery color
    nodeGroup.append('circle')
      .attr('r', (d: any) => getRadius(d.depth))
      .attr('fill', NODE_BG)
      .attr('stroke', (d: any) => STATUS_COLORS[d.color] || NODE_STROKE_DEFAULT)
      .attr('stroke-width', (d: any) => d.depth === 0 ? 2.5 : 1.5)
      .attr('filter', 'url(#node-shadow)');

    // Progress arc
    nodeGroup.each(function(d: any) {
      const r = getRadius(d.depth);
      const arc = d3.arc()
        .innerRadius(r - 1)
        .outerRadius(r + 2)
        .startAngle(0)
        .endAngle(((d.progress || 0) / 100) * Math.PI * 2);

      d3.select(this).append('path')
        .attr('d', arc as any)
        .attr('fill', STATUS_COLORS[d.color] || '#94a3b8')
        .attr('opacity', 0.8);
    });

    // Progress text (inside node)
    nodeGroup.append('text')
      .text((d: any) => d.progress > 0 ? `${d.progress}%` : '')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', TEXT_COLOR)
      .attr('font-size', (d: any) => d.depth === 0 ? '10px' : '8px')
      .attr('font-weight', '600');

    // Node name (below)
    nodeGroup.append('text')
      .text((d: any) => truncate(d.name, d.depth === 0 ? 10 : 7))
      .attr('text-anchor', 'middle')
      .attr('dy', (d: any) => getRadius(d.depth) + 14)
      .attr('fill', LABEL_COLOR)
      .attr('font-size', (d: any) => d.depth === 0 ? '11px' : '9px')
      .attr('font-weight', (d: any) => d.depth === 0 ? '600' : '400');

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [nodes, selectedNodeId, width, height, onNodeClick]);

  return (
    <div className="relative bg-slate-50 rounded-2xl overflow-hidden border border-slate-200">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="w-full h-full"
        viewBox={`0 0 ${width} ${height}`}
      />
      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute bg-white text-slate-800 px-3 py-2 rounded-lg text-xs shadow-lg pointer-events-none z-10 border border-slate-200"
          style={{ left: tooltip.x, top: tooltip.y, transform: 'translate(-50%, -100%)' }}
        >
          <p className="font-bold text-slate-900">{tooltip.node.name}</p>
          <p className="text-slate-500">
            掌握度 {tooltip.node.progress}% · {tooltip.node.availableQuestions} 題可用
          </p>
        </div>
      )}
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────

function getRadius(depth: number): number {
  return depth <= 0 ? 32 : depth === 1 ? 20 : 14;
}

function truncate(str: string, maxLen: number): string {
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}

function drag(simulation: d3.Simulation<any, any>) {
  return d3.drag()
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
    });
}
