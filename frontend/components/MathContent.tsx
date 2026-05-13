/**
 * @file Markdown + KaTeX 數學公式渲染元件。
 *
 * 用於 /review 題目內容、AI 教練回覆等可能含 $...$ / $$...$$ LaTeX 的文字。
 * 支援 inline 公式 `$x^2$` 與 block 公式 `$$\\frac{a}{b}$$`，以及一般 Markdown。
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
}

/**
 * 將 Markdown + LaTeX 字串渲染為 HTML，保留換行（\n → <br>）。
 *
 * @param props.children - 文字內容
 * @param props.className - 額外樣式
 */
export default function MathContent({ children, className = '' }: MathContentProps) {
  return (
    <div className={`prose prose-sm max-w-none whitespace-pre-line ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          // 移除預設 wrapping <p> 對 prose 的影響
          p: ({ children }) => <span>{children}</span>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
