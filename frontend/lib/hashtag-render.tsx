import React from 'react';

const HASHTAG_RE = /(?<=\s|^)#([\p{L}\p{N}_-]+)/gu;

/**
 * 將字串內的 #hashtag 拆出渲染為 pill 樣式。
 * 其餘文字保持原樣（包含換行）。
 */
export function renderHashtags(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  let key = 0;
  // 每次呼叫必須 reset lastIndex，因為 /g flag 會保留狀態
  HASHTAG_RE.lastIndex = 0;
  while ((match = HASHTAG_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push(
      <span
        key={`tag-${key++}`}
        className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-medium mx-0.5"
      >
        #{match[1]}
      </span>
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}
