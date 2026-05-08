'use client';

/**
 * 章節閱讀頁 — Sprint 1 T07
 *
 * 路徑：/library/read/reading?docId={uuid}&subjectId={uuid}&chapter={anchor}
 *
 * 三欄布局：
 * - 左：章節目錄（從 markdown H2/H3 提取）
 * - 中：markdown 內文 + 章節結尾 RetrievalCard / InlinePractice（T08/T09 接入）
 * - 右：當前章節資訊（含資源連結回 /knowledge）
 *
 * P0 範圍：純檢視 + parse_status loading/failed UX。
 * RetrievalCard / InlinePractice 會在 T08 / T09 直接掛入此頁。
 */

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, BookOpen, ListTree, ChevronRight } from 'lucide-react';

import InlinePractice from '@/components/InlinePractice';
import MathContent from '@/components/MathContent';
import RetrievalCard from '@/components/RetrievalCard';
import { useReadingPageState } from '@/hooks/use-reading-page-state';
import { useAuth } from '@/lib/auth-context';

export default function ReadingClient() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const {
    resourceId,
    subjectId,
    currentChapter,
    parseStatus,
    parseFailureReason,
    markdown,
    chapters,
    scaffolds,
    loading,
    error,
  } = useReadingPageState();
  const [showToc, setShowToc] = useState(true);

  // Filter scaffolds by current chapter heading match
  const chapterScaffolds = useMemo(() => {
    if (!currentChapter) return scaffolds;
    const target = chapters.find((c) => c.anchorId === currentChapter)?.heading;
    if (!target) return scaffolds;
    return scaffolds.filter((s) => s.chapter_heading === target);
  }, [currentChapter, scaffolds, chapters]);

  // Auto-scroll to current chapter when URL changes — find heading by text content
  useEffect(() => {
    if (!currentChapter || loading) return;
    const target = chapters.find((c) => c.anchorId === currentChapter)?.heading;
    if (!target) return;
    // ReactMarkdown renders H2/H3 inside <article>; locate by text content
    const headings = document.querySelectorAll('article h2, article h3');
    for (const h of Array.from(headings)) {
      if ((h.textContent || '').trim() === target) {
        h.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    }
  }, [currentChapter, loading, chapters]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Link href="/login" className="text-emerald-600 hover:underline">請先登入 →</Link>
      </div>
    );
  }

  if (!resourceId) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <h1 className="text-xl font-bold text-slate-800 mb-2">未指定資源</h1>
        <p className="text-sm text-slate-500">請從學習庫點選資源後進入此頁。</p>
        <Link
          href="/knowledge"
          className="mt-4 px-4 py-2 rounded-full bg-emerald-500 text-white hover:bg-emerald-600"
        >
          回學習庫
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link
          href={subjectId ? `/knowledge?subjectId=${subjectId}` : '/knowledge'}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> 學習庫
        </Link>
        <button
          type="button"
          onClick={() => setShowToc((v) => !v)}
          className="lg:hidden flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <ListTree className="w-4 h-4" /> 目錄
        </button>
        <div className="ml-auto text-xs text-slate-400">
          {chapters.length > 0 ? `${chapters.length} 個章節` : ''}
        </div>
      </header>

      {/* Main */}
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-4 p-4">
        {/* Left: TOC */}
        {showToc && (
          <aside className="lg:w-64 shrink-0 lg:sticky lg:top-20 lg:self-start lg:max-h-[calc(100vh-6rem)] lg:overflow-auto bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-1">
              <ListTree className="w-4 h-4" /> 章節目錄
            </h2>
            {chapters.length === 0 ? (
              <p className="text-xs text-slate-400">（尚無章節結構）</p>
            ) : (
              <nav className="space-y-1">
                {chapters.map((c) => {
                  const isActive = currentChapter === c.anchorId;
                  return (
                    <Link
                      key={c.anchorId}
                      href={`/library/read/reading?docId=${resourceId}${subjectId ? `&subjectId=${subjectId}` : ''}&chapter=${c.anchorId}`}
                      className={`block ${c.level === 3 ? 'pl-4' : ''} text-xs py-1 px-2 rounded transition-colors ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-700 font-medium'
                          : 'text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {c.heading}
                    </Link>
                  );
                })}
              </nav>
            )}
          </aside>
        )}

        {/* Center: markdown body */}
        <main className="flex-1 min-w-0 bg-white rounded-2xl border border-slate-200 p-6">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-rose-600 text-sm">{error}</div>
          ) : (parseStatus === 'queued' || parseStatus === 'parsing') && !markdown ? (
            <div className="rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50 p-6 text-center">
              <div className="text-3xl mb-2">⏳</div>
              <h2 className="text-base font-bold text-amber-800 mb-2">multimodal Pro 解析中</h2>
              <p className="text-sm text-amber-700 leading-relaxed">
                含表格、圖片、章節結構，完整原文約 1-2 分鐘後可讀。
                <br />
                此頁每 5 秒自動更新狀態，你可以先去做其他事，稍後再回來。
              </p>
            </div>
          ) : parseStatus === 'failed' && !markdown ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center">
              <div className="text-3xl mb-2">❌</div>
              <h2 className="text-base font-bold text-rose-800 mb-2">原文解析失敗</h2>
              {parseFailureReason && (
                <p className="text-sm text-rose-700 mb-3">{parseFailureReason}</p>
              )}
              <p className="text-xs text-rose-600">你可以刪除後重新上傳，或先看下方知識節點摘要。</p>
            </div>
          ) : markdown ? (
            <>
              <article className="prose prose-slate max-w-none">
                <MathContent>{markdown}</MathContent>
              </article>
              {/* T09：當前章節讀完底部 InlinePractice */}
              {currentChapter && (
                <InlinePractice
                  resourceId={resourceId}
                  chapterHeading={chapters.find((c) => c.anchorId === currentChapter)?.heading ?? ''}
                />
              )}
            </>
          ) : (
            <div className="text-center py-12 text-sm text-slate-500">
              （尚無解析後的內容）
            </div>
          )}
        </main>

        {/* Right: chapter info + scaffolds slot */}
        <aside className="lg:w-72 shrink-0 lg:sticky lg:top-20 lg:self-start space-y-3">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-bold text-slate-700 mb-2 flex items-center gap-1">
              <BookOpen className="w-4 h-4" /> 章節資訊
            </h2>
            {currentChapter ? (
              <p className="text-xs text-slate-600">
                當前：{chapters.find((c) => c.anchorId === currentChapter)?.heading ?? currentChapter}
              </p>
            ) : (
              <p className="text-xs text-slate-400">點左側目錄進入特定章節</p>
            )}
            <div className="mt-3 text-xs text-slate-500 space-y-1">
              <div>鷹架總數：{scaffolds.length}</div>
              <div>當前章節鷹架：{chapterScaffolds.length}</div>
            </div>
          </div>

          {/* T08：當前章節 takeaway/elaborative 鷹架（retrieval-first） */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-1">
              <ChevronRight className="w-4 h-4" /> 章節重點與思考
            </h2>
            {chapterScaffolds.length === 0 ? (
              <p className="text-xs text-slate-400 italic">
                {currentChapter ? '此章節尚無學習鷹架' : '點左側目錄選擇章節'}
              </p>
            ) : (
              <div className="space-y-2 -mx-2">
                {chapterScaffolds
                  .filter((s) => s.type === 'takeaway' || s.type === 'elaborative')
                  .map((s) =>
                    s.retrieval_prompt ? (
                      <RetrievalCard
                        key={s.id}
                        scaffoldId={s.id}
                        chapterHeading={s.chapter_heading}
                        retrievalPrompt={s.retrieval_prompt}
                        content={s.content}
                      />
                    ) : (
                      <div
                        key={s.id}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-3 mx-2"
                      >
                        <span className="text-xs font-bold text-slate-500">
                          {s.type === 'elaborative' ? '💭 延伸思考' : '📌 重點'}
                        </span>
                        <p className="text-sm text-slate-700 mt-1">{s.content}</p>
                      </div>
                    ),
                  )}
                {/* strategy 類型不需檢索觸發 */}
                {chapterScaffolds
                  .filter((s) => s.type === 'strategy')
                  .map((s) => (
                    <div
                      key={s.id}
                      className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3 mx-2"
                    >
                      <span className="text-xs font-bold text-indigo-700">
                        📚 學習策略
                      </span>
                      <p className="text-sm text-slate-700 mt-1">{s.content}</p>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

