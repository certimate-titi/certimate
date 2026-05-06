/**
 * @file ShareBadgeCard.tsx — 考後分享徽章卡片（無絕對分數版本）
 *
 * 設計原則：
 * - 三種正向指標：A 進步幅度 + B 累積里程 + D 學習風格徽章
 * - 不顯示絕對分數，避免分享壓力
 * - TiTi 品牌色（emerald + slate + 白底）
 * - 兩種尺寸：square (1080×1080) / story (1080×1920)，共用元件
 */
'use client';

import { Sparkles } from 'lucide-react';
import type { ShareBadgeResponse } from '@/types/api';

export interface ShareBadgeCardProps {
  data: ShareBadgeResponse;
  variant?: 'square' | 'story';
  /** 用於 html2canvas 截圖的 DOM id */
  domId?: string;
}

const STYLE_COLOR: Record<string, { bg: string; text: string; ring: string }> = {
  tactical:   { bg: 'bg-rose-50',    text: 'text-rose-700',    ring: 'ring-rose-200' },
  socratic:   { bg: 'bg-indigo-50',  text: 'text-indigo-700',  ring: 'ring-indigo-200' },
  sprint:     { bg: 'bg-amber-50',   text: 'text-amber-700',   ring: 'ring-amber-200' },
  marathon:   { bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200' },
  steady:     { bg: 'bg-teal-50',    text: 'text-teal-700',    ring: 'ring-teal-200' },
  reflective: { bg: 'bg-purple-50',  text: 'text-purple-700',  ring: 'ring-purple-200' },
  explorer:   { bg: 'bg-sky-50',     text: 'text-sky-700',     ring: 'ring-sky-200' },
};

export default function ShareBadgeCard({ data, variant = 'square', domId }: ShareBadgeCardProps) {
  const isStory = variant === 'story';
  const style = STYLE_COLOR[data.learning_style.type_id] ?? STYLE_COLOR.explorer;
  const dateStr = data.exam_meta.completed_at
    ? new Date(data.exam_meta.completed_at).toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' })
    : '';

  return (
    <div
      id={domId}
      className={`bg-white relative ${
        isStory ? 'aspect-[9/16] max-w-[360px]' : 'aspect-square max-w-[480px]'
      } w-full rounded-3xl shadow-xl overflow-hidden`}
      style={{ fontFamily: '"Inter", "Noto Sans TC", system-ui, sans-serif' }}
    >
      {/* 上方品牌條（emerald gradient） */}
      <div className={`absolute inset-x-0 top-0 ${isStory ? 'h-32' : 'h-20'} bg-gradient-to-r from-emerald-500 via-emerald-400 to-teal-400`}>
        <div className="absolute inset-0 flex items-center justify-between px-6">
          <div className="flex items-center gap-2 text-white">
            <Sparkles className="h-5 w-5" />
            <span className="font-bold tracking-wider text-sm">TiTi · 智慧備考</span>
          </div>
          <span className="text-xs text-white/80 tracking-wide">{dateStr}</span>
        </div>
      </div>

      {/* 內容區 */}
      <div className={`relative ${isStory ? 'pt-44 pb-12' : 'pt-28 pb-8'} px-6 sm:px-8 flex flex-col items-center text-center`}>

        {/* 用戶名 + 科目 */}
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400 mb-1">{data.user.display_name}</p>
        <h2 className={`${isStory ? 'text-2xl' : 'text-xl'} font-bold text-slate-900 mb-1 leading-tight`}>
          完成挑戰
        </h2>
        <p className={`${isStory ? 'text-base' : 'text-sm'} font-medium text-emerald-600 mb-6`}>
          {data.exam_meta.subject_name || data.exam_meta.title}
        </p>

        {/* A. 進步幅度 */}
        <div className="w-full mb-6">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 mb-2">本次表現</p>
          <p className={`${isStory ? 'text-2xl' : 'text-xl'} font-bold text-slate-900`}>
            {data.improvement.message}
          </p>
        </div>

        {/* 分隔線 */}
        <div className="w-16 h-0.5 bg-slate-200 rounded-full mb-6" />

        {/* B. 累積里程（3 欄） */}
        <div className="w-full grid grid-cols-3 gap-2 mb-6">
          <div className="text-center">
            <p className={`${isStory ? 'text-2xl' : 'text-xl'} font-bold text-slate-900`}>
              {data.cumulative.total_exams}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">累積測驗</p>
          </div>
          <div className="text-center border-x border-slate-100">
            <p className={`${isStory ? 'text-2xl' : 'text-xl'} font-bold text-slate-900`}>
              {data.cumulative.total_questions}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">作答題數</p>
          </div>
          <div className="text-center">
            <p className={`${isStory ? 'text-2xl' : 'text-xl'} font-bold text-slate-900`}>
              {data.cumulative.streak_days}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">連續天數</p>
          </div>
        </div>

        {/* D. 學習風格徽章 */}
        <div className={`w-full ${style.bg} rounded-2xl px-4 py-4 ring-1 ${style.ring}`}>
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className={isStory ? 'text-3xl' : 'text-2xl'}>{data.learning_style.emoji}</span>
            <p className={`${isStory ? 'text-lg' : 'text-base'} font-bold ${style.text}`}>
              {data.learning_style.label}
            </p>
          </div>
          <p className="text-xs text-slate-600 italic">
            「{data.learning_style.description}」
          </p>
        </div>

        {/* 底部水印 */}
        <p className="absolute bottom-3 left-0 right-0 text-center text-[9px] text-slate-300 tracking-wider">
          certimate-titi.web.app · 智慧備考 SaaS
        </p>
      </div>
    </div>
  );
}
