'use client';

import { useState } from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';

// 模擬 5 個概念（少量）
const fewDomains = [
  { domain: '運算', strength: 80 },
  { domain: '儲存', strength: 65 },
  { domain: '網路', strength: 70 },
  { domain: '資料庫', strength: 55 },
  { domain: '安全性', strength: 90 },
];

// 模擬 15 個概念（大量）
const manyDomains = [
  { domain: '機器學習基礎', strength: 82 },
  { domain: '深度學習架構', strength: 68 },
  { domain: '自然語言處理', strength: 75 },
  { domain: '電腦視覺', strength: 60 },
  { domain: '強化學習', strength: 45 },
  { domain: '資料前處理', strength: 88 },
  { domain: '特徵工程', strength: 72 },
  { domain: '模型評估', strength: 65 },
  { domain: '統計分析', strength: 78 },
  { domain: '線性代數', strength: 55 },
  { domain: '機率論', strength: 62 },
  { domain: '最佳化理論', strength: 48 },
  { domain: 'MLOps 部署', strength: 40 },
  { domain: '資料倫理', strength: 85 },
  { domain: 'AI 法規', strength: 70 },
];

// 方案 B: 分組合併後的資料（含子概念）
const groupedDomains = [
  { domain: 'AI 核心', strength: 66, children: [
    { domain: '機器學習基礎', strength: 82 },
    { domain: '深度學習架構', strength: 68 },
    { domain: '強化學習', strength: 45 },
  ]},
  { domain: '應用領域', strength: 68, children: [
    { domain: '自然語言處理', strength: 75 },
    { domain: '電腦視覺', strength: 60 },
  ]},
  { domain: '資料工程', strength: 80, children: [
    { domain: '資料前處理', strength: 88 },
    { domain: '特徵工程', strength: 72 },
  ]},
  { domain: '數學基礎', strength: 65, children: [
    { domain: '統計分析', strength: 78 },
    { domain: '線性代數', strength: 55 },
    { domain: '機率論', strength: 62 },
    { domain: '最佳化理論', strength: 48 },
  ]},
  { domain: '評估部署', strength: 53, children: [
    { domain: '模型評估', strength: 65 },
    { domain: 'MLOps 部署', strength: 40 },
  ]},
  { domain: '治理合規', strength: 78, children: [
    { domain: '資料倫理', strength: 85 },
    { domain: 'AI 法規', strength: 70 },
  ]},
];

const EMERALD = '#10b981';
const EMERALD_LIGHT = 'rgba(16, 185, 129, 0.2)';

export default function RadarDemoPage() {
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 mb-2 text-center">能力分佈圖 — 方案比較</h1>
        <p className="text-slate-500 text-center mb-12">當概念數量超過 8 個時，雷達圖會變得難以閱讀。以下是三種替代方案。</p>

        {/* 現狀對照 */}
        <div className="mb-16">
          <h2 className="text-lg font-bold text-slate-700 mb-1">現狀：5 個概念（雷達圖效果好）</h2>
          <p className="text-sm text-slate-400 mb-4">概念少時，雷達圖清晰易讀，能一眼看出強弱分佈。</p>
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 max-w-md mx-auto">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={fewDomains}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="domain" tick={{ fontSize: 12, fill: '#64748b' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar dataKey="strength" stroke={EMERALD} fill={EMERALD_LIGHT} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 問題展示 */}
        <div className="mb-16">
          <h2 className="text-lg font-bold text-red-600 mb-1">問題：15 個概念（雷達圖崩潰）</h2>
          <p className="text-sm text-slate-400 mb-4">概念過多時，標籤重疊、形狀難以辨識、無法有效比較。</p>
          <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-6 max-w-md mx-auto">
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={manyDomains}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="domain" tick={{ fontSize: 9, fill: '#64748b' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar dataKey="strength" stroke={EMERALD} fill={EMERALD_LIGHT} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <hr className="border-slate-200 mb-16" />
        <h2 className="text-xl font-bold text-slate-900 mb-8 text-center">三種解決方案</h2>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* 方案 A */}
          <div className="bg-white rounded-2xl shadow-sm border-2 border-slate-200 p-6">
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded">方案 A</span>
              <h3 className="font-bold text-slate-900">水平長條圖</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">概念多時自動切換。按強度排序，一目瞭然。</p>
            <ResponsiveContainer width="100%" height={420}>
              <BarChart
                data={[...manyDomains].sort((a, b) => b.strength - a.strength)}
                layout="vertical"
                margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="domain" width={90} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => [`${v}%`, '強度']} />
                <Bar dataKey="strength" fill={EMERALD} radius={[0, 6, 6, 0]} barSize={18} />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 text-xs text-slate-500 space-y-1">
              <p>&#10003; 無概念數量上限</p>
              <p>&#10003; 強弱排序直觀</p>
              <p>&#10007; 無法看出「形狀」全貌</p>
            </div>
          </div>

          {/* 方案 B */}
          <div className="bg-white rounded-2xl shadow-sm border-2 border-emerald-300 p-6 ring-2 ring-emerald-100">
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-emerald-100 text-emerald-700 text-xs font-bold px-2 py-0.5 rounded">方案 B 推薦</span>
              <h3 className="font-bold text-slate-900">分組雷達圖</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">將 15 個概念合併為 6 個上層分類，點擊分類可展開子概念。</p>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={groupedDomains}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="domain" tick={{ fontSize: 12, fill: '#334155' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar dataKey="strength" stroke={EMERALD} fill={EMERALD_LIGHT} strokeWidth={2} dot={{ r: 4, fill: EMERALD }} />
              </RadarChart>
            </ResponsiveContainer>
            <p className="text-[10px] text-slate-400 text-center mb-3">點擊下方分類可展開 / 收合子概念</p>
            <div className="space-y-1">
              {groupedDomains.map((g, i) => {
                const isExpanded = expandedGroup === g.domain;
                return (
                  <div key={i}>
                    <button
                      type="button"
                      onClick={() => setExpandedGroup(isExpanded ? null : g.domain)}
                      className={`w-full flex items-center gap-2 text-xs py-1.5 px-2 rounded-lg transition-colors ${
                        isExpanded ? 'bg-emerald-50' : 'hover:bg-slate-50'
                      }`}
                    >
                      <span className={`transition-transform text-slate-400 text-[10px] ${isExpanded ? 'rotate-90' : ''}`}>&#9654;</span>
                      <span className="font-medium text-slate-700 w-16 shrink-0 text-left">{g.domain}</span>
                      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-400 rounded-full transition-all" style={{ width: `${g.strength}%` }} />
                      </div>
                      <span className="text-slate-400 w-8 text-right">{g.strength}</span>
                    </button>
                    {isExpanded && (
                      <div className="ml-6 mt-1 mb-2 space-y-1 border-l-2 border-emerald-200 pl-3">
                        {g.children.map((child, ci) => (
                          <div key={ci} className="flex items-center gap-2 text-xs">
                            <span className="text-slate-500 w-20 shrink-0 truncate">{child.domain}</span>
                            <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-emerald-300 rounded-full" style={{ width: `${child.strength}%` }} />
                            </div>
                            <span className="text-slate-400 w-6 text-right text-[10px]">{child.strength}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div className="mt-4 text-xs text-slate-500 space-y-1">
              <p>&#10003; 保持雷達圖的「形狀」直覺</p>
              <p>&#10003; 點擊分類展開子概念細節</p>
              <p>&#10003; 標籤不重疊</p>
            </div>
          </div>

          {/* 方案 C */}
          <div className="bg-white rounded-2xl shadow-sm border-2 border-slate-200 p-6">
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-purple-100 text-purple-700 text-xs font-bold px-2 py-0.5 rounded">方案 C</span>
              <h3 className="font-bold text-slate-900">自適應切換</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">{'概念 ≤ 8 → 雷達圖；> 8 → 自動切換水平長條圖。'}</p>

            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-slate-600 mb-2">{'≤ 8 個概念時：雷達圖'}</p>
                <div className="bg-slate-50 rounded-xl p-2">
                  <ResponsiveContainer width="100%" height={180}>
                    <RadarChart data={fewDomains}>
                      <PolarGrid stroke="#e2e8f0" />
                      <PolarAngleAxis dataKey="domain" tick={{ fontSize: 10, fill: '#64748b' }} />
                      <Radar dataKey="strength" stroke={EMERALD} fill={EMERALD_LIGHT} strokeWidth={2} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <div className="flex-1 h-px bg-slate-200" />
                <span>自動切換</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-600 mb-2">{'> 8 個概念時：長條圖'}</p>
                <div className="bg-slate-50 rounded-xl p-2">
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart
                      data={[...manyDomains].sort((a, b) => b.strength - a.strength).slice(0, 8)}
                      layout="vertical"
                      margin={{ left: 5, right: 10 }}
                    >
                      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 9 }} />
                      <YAxis type="category" dataKey="domain" width={75} tick={{ fontSize: 9 }} />
                      <Bar dataKey="strength" fill={EMERALD} radius={[0, 4, 4, 0]} barSize={14} />
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-[10px] text-slate-400 text-center">顯示前 8 項，可展開查看全部</p>
                </div>
              </div>
            </div>
            <div className="mt-4 text-xs text-slate-500 space-y-1">
              <p>&#10003; 少量時保留雷達直覺</p>
              <p>&#10003; 大量時自動適應</p>
              <p>&#10007; 兩種圖表切換可能造成認知不一致</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
