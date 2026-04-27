/**
 * @file 成就網格元件，將成就分為「已獲得」與「待解鎖」兩區呈現。
 */
'use client';

import type { Achievement } from '@/types';
import AchievementBadge from './AchievementBadge';

/**
 * AchievementGrid 的 props。
 */
interface AchievementGridProps {
  /** 全部成就清單（含已解鎖與未解鎖） */
  achievements: Achievement[];
}

/**
 * 成就網格。
 *
 * 依 `unlockedAt` 切分為已獲得 / 待解鎖兩個區塊，並各自以 `AchievementBadge` 呈現。
 *
 * @param props.achievements - 全部成就清單
 */
export default function AchievementGrid({ achievements }: AchievementGridProps) {
  const unlocked = achievements.filter(a => a.unlockedAt);
  const locked = achievements.filter(a => !a.unlockedAt);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">
          已獲得 ({unlocked.length}/{achievements.length})
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          {unlocked.map(a => (
            <AchievementBadge key={a.id} achievement={a} />
          ))}
        </div>
      </div>

      {locked.length > 0 && (
        <div>
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">
            待解鎖
          </h3>
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
            {locked.map(a => (
              <AchievementBadge key={a.id} achievement={a} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
