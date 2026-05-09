/**
 * @file AI 補洞鷹架卡片元件（amber 邊框）。
 *
 * 依 A.3.4 信心分數對應視覺規則：
 *   0-30：不應渲染（父層判斷）
 *   31-49：灰底 amber 邊框 + 低信心警告
 *   50-79：標準 amber 邊框
 *   80-100：amber 邊框 + 「佐證充足」小標
 *
 * 右上角「AI 推論」徽章常駐，浮水印常駐不可關閉。
 * 練習題答案預設摺疊，點「揭曉答案」展開。
 * 底部「標記不準確」ghost button 開啟 ReportInaccurateModal。
 */
'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Flag, CheckCircle2 } from 'lucide-react';
import type { OrphanFillResponse } from '@/types/api';
import ReportInaccurateModal from './ReportInaccurateModal';

/**
 * OrphanScaffoldCard 的 props。
 */
export interface OrphanScaffoldCardProps {
  /** 已生成的 AI 補洞鷹架資料 */
  data: OrphanFillResponse;
  /** 回報成功後通知父元件（父元件負責隱藏卡片） */
  onReported?: () => void;
}

/**
 * 依信心分數決定容器的樣式設定。
 */
function getScoreStyle(score: number): {
  container: string;
  warning: string | null;
  badge: string | null;
} {
  if (score <= 30) {
    // 父層應攔截，但防禦性處理
    return {
      container: 'border-2 border-amber-500 rounded-xl bg-white',
      warning: null,
      badge: null,
    };
  }
  if (score <= 49) {
    return {
      container: 'border-2 border-amber-500 rounded-xl bg-slate-50',
      warning: 'AI 信心低，建議搭配其他資源',
      badge: null,
    };
  }
  if (score <= 79) {
    return {
      container: 'border-2 border-amber-500 rounded-xl bg-white',
      warning: null,
      badge: null,
    };
  }
  // 80-100
  return {
    container: 'border-2 border-amber-500 rounded-xl bg-white',
    warning: null,
    badge: '佐證充足',
  };
}

/**
 * AI 補洞鷹架卡片。
 *
 * trust_level = AI_INFERRED 時專用；不可顯示「正式教材」字樣。
 */
export default function OrphanScaffoldCard({ data, onReported }: OrphanScaffoldCardProps) {
  const [answerRevealed, setAnswerRevealed] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reported, setReported] = useState(false);
  const [reportedMessage, setReportedMessage] = useState('');

  const { score, style } = (() => {
    const s = data.confidence_score;
    return { score: s, style: getScoreStyle(s) };
  })();

  function handleReported() {
    setReportModalOpen(false);
    setReported(true);
    setReportedMessage('已回報，感謝回饋');
    onReported?.();
    // 3 秒後清除訊息（但父層會移除此元件，保留作保底）
    setTimeout(() => setReportedMessage(''), 3000);
  }

  if (reported) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-5 text-center">
        <CheckCircle2 className="h-5 w-5 mx-auto mb-2 text-emerald-500" />
        <p className="text-xs text-slate-600 font-medium">已回報，感謝回饋</p>
        <p className="text-[11px] text-slate-400 mt-1">此鷹架已對您隱藏</p>
      </div>
    );
  }

  return (
    <>
      <div className={style.container}>
        {/* ── Header：AI 推論徽章 + 低信心警告 ── */}
        <div className="relative px-4 pt-4 pb-3">
          {/* AI 推論徽章（右上角） */}
          <span className="absolute top-3 right-3 bg-amber-500 text-white text-[10px] px-2 py-0.5 rounded-full font-semibold leading-none">
            AI 推論
          </span>

          {/* 佐證充足標（score 80+） */}
          {style.badge && (
            <span className="inline-flex items-center gap-1 text-[10px] text-amber-700 bg-amber-100 border border-amber-300 px-2 py-0.5 rounded-full font-semibold mb-2">
              <CheckCircle2 className="h-2.5 w-2.5" />
              {style.badge}
            </span>
          )}

          {/* 低信心警告（31-49） */}
          {style.warning && (
            <div className="flex items-start gap-1.5 rounded-md bg-amber-50 border border-amber-200 px-2.5 py-1.5 mb-3 pr-16">
              <span className="text-[10px] text-amber-700 leading-relaxed">{style.warning}</span>
            </div>
          )}
        </div>

        {/* ── 段落一：定義 ── */}
        <div className="px-4 pb-3">
          <h4 className="text-[10px] font-bold text-amber-700 uppercase tracking-wide mb-1.5">
            定義
          </h4>
          <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
            {data.definition}
          </p>
        </div>

        <div className="mx-4 border-t border-amber-100" />

        {/* ── 段落二：範例 ── */}
        <div className="px-4 py-3">
          <h4 className="text-[10px] font-bold text-amber-700 uppercase tracking-wide mb-1.5">
            範例
          </h4>
          <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
            {data.illustration}
          </p>
        </div>

        <div className="mx-4 border-t border-amber-100" />

        {/* ── 段落三：練習題 ── */}
        <div className="px-4 py-3">
          <h4 className="text-[10px] font-bold text-amber-700 uppercase tracking-wide mb-2">
            練習題
          </h4>
          <p className="text-xs text-slate-800 leading-relaxed mb-3 font-medium">
            {data.practice_question.stem}
          </p>
          <ul className="space-y-1 mb-3">
            {(['A', 'B', 'C', 'D'] as const).map((opt) => (
              <li
                key={opt}
                className={`flex items-start gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors ${
                  answerRevealed && data.practice_question.answer === opt
                    ? 'bg-emerald-50 border border-emerald-300 text-emerald-800 font-semibold'
                    : 'bg-slate-50 text-slate-700'
                }`}
              >
                <span className="font-semibold shrink-0 text-slate-500">{opt}.</span>
                <span>{data.practice_question.options[opt]}</span>
              </li>
            ))}
          </ul>

          {/* 揭曉答案按鈕 */}
          {!answerRevealed ? (
            <button
              onClick={() => setAnswerRevealed(true)}
              className="flex items-center gap-1 text-[11px] text-amber-600 font-semibold hover:text-amber-700 transition-colors"
            >
              <ChevronDown className="h-3.5 w-3.5" />
              揭曉答案
            </button>
          ) : (
            <div className="rounded-md bg-emerald-50 border border-emerald-200 px-3 py-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-emerald-700">
                  正確答案：{data.practice_question.answer}
                </span>
                <button
                  onClick={() => setAnswerRevealed(false)}
                  className="flex items-center gap-0.5 text-[10px] text-slate-400 hover:text-slate-600"
                >
                  <ChevronUp className="h-3 w-3" />
                  收合
                </button>
              </div>
              <p className="text-[11px] text-slate-700 leading-relaxed whitespace-pre-line">
                {data.practice_question.explanation}
              </p>
            </div>
          )}
        </div>

        {/* ── 浮水印 footer（常駐不可關閉） ── */}
        <div className="text-[11px] text-amber-700 bg-amber-50 px-3 py-2 rounded-b-xl border-t border-amber-100">
          此鷹架由 AI 從考古題反推生成，尚未經教師人工審核。
          <br />
          引用佐證：{data.evidence_count} 道考古題（{data.evidence_year_range}）
          &nbsp;信心分數：{score}/100
        </div>
      </div>

      {/* ── 標記不準確 ghost button ── */}
      <div className="mt-2 text-center">
        <button
          onClick={() => setReportModalOpen(true)}
          className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-600 transition-colors"
        >
          <Flag className="h-3 w-3" />
          這份內容有問題嗎？[標記不準確]
        </button>
      </div>

      {/* ── 回報 Modal ── */}
      {reportModalOpen && (
        <ReportInaccurateModal
          scaffoldId={data.scaffold_id}
          onClose={() => setReportModalOpen(false)}
          onReported={handleReported}
        />
      )}

      {/* 回報成功提示（保底用） */}
      {reportedMessage && (
        <p className="text-center text-[11px] text-emerald-600 mt-1">{reportedMessage}</p>
      )}
    </>
  );
}
