'use client';

/**
 * VideoTimestampJump — 影片時間戳跳轉清單（Sprint 2.5 T22）
 *
 * UX：
 * - 從 K-06-video prompt 產出的 chapter_heading 解析時間戳（"00:32-02:15 ..."）
 * - 點任一條 → 影片 seek 到 start_time_sec + 自動播放
 * - 當前播放秒數附近的條目高亮（emerald 邊框）
 * - takeaway 顯示 📌 / pitfall 顯示 ⚠️ / elaborative 顯示 💭
 *
 * 不打 API、不寫互動 log（純 client-side 跳轉）。
 */

import type { ScaffoldEntry } from '@/hooks/use-reading-page-state';
import { AlertTriangle, Bookmark, MessageCircle } from 'lucide-react';

export interface VideoTimestampJumpProps {
  /** 時間戳鷹架（type=takeaway/pitfall/elaborative，chapter_heading 含時間戳格式）*/
  scaffolds: ScaffoldEntry[];
  /** 當前影片播放秒數（Math.floor）*/
  currentSec: number;
  /** 點擊時跳到指定秒數 */
  onJumpTo: (sec: number) => void;
}

interface ParsedTimestamp {
  startSec: number;
  endSec: number;
  label: string;
}

/**
 * 從 chapter_heading 解析時間戳。
 *
 * 支援格式：
 *   "00:32-02:15 AI 三層級分類"
 *   "12:34 No-code 平台"（單一時間戳）
 *   "1:23:45 ..."（小時級）
 */
function parseTimestamp(heading: string | null): ParsedTimestamp | null {
  if (!heading) return null;
  // 匹配 "MM:SS-MM:SS" 或 "HH:MM:SS-HH:MM:SS"
  const rangeMatch = /^(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)/.exec(heading);
  if (rangeMatch) {
    return {
      startSec: hmsToSec(rangeMatch[1]),
      endSec: hmsToSec(rangeMatch[2]),
      label: rangeMatch[3].trim(),
    };
  }
  const singleMatch = /^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)/.exec(heading);
  if (singleMatch) {
    const sec = hmsToSec(singleMatch[1]);
    return { startSec: sec, endSec: sec + 60, label: singleMatch[2].trim() };
  }
  return null;
}

function hmsToSec(hms: string): number {
  const parts = hms.split(':').map(Number);
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return 0;
}

function formatSec(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

const TYPE_ICON = {
  takeaway: { Icon: Bookmark, color: 'text-emerald-600', label: '重點' },
  pitfall: { Icon: AlertTriangle, color: 'text-rose-600', label: '迷思' },
  elaborative: { Icon: MessageCircle, color: 'text-indigo-600', label: '思考' },
} as const;

export default function VideoTimestampJump({
  scaffolds,
  currentSec,
  onJumpTo,
}: VideoTimestampJumpProps) {
  // 解析每筆鷹架的時間戳，過濾無時間戳的
  const items = scaffolds
    .map((s) => ({ s, ts: parseTimestamp(s.chapter_heading) }))
    .filter((x): x is { s: ScaffoldEntry; ts: ParsedTimestamp } => x.ts !== null)
    .sort((a, b) => a.ts.startSec - b.ts.startSec);

  if (items.length === 0) {
    return (
      <p className="text-xs text-slate-400 italic">
        此影片鷹架尚無時間戳格式（K-06-video v1+ 才產出）
      </p>
    );
  }

  return (
    <ol className="space-y-1.5">
      {items.map(({ s, ts }) => {
        const isActive = currentSec >= ts.startSec && currentSec < ts.endSec;
        const typeKey = (s.type === 'pitfall' || s.type === 'elaborative') ? s.type : 'takeaway';
        const { Icon, color, label } = TYPE_ICON[typeKey as keyof typeof TYPE_ICON];
        return (
          <li key={s.id}>
            <button
              type="button"
              onClick={() => onJumpTo(ts.startSec)}
              className={`w-full flex items-start gap-2 text-left px-2 py-1.5 rounded-lg transition-colors ${
                isActive
                  ? 'bg-emerald-50 border border-emerald-200'
                  : 'hover:bg-slate-50 border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${color}`} aria-label={label} />
              <span className="font-mono text-[10px] tabular-nums text-slate-500 shrink-0 pt-0.5">
                {formatSec(ts.startSec)}
              </span>
              <span className="text-xs text-slate-700 flex-1 truncate">{ts.label}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
