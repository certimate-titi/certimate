'use client';

/**
 * PPT 簡報 viewer — Sprint 3 T27
 *
 * 路徑：/library/slides/slides?docId={uuid}&subjectId={uuid}&n={slideNum}
 *
 * 兩種模式：
 * 1. 網格模式（預設）：所有投影片縮圖 4 列展示
 * 2. 全屏模式（?n=N）：單張投影片放大 + 下方 slide_retrieval card
 *
 * Sprint 3 簡化：縮圖直接用 markdown 中段落分割顯示文字摘要（避免實際 PPT
 * 縮圖渲染複雜）。Sprint 4+ 評估接 webp 縮圖。
 */

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ChevronLeft, ChevronRight, Grid3x3 } from 'lucide-react';

import RetrievalCard from '@/components/RetrievalCard';
import PitfallAlert from '@/components/PitfallAlert';
import MathContent from '@/components/MathContent';
import { resourceParseService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import type { ScaffoldEntry } from '@/hooks/use-reading-page-state';

interface SlideEntry {
  num: number;
  title: string;
  body: string;
}

export default function SlidesClient() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const resourceId = searchParams.get('docId') ?? '';
  const subjectId = searchParams.get('subjectId') ?? '';
  const currentSlideNum = parseInt(searchParams.get('n') ?? '0', 10) || 0;

  const [markdown, setMarkdown] = useState<string>('');
  const [scaffolds, setScaffolds] = useState<ScaffoldEntry[]>([]);
  const [filename, setFilename] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!resourceId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all([
      resourceParseService.getMarkdown(resourceId).catch(() => null),
      resourceParseService.getParsed(resourceId).catch(() => null),
    ]).then(([md, parsed]) => {
      if (cancelled) return;
      const meta = md as { markdown?: string; filename?: string } | null;
      setMarkdown(meta?.markdown ?? '');
      setFilename(meta?.filename ?? '簡報');
      setScaffolds((parsed as unknown as { scaffolds?: ScaffoldEntry[] })?.scaffolds ?? []);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [resourceId]);

  // 從 markdown 切出投影片（每張投影片由 [Slide N] anchor 開始）
  const slides = useMemo(() => extractSlides(markdown), [markdown]);
  const currentSlide = slides.find((s) => s.num === currentSlideNum);
  const currentScaffolds = useMemo(
    () => scaffolds.filter((s) => s.chapter_heading?.startsWith(`Slide ${currentSlideNum} `)),
    [scaffolds, currentSlideNum],
  );

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
        <h1 className="text-xl font-bold text-slate-800 mb-2">未指定簡報</h1>
        <Link href="/knowledge" className="mt-4 px-4 py-2 rounded-full bg-emerald-500 text-white">
          回學習庫
        </Link>
      </div>
    );
  }

  // 全屏單張模式
  if (currentSlideNum > 0 && currentSlide) {
    return (
      <SlideFullscreen
        slide={currentSlide}
        totalCount={slides.length}
        resourceId={resourceId}
        subjectId={subjectId}
        scaffolds={currentScaffolds}
        filename={filename}
      />
    );
  }

  // 網格模式
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link
          href={subjectId ? `/knowledge?subjectId=${subjectId}` : '/knowledge'}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> 學習庫
        </Link>
        <div className="text-sm font-medium text-slate-700 truncate flex-1">{filename}</div>
        <div className="text-xs text-slate-400 flex items-center gap-1">
          <Grid3x3 className="w-3.5 h-3.5" /> {slides.length} 張
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : slides.length === 0 ? (
          <div className="rounded-2xl bg-white border border-slate-200 p-6 text-center text-sm text-slate-500">
            此簡報尚未解析出投影片結構（K-06-slides v1+ 才產出）。
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {slides.map((slide) => (
              <Link
                key={slide.num}
                href={`/library/slides/slides?docId=${resourceId}${subjectId ? `&subjectId=${subjectId}` : ''}&n=${slide.num}`}
                className="bg-white rounded-2xl border border-slate-200 p-4 hover:border-emerald-300 hover:shadow-md transition-all"
              >
                <p className="text-xs font-bold text-slate-400 mb-1">Slide {slide.num}</p>
                <h3 className="text-sm font-bold text-slate-800 mb-2 line-clamp-2">{slide.title}</h3>
                <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">{slide.body}</p>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function SlideFullscreen({
  slide, totalCount, resourceId, subjectId, scaffolds, filename,
}: {
  slide: SlideEntry;
  totalCount: number;
  resourceId: string;
  subjectId: string;
  scaffolds: ScaffoldEntry[];
  filename: string;
}) {
  const prevHref =
    slide.num > 1
      ? `/library/slides/slides?docId=${resourceId}${subjectId ? `&subjectId=${subjectId}` : ''}&n=${slide.num - 1}`
      : null;
  const nextHref =
    slide.num < totalCount
      ? `/library/slides/slides?docId=${resourceId}${subjectId ? `&subjectId=${subjectId}` : ''}&n=${slide.num + 1}`
      : null;
  const gridHref =
    `/library/slides/slides?docId=${resourceId}${subjectId ? `&subjectId=${subjectId}` : ''}`;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link href={gridHref} className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900">
          <Grid3x3 className="w-4 h-4" /> 網格
        </Link>
        <div className="text-sm font-medium text-slate-700 truncate flex-1">{filename}</div>
        <div className="text-xs text-slate-500">{slide.num} / {totalCount}</div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-4">
        <article className="bg-white rounded-2xl border border-slate-200 p-8 min-h-[400px]">
          <p className="text-sm font-bold text-slate-400 mb-2">Slide {slide.num}</p>
          <h2 className="text-2xl font-bold text-slate-900 mb-4">{slide.title}</h2>
          <div className="text-slate-700 leading-relaxed whitespace-pre-line">{slide.body}</div>
        </article>

        {/* 投影片下方鷹架：slide_retrieval (type=takeaway) + pitfall */}
        {scaffolds.length > 0 && (
          <div className="space-y-2">
            {scaffolds
              .filter((s) => s.type === 'pitfall')
              .map((s) => (
                <PitfallAlert
                  key={s.id}
                  scaffoldId={s.id}
                  chapterHeading={s.chapter_heading}
                  content={s.content}
                />
              ))}
            {scaffolds
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
                    className="rounded-xl border border-slate-200 bg-slate-50 p-3"
                  >
                    <span className="text-xs font-bold text-slate-500">
                      {s.type === 'elaborative' ? '💭 重述故事線' : '📌 重點'}
                    </span>
                    <div className="text-sm text-slate-700 mt-1"><MathContent>{s.content}</MathContent></div>
                  </div>
                ),
              )}
          </div>
        )}

        {/* 翻頁 */}
        <div className="flex items-center justify-between gap-2">
          {prevHref ? (
            <Link
              href={prevHref}
              className="flex items-center gap-1 px-4 py-2 rounded-full bg-white border border-slate-200 text-sm text-slate-700 hover:border-slate-300"
            >
              <ChevronLeft className="w-4 h-4" /> 上一張
            </Link>
          ) : <div />}
          {nextHref ? (
            <Link
              href={nextHref}
              className="flex items-center gap-1 px-4 py-2 rounded-full bg-emerald-500 text-white text-sm hover:bg-emerald-600"
            >
              下一張 <ChevronRight className="w-4 h-4" />
            </Link>
          ) : <div />}
        </div>
      </main>
    </div>
  );
}

/**
 * 從 markdown 切出投影片清單。
 *
 * K-06-slides 規範 markdown 含 [Slide N] anchor + ## 標題。
 * Fallback：若無 anchor，把每個 ## 視為一張投影片。
 */
function extractSlides(md: string): SlideEntry[] {
  if (!md) return [];
  const slides: SlideEntry[] = [];
  // 用 [Slide N] 切
  const parts = md.split(/\[Slide\s+(\d+)\]/);
  if (parts.length > 2) {
    // [text][num][text][num]...
    for (let i = 1; i < parts.length; i += 2) {
      const num = parseInt(parts[i], 10);
      const body = (parts[i + 1] || '').trim();
      const titleMatch = /^##?\s+(.+?)\s*$/m.exec(body);
      const title = titleMatch ? titleMatch[1].trim() : `投影片 ${num}`;
      const bodyText = body.replace(/^##?\s+.+\s*$/m, '').trim().slice(0, 500);
      slides.push({ num, title, body: bodyText });
    }
    return slides;
  }
  // Fallback: split by ## headings
  const lines = md.split('\n');
  let current: SlideEntry | null = null;
  let counter = 1;
  for (const line of lines) {
    const m = /^##\s+(.+?)\s*$/.exec(line);
    if (m) {
      if (current) slides.push(current);
      current = { num: counter++, title: m[1].trim(), body: '' };
    } else if (current) {
      current.body += line + '\n';
    }
  }
  if (current) slides.push(current);
  return slides;
}
