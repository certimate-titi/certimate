/**
 * @file Markdown + KaTeX 數學公式渲染元件。
 *
 * 用於 /review 題目內容、AI 教練回覆等可能含 $...$ / $$...$$ LaTeX 的文字。
 * 支援 inline 公式 `$x^2$` 與 block 公式 `$$\\frac{a}{b}$$`，以及一般 Markdown。
 * GFM 擴充：表格、刪除線、任務清單、自動連結。
 */
'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface MathContentProps {
  /** 待渲染的 Markdown / LaTeX 文字 */
  children: string;
  /** 額外 className（套用到容器 div） */
  className?: string;
  /**
   * inline 模式（預設 true）：
   * - 段落 `<p>` 改 `<span>` 避免 prose-sm 行距；換行靠 `whitespace-pre-line` 將 \n 顯示成 <br>。
   * - 適合 AI 聊天訊息、題幹、scaffold content 等短文。
   *
   * 設 `false` 為「文件模式」：保留 prose 段落 / 程式碼區塊 / 表格的完整樣式，
   * 適合 /knowledge 文件分頁、考古題全文渲染。
   */
  inline?: boolean;
}

/**
 * 將 Markdown + LaTeX 字串渲染為 HTML。
 *
 * @param props.children - 文字內容
 * @param props.className - 額外樣式
 * @param props.inline - 是否為 inline 短文模式（預設 true）
 */
export default function MathContent({ children, className = '', inline = true }: MathContentProps) {
  const wrapperCls = inline
    ? `prose prose-sm max-w-none whitespace-pre-line ${className}`
    : `prose prose-sm max-w-none prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-pre:rounded-lg prose-pre:p-3 prose-pre:overflow-x-auto prose-code:before:content-none prose-code:after:content-none prose-code:bg-slate-100 prose-code:text-slate-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-table:my-3 prose-th:border prose-th:border-slate-300 prose-th:bg-slate-100 prose-th:px-2 prose-th:py-1 prose-td:border prose-td:border-slate-300 prose-td:px-2 prose-td:py-1 ${className}`;

  return (
    <div className={wrapperCls}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={
          inline
            ? {
                // inline 模式：移除預設 wrapping <p> 對 prose 行距的影響
                p: ({ children }) => <span>{children}</span>,
              }
            : undefined
        }
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
