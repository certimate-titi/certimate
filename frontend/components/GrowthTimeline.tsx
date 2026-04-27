/**
 * @file 學習成長里程碑時間軸元件，依時序垂直呈現各類學習事件。
 */
'use client';

import { Upload, FileText, Trophy, Star, Flame } from 'lucide-react';
import type { GrowthMilestone } from '@/types';

/**
 * GrowthTimeline 的 props。
 */
interface GrowthTimelineProps {
  /** 里程碑清單（含類型、標籤、日期） */
  milestones: GrowthMilestone[];
}

const milestoneIcons = {
  upload: Upload,
  exam: FileText,
  pass: Trophy,
  mastery: Star,
  streak: Flame,
};

const milestoneColors = {
  upload: 'bg-blue-100 text-blue-600',
  exam: 'bg-indigo-100 text-indigo-600',
  pass: 'bg-amber-100 text-amber-600',
  mastery: 'bg-emerald-100 text-emerald-600',
  streak: 'bg-orange-100 text-orange-600',
};

/**
 * 成長時間軸。
 *
 * 為每個里程碑依 `type` 渲染對應 icon 與配色；空清單時顯示鼓勵性提示。
 *
 * @param props.milestones - 里程碑清單
 */
export default function GrowthTimeline({ milestones }: GrowthTimelineProps) {
  if (milestones.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        開始你的學習旅程，里程碑將在這裡顯示！
      </div>
    );
  }

  return (
    <div className="relative pl-8">
      {/* Vertical line */}
      <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-slate-200" />

      <div className="space-y-6">
        {milestones.map((milestone, idx) => {
          const Icon = milestoneIcons[milestone.type];
          const colorClass = milestoneColors[milestone.type];

          return (
            <div key={idx} className="relative flex items-start gap-4">
              {/* Dot on the line */}
              <div className={`absolute -left-5 top-1 h-6 w-6 rounded-full flex items-center justify-center ${colorClass}`}>
                <Icon className="h-3 w-3" />
              </div>

              <div>
                <p className="text-sm font-medium text-slate-900">{milestone.label}</p>
                <p className="text-xs text-slate-400">
                  {new Date(milestone.date).toLocaleDateString('zh-TW', {
                    year: 'numeric', month: 'long', day: 'numeric',
                  })}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
