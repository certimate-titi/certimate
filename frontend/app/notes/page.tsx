/**
 * @file 路由 `/notes` — 我的筆記中心（Timeline + 左側分類樹）。
 *
 * Layout：左 sidebar（分類樹 240px）+ 右 main（unified timeline）
 * Mobile < 768px：sidebar 改為 drawer（漢堡按鈕開啟）
 */
'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, Menu, Plus, X } from 'lucide-react';
import { subjectService, userNoteService } from '@/lib/api/services';
import type { UserSubject } from '@/types';
import type { UserNote } from '@/types/api';
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

  // ── New Note Form state ───────────────────────────────────────────────────
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [refreshSignal, setRefreshSignal] = useState(0);
  const newContentRef = useRef<HTMLTextAreaElement>(null);

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
  // 注意：/subjects/mine 回的 record 結構為 {id, name, ...}，無 subjectId 欄位。
  // type UserSubject 期待 subjectId 與後端 schema 落差，fallback 到 id 才能正常 query。
  const activeUserSubject = subjects.find((s) => s.id === filter.activeUserSubjectId);
  const subjectIdForApi = activeUserSubject?.subjectId ?? activeUserSubject?.id ?? null;

  const handleCountsUpdate = useCallback((counts: { note: number; annotation: number; scaffold: number }) => {
    setKindCounts((prev) => {
      const key = filter.activeUserSubjectId;
      if (!key) return prev;
      const existing = prev[key];
      if (existing?.note === counts.note && existing?.annotation === counts.annotation && existing?.scaffold === counts.scaffold) return prev;
      return { ...prev, [key]: counts };
    });
  }, [filter.activeUserSubjectId]);

  function handleOpenCreate() {
    setNewTitle('');
    setNewContent('');
    setCreateError(null);
    setCreating(true);
    // 等 DOM 渲染後 focus textarea
    setTimeout(() => newContentRef.current?.focus(), 50);
  }

  async function handleSaveNewNote() {
    if (!newContent.trim()) return;
    // subject_id：優先 active，否則第一個 enrolled
    const targetSubjectId =
      subjectIdForApi ??
      (subjects.length > 0 ? subjects[0].subjectId : null);
    if (!targetSubjectId) {
      setCreateError('請先選擇科目');
      return;
    }
    setCreateSaving(true);
    setCreateError(null);
    try {
      await userNoteService.create({
        subject_id: targetSubjectId,
        title: newTitle.trim() || null,
        content: newContent.trim(),
      });
      setCreating(false);
      setNewTitle('');
      setNewContent('');
      // 通知 NotesTimeline 重新 fetch
      setRefreshSignal((s) => s + 1);
    } catch (e) {
      const err = e as { message?: string };
      setCreateError(err.message || '儲存失敗，請稍後再試');
    } finally {
      setCreateSaving(false);
    }
  }

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

            <div className="flex-1 overflow-hidden flex flex-col">
              {/* Inline New Note Form */}
              {creating && notesView === 'timeline' && (
                <div className="mx-4 mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4 shadow-sm shrink-0">
                  <div className="flex items-center gap-2 mb-3">
                    <Plus className="h-4 w-4 text-emerald-600" />
                    <span className="text-sm font-semibold text-emerald-700">新增自由筆記</span>
                    <button
                      type="button"
                      onClick={() => setCreating(false)}
                      className="ml-auto p-1 rounded-lg hover:bg-emerald-100 text-emerald-500 transition-colors"
                      aria-label="關閉"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="標題（選填）"
                      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-emerald-300 bg-white"
                    />
                    <textarea
                      ref={newContentRef}
                      value={newContent}
                      onChange={(e) => setNewContent(e.target.value)}
                      rows={4}
                      placeholder="筆記內容（必填）"
                      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-emerald-300 resize-none bg-white"
                    />
                    <p className="text-[10px] text-slate-400 leading-relaxed">
                      💡 在內容中打 <code className="bg-slate-100 px-1 py-0.5 rounded text-emerald-700">#標籤</code> 即可標記重點（例：<code className="bg-slate-100 px-1 py-0.5 rounded text-emerald-700">#深度學習</code> <code className="bg-slate-100 px-1 py-0.5 rounded text-emerald-700">#應用</code>），標籤自動出現在「🕸️ 標籤圖譜」並連結 AI 對話 / 鷹架深讀同名 tag
                    </p>
                    {createError && (
                      <p className="text-xs text-rose-500">{createError}</p>
                    )}
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setCreating(false)}
                        className="text-xs px-3 py-1 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
                      >
                        取消
                      </button>
                      <button
                        type="button"
                        disabled={!newContent.trim() || createSaving}
                        onClick={handleSaveNewNote}
                        className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-500 text-white font-semibold hover:bg-emerald-600 disabled:opacity-50 transition-colors"
                      >
                        <Check className="h-3 w-3" />
                        {createSaving ? '儲存中...' : '儲存筆記'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

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
                  onCreateRequest={handleOpenCreate}
                  refreshSignal={refreshSignal}
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
