'use client';

/**
 * @file SocraticBadge — 「蘇格拉底引導模式」標籤
 *
 * 與既有錯題詳解 AI 教練（emerald 色系）視覺錯開，採 violet 色系，
 * 提醒學生此為引導模式——AI 只問問題，不直接給答案。
 */

interface SocraticBadgeProps {
  className?: string;
}

export default function SocraticBadge({ className = '' }: SocraticBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-100 text-violet-700 border border-violet-300 text-[10px] font-semibold select-none ${className}`}
      title="蘇格拉底引導模式：AI 透過提問引導你思考，不直接給出答案"
    >
      <span className="text-[11px]">&#x1F9D0;</span>
      蘇格拉底引導
    </span>
  );
}
