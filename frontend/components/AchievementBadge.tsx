/**
 * @file 成就徽章卡片元件，呈現單一 Achievement 的解鎖狀態與圖示。
 */
'use client';

import { motion } from 'motion/react';
import type { Achievement } from '@/types';

/**
 * AchievementBadge 的 props。
 */
interface AchievementBadgeProps {
  /** 成就資料（含 unlockedAt 解鎖時間） */
  achievement: Achievement;
}

/**
 * 成就徽章。
 *
 * 依 `achievement.unlockedAt` 決定是否點亮；未解鎖呈現灰階虛線框樣式。
 *
 * @param props.achievement - 成就資料
 */
export default function AchievementBadge({ achievement }: AchievementBadgeProps) {
  const unlocked = !!achievement.unlockedAt;

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`flex flex-col items-center p-4 rounded-2xl border-2 transition-colors ${
        unlocked
          ? 'border-emerald-200 bg-white shadow-sm'
          : 'border-dashed border-slate-200 bg-slate-50'
      }`}
    >
      <div className={`text-3xl mb-2 ${unlocked ? '' : 'grayscale opacity-40'}`}>
        {achievement.iconEmoji}
      </div>
      <h4 className={`text-sm font-bold text-center ${unlocked ? 'text-slate-900' : 'text-slate-400'}`}>
        {achievement.name}
      </h4>
      <p className={`text-[10px] text-center mt-1 ${unlocked ? 'text-slate-500' : 'text-slate-300'}`}>
        {achievement.description}
      </p>
      {unlocked && achievement.unlockedAt && (
        <span className="text-[10px] text-emerald-600 mt-2 font-medium">
          {new Date(achievement.unlockedAt).toLocaleDateString('zh-TW')}
        </span>
      )}
    </motion.div>
  );
}
