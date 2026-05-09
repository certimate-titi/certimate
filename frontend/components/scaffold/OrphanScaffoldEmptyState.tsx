/**
 * @file AI 補洞鷹架空態元件——生成中與佐證不足兩種模式。
 */
'use client';

import { Loader2, AlertTriangle } from 'lucide-react';

/**
 * OrphanScaffoldEmptyState 的 props。
 */
export interface OrphanScaffoldEmptyStateProps {
  /** 'generating'：AI 生成中；'insufficient'：佐證題不足 */
  mode: 'generating' | 'insufficient';
  /** 生成中模式：預估剩餘秒數 */
  estimatedSeconds?: number;
  /** 佐證不足模式：目前佐證題數 */
  evidenceCount?: number;
}

/**
 * 顯示 AI 補洞鷹架的非 ready 狀態（生成中 / 佐證不足）。
 *
 * 生成中：灰底 spinner + 預估時間
 * 佐證不足：灰底警告圖示 + 說明文字
 */
export default function OrphanScaffoldEmptyState({
  mode,
  estimatedSeconds,
  evidenceCount,
}: OrphanScaffoldEmptyStateProps) {
  if (mode === 'generating') {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center">
        <Loader2 className="h-6 w-6 mx-auto mb-2 text-slate-400 animate-spin" />
        <p className="text-xs font-semibold text-slate-600 mb-1">AI 補洞鷹架生成中</p>
        {estimatedSeconds ? (
          <p className="text-[11px] text-slate-400">
            預計約 {estimatedSeconds} 秒後可見
          </p>
        ) : (
          <p className="text-[11px] text-slate-400">請稍候...</p>
        )}
      </div>
    );
  }

  // mode === 'insufficient'
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center">
      <AlertTriangle className="h-6 w-6 mx-auto mb-2 text-slate-400" />
      <p className="text-xs font-semibold text-slate-600 mb-1">佐證題不足，無法自動補洞</p>
      <p className="text-[11px] text-slate-400">
        {evidenceCount !== undefined
          ? `目前僅找到 ${evidenceCount} 道相關考古題（至少需要 3 道）`
          : '此節點對應的考古題佐證不足，尚無法生成 AI 補洞鷹架'}
      </p>
    </div>
  );
}
