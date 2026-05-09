/**
 * @file BadgeShelf — 6 個徽章 grid，已解鎖 vs 待解鎖視覺差異。
 *
 * B.3 徽章里程碑系統（6 個）：
 *   啟程者 / 探索者 / 建設者 / 甜蜜點達陣者 / 高頻王者 / 知識完整者
 *
 * 嚴禁假徽章（B.5 紅線）：
 * - 所有徽章必須綁定 mastery 計算結果
 * - 不允許「登入即解鎖」之類的假徽章
 */
'use client';

import { BADGES, type BadgeId } from '@/lib/completion-calc';
import { Lock } from 'lucide-react';

interface BadgeShelfProps {
  /** 已解鎖徽章 ID 列表（來自 calcCompletion().unlockedBadges） */
  unlockedBadges: BadgeId[];
}

export default function BadgeShelf({ unlockedBadges }: BadgeShelfProps) {
  const unlockedSet = new Set(unlockedBadges);

  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
      {BADGES.map((badge) => {
        const isUnlocked = unlockedSet.has(badge.id);
        return (
          <div
            key={badge.id}
            title={`${badge.label}：${badge.triggerDesc}`}
            className={`
              flex flex-col items-center gap-1 p-3 rounded-xl border text-center
              transition-all duration-300
              ${isUnlocked
                ? 'bg-gradient-to-b from-amber-50 to-white border-amber-300 shadow-sm'
                : 'bg-slate-50 border-slate-200 opacity-50 grayscale'
              }
            `}
          >
            {/* 徽章圖示 */}
            <div className="relative">
              <span className={`text-2xl ${isUnlocked ? '' : 'opacity-40'}`}>
                {badge.emoji}
              </span>
              {!isUnlocked && (
                <div className="absolute -bottom-0.5 -right-0.5 bg-slate-300 rounded-full p-0.5">
                  <Lock className="h-2 w-2 text-white" />
                </div>
              )}
            </div>

            {/* 徽章名稱 */}
            <span
              className={`text-[10px] font-semibold leading-tight ${
                isUnlocked ? 'text-amber-700' : 'text-slate-400'
              }`}
            >
              {badge.label}
            </span>

            {/* 解鎖說明（已解鎖才顯示） */}
            {isUnlocked && (
              <span className="text-[9px] text-slate-500 leading-tight">
                {badge.description}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
