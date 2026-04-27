/**
 * @file 測驗載入過場全螢幕動畫元件——用於 AI 出題等待過程。
 */
'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import TiTiLogo from '@/components/TiTiLogo';

/**
 * 載入動畫的單一階段。
 */
interface Stage {
  /** 階段顯示文字 */
  label: string;
  /** 階段持續毫秒數 */
  duration: number; // ms
  /** 階段結束時的目標進度百分比（0–100），可選 */
  progress?: number; // target progress percentage (0-100)
}

/**
 * ExamLoadingOverlay 的 props。
 */
interface ExamLoadingOverlayProps {
  /** 載入階段定義（依序播放） */
  stages: Stage[];
  /** 全部階段播完且進度達 100% 後的回呼 */
  onComplete: () => void;
  /** 是否顯示遮罩 */
  isVisible: boolean;
}

/**
 * 測驗載入全螢幕遮罩。
 *
 * 依序播放 `stages`，每階段內以 20 步插值更新進度條；隱藏時自動重置內部狀態。
 *
 * @param props.stages - 階段清單
 * @param props.onComplete - 完成回呼
 * @param props.isVisible - 顯示開關
 */
export default function ExamLoadingOverlay({ stages, onComplete, isVisible }: ExamLoadingOverlayProps) {
  const [currentStage, setCurrentStage] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isVisible) {
      setCurrentStage(0);
      setProgress(0);
      return;
    }

    let stageIdx = 0;
    let cancelled = false;

    const runStages = async () => {
      for (let i = 0; i < stages.length; i++) {
        if (cancelled) return;
        stageIdx = i;
        setCurrentStage(i);

        const stage = stages[i];
        const steps = 20;
        const stepDuration = stage.duration / steps;

        // Determine start and end progress for this stage
        const hasExplicitProgress = stages.every(s => s.progress !== undefined);
        const startProgress = hasExplicitProgress
          ? (i === 0 ? 0 : stages[i - 1].progress!)
          : Math.round((i / stages.length) * 100);
        const endProgress = hasExplicitProgress
          ? stage.progress!
          : Math.round(((i + 1) / stages.length) * 100);

        for (let s = 0; s <= steps; s++) {
          if (cancelled) return;
          const interpolated = startProgress + ((s / steps) * (endProgress - startProgress));
          setProgress(Math.round(interpolated));
          await new Promise(r => setTimeout(r, stepDuration));
        }
      }

      if (!cancelled) {
        setProgress(100);
        setTimeout(() => {
          if (!cancelled) onComplete();
        }, 300);
      }
    };

    runStages();
    return () => { cancelled = true; };
  }, [isVisible, stages, onComplete]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 bg-slate-900/95 flex items-center justify-center"
        >
          <div className="text-center max-w-md px-8">
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              className="mx-auto h-20 w-20 rounded-full bg-white flex items-center justify-center mb-8 shadow-lg shadow-emerald-500/30"
            >
              <TiTiLogo size={48} />
            </motion.div>

            <motion.p
              key={currentStage}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xl font-bold text-white mb-2"
            >
              {stages[currentStage]?.label ?? '準備中...'}
            </motion.p>

            <p className="text-sm text-slate-400 mb-8">AI 正在為你量身打造測驗</p>

            <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-emerald-500 rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>

            <p className="text-xs text-slate-500 mt-3">{progress}%</p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
