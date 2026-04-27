/**
 * @file 連續學習天數計數器元件，顯示火焰圖示、連續天數與凍結保護次數。
 */
'use client';

import { Flame, Snowflake } from 'lucide-react';
import { motion } from 'motion/react';
import type { LearningStreak } from '@/types';

/**
 * StreakCounter 的 props。
 */
interface StreakCounterProps {
  /** 連續學習狀態（含 currentStreak、freezesRemaining） */
  streak: LearningStreak;
}

/**
 * 連續學習天數計數器。
 *
 * 連續天數 > 0 時火焰點亮並有抖動動畫；剩餘凍結次數會以雪花圖示呈現。
 *
 * @param props.streak - 連續學習狀態
 */
export default function StreakCounter({ streak }: StreakCounterProps) {
  const isActive = streak.currentStreak > 0;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className="flex items-center gap-3 bg-white px-4 py-2 rounded-full shadow-sm border border-slate-200"
    >
      <motion.div
        animate={isActive ? { rotate: [0, -8, 8, -4, 0] } : {}}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <Flame className={`h-5 w-5 ${isActive ? 'text-orange-500' : 'text-slate-300'}`} />
      </motion.div>

      <div className="flex flex-col">
        <span className={`text-sm font-bold leading-tight ${isActive ? 'text-orange-600' : 'text-slate-400'}`}>
          {streak.currentStreak} 天連續
        </span>
        {streak.currentStreak === 0 && (
          <span className="text-[10px] text-slate-400">休息也是學習的一部分</span>
        )}
      </div>

      {streak.freezesRemaining > 0 && (
        <div className="flex items-center gap-1 ml-1 text-blue-500" title={`剩餘 ${streak.freezesRemaining} 次凍結保護`}>
          <Snowflake className="h-3 w-3" />
          <span className="text-[10px] font-medium">{streak.freezesRemaining}</span>
        </div>
      )}
    </motion.div>
  );
}
