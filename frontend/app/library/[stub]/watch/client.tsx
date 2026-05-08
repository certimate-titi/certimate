'use client';

/**
 * 影片觀看頁 — Sprint 2.5 T21
 *
 * 路徑：/library/view/watch?docId={uuid}&subjectId={uuid}&t={sec}
 *
 * 三區塊：
 * - 上：影片播放器（HTML5 <video> 或 YouTube embed）
 * - 右：時間戳重點清單（VideoTimestampJump 列表，點擊 seek 影片）
 *   - takeaway 摺疊式 RetrievalCard（同 reading 頁）
 *   - pitfall 直接展開 PitfallAlert
 * - 下：相關章節資訊
 *
 * 不強制暫停（per CEO Q4 決議），用戶自律。
 */

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, Clock } from 'lucide-react';

import PitfallAlert from '@/components/PitfallAlert';
import RetrievalCard from '@/components/RetrievalCard';
import VideoTimestampJump from '@/components/VideoTimestampJump';
import { resourceParseService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import type { ScaffoldEntry } from '@/hooks/use-reading-page-state';

interface ResourceMeta {
  resource_id: string;
  filename?: string | null;
  status?: string | null;
  parse_status?: string | null;
  markdown?: string;
  youtube_url?: string | null;
  gcs_path?: string | null;
  // duration 由前端 video 載入後取得
}

export default function WatchClient() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const resourceId = searchParams.get('docId') ?? '';
  const subjectId = searchParams.get('subjectId') ?? '';
  const targetSec = parseInt(searchParams.get('t') ?? '0', 10) || 0;

  const [resource, setResource] = useState<ResourceMeta | null>(null);
  const [scaffolds, setScaffolds] = useState<ScaffoldEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentSec, setCurrentSec] = useState<number>(0);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Fetch resource + scaffolds
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
      setResource((md as ResourceMeta) ?? null);
      const sc = (parsed as unknown as { scaffolds?: ScaffoldEntry[] })?.scaffolds ?? [];
      setScaffolds(sc);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [resourceId]);

  // Seek video on initial mount when ?t= present
  useEffect(() => {
    if (!videoRef.current || targetSec <= 0) return;
    const handler = () => { if (videoRef.current) videoRef.current.currentTime = targetSec; };
    videoRef.current.addEventListener('loadedmetadata', handler, { once: true });
    return () => videoRef.current?.removeEventListener('loadedmetadata', handler);
  }, [targetSec]);

  const handleJumpTo = (sec: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = sec;
      void videoRef.current.play();
    }
    setCurrentSec(sec);
  };

  // Filter scaffolds with timestamps (takeaway / pitfall)
  const timestampedScaffolds = useMemo(
    () => scaffolds.filter(
      (s) => s.type === 'takeaway' || s.type === 'pitfall' || s.type === 'elaborative',
    ),
    [scaffolds],
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
        <h1 className="text-xl font-bold text-slate-800 mb-2">未指定影片</h1>
        <Link href="/knowledge" className="mt-4 px-4 py-2 rounded-full bg-emerald-500 text-white">
          回學習庫
        </Link>
      </div>
    );
  }

  // Derive video src（HTML5 video）— 假設 gcs_path 已是公開 URL 或前端 fallback API
  const videoSrc = resource?.gcs_path?.startsWith('http')
    ? resource.gcs_path
    : resource?.gcs_path
    ? `https://storage.googleapis.com/${resource.gcs_path.replace(/^gs:\/\//, '')}`
    : '';
  const youtubeUrl = resource?.youtube_url ?? '';

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link
          href={subjectId ? `/knowledge?subjectId=${subjectId}` : '/knowledge'}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> 學習庫
        </Link>
        <div className="text-sm font-medium text-slate-700 truncate flex-1">
          {resource?.filename ?? '影片'}
        </div>
      </header>

      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-4 p-4">
        {/* 左：影片播放器 */}
        <main className="flex-1 min-w-0">
          {loading ? (
            <div className="aspect-video bg-slate-100 rounded-2xl flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : youtubeUrl ? (
            <div className="aspect-video rounded-2xl overflow-hidden bg-black">
              <iframe
                src={`https://www.youtube.com/embed/${extractYoutubeId(youtubeUrl)}?start=${targetSec}`}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                title="YouTube 影片"
              />
            </div>
          ) : videoSrc ? (
            <video
              ref={videoRef}
              src={videoSrc}
              controls
              className="w-full aspect-video rounded-2xl bg-black"
              onTimeUpdate={(e) => setCurrentSec(Math.floor((e.target as HTMLVideoElement).currentTime))}
            >
              你的瀏覽器不支援 HTML5 video。
            </video>
          ) : (
            <div className="aspect-video bg-slate-100 rounded-2xl flex items-center justify-center text-sm text-slate-500">
              無法載入影片來源
            </div>
          )}

          {/* 影片下方：當前秒數對應的章節資訊（簡單呈現）*/}
          <div className="mt-3 px-2 text-xs text-slate-500 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" />
            目前位置：{formatTime(currentSec)}
          </div>
        </main>

        {/* 右：時間戳重點清單 */}
        <aside className="lg:w-80 shrink-0 space-y-3">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-bold text-slate-700 mb-3">時間戳重點</h2>
            {timestampedScaffolds.length === 0 ? (
              <p className="text-xs text-slate-400 italic">
                {loading ? '載入中⋯' : '此影片尚無時間戳重點'}
              </p>
            ) : (
              <VideoTimestampJump
                scaffolds={timestampedScaffolds}
                currentSec={currentSec}
                onJumpTo={handleJumpTo}
              />
            )}
          </div>

          {/* 詳細鷹架（含 RetrievalCard / PitfallAlert）*/}
          {timestampedScaffolds.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <h2 className="text-sm font-bold text-slate-700 mb-3">章節重點與思考</h2>
              <div className="space-y-2 -mx-2">
                {timestampedScaffolds
                  .filter((s) => s.type === 'pitfall')
                  .map((s) => (
                    <PitfallAlert
                      key={s.id}
                      scaffoldId={s.id}
                      chapterHeading={s.chapter_heading}
                      content={s.content}
                    />
                  ))}
                {timestampedScaffolds
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
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function extractYoutubeId(url: string): string {
  // 支援 youtu.be / youtube.com/watch?v= / youtube.com/embed/
  const m =
    /(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([\w-]{11})/.exec(url);
  return m?.[1] ?? '';
}
