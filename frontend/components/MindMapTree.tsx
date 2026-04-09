'use client';

import { useState, useCallback } from 'react';
import { ChevronRight, ChevronDown, FileText, BookOpen } from 'lucide-react';

export interface MindMapNode {
  id: string;
  name: string;
  depth: number;
  parent_id: string | null;
  resource_id: string | null;
  mastery_color: string;
  mastery_rate: number;
  source_page: number | null;
  children: MindMapNode[];
  // V3 有機生長欄位
  progress_percentage?: number;
  status?: string;
}

interface MindMapTreeProps {
  nodes: MindMapNode[];
  selectedNodeId: string | null;
  onNodeClick: (nodeId: string) => void;
}

const MASTERY_COLORS: Record<string, { dot: string; bg: string; text: string }> = {
  green: { dot: 'bg-emerald-500', bg: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-700' },
  orange: { dot: 'bg-amber-500', bg: 'bg-amber-50 border-amber-200', text: 'text-amber-700' },
  yellow: { dot: 'bg-amber-400', bg: 'bg-amber-50 border-amber-200', text: 'text-amber-600' },
  red: { dot: 'bg-rose-500', bg: 'bg-rose-50 border-rose-200', text: 'text-rose-700' },
  gray: { dot: 'bg-slate-300', bg: 'bg-white border-slate-200', text: 'text-slate-600' },
};

// V3: 純 progress 驅動顏色
function getNodeColor(node: MindMapNode): string {
  return node.mastery_color || 'gray';
}

const DEPTH_STYLES = [
  'text-base font-bold text-slate-900',     // depth 0: root
  'text-sm font-semibold text-slate-800',    // depth 1: chapter
  'text-sm font-medium text-slate-700',      // depth 2: section
  'text-xs font-normal text-slate-600',      // depth 3: subsection
];

function TreeNode({
  node,
  selectedNodeId,
  onNodeClick,
  expandedIds,
  toggleExpand,
  isLast,
}: {
  node: MindMapNode;
  selectedNodeId: string | null;
  onNodeClick: (id: string) => void;
  expandedIds: Set<string>;
  toggleExpand: (id: string) => void;
  isLast: boolean;
}) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedIds.has(node.id);
  const isSelected = node.id === selectedNodeId;
  const nodeColor = getNodeColor(node);
  const colors = MASTERY_COLORS[nodeColor] || MASTERY_COLORS.gray;
  const displayRate = node.mastery_rate;
  const depthStyle = DEPTH_STYLES[Math.min(node.depth, 3)];
  const isRoot = node.depth === 0;

  return (
    <div className="relative">
      {/* Vertical connector line from parent */}
      {!isRoot && (
        <div
          className="absolute left-3 top-0 w-px bg-slate-200"
          style={{ height: isLast ? '20px' : '100%' }}
        />
      )}

      {/* Horizontal connector line */}
      {!isRoot && (
        <div className="absolute left-3 top-5 w-4 h-px bg-slate-200" />
      )}

      {/* Node content */}
      <div className={`${isRoot ? '' : 'ml-7'} mb-1`}>
        <button
          onClick={() => {
            if (hasChildren) toggleExpand(node.id);
            onNodeClick(node.id);
          }}
          className={`
            w-full text-left px-3 py-2 rounded-lg border transition-all duration-150
            flex items-center gap-2 group
            ${isSelected
              ? 'border-emerald-400 bg-emerald-50 shadow-sm'
              : `${colors.bg} hover:shadow-sm hover:border-emerald-300`
            }
          `}
        >
          {/* Expand/collapse icon */}
          {hasChildren ? (
            <span className="shrink-0 text-slate-400">
              {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            </span>
          ) : (
            <span className="shrink-0 w-3.5" />
          )}

          {/* Mastery dot */}
          <span className={`shrink-0 w-2 h-2 rounded-full ${colors.dot}`} />

          {/* Node icon */}
          {isRoot ? (
            <BookOpen className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
          ) : node.depth === 1 ? (
            <FileText className="h-3 w-3 text-slate-400 shrink-0" />
          ) : null}

          {/* Node name */}
          <span className={`${depthStyle} truncate flex-1`}>
            {node.name}
          </span>

          {/* Page reference */}
          {node.source_page && node.depth > 0 && (
            <span className="text-[10px] text-slate-400 shrink-0">p.{node.source_page}</span>
          )}

          {/* Mastery percentage */}
          {displayRate > 0 && (
            <span className={`text-[10px] font-medium shrink-0 ${colors.text}`}>
              {displayRate}%
            </span>
          )}
        </button>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="relative mt-0.5">
            {node.children.map((child, idx) => (
              <TreeNode
                key={child.id}
                node={child}
                selectedNodeId={selectedNodeId}
                onNodeClick={onNodeClick}
                expandedIds={expandedIds}
                toggleExpand={toggleExpand}
                isLast={idx === node.children.length - 1}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function MindMapTree({ nodes, selectedNodeId, onNodeClick }: MindMapTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => {
    // Auto-expand root and depth-1 nodes
    const initial = new Set<string>();
    const expand = (nodeList: MindMapNode[]) => {
      for (const n of nodeList) {
        if (n.depth <= 1) {
          initial.add(n.id);
          expand(n.children);
        }
      }
    };
    expand(nodes);
    return initial;
  });

  const toggleExpand = useCallback((id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  if (nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400">
        <BookOpen className="h-10 w-10 mb-3 text-slate-300" />
        <p className="text-sm font-medium">尚無知識節點</p>
        <p className="text-xs mt-1">上傳文件後自動生成心智圖</p>
      </div>
    );
  }

  return (
    <div className="py-2 px-1">
      {nodes.map((root, idx) => (
        <TreeNode
          key={root.id}
          node={root}
          selectedNodeId={selectedNodeId}
          onNodeClick={onNodeClick}
          expandedIds={expandedIds}
          toggleExpand={toggleExpand}
          isLast={idx === nodes.length - 1}
        />
      ))}

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-center gap-4 text-[10px] text-slate-400">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> 精熟</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> 部分</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" /> 需加強</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300" /> 未測驗</span>
      </div>
    </div>
  );
}
