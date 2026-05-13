/**
 * @file 路由 `/notes` — 我的筆記中心（Timeline + 左側分類樹）。
 *
 * Layout：左 sidebar（分類樹 240px）+ 右 main（unified timeline）
 * Mobile < 768px：sidebar 改為 drawer（漢堡按鈕開啟）
 */
'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { subjectService } from '@/lib/api/services';
import type { UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import NotesClassifyTree from '@/components/NotesClassifyTree';
import NotesTimeline from '@/components/NotesTimeline';
import NotesTagGraph from '@/components/NotesTagGraph';
import { useNotesFilter } from '@/hooks/use-notes-filter';
import type { NoteKind } from '@/hooks/use-notes-filter';

export default function NotesPageWrapper() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center min-h-screen">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <NotesPage />
    </Suspense>
  );
}

function NotesPage() {
  const { isAuthenticated, loading: authLoading, onboardingCompleted, isPro } = useAuth();
  const router = useRouter();

  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [kindCounts, setKindCounts] = useState<Record<string, { note: number; annotation: number; scaffold: number }>>({});
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [notesView, setNotesView] = useState<'timeline' | 'graph'>('timeline');

  // Auth guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (!onboardingCompleted) { router.replace('/onboarding'); return; }
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load subjects
  useEffect(() => {
    if (!isAuthenticated) return;
    subjectService.getUserSubjects()
      .then((res) => { setSubjects(res.subjects ?? []); })
      .catch(() => { /* silently ignore */ })
      .finally(() => setLoadingSubjects(false));
  }, [isAuthenticated]);

  // subjects shape for useNotesFilter
  const subjectsForFilter = subjects.map((s) => ({
    id: s.id,
    subjectId: s.subjectId,
    subjectName: s.subjectName,
  }));

  const filter = useNotesFilter(subjectsForFilter);

  // subjectId (後端 UUID) for API
  const activeUserSubject = subjects.find((s) => s.id === filter.activeUserSubjectId);
  const subjectIdForApi = activeUserSubject?.subjectId ?? null;

  const handleCountsUpdate = useCallback((counts: { note: number; annotation: number; scaffold: number }) => {
    setKindCounts((prev) => {
      const key = filter.activeUserSubjectId;
      if (!key) return prev;
      const existing = prev[key];
      if (existing?.note === counts.note && existing?.annotation === counts.annotation && existing?.scaffold === counts.scaffold) return prev;
      return { ...prev, [key]: counts };
    });
  }, [filter.activeUserSubjectId]);

  if (authLoading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const sidebarContent = (
    <NotesClassifyTree
      subjects={subjectsForFilter}
      filterState={filter}
      filterActions={filter}
      counts={kindCounts}
    />
  );

  return (
    <div className="flex h-[calc(100vh-64px)] bg-slate-50 overflow-hidden">
      {/* ── Desktop sidebar ─────────────────────────────────────── */}
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-slate-200 overflow-hidden">
        {sidebarContent}
      </aside>

      {/* ── Mobile drawer backdrop ───────────────────────────────── */}
      {drawerOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={() => setDrawerOpen(false)}
        />
      )}

      {/* ── Mobile drawer ────────────────────────────────────────── */}
      <aside
        className={`fixed top-16 left-0 bottom-0 w-72 z-50 flex flex-col bg-white shadow-xl transition-transform duration-200 md:hidden ${
          drawerOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <span className="text-sm font-semibold text-slate-700">分類</span>
          <button
            type="button"
            onClick={() => setDrawerOpen(false)}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {sidebarContent}
        </div>
      </aside>

      {/* ── Main area ────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-slate-200 shrink-0">
          {/* Hamburger — mobile only */}
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="md:hidden p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
            aria-label="開啟分類選單"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-tight">我的筆記</h1>
            <p className="text-xs text-slate-500">Timeline · 三合一筆記中心</p>
          </div>
          {/* View toggle — desktop */}
          <div className="ml-auto hidden md:flex items-center gap-1 p-1 bg-slate-100 rounded-xl">
            <button
              type="button"
              onClick={() => setNotesView('timeline')}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                notesView === 'timeline'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              📋 Timeline
            </button>
            <button
              type="button"
              onClick={() => setNotesView('graph')}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                notesView === 'graph'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              🕸️ 標籤圖譜
            </button>
          </div>
        </div>

        {/* Loading state */}
        {loadingSubjects ? (
          <div className="flex items-center justify-center flex-1">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : subjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center flex-1 gap-3 text-center px-4">
            <p className="text-slate-500 text-sm">尚未加入任何科目</p>
            <button
              onClick={() => router.push('/onboarding')}
              className="rounded-full bg-emerald-500 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-600 transition-colors"
            >
              前往新增科目
            </button>
          </div>
        ) : (
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Mobile view toggle */}
            <div className="md:hidden flex items-center gap-1 p-2 bg-white border-b border-slate-200">
              <button
                type="button"
                onClick={() => setNotesView('timeline')}
                className={`flex-1 text-xs py-1.5 rounded-lg font-medium transition-colors ${
                  notesView === 'timeline' ? 'bg-slate-100 text-slate-900' : 'text-slate-500'
                }`}
              >
                📋 Timeline
              </button>
              <button
                type="button"
                onClick={() => setNotesView('graph')}
                className={`flex-1 text-xs py-1.5 rounded-lg font-medium transition-colors ${
                  notesView === 'graph' ? 'bg-slate-100 text-slate-900' : 'text-slate-500'
                }`}
              >
                🕸️ 標籤圖譜
              </button>
            </div>

            {/* Mobile active filter chip */}
            <div className="md:hidden">
              {(filter.kindFilter || filter.searchQuery.trim()) && (
                <div className="flex flex-wrap gap-1.5 px-4 py-2 bg-white border-b border-slate-200">
                  {filter.kindFilter && (
                    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border bg-emerald-50 text-emerald-700 border-emerald-200">
                      {filter.kindFilter}
                      <button type="button" onClick={() => filter.setKindFilter(null)}>
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                  {filter.searchQuery.trim() && (
                    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border bg-slate-50 text-slate-700 border-slate-200">
                      「{filter.searchQuery}」
                      <button type="button" onClick={filter.resetFilters}>
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="flex-1 overflow-hidden">
              {notesView === 'timeline' ? (
                <NotesTimeline
                  subjectId={subjectIdForApi}
                  kindFilter={filter.kindFilter}
                  searchQuery={filter.searchQuery}
                  sortOrder={filter.sortOrder}
                  onSortChange={filter.setSortOrder}
                  onKindFilterChange={(kind: NoteKind | null) => filter.setKindFilter(kind)}
                  onResetFilters={filter.resetFilters}
                  onCountsUpdate={handleCountsUpdate}
                  isPro={isPro}
                  onUpgradeClick={() => router.push('/account')}
                  activeTag={activeTag}
                  onTagFilterChange={setActiveTag}
                />
              ) : (
                <NotesTagGraph
                  subjectId={subjectIdForApi}
                  activeTag={activeTag}
                  onTagClick={(tag) => {
                    setActiveTag(tag);
                    setNotesView('timeline');
                  }}
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
