'use client';

import { useState, useMemo } from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer,
} from 'recharts';
import type { DomainAnalysis } from '@/types';

/**
 * 分組雷達圖元件（方案 B）
 *
 * 後端 API 回傳已分組的資料，每個 domain 可能包含 children[]。
 * - 有 children：顯示為可展開的分組，雷達圖顯示分組級別
 * - 無 children：直接顯示為獨立概念
 *
 * 前端 fallback：若 API 回傳 > 6 個無 children 的概念，
 * 前端自動平均分組（相容舊版 API）。
 */

const MAX_GROUPS = 6;
const EMERALD = '#10b981';
const EMERALD_LIGHT = 'rgba(16, 185, 129, 0.2)';

interface RadarItem {
  domain: string;
  strength: number;
  node_id?: string;
  children: { domain: string; strength: number }[];
}

function toRadarItems(domains: DomainAnalysis[]): RadarItem[] {
  // 如果 API 已提供 children，直接使用
  const hasApiGrouping = domains.some(d => d.children && d.children.length > 0);

  if (hasApiGrouping || domains.length <= MAX_GROUPS) {
    return domains.map(d => ({
      domain: d.domain,
      strength: d.percentage,
      node_id: d.node_id,
      children: (d.children || []).map(c => ({
        domain: c.domain,
        strength: c.percentage,
      })),
    }));
  }

  // Fallback：前端自動分組（相容舊版 API）
  const groupSize = Math.ceil(domains.length / MAX_GROUPS);
  const groups: RadarItem[] = [];
  for (let i = 0; i < domains.length; i += groupSize) {
    const chunk = domains.slice(i, i + groupSize);
    const totalQ = chunk.reduce((s, d) => s + d.total, 0);
    const totalC = chunk.reduce((s, d) => s + d.correct, 0);
    const avg = totalQ > 0 ? Math.round((totalC / totalQ) * 100) : 0;
    groups.push({
      domain: chunk.length === 1 ? chunk[0].domain : `${chunk[0].domain.slice(0, 4)}等${chunk.length}項`,
      strength: avg,
      node_id: chunk.length === 1 ? chunk[0].node_id : undefined,
      children: chunk.map(d => ({ domain: d.domain, strength: d.percentage })),
    });
  }
  return groups;
}

interface DomainRadarChartProps {
  domains: DomainAnalysis[];
  onDomainClick?: (domain: string, nodeId?: string) => void;
}

export default function DomainRadarChart({ domains, onDomainClick }: DomainRadarChartProps) {
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  const items = useMemo(() => toRadarItems(domains), [domains]);

  if (domains.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">能力分佈</h3>
        <div className="aspect-square w-full bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-center">
          <span className="text-xs text-slate-400">尚無測驗資料</span>
        </div>
      </div>
    );
  }

  const hasExpandable = items.some(g => g.children.length > 1);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">能力分佈</h3>

      {/* 雷達圖 */}
      <div className="w-full bg-slate-50 rounded-2xl border border-slate-100 p-2">
        <ResponsiveContainer width="100%" height={220}>
          <RadarChart data={items}>
            <PolarGrid stroke="#e2e8f0" />
            <PolarAngleAxis
              dataKey="domain"
              tick={{ fontSize: items.length > 5 ? 9 : 10, fill: '#64748b' }}
            />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
            <Radar
              dataKey="strength"
              stroke={EMERALD}
              fill={EMERALD_LIGHT}
              strokeWidth={2}
              dot={{ r: 3, fill: EMERALD }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* 分類列表 */}
      {hasExpandable && (
        <p className="text-[10px] text-slate-400 text-center">點擊分類可展開子概念</p>
      )}
      <div className="space-y-0.5">
        {items.map((g, i) => {
          const isExpanded = expandedGroup === g.domain;
          const hasChildren = g.children.length > 1;

          return (
            <div key={i}>
              {hasChildren ? (
                <button
                  type="button"
                  onClick={() => setExpandedGroup(isExpanded ? null : g.domain)}
                  className={`w-full flex items-center gap-1.5 text-xs py-1.5 px-2 rounded-lg transition-colors ${
                    isExpanded ? 'bg-emerald-50' : 'hover:bg-slate-50'
                  }`}
                >
                  <span className={`transition-transform text-slate-400 text-[9px] ${isExpanded ? 'rotate-90' : ''}`}>&#9654;</span>
                  <span className="font-medium text-slate-700 w-14 shrink-0 text-left truncate">{g.domain}</span>
                  <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full transition-all" style={{ width: `${g.strength}%` }} />
                  </div>
                  <span className="text-slate-400 w-7 text-right text-[10px]">{g.strength}%</span>
                </button>
              ) : onDomainClick ? (
                <button
                  type="button"
                  onClick={() => onDomainClick(g.domain, g.node_id)}
                  className="w-full flex items-center gap-1.5 text-xs py-1.5 px-2 rounded-lg hover:bg-emerald-50 transition-colors"
                  title="開啟知識地圖"
                >
                  <span className="text-emerald-500 text-[9px]">→</span>
                  <span className="font-medium text-slate-700 w-14 shrink-0 truncate text-left">{g.domain}</span>
                  <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full transition-all" style={{ width: `${g.strength}%` }} />
                  </div>
                  <span className="text-slate-400 w-7 text-right text-[10px]">{g.strength}%</span>
                </button>
              ) : (
                <div className="flex items-center gap-1.5 text-xs py-1.5 px-2">
                  <span className="text-slate-300 text-[9px]">●</span>
                  <span className="font-medium text-slate-700 w-14 shrink-0 truncate">{g.domain}</span>
                  <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full transition-all" style={{ width: `${g.strength}%` }} />
                  </div>
                  <span className="text-slate-400 w-7 text-right text-[10px]">{g.strength}%</span>
                </div>
              )}
              {isExpanded && hasChildren && (
                <div className="ml-5 mt-0.5 mb-1.5 space-y-0.5 border-l-2 border-emerald-200 pl-2.5">
                  {g.children.map((child, ci) => (
                    <div key={ci} className="flex items-center gap-1.5 text-xs">
                      <span className="text-slate-500 w-16 shrink-0 truncate text-[10px]">{child.domain}</span>
                      <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-300 rounded-full" style={{ width: `${child.strength}%` }} />
                      </div>
                      <span className="text-slate-400 w-6 text-right text-[10px]">{child.strength}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
