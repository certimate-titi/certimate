/**
 * @file 知識節點詳情側欄——三分頁（節點資訊 / 我的筆記 / AI 教練）容器元件。
 *
 * 遵循 71fdd70 整合精神：鷹架（ScaffoldMaterial）整合於「節點資訊」tab，
 * 不再單獨佔用 tab，降低學習者分散注意力（Sweller split-attention 原則）。
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { FileText, NotebookPen, Sparkles } from 'lucide-react';

/** 節點詳情側欄分頁類型。 */
export type NodeDetailTab = 'info' | 'notebook' | 'coach';

/**
 * NodeDetailPanel 的 props。
 */
export interface NodeDetailPanelProps {
  /** 當前選取的節點 ID；null 時顯示提示 */
  nodeId: string | null;
  /** 節點顯示名稱（含 fallback） */
  nodeLabel: string | null;
  /** 當前 active 的分頁 */
  activeTab: NodeDetailTab;
  /** 切換分頁時觸發 */
  onTabChange: (tab: NodeDetailTab) => void;
  /** 節點資訊分頁的內容（含概念說明 + 學習鷹架 + 練習動作） */
  infoSlot: React.ReactNode;
  /** 我的筆記分頁的內容 */
  notebookSlot: React.ReactNode;
  /** AI 教練分頁的內容 */
  coachSlot: React.ReactNode;
}

const TAB_ORDER: NodeDetailTab[] = ['info', 'notebook', 'coach'];

const TAB_META: Record<NodeDetailTab, { label: string; Icon: React.ComponentType<{ className?: string }> }> = {
  info: { label: '節點資訊', Icon: FileText },
  notebook: { label: '我的筆記', Icon: NotebookPen },
  coach: { label: 'AI 教練', Icon: Sparkles },
};

/**
 * 節點詳情側欄。
 *
 * 採 slot 注入模式（3 個 ReactNode 由父層傳入），支援鍵盤左右鍵切換 tab；
 * `nodeId` 為 null 時顯示「點選左側節點以查看詳情」提示。
 *
 * 鷹架（ScaffoldMaterial）整合於 infoSlot，不再單獨成 tab。
 *
 * @param props.nodeId - 當前節點 ID
 * @param props.nodeLabel - 節點顯示名稱
 * @param props.activeTab - 當前分頁
 * @param props.onTabChange - 分頁切換回呼
 * @param props.infoSlot - 節點資訊 + 學習鷹架 + 練習動作（一體）
 * @param props.notebookSlot - 筆記內容
 * @param props.coachSlot - AI 教練內容
 */
export default function NodeDetailPanel({
  nodeId,
  nodeLabel,
  activeTab,
  onTabChange,
  infoSlot,
  notebookSlot,
  coachSlot,
}: NodeDetailPanelProps) {
  const tablistRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(Boolean(nodeId));

  useEffect(() => {
    setVisible(Boolean(nodeId));
  }, [nodeId]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    const idx = TAB_ORDER.indexOf(activeTab);
    const next = e.key === 'ArrowRight'
      ? TAB_ORDER[(idx + 1) % TAB_ORDER.length]
      : TAB_ORDER[(idx - 1 + TAB_ORDER.length) % TAB_ORDER.length];
    onTabChange(next);
  }

  if (!visible) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-sm text-slate-400">
        點選左側節點以查看詳情
      </div>
    );
  }

  const slotMap: Record<NodeDetailTab, React.ReactNode> = {
    info: infoSlot,
    notebook: notebookSlot,
    coach: coachSlot,
  };

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-900 truncate" title={nodeLabel ?? undefined}>
          {nodeLabel || '節點詳情'}
        </h2>
      </header>
      <div
        ref={tablistRef}
        role="tablist"
        aria-label="節點詳情分頁"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className="flex border-b border-slate-200 bg-slate-50 overflow-x-auto focus:outline-none"
      >
        {TAB_ORDER.map((tab) => {
          const { label, Icon } = TAB_META[tab];
          const active = tab === activeTab;
          return (
            <button
              key={tab}
              role="tab"
              aria-selected={active}
              aria-controls={`tab-panel-${tab}`}
              onClick={() => onTabChange(tab)}
              className={`flex flex-1 min-w-[72px] items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
                active
                  ? 'border-b-2 border-emerald-500 bg-white text-slate-900'
                  : 'border-b-2 border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{label}</span>
            </button>
          );
        })}
      </div>
      <div
        id={`tab-panel-${activeTab}`}
        role="tabpanel"
        className="flex-1 overflow-y-auto"
      >
        {slotMap[activeTab]}
      </div>
    </div>
  );
}
