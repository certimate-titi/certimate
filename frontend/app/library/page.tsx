/**
 * @file 路由 `/library` — 學習庫總覽頁。
 *
 * 雙 Tab：「我的素材」（重用 `/account/resource-library` 元件）與
 * 「知識地圖」（重用 `/knowledge` 元件），以 EmbedProvider 標記為嵌入模式。
 */
'use client';

import { useEffect, useState } from 'react';
import { FolderOpen, Network } from 'lucide-react';
import KnowledgeBasePage from '../knowledge/page';
import ResourceLibraryPage from '../account/resource-library/page';
import { EmbedProvider } from '@/lib/embed-context';

type Tab = 'materials' | 'map';

const TABS: Array<{ key: Tab; label: string; icon: typeof FolderOpen; desc: string }> = [
  {
    key: 'materials',
    label: '我的素材',
    icon: FolderOpen,
    desc: '你上傳的 PDF、影片、筆記 — 查看解析狀態與原始內容',
  },
  {
    key: 'map',
    label: '知識地圖',
    icon: Network,
    desc: 'AI 從素材萃取的知識結構 — 心智圖、節點關聯與學習路徑',
  },
];

export default function LibraryPage() {
  const [tab, setTab] = useState<Tab>('materials');

  useEffect(() => {
    const hash = window.location.hash.replace('#', '');
    if (hash === 'map' || hash === 'materials') setTab(hash);
  }, []);

  const switchTab = (t: Tab) => {
    setTab(t);
    window.history.replaceState(null, '', `#${t}`);
  };

  const active = TABS.find((x) => x.key === tab)!;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="sticky top-16 z-40 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 -mb-px pt-2">
            {TABS.map((t) => {
              const Icon = t.icon;
              const isActive = t.key === tab;
              return (
                <button
                  key={t.key}
                  onClick={() => switchTab(t.key)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    isActive
                      ? 'border-emerald-500 text-emerald-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {t.label}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-slate-500 py-2">{active.desc}</p>
        </div>
      </div>

      <EmbedProvider>
        {tab === 'materials' ? <ResourceLibraryPage /> : <KnowledgeBasePage />}
      </EmbedProvider>
    </div>
  );
}
