'use client';

import { useEffect, useState } from 'react';
import { Trophy, Eye, X } from 'lucide-react';
import { knowledgeService, type NodeScaffoldItem } from '@/lib/api/services';

export interface ScaffoldReplayCardProps {
  nodeId: string | null;
  masteryLevel: string | null | undefined;
  isPro: boolean;
}

const STORAGE_PREFIX = 'certimate_scaffold_replay_dismissed_';

export default function ScaffoldReplayCard({ nodeId, masteryLevel, isPro }: ScaffoldReplayCardProps) {
  const [dismissed, setDismissed] = useState(false);
  const [entries, setEntries] = useState<NodeScaffoldItem[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setExpanded(false);
    if (!nodeId || masteryLevel !== 'mastered' || !isPro) {
      setDismissed(true);
      return;
    }
    const key = STORAGE_PREFIX + nodeId;
    if (typeof window !== 'undefined' && localStorage.getItem(key) === '1') {
      setDismissed(true);
      return;
    }
    setDismissed(false);
    knowledgeService
      .getNodeScaffolds(nodeId)
      .then((res) => setEntries((res.scaffolds || []).filter((s) => s.user_response && s.reference_answer)))
      .catch(() => setEntries([]));
  }, [nodeId, masteryLevel, isPro]);

  if (dismissed || entries.length === 0 || !nodeId) return null;

  function handleDismiss() {
    if (nodeId) localStorage.setItem(STORAGE_PREFIX + nodeId, '1');
    setDismissed(true);
  }

  return (
    <div className="mx-3 my-2 rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-3 relative">
      <button
        onClick={handleDismiss}
        className="absolute top-1.5 right-1.5 p-0.5 rounded hover:bg-emerald-100"
        aria-label="關閉"
      >
        <X className="h-3 w-3 text-slate-400" />
      </button>
      <div className="flex items-center gap-2 mb-1">
        <Trophy className="h-4 w-4 text-emerald-500" />
        <h4 className="text-xs font-bold text-emerald-700">恭喜！你已掌握這個節點</h4>
      </div>
      <p className="text-[11px] text-slate-600 leading-relaxed">
        你曾經在這裡思考過 {entries.length} 個深讀提問，是否要回顧當時的筆記？
      </p>
      {!expanded ? (
        <button
          onClick={() => setExpanded(true)}
          className="mt-2 inline-flex items-center gap-1 text-[11px] text-emerald-600 font-semibold hover:text-emerald-700"
        >
          <Eye className="h-3 w-3" /> 展開回顧
        </button>
      ) : (
        <ul className="mt-2 space-y-2">
          {entries.map((e) => (
            <li key={e.id} className="rounded-md bg-white border border-emerald-100 p-2">
              <p className="text-[11px] font-semibold text-slate-700 mb-1">{e.content}</p>
              <p className="text-[10px] text-slate-500 mb-1">
                <span className="font-semibold text-slate-600">你當時寫的：</span>
                {e.user_response}
              </p>
              <p className="text-[10px] text-emerald-700">
                <span className="font-semibold">參考答案：</span>
                {e.reference_answer}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
