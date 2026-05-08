'use client';

/**
 * 概念中心頁 — Sprint 4 T39
 *
 * 路徑：/library/concept/concept?subjectId={uuid}&q={concept_keyword}
 *
 * 顯示某個概念在所有資源中的對照：
 * - PDF 教材觀點：scaffold takeaway 含關鍵字的章節
 * - 影片觀點：含時間戳的章節（K-06-video）
 * - 考古題觀點：包含關鍵字的 question
 * - 跨資源 pitfall 彙整：相同概念的迷思警示
 *
 * Sprint 4 簡化版：
 * - client-side 從現有 /resources + /parsed 撈 + filter
 * - Sprint 5 P4 評估：擴後端 concept-center endpoint + voyage embedding 對齊
 */

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, Search, FileText, Film, HelpCircle, AlertTriangle } from 'lucide-react';

import { resourceParseService, documentService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

interface ConceptHit {
  resourceId: string;
  resourceName: string;
  resourceType: 'pdf' | 'video' | 'quiz' | 'other';
  chapterHeading: string | null;
  scaffoldType: string;
  content: string;
}

export default function ConceptClient() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const subjectId = searchParams.get('subjectId') ?? '';
  const initialQ = searchParams.get('q') ?? '';

  const [query, setQuery] = useState(initialQ);
  const [results, setResults] = useState<ConceptHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (initialQ) void runSearch(initialQ);
  }, [initialQ]);

  const runSearch = async (q: string) => {
    if (!q.trim() || !subjectId) return;
    setLoading(true);
    setSearched(true);
    try {
      // 取所有資源（簡化版：用全用戶清單，filter subject 在客戶端）
      const docsResp = await documentService.list().catch(() => null);
      const allDocs = (docsResp?.documents ?? []) as Array<{ id: string; title: string; sourceType?: string; subjectId?: string }>;
      const docs = subjectId ? allDocs.filter((d) => d.subjectId === subjectId) : allDocs;
      const hits: ConceptHit[] = [];
      // 對每份資源 fetch /parsed 並 filter scaffolds
      const limited = docs.slice(0, 20);
      const parsedList = await Promise.all(
        limited.map((d) =>
          resourceParseService.getParsed(d.id).catch(() => null).then((p) => ({ d, p })),
        ),
      );
      for (const { d, p } of parsedList) {
        const scaffolds = (p as unknown as { scaffolds?: Array<{ chapter_heading: string|null; type: string; content: string }> })?.scaffolds ?? [];
        for (const s of scaffolds) {
          if (s.content.includes(q) || (s.chapter_heading || '').includes(q)) {
            hits.push({
              resourceId: d.id,
              resourceName: d.title,
              resourceType: resolveType(d.sourceType),
              chapterHeading: s.chapter_heading,
              scaffoldType: s.type,
              content: s.content,
            });
          }
        }
      }
      setResults(hits);
    } finally {
      setLoading(false);
    }
  };

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

  // group hits by source type
  const byType = {
    pdf: results.filter((r) => r.resourceType === 'pdf'),
    video: results.filter((r) => r.resourceType === 'video'),
    quiz: results.filter((r) => r.resourceType === 'quiz'),
    pitfall: results.filter((r) => r.scaffoldType === 'pitfall'),
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link
          href={subjectId ? `/knowledge?subjectId=${subjectId}` : '/knowledge'}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> 學習庫
        </Link>
        <div className="text-sm font-medium text-slate-700">概念中心</div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* 搜尋列 */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') void runSearch(query); }}
              placeholder="搜尋概念（如：No-code、機器學習、AI 治理）"
              className="w-full pl-10 pr-4 py-3 rounded-2xl border border-slate-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 text-sm"
            />
          </div>
          <p className="text-xs text-slate-500 mt-2">
            搜尋後會聚合所有資源中提及此概念的鷹架內容（包含 PDF / 影片 / 考古題 / 迷思）
          </p>
        </div>

        {!subjectId && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center text-sm text-slate-500">
            請先指定科目（?subjectId=...）
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && searched && results.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center text-sm text-slate-500">
            找不到「{query}」的相關鷹架內容
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="space-y-6">
            <p className="text-xs text-slate-500">
              找到 {results.length} 筆關於「{query}」的內容，跨 {new Set(results.map((r) => r.resourceId)).size} 份資源
            </p>

            {byType.pitfall.length > 0 && (
              <ConceptSection
                icon={<AlertTriangle className="w-4 h-4 text-rose-600" />}
                title={`⚠️ 跨資源迷思彙整（${byType.pitfall.length} 條）`}
                hits={byType.pitfall}
                color="rose"
              />
            )}

            {byType.pdf.length > 0 && (
              <ConceptSection
                icon={<FileText className="w-4 h-4 text-emerald-600" />}
                title={`📄 PDF 教材觀點（${byType.pdf.length} 筆）`}
                hits={byType.pdf}
                color="emerald"
              />
            )}

            {byType.video.length > 0 && (
              <ConceptSection
                icon={<Film className="w-4 h-4 text-blue-600" />}
                title={`🎬 影片觀點（${byType.video.length} 筆）`}
                hits={byType.video}
                color="blue"
              />
            )}

            {byType.quiz.length > 0 && (
              <ConceptSection
                icon={<HelpCircle className="w-4 h-4 text-slate-700" />}
                title={`❓ 考古題（${byType.quiz.length} 筆）`}
                hits={byType.quiz}
                color="slate"
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function ConceptSection({
  icon, title, hits, color,
}: {
  icon: React.ReactNode;
  title: string;
  hits: ConceptHit[];
  color: 'emerald' | 'blue' | 'rose' | 'slate';
}) {
  const colorClasses = {
    emerald: 'border-emerald-200 bg-emerald-50/30',
    blue: 'border-blue-200 bg-blue-50/30',
    rose: 'border-rose-200 bg-rose-50/40',
    slate: 'border-slate-200 bg-slate-50/30',
  };
  return (
    <section className={`rounded-2xl border ${colorClasses[color]} p-4`}>
      <h2 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
        {icon} {title}
      </h2>
      <div className="space-y-2">
        {hits.map((h, i) => (
          <Link
            key={`${h.resourceId}-${i}`}
            href={`/library/read/reading?docId=${h.resourceId}`}
            className="block bg-white rounded-xl border border-slate-200 p-3 hover:border-slate-300"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-slate-500">{h.resourceName}</span>
              {h.chapterHeading && (
                <span className="text-xs text-slate-400">· {h.chapterHeading}</span>
              )}
            </div>
            <p className="text-sm text-slate-700 line-clamp-3">{h.content}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

function resolveType(sourceType?: string): ConceptHit['resourceType'] {
  if (!sourceType) return 'pdf';
  const t = sourceType.toLowerCase();
  if (t.includes('video') || t.includes('youtube')) return 'video';
  if (t.includes('quiz') || t.includes('historical_exam')) return 'quiz';
  return 'pdf';
}
