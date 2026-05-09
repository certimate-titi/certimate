/**
 * @file CompletionProgressBar — 雙進度條（甜蜜點 / 全覆蓋），錨定 85% 甜蜜點刻度。
 *
 * 視覺設計：
 * - 單條進度條，85% 處有甜蜜點刻度線（鉛垂虛線 + 「🎯 甜蜜點」標籤）
 * - 達到 85% 前：bar 為 emerald；達到後：bar 為 amber（稀缺感消退 → 提醒邊際效益）
 * - 進度條只動於 mastery 更新時（B.5 假進度感紅線）
 *
 * TODO: backend wire-up — percent 來自 calcCompletion()，
 *       後端提供 /api/v1/subjects/{id}/completion 後改為 API 資料。
 */
'use client';

interface CompletionProgressBarProps {
  /** 完成度百分比 0~100 */
  percent: number;
  /** 是否已達甜蜜點（85%） */
  sweetSpotReached: boolean;
  /** 顯示標籤（科目名稱等） */
  label?: string;
}

export default function CompletionProgressBar({
  percent,
  sweetSpotReached,
  label,
}: CompletionProgressBarProps) {
  const clamped = Math.min(Math.max(percent, 0), 100);
  const barColor = sweetSpotReached
    ? 'bg-amber-400'
    : 'bg-emerald-500';

  return (
    <div className="w-full">
      {/* 頂部標籤列 */}
      <div className="flex items-center justify-between mb-1.5">
        {label && (
          <span className="text-xs font-medium text-slate-600 truncate">{label}</span>
        )}
        <span className="text-xs font-bold text-slate-800 ml-auto">
          {clamped}%
          {sweetSpotReached && (
            <span className="ml-1.5 text-amber-600 font-semibold">✓ 甜蜜點</span>
          )}
        </span>
      </div>

      {/* 進度條容器（相對定位，讓甜蜜點刻度線可絕對定位） */}
      <div className="relative h-3 w-full bg-slate-100 rounded-full overflow-visible">
        {/* 實際進度 */}
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${clamped}%` }}
        />

        {/* 85% 甜蜜點刻度線（在 overflow-visible 容器內，超出部分仍可見） */}
        <div
          className="absolute top-[-4px] bottom-[-4px] w-0.5 bg-amber-400 rounded-full"
          style={{ left: '85%' }}
          title="85% 甜蜜點：效益最高的備考完成度"
        />

        {/* 甜蜜點標籤（刻度線上方） */}
        <div
          className="absolute text-[9px] text-amber-600 font-semibold whitespace-nowrap"
          style={{ left: '85%', top: '-18px', transform: 'translateX(-50%)' }}
        >
          🎯 85%
        </div>
      </div>

      {/* 底部提示 */}
      <div className="flex justify-between mt-1">
        <span className="text-[10px] text-slate-400">0%</span>
        <span className="text-[10px] text-slate-400">100%</span>
      </div>
    </div>
  );
}
