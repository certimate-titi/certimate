'use client';

import type { Achievement } from '@/types';
import AchievementBadge from './AchievementBadge';

interface AchievementGridProps {
  achievements: Achievement[];
}

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
