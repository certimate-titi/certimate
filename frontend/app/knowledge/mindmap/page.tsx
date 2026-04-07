'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Network, ArrowLeft } from 'lucide-react';
import { knowledgeService, subjectService } from '@/lib/api/services';
import type { KnowledgeNode, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import MindMapTree, { type MindMapNode } from '@/components/MindMapTree';

export default function FullMindMapPage() {
  const { isAuthenticated, loading: authLoading, onboardingCompleted } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSubjectId = searchParams.get('subjectId') || '';

  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState(initialSubjectId);
  const [mindMapNodes, setMindMapNodes] = useState<MindMapNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (!onboardingCompleted) { router.replace('/onboarding'); return; }

    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects);
      if (!activeSubjectId && res.subjects.length > 0) {
        setActiveSubjectId(res.subjects[0].id);
      }
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router, activeSubjectId]);

  useEffect(() => {
    if (!activeSubjectId) return;
    setLoading(true);
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    knowledgeService.getMap(targetSubjectId).then((mapRes: Record<string, unknown>) => {
      setMindMapNodes((mapRes.nodes || []) as unknown as MindMapNode[]);
      setLoading(false);
    }).catch(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSubjectId]);

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId);
  };

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <>
      {subjects.length > 0 && (
        <SubjectSwitcher
          subjects={subjects}
          activeSubjectId={activeSubjectId}
          onSwitch={setActiveSubjectId}
          onAddSubject={() => router.push('/onboarding')}
          allowAdd={false}
        />
      )}
      <div className="flex-1 flex flex-col h-[calc(100vh-64px-48px)] overflow-hidden bg-white">
        <header className="border-b border-slate-200 px-6 py-3 flex items-center gap-4 shrink-0">
          <button onClick={() => router.push('/knowledge')} className="text-slate-400 hover:text-slate-600">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-emerald-500" />
            <h1 className="text-lg font-bold text-slate-900">完整知識心智圖</h1>
          </div>
          <div className="ml-auto flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> 精熟 (&ge;80%)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> 部分 (60-79%)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" /> 需加強 (&lt;60%)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300" /> 未測驗</span>
          </div>
        </header>

        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : mindMapNodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-400">
              <div className="text-center">
                <Network className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                <p>尚無心智圖節點</p>
                <p className="text-xs mt-1">上傳教材後系統會自動生成</p>
              </div>
            </div>
          ) : (
            <MindMapTree
              nodes={mindMapNodes}
              selectedNodeId={selectedNodeId}
              onNodeClick={handleNodeClick}
            />
          )}
        </div>
      </div>
    </>
  );
}
