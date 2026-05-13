/**
 * @file 路由 `/notes` — 我的筆記獨立頁。
 *
 * 從 /knowledge 右側 tab 移出，作為全站頂層筆記中心；
 * 整合 IntegratedNotebook（不綁 nodeId），以科目為單位列出所有筆記。
 */
'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { subjectService } from '@/lib/api/services';
import type { UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import IntegratedNotebook from '@/components/IntegratedNotebook';

export default function NotesPageWrapper() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <NotesPage />
    </Suspense>
  );
}

function NotesPage() {
  const { isAuthenticated, loading: authLoading, onboardingCompleted, isProPlus, subscriptionTier } = useAuth();
  const router = useRouter();

  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');
  const [loadingSubjects, setLoadingSubjects] = useState(true);

  const isPro = isProPlus || subscriptionTier === 'PRO_199';

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
      .then((res) => {
        const list = res.subjects ?? [];
        setSubjects(list);
        if (list.length > 0 && !activeSubjectId) {
          setActiveSubjectId(list[0].id);
        }
      })
      .catch(() => {/* silently ignore */})
      .finally(() => setLoadingSubjects(false));
  }, [isAuthenticated]); // eslint-disable-line react-hooks/exhaustive-deps

  if (authLoading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const activeSubject = subjects.find((s) => s.id === activeSubjectId);
  const subjectIdForApi = activeSubject?.subjectId || activeSubjectId || null;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-900">我的筆記</h1>
            <p className="text-sm text-slate-500 mt-1">跨節點筆記、AI 對話標記與鷹架深讀整合檢視</p>
          </div>
          {/* Subject Switcher */}
          {subjects.length > 0 && (
            <SubjectSwitcher
              subjects={subjects}
              activeSubjectId={activeSubjectId}
              onSwitch={setActiveSubjectId}
              onAddSubject={() => router.push('/onboarding')}
            />
          )}
        </div>

        {/* Content */}
        {loadingSubjects ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : subjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
            <p className="text-slate-500 text-sm">尚未加入任何科目</p>
            <button
              onClick={() => router.push('/onboarding')}
              className="rounded-full bg-emerald-500 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-600 transition-colors"
            >
              前往新增科目
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <IntegratedNotebook
              nodeId={null}
              fallbackResourceId={null}
              nodeLabel={null}
              subjectId={subjectIdForApi}
              isPro={isPro}
              onUpgradeClick={() => router.push('/account')}
            />
          </div>
        )}
      </div>
    </div>
  );
}
