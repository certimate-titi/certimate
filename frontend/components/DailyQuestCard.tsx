'use client';

import { CheckCircle2, Circle, BookOpen, Compass, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import type { DailyQuest } from '@/types';

interface DailyQuestCardProps {
  quest: DailyQuest;
}

const questIcons = {
  review: BookOpen,
  explore: Compass,
  quiz: Zap,
};

export default function DailyQuestCard({ quest }: DailyQuestCardProps) {
  const Icon = questIcons[quest.type];

  return (
    <motion.div
      layout
      className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
        quest.completed
          ? 'bg-emerald-50/50 border-emerald-100'
          : 'bg-white border-slate-200'
      }`}
    >
      <div className="shrink-0">
        {quest.completed ? (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 400 }}
          >
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          </motion.div>
        ) : (
          <Circle className="h-5 w-5 text-slate-300" />
        )}
      </div>

      <Icon className={`h-4 w-4 shrink-0 ${quest.completed ? 'text-emerald-400' : 'text-slate-400'}`} />

      <span className={`text-sm flex-1 ${quest.completed ? 'text-slate-400 line-through' : 'text-slate-700'}`}>
        {quest.description}
      </span>

      {typeof quest.progress === 'number' && typeof quest.target === 'number' && (
        <span className={`text-[11px] font-semibold tabular-nums px-1.5 py-0.5 rounded ${
          quest.completed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
        }`}>
          {quest.progress}/{quest.target}
        </span>
      )}

      {quest.xpReward > 0 && (
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
          quest.completed ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'
        }`}>
          +{quest.xpReward} XP
        </span>
      )}
    </motion.div>
  );
}
