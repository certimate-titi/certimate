'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { BrainCircuit } from 'lucide-react';

interface Stage {
  label: string;
  duration: number; // ms
}

interface ExamLoadingOverlayProps {
  stages: Stage[];
  onComplete: () => void;
  isVisible: boolean;
}

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

        for (let s = 0; s <= steps; s++) {
          if (cancelled) return;
          const stageProgress = (i / stages.length) + ((s / steps) * (1 / stages.length));
          setProgress(Math.round(stageProgress * 100));
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
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="mx-auto h-16 w-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-8"
            >
              <BrainCircuit className="h-8 w-8 text-emerald-400" />
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
