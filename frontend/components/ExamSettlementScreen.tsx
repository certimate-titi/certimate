'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { TrendingUp, AlertTriangle, Target, Sparkles } from 'lucide-react';

interface SettlementData {
  upgradedTopics: number;
  blindSpots: number;
  previousProgress: number;
  newProgress: number;
}

interface ExamSettlementScreenProps {
  isVisible: boolean;
  data: SettlementData | null;
  onComplete: () => void;
}

/**
 * 考試結算全螢幕動畫 — 顯示成長敘事。
 *
 * 流程：
 * 1. 升級考點數（3s）
 * 2. 盲點偵測（2s）
 * 3. 整體進度變化（3s）
 * 4. 自動淡出
 */
export default function ExamSettlementScreen({
  isVisible,
  data,
  onComplete,
}: ExamSettlementScreenProps) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!isVisible || !data) return;

    setStage(0);
    const timers = [
      setTimeout(() => setStage(1), 500),
      setTimeout(() => setStage(2), 2500),
      setTimeout(() => setStage(3), 4500),
      setTimeout(() => {
        onComplete();
      }, 7000),
    ];

    return () => timers.forEach(clearTimeout);
  }, [isVisible, data, onComplete]);

  if (!data) return null;

  const progressDelta = data.newProgress - data.previousProgress;
  const progressSign = progressDelta >= 0 ? '+' : '';

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/95"
        >
          <div className="text-center max-w-md mx-auto px-6">
            {/* Stage 1: 升級考點 */}
            <AnimatePresence>
              {stage >= 1 && (
                <motion.div
                  initial={{ y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.6 }}
                  className="mb-8"
                >
                  <div className="flex items-center justify-center gap-3 mb-2">
                    <TrendingUp className="h-8 w-8 text-emerald-400" />
                    <span className="text-5xl font-black text-emerald-400">
                      {data.upgradedTopics}
                    </span>
                  </div>
                  <p className="text-emerald-300 text-lg">個考點升級</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Stage 2: 盲點偵測 */}
            <AnimatePresence>
              {stage >= 2 && (
                <motion.div
                  initial={{ y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.6 }}
                  className="mb-8"
                >
                  {data.blindSpots > 0 ? (
                    <>
                      <div className="flex items-center justify-center gap-3 mb-2">
                        <AlertTriangle className="h-8 w-8 text-amber-400" />
                        <span className="text-5xl font-black text-amber-400">
                          {data.blindSpots}
                        </span>
                      </div>
                      <p className="text-amber-300 text-lg">個盲點待突破</p>
                    </>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <Sparkles className="h-6 w-6 text-yellow-400" />
                      <p className="text-yellow-300 text-lg">零盲點！完美表現</p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Stage 3: 進度變化 */}
            <AnimatePresence>
              {stage >= 3 && (
                <motion.div
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.8, type: 'spring' }}
                >
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <Target className="h-6 w-6 text-blue-400" />
                    <p className="text-blue-300">整體進度</p>
                  </div>
                  <div className="flex items-baseline justify-center gap-3">
                    <span className="text-3xl text-slate-500 line-through">
                      {Math.round(data.previousProgress * 100)}%
                    </span>
                    <span className="text-xl text-slate-400">→</span>
                    <span className="text-6xl font-black text-white">
                      {Math.round(data.newProgress * 100)}%
                    </span>
                  </div>
                  <p className={`text-lg mt-2 font-medium ${progressDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {progressSign}{Math.round(progressDelta * 100)}%
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
