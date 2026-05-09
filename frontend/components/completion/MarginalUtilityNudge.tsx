/**
 * @file MarginalUtilityNudge — B.4 邊際效益遞減教育提示卡（非 modal）
 *
 * 觸發條件（B.4）：
 * - 完成度 ≥ 85%（甜蜜點）且 < 95%
 * - 提示用戶此區間的額外投入報酬遞減
 *
 * 設計原則：
 * - 非 modal，不打斷操作
 * - 可手動關閉（session 內記憶關閉狀態）
 */
'use client';

import { useState } from 'react';
import { X, TrendingDown } from 'lucide-react';

interface MarginalUtilityNudgeProps {
  /** 當前完成度百分比 */
  percent: number;
  /** 是否應顯示（由父元件依 showMarginalUtilityNudge 決定） */
  show: boolean;
}

export default function MarginalUtilityNudge({ percent, show }: MarginalUtilityNudgeProps) {
  const [dismissed, setDismissed] = useState(false);

  if (!show || dismissed) return null;

  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
      {/* 圖示 */}
      <div className="shrink-0 mt-0.5">
        <TrendingDown className="h-4 w-4 text-amber-500" />
      </div>

      {/* 文字 */}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-amber-800 mb-0.5">
          你已達 {percent}%！效益最高區段已突破
        </p>
        <p className="text-[11px] text-amber-700 leading-relaxed">
          研究顯示：備考完成度從 85% 再往上每提升 1%，
          需付出的額外努力呈指數成長，但考試通過率提升有限。
          <strong className="font-semibold"> 現在是衝刺弱點、練習錯題的最佳時機。</strong>
        </p>
      </div>

      {/* 關閉鈕 */}
      <button
        onClick={() => setDismissed(true)}
        className="shrink-0 text-amber-400 hover:text-amber-600 transition-colors mt-0.5"
        aria-label="關閉提示"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
