'use client';

import { useEffect, useState } from 'react';
import { learningJourneyService, type PendingJourneyItem } from '@/lib/api/services';

export default function PendingJourneysBanner() {
  const [items, setItems] = useState<PendingJourneyItem[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refresh = () => {
    learningJourneyService
      .listPending()
      .then(res => setItems(Array.isArray(res?.items) ? res.items : []))
      .catch(() => setItems([]));
  };

  useEffect(() => {
    refresh();
  }, []);

  if (items.length === 0) return null;

  const handle = async (journeyId: string, action: 'passed' | 'failed' | 'quit') => {
    setBusyId(journeyId);
    try {
      if (action === 'quit') {
        if (!confirm('確定不再報考？資料將保留 30 天後自動清除。')) return;
        await learningJourneyService.quit(journeyId);
      } else {
        await learningJourneyService.confirmResult(journeyId, action);
      }
      refresh();
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="bg-indigo-50 border-b border-indigo-200 px-4 py-3">
      <div className="container mx-auto max-w-6xl space-y-2">
        {items.map(it => (
          <div key={it.id} className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div className="text-sm text-indigo-900">
              <span className="font-bold">{it.subject_name}</span>
              <span className="ml-2 text-indigo-700">
                {it.exam_result_status === 'failed' ? '已確認未考取，請選擇下一步' : `放榜日 ${it.result_date ?? ''} 已到，請確認考試結果`}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs font-bold">
              {it.exam_result_status !== 'failed' && (
                <>
                  <button
                    disabled={busyId === it.id}
                    onClick={() => handle(it.id, 'passed')}
                    className="text-emerald-700 hover:text-emerald-900"
                  >
                    確認考取
                  </button>
                  <button
                    disabled={busyId === it.id}
                    onClick={() => handle(it.id, 'failed')}
                    className="text-rose-700 hover:text-rose-900"
                  >
                    未考取
                  </button>
                </>
              )}
              {it.exam_result_status === 'failed' && (
                <button
                  disabled={busyId === it.id}
                  onClick={() => handle(it.id, 'quit')}
                  className="text-slate-700 hover:text-slate-900"
                >
                  不再報考
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
