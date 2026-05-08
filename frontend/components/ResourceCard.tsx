'use client';

/**
 * ResourceCard — 資源庫卡片視覺差異化（Sprint 3 T31）
 *
 * 對應 ux-redesign-plan.md「File-Type Aware UI」：
 * 不同檔案類型有專屬視覺語言（icon / 顏色 / 元數據 / CTA）。
 *
 * 7 種類型：
 *   pdf      📄 emerald   章節數 / 已讀比例
 *   video    🎬 blue      時長 / 已看
 *   slides   📊 purple    投影片數 / 已過
 *   audio    🎧 amber     時長 / 已聽
 *   notes    📝 indigo    DOCX 個人筆記
 *   image    🖼 rose       單張圖片
 *   quiz     ❓ slate     試題卷 / 已答
 *
 * 每張卡片包含：
 *   - 類型 icon + 類型 badge
 *   - 標題（檔名）
 *   - 元數據（依類型不同）
 *   - 進度條（依已用 / 總量）
 *   - 上次中斷處
 *   - 主要 CTA 按鈕（讀 / 看 / 過 / 聽 / 作答）+ 刪除
 */

import Link from 'next/link';
import {
  FileText, Film, LayoutGrid, Headphones, FileEdit, Image as ImageIcon,
  HelpCircle, Trash2, Clock, BookOpen,
} from 'lucide-react';

export type ResourceType =
  | 'pdf' | 'video' | 'slides' | 'audio' | 'notes' | 'image' | 'quiz';

export interface ResourceCardProps {
  /** Resource UUID */
  id: string;
  /** Subject UUID（用於 reading 路由 link）*/
  subjectId?: string;
  /** 類型 */
  type: ResourceType;
  /** 檔名 */
  name: string;
  /** 元數據（依類型不同顯示）*/
  metadata?: {
    /** 頁數 (pdf) / 投影片數 (slides) / 題數 (quiz) */
    count?: number;
    /** 時長秒（video / audio）*/
    durationSec?: number;
    /** 章節數 (pdf) / 段落數 */
    chapters?: number;
    /** 鷹架總數 */
    scaffoldCount?: number;
    /** 已讀 / 已看 / 已答比率 0-1 */
    progress?: number;
    /** 上次中斷處（章節 / 時間戳）*/
    resumeText?: string | null;
  };
  /** 解析狀態 */
  status?: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | string;
  /** 點擊刪除 callback */
  onDelete?: () => void;
}

const TYPE_CONFIG: Record<ResourceType, {
  Icon: typeof FileText;
  emoji: string;
  badge: string;
  cta: string;
  routePath: (id: string, subjectId?: string) => string;
  iconColor: string;
  bgColor: string;
  ringColor: string;
}> = {
  pdf: {
    Icon: FileText,
    emoji: '📄',
    badge: 'PDF',
    cta: '讀',
    routePath: (id, sid) => `/library/read/reading?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
    ringColor: 'border-emerald-200 hover:border-emerald-400',
  },
  video: {
    Icon: Film,
    emoji: '🎬',
    badge: '影片',
    cta: '看',
    routePath: (id, sid) => `/library/view/watch?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-50',
    ringColor: 'border-blue-200 hover:border-blue-400',
  },
  slides: {
    Icon: LayoutGrid,
    emoji: '📊',
    badge: '簡報',
    cta: '過',
    routePath: (id, sid) => `/library/slides/slides?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-purple-600',
    bgColor: 'bg-purple-50',
    ringColor: 'border-purple-200 hover:border-purple-400',
  },
  audio: {
    Icon: Headphones,
    emoji: '🎧',
    badge: '音訊',
    cta: '聽',
    routePath: (id, sid) => `/library/view/watch?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-amber-600',
    bgColor: 'bg-amber-50',
    ringColor: 'border-amber-200 hover:border-amber-400',
  },
  notes: {
    Icon: FileEdit,
    emoji: '📝',
    badge: '筆記',
    cta: '讀',
    routePath: (id, sid) => `/library/read/reading?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    ringColor: 'border-indigo-200 hover:border-indigo-400',
  },
  image: {
    Icon: ImageIcon,
    emoji: '🖼',
    badge: '圖片',
    cta: '看',
    routePath: (id, sid) => `/library/read/reading?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-rose-600',
    bgColor: 'bg-rose-50',
    ringColor: 'border-rose-200 hover:border-rose-400',
  },
  quiz: {
    Icon: HelpCircle,
    emoji: '❓',
    badge: '試題卷',
    cta: '作答',
    routePath: (id, sid) => `/library/quiz/quiz?docId=${id}${sid ? `&subjectId=${sid}` : ''}`,
    iconColor: 'text-slate-700',
    bgColor: 'bg-slate-100',
    ringColor: 'border-slate-300 hover:border-slate-500',
  },
};

function formatDuration(sec?: number): string | null {
  if (!sec || sec <= 0) return null;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function ResourceCard({
  id,
  subjectId,
  type,
  name,
  metadata,
  status,
  onDelete,
}: ResourceCardProps) {
  const config = TYPE_CONFIG[type];
  const { Icon, badge, cta, routePath, iconColor, bgColor, ringColor } = config;
  const progress = metadata?.progress ?? 0;
  const progressPct = Math.round(progress * 100);

  const isReady = status === 'COMPLETED';
  const isProcessing = status === 'PENDING' || status === 'PROCESSING';
  const isFailed = status === 'FAILED';

  return (
    <div
      className={`bg-white rounded-2xl border ${ringColor} p-4 transition-all relative group`}
      aria-label={`${badge} 資源：${name}`}
    >
      <div className="flex items-start gap-3">
        {/* Icon area */}
        <div className={`shrink-0 w-12 h-12 rounded-xl ${bgColor} flex items-center justify-center`}>
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>

        <div className="flex-1 min-w-0">
          {/* Type badge + status */}
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold ${iconColor}`}>{badge}</span>
            {isProcessing && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                處理中
              </span>
            )}
            {isFailed && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                ❌ 失敗
              </span>
            )}
            {isReady && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                ✓ 完成
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="text-sm font-medium text-slate-900 truncate" title={name}>
            {name}
          </h3>

          {/* Metadata row */}
          <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-2">
            {metadata?.count !== undefined && metadata.count > 0 && (
              <span>
                {type === 'pdf' || type === 'notes' ? `${metadata.count} 頁` :
                 type === 'slides' ? `${metadata.count} 張` :
                 type === 'quiz' ? `${metadata.count} 題` :
                 `${metadata.count}`}
              </span>
            )}
            {metadata?.durationSec !== undefined && (
              <span className="inline-flex items-center gap-0.5">
                <Clock className="w-3 h-3" /> {formatDuration(metadata.durationSec)}
              </span>
            )}
            {metadata?.chapters !== undefined && metadata.chapters > 0 && (
              <span>{metadata.chapters} 章節</span>
            )}
            {metadata?.scaffoldCount !== undefined && metadata.scaffoldCount > 0 && (
              <span>{metadata.scaffoldCount} 鷹架</span>
            )}
          </p>

          {/* Progress bar */}
          {isReady && progress > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${iconColor.replace('text-', 'bg-')} transition-all`}
                  style={{ width: `${progressPct}%` }}
                  role="progressbar"
                  aria-valuenow={progressPct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                />
              </div>
              <span className="text-[10px] tabular-nums text-slate-500 shrink-0">{progressPct}%</span>
            </div>
          )}

          {/* Resume hint */}
          {metadata?.resumeText && isReady && (
            <p className="mt-2 text-xs text-slate-500 flex items-center gap-1 truncate">
              <BookOpen className="w-3 h-3 shrink-0" />
              上次：{metadata.resumeText}
            </p>
          )}
        </div>

        {/* CTA + Delete */}
        <div className="shrink-0 flex flex-col items-end gap-1">
          {isReady && (
            <Link
              href={routePath(id, subjectId)}
              className={`px-3 py-1.5 rounded-full bg-white border ${ringColor} text-xs font-medium ${iconColor} hover:bg-slate-50`}
            >
              {cta}
            </Link>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="p-1 text-slate-300 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
              aria-label="刪除資源"
              title="刪除"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * 從檔名推測 ResourceType（給 caller 用）。
 *
 * 實際路由分流仍由後端 _select_prompt_template 決定，但前端視覺需要相同分類。
 */
export function resolveResourceType(
  name: string,
  detectedContentType?: string | null,
  youtubeUrl?: string | null,
): ResourceType {
  if (youtubeUrl) return 'video';
  if (detectedContentType === 'practice_questions') return 'quiz';
  const ext = name.toLowerCase().split('.').pop() ?? '';
  if (['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'].includes(ext)) return 'video';
  if (['mp3', 'wav', 'm4a', 'flac', 'ogg', 'wma', 'aac'].includes(ext)) return 'audio';
  if (['ppt', 'pptx'].includes(ext)) return 'slides';
  if (['doc', 'docx'].includes(ext)) return 'notes';
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'image';
  return 'pdf'; // default for pdf, md, txt 等
}
