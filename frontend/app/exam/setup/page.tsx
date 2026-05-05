/**
 * @file 路由 `/exam/setup` — 考試設定頁。
 *
 * 讓使用者選擇科目、知識節點、題型、題數與難度，並建立模擬考；
 * 建立成功後導向 `/exam/workspace`。包含訂閱方案題數上限檢查、
 * 中斷考試恢復與向量庫知識點載入動畫。
 */
'use client';

import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2, FileText, Youtube, BrainCircuit, Play, Lock, ChevronDown, Sparkles, RotateCcw, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import { documentService, examService, subjectService, knowledgeService, resourceParseService } from '@/lib/api/services';
import { apiClient } from '@/lib/api/client';
import type { Document, QuestionType, UserSubject, SubscriptionTier } from '@/types';
import QuotaBadge from '@/components/QuotaBadge';
import { useQuotaGuard, invalidateQuotaCache } from '@/hooks/use-quota';

interface SystemNode {
  id: string;
  name: string;
  availableQuestions: number;
}
import ExamLoadingOverlay from '@/components/ExamLoadingOverlay';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import { useAuth } from '@/lib/auth-context';

const QUESTION_COUNTS = [10, 20, 50, 100] as const;

const TIER_QUESTION_LIMITS: Record<SubscriptionTier, { max: number; upgradeMessage: string | null }> = {
  FREE: { max: 10, upgradeMessage: 'FREE 方案每次測驗最多 10 題，升級 PRO 最多可出 50 題' },
  PRO_199: { max: 50, upgradeMessage: 'PRO 方案每次測驗最多 50 題，升級 PRO_PLUS 最多可出 100 題' },
  PRO_PLUS_399: { max: 100, upgradeMessage: 'PRO_PLUS 方案每次測驗最多 100 題，升級 ULTRA 無題數上限' },
  ULTRA_1599: { max: Infinity, upgradeMessage: null },
  EDU: { max: 50, upgradeMessage: 'EDU 方案每次測驗最多 50 題' },
};

const LOADING_STAGES = [
  { label: '正在從向量庫提取知識點...', progress: 10, duration: 1500 },
  { label: 'AI 正在分析考點與出題比例...', progress: 30, duration: 2000 },
  { label: 'AI 教練正在出題...', progress: 50, duration: 2500 },
  { label: 'AI 教練正在設計考題陷阱與詳解...', progress: 75, duration: 2000 },
  { label: '校對格式與排版中...', progress: 90, duration: 1500 },
  { label: '考卷準備完畢!', progress: 100, duration: 500 },
];

const sourceTypeIcons: Record<string, { icon: typeof FileText; color: string }> = {
  PDF: { icon: FileText, color: 'text-blue-500' },
  MARKDOWN: { icon: FileText, color: 'text-slate-500' },
  YOUTUBE_URL: { icon: Youtube, color: 'text-red-500' },
  IMAGE_MATH: { icon: BrainCircuit, color: 'text-purple-500' },
};

export default function ExamSetupPageWrapper() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
      <ExamSetupPage />
    </Suspense>
  );
}

function ExamSetupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedNodeId = searchParams.get('nodeId');
  const { isAuthenticated, loading: authLoading, onboardingCompleted, subscriptionTier, isUltra, isAdmin } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Subject state
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');

  // System knowledge nodes (from historical exam bank)
  const [systemNodes, setSystemNodes] = useState<SystemNode[]>([]);
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());

  // Setup state
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const [questionCount, setQuestionCount] = useState<typeof QUESTION_COUNTS[number]>(20);
  const [difficulty, setDifficulty] = useState<1 | 2 | 3>(2);
  const [examMode, setExamMode] = useState<'hybrid' | 'historical_only'>('hybrid');
  // Spec 19 §「題目排列模式」— interleaved（預設、跨節點交錯）/ grouped（同節點集中）/ sequential（按難度）
  const [orderMode, setOrderMode] = useState<'interleaved' | 'grouped' | 'sequential'>('interleaved');
  const [questionTypes, setQuestionTypes] = useState<Set<QuestionType>>(
    new Set(['MULTIPLE_CHOICE'])
  );
  const [isGenerating, setIsGenerating] = useState(false);
  // L-quota: 模擬測驗配額守門
  const examGuard = useQuotaGuard('monthly_exams');
  // L80：真實生成進度（取代假階段動畫）
  const [livePercent, setLivePercent] = useState<number | null>(null);
  const [liveStageLabel, setLiveStageLabel] = useState<string | null>(null);
  const [generatedExamId, setGeneratedExamId] = useState<string | null>(null);
  const generatedExamIdRef = useRef<string | null>(null);

  // Advanced recipe (B2B teacher only)
  const [showAdvancedRecipe, setShowAdvancedRecipe] = useState(false);
  const [customPointRatio, setCustomPointRatio] = useState<Record<string, number>>({});
  const [customBloomRatio, setCustomBloomRatio] = useState<Record<string, number>>({
    'remember': 20, 'understand': 20, 'apply': 20,
    'analyze': 15, 'evaluate': 15, 'create': 10,
  });
  const [loadingHistoricalStats, setLoadingHistoricalStats] = useState(false);

  // Load subjects + guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (!onboardingCompleted) {
      router.replace('/onboarding');
      return;
    }

    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects);
      if (res.subjects.length > 0) {
        const saved = localStorage.getItem('certimate_active_subject_id');
        const match = saved && res.subjects.find((s: UserSubject) => s.id === saved);
        setActiveSubjectId(match ? saved : res.subjects[0].id);
      }
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load & filter docs by active subject
  useEffect(() => {
    if (!activeSubjectId) return;

    setLoadingDocs(true);
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    documentService.list().then(async res => {
      const filteredDocs = res.documents.filter(d =>
        d.status === 'COMPLETED' && d.subjectId === targetSubjectId
      );
      setDocuments(filteredDocs);

      // Always load system knowledge nodes (historical exam bank)
      try {
        interface KnNode { id: string; name: string; depth: number; children?: KnNode[]; available_questions?: number }
        const mapRes = await apiClient.get<{ nodes?: KnNode[] }>(
          `/knowledge-map/subjects/${targetSubjectId}/nodes`
        );
        const childNodes: SystemNode[] = [];
        for (const root of (mapRes.nodes || [])) {
          // Include root if it has questions directly
          if ((root.available_questions || 0) > 0 && (!root.children || root.children.length === 0)) {
            childNodes.push({ id: root.id, name: root.name, availableQuestions: root.available_questions || 0 });
          }
          for (const child of (root.children || [])) {
            // Only include nodes that actually have questions
            if ((child.available_questions || 0) > 0) {
              childNodes.push({
                id: child.id,
                name: child.name,
                availableQuestions: child.available_questions || 0,
              });
            }
          }
        }
        setSystemNodes(childNodes);
        // Auto-select all historical nodes if in historical_only mode
        if (childNodes.length > 0 && filteredDocs.length === 0) {
          setSelectedNodeIds(new Set(childNodes.map(n => n.id)));
        }
      } catch {
        setSystemNodes([]);
      }

      setLoadingDocs(false);

      // Auto-select document if nodeId is provided (from knowledge map)
      if (preselectedNodeId && filteredDocs.length > 0) {
        if (filteredDocs.length === 1) {
          setSelectedDocIds(new Set([filteredDocs[0].id]));
        } else {
          try {
            const nodeDetail = await apiClient.get<Record<string, unknown>>(`/knowledge-map/nodes/${preselectedNodeId}`);
            const resourceName = (nodeDetail as Record<string, Record<string, unknown>>)?.source_info?.node_name as string;
            const matchingDoc = filteredDocs.find(d =>
              resourceName && d.title.includes(resourceName.substring(0, 10))
            );
            if (matchingDoc) {
              setSelectedDocIds(new Set([matchingDoc.id]));
            } else {
              setSelectedDocIds(new Set([filteredDocs[0].id]));
            }
          } catch {
            setSelectedDocIds(new Set([filteredDocs[0].id]));
          }
        }
      }
    }).catch(() => setLoadingDocs(false));
  }, [activeSubjectId, subjects, preselectedNodeId]);

  const tierLimit = TIER_QUESTION_LIMITS[subscriptionTier];

  // Auto-clamp question count when tier changes
  useEffect(() => {
    if (questionCount > tierLimit.max) {
      const validCounts = QUESTION_COUNTS.filter(c => c <= tierLimit.max);
      setQuestionCount(validCounts.length > 0 ? validCounts[validCounts.length - 1] : QUESTION_COUNTS[0]);
    }
  }, [subscriptionTier, tierLimit.max, questionCount]);

  const toggleDoc = (docId: string) => {
    setValidationError(null);
    setSelectedDocIds(prev => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
  };

  const toggleNode = (nodeId: string) => {
    setValidationError(null);
    setSelectedNodeIds(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const toggleQuestionType = (qt: QuestionType) => {
    setQuestionTypes(prev => {
      const next = new Set(prev);
      if (next.has(qt)) {
        if (next.size > 1) next.delete(qt); // At least one type required
      } else {
        next.add(qt);
      }
      return next;
    });
  };

  // Auto-initialize point ratio when nodes change
  useEffect(() => {
    if (!showAdvancedRecipe) return;
    const selectedNodes = systemNodes.filter(n => selectedNodeIds.has(n.id));
    if (selectedNodes.length === 0) return;
    // Only init if empty or nodes changed
    const currentKeys = Object.keys(customPointRatio).sort().join(',');
    const newKeys = selectedNodes.map(n => n.id).sort().join(',');
    if (currentKeys !== newKeys) {
      const evenShare = Math.floor(100 / selectedNodes.length);
      const remainder = 100 - evenShare * selectedNodes.length;
      const ratio: Record<string, number> = {};
      selectedNodes.forEach((n, i) => {
        ratio[n.id] = evenShare + (i < remainder ? 1 : 0);
      });
      setCustomPointRatio(ratio);
    }
  }, [showAdvancedRecipe, selectedNodeIds, systemNodes]); // eslint-disable-line react-hooks/exhaustive-deps

  const updatePointRatio = (nodeId: string, value: number) => {
    setCustomPointRatio(prev => {
      const updated = { ...prev, [nodeId]: value };
      // Normalize others proportionally so total = 100
      const others = Object.keys(updated).filter(k => k !== nodeId);
      const othersTotal = others.reduce((s, k) => s + (prev[k] || 0), 0);
      const remaining = 100 - value;
      if (othersTotal > 0) {
        others.forEach(k => {
          updated[k] = Math.round((prev[k] / othersTotal) * remaining);
        });
        // Fix rounding: adjust first other
        const newSum = Object.values(updated).reduce((s, v) => s + v, 0);
        if (newSum !== 100 && others.length > 0) {
          updated[others[0]] += 100 - newSum;
        }
      }
      return updated;
    });
  };

  const updateBloomRatio = (level: string, value: number) => {
    setCustomBloomRatio(prev => {
      const updated = { ...prev, [level]: value };
      const others = Object.keys(updated).filter(k => k !== level);
      const othersTotal = others.reduce((s, k) => s + (prev[k] || 0), 0);
      const remaining = 100 - value;
      if (othersTotal > 0) {
        others.forEach(k => {
          updated[k] = Math.round((prev[k] / othersTotal) * remaining);
        });
        const newSum = Object.values(updated).reduce((s, v) => s + v, 0);
        if (newSum !== 100 && others.length > 0) {
          updated[others[0]] += 100 - newSum;
        }
      }
      return updated;
    });
  };

  const loadHistoricalStats = async () => {
    if (!activeSubjectId) return;
    setLoadingHistoricalStats(true);
    try {
      const stats = await apiClient.get<{
        node_distribution?: Record<string, number>;
        bloom_distribution?: Record<string, number>;
      }>(`/exams/subjects/${activeSubjectId}/historical-stats`);
      if (stats.node_distribution) {
        // Map to selected nodes only
        const mapped: Record<string, number> = {};
        let total = 0;
        for (const [nodeId, pct] of Object.entries(stats.node_distribution)) {
          if (selectedNodeIds.has(nodeId)) {
            mapped[nodeId] = pct;
            total += pct;
          }
        }
        // Normalize to 100%
        if (total > 0) {
          for (const k of Object.keys(mapped)) {
            mapped[k] = Math.round((mapped[k] / total) * 100);
          }
          const sum = Object.values(mapped).reduce((s, v) => s + v, 0);
          const first = Object.keys(mapped)[0];
          if (first && sum !== 100) mapped[first] += 100 - sum;
          setCustomPointRatio(mapped);
        }
      }
      if (stats.bloom_distribution) {
        setCustomBloomRatio(stats.bloom_distribution);
      }
    } catch {
      // Silently fail — historical stats may not be available
    } finally {
      setLoadingHistoricalStats(false);
    }
  };

  const handleGenerate = useCallback(async () => {
    const hasSelection = selectedDocIds.size > 0 || selectedNodeIds.size > 0;
    if (!hasSelection) {
      setValidationError('請至少選擇一個知識範圍');
      return;
    }
    setValidationError(null);
    setIsGenerating(true);
    setLivePercent(0);
    setLiveStageLabel('準備中…');

    try {
      const config: Record<string, unknown> = {
        selectedDocumentIds: Array.from(selectedDocIds),
        selectedNodeIds: Array.from(selectedNodeIds),
        questionCount,
        difficulty,
        questionTypes: Array.from(questionTypes),
        examMode,
        question_order_mode: orderMode,  // Spec 19 §排列模式
      };
      // Attach custom ratios if advanced recipe is enabled
      if (showAdvancedRecipe && Object.keys(customPointRatio).length > 0) {
        config.customPointRatio = customPointRatio;
      }
      if (showAdvancedRecipe && Object.keys(customBloomRatio).length > 0) {
        config.customBloomRatio = customBloomRatio;
      }
      // 啟動 polling（每 2 秒查 generation-progress）
      let pollTimer: ReturnType<typeof setInterval> | null = null;
      const startPolling = (id: string) => {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(async () => {
          try {
            const p = await examService.getGenerationProgress(id);
            setLivePercent(p.percent);
            setLiveStageLabel(p.stage_label);
            if (p.status === 'READY' || p.status === 'IN_PROGRESS' || p.status === 'SUBMITTED') {
              if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
            } else if (p.status === 'FAILED') {
              if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
            }
          } catch { /* keep polling */ }
        }, 2000);
      };

      const result = await examService.create({ config: config as never });
      const examId = result.exam?.id || result.exam_id || result.examId || null;
      generatedExamIdRef.current = examId;
      setGeneratedExamId(examId);
      invalidateQuotaCache(); // L-quota: 模擬測驗 +1，重整計數
      // 開始 polling（在等 create 期間若 examId 已落地，可在前置 step 啟動 — 但最簡 MVP 在這裡）
      if (examId) startPolling(examId);
      // examService.create 完成 = AI 已 generate 完，立即停止 polling 並導航
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      setLivePercent(100);
      router.push(`/exam/workspace?examId=${examId}`);
    } catch (e: unknown) {
      console.error('Exam generation failed:', e);
      const msg = e instanceof Error ? e.message : '';
      // If we already have an exam_id from Step 1, navigate anyway (Step 2 might have failed but exam exists)
      if (generatedExamIdRef.current) {
        router.push(`/exam/workspace?examId=${generatedExamIdRef.current}`);
        return;
      }
      setValidationError(msg || '測驗生成失敗，請稍後再試');
      setIsGenerating(false);
    }
  }, [selectedDocIds, selectedNodeIds, questionCount, difficulty, questionTypes, examMode, router]);

  // Backup: navigate when loading animation completes
  const handleLoadingComplete = useCallback(() => {
    const examId = generatedExamIdRef.current;
    if (examId) {
      router.push(`/exam/workspace?examId=${examId}`);
    }
  }, [router]);

  const difficultyLabels = ['基礎概念', '綜合應用', '情境魔王題'];
  const qtLabels: Record<QuestionType, string> = {
    MULTIPLE_CHOICE: '單選題',
    FILL_IN_BLANK: '填空題',
    MATH_FORMULA: '計算題',
  };

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 md:px-6 py-3 flex items-center justify-between shrink-0 gap-3">
        <div className="min-w-0">
          <h1 className="text-base md:text-lg font-bold text-slate-900 truncate">自訂模擬考卷</h1>
          <p className="text-[10px] md:text-xs text-slate-500 hidden sm:block">選擇範圍與難度，AI 將動態生成專屬考題</p>
        </div>
        {subjects.length > 0 && (
          <div className="shrink-0">
            <SubjectSwitcher
              subjects={subjects}
              activeSubjectId={activeSubjectId}
              onSwitch={(id) => { setActiveSubjectId(id); localStorage.setItem('certimate_active_subject_id', id); }}
              onAddSubject={() => router.push('/onboarding')}
              allowAdd={false}
              variant="compact"
            />
          </div>
        )}
      </header>

      <div className="flex-1 overflow-y-auto py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          <ExamLoadingOverlay
            stages={LOADING_STAGES}
            onComplete={handleLoadingComplete}
            isVisible={isGenerating}
            livePercent={livePercent}
            liveStageLabel={liveStageLabel}
          />

      <div className="text-center mb-10">
        <p className="text-slate-600">選擇你想測驗的範圍與難度，AI 將為你動態生成專屬考題。</p>
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="grid md:grid-cols-2">
          {/* Left Column: Scope Selection */}
          <div className="p-8 border-b md:border-b-0 md:border-r border-slate-200 bg-slate-50/50 flex flex-col">
            <h2 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 text-sm">1</span>
              選擇測驗範圍
            </h2>

            <div className="max-h-[50vh] overflow-y-auto pr-1 space-y-4">
            {loadingDocs ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-20 bg-slate-200 rounded-2xl animate-pulse" />
                ))}
              </div>
            ) : documents.length > 0 && examMode !== 'historical_only' ? (
              <div className="space-y-4">
                {documents.map(doc => {
                  const isSelected = selectedDocIds.has(doc.id);
                  const { icon: Icon, color } = sourceTypeIcons[doc.sourceType] || sourceTypeIcons.PDF;

                  return (
                    <label
                      key={doc.id}
                      className={`flex items-start gap-3 p-4 rounded-2xl border-2 cursor-pointer transition-colors relative ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-slate-200 bg-white hover:border-emerald-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleDoc(doc.id)}
                        className="mt-1 h-4 w-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                      />
                      <div className="flex-1">
                        <span className={`font-semibold block mb-1 ${isSelected ? 'text-emerald-900' : 'text-slate-700'}`}>
                          {doc.title}
                        </span>
                        <span className={`text-xs flex items-center gap-1 ${isSelected ? 'text-emerald-700/80' : 'text-slate-500'}`}>
                          <Icon className={`h-3 w-3 ${color}`} />
                          {doc.sourceType === 'YOUTUBE_URL' ? 'YouTube 影片' : doc.sourceType} • 全部章節
                        </span>
                      </div>
                      {isSelected && (
                        <CheckCircle2 className="h-5 w-5 text-emerald-500 absolute top-4 right-4" />
                      )}
                    </label>
                  );
                })}
              </div>
            ) : null}

            {/* 考古題題庫 — 始終顯示（有系統節點時） */}
            {systemNodes.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-slate-500 font-medium">
                    📚 考古題題庫（系統內建 · {systemNodes.reduce((sum, n) => sum + n.availableQuestions, 0)} 題可用）
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setValidationError(null);
                      if (selectedNodeIds.size === systemNodes.length) {
                        setSelectedNodeIds(new Set());
                      } else {
                        setSelectedNodeIds(new Set(systemNodes.map(n => n.id)));
                      }
                    }}
                    className="text-xs text-emerald-600 hover:text-emerald-700 font-medium whitespace-nowrap"
                  >
                    {selectedNodeIds.size === systemNodes.length ? '取消全選' : '全選'}
                  </button>
                </div>
                {systemNodes.map(node => {
                  const isSelected = selectedNodeIds.has(node.id);
                  return (
                    <label
                      key={node.id}
                      className={`flex items-start gap-3 p-4 rounded-2xl border-2 cursor-pointer transition-colors relative ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-slate-200 bg-white hover:border-emerald-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleNode(node.id)}
                        className="mt-1 h-4 w-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                      />
                      <div className="flex-1">
                        <span className={`font-semibold block mb-1 ${isSelected ? 'text-emerald-900' : 'text-slate-700'}`}>
                          {node.name}
                        </span>
                        <span className={`text-xs flex items-center gap-1 ${isSelected ? 'text-emerald-700/80' : 'text-slate-500'}`}>
                          <FileText className="h-3 w-3 text-emerald-500" />
                          {node.availableQuestions} 題可用
                        </span>
                      </div>
                      {isSelected && (
                        <CheckCircle2 className="h-5 w-5 text-emerald-500 absolute top-4 right-4" />
                      )}
                    </label>
                  );
                })}
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center text-slate-400 py-8">
                <p className="text-sm">尚無可用的測驗範圍</p>
                <p className="text-xs mt-1">上傳文件後即可生成考題</p>
                <p className="text-xs mt-2 text-slate-300">若已上傳資源但此處為空，可能資源解析失敗，請至知識庫頁面查看狀態</p>
              </div>
            ) : null}
            </div>
          </div>

          {/* Right Column: Parameters */}
          <div className="p-8">
            <h2 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 text-sm">2</span>
              設定測驗參數
            </h2>

            <div className="space-y-8">
              {/* Question Count */}
              <div>
                {/* 出題模式切換 */}
                <label className="block text-sm font-medium text-slate-700 mb-3">出題模式</label>
                <div className="grid grid-cols-2 gap-2 mb-6">
                  <button
                    onClick={() => {
                      setExamMode('hybrid');
                      setSelectedNodeIds(new Set());
                    }}
                    className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors border-2 ${
                      examMode === 'hybrid'
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                        : 'border-slate-200 text-slate-600 hover:border-emerald-300'
                    }`}
                  >
                    <span className="block font-bold">AI 混合模式</span>
                    <span className="text-xs opacity-75">20% 考古 + 80% AI</span>
                  </button>
                  <button
                    onClick={() => {
                      setExamMode('historical_only');
                      // Auto-select all historical nodes, deselect documents
                      setSelectedDocIds(new Set());
                      if (systemNodes.length > 0) {
                        setSelectedNodeIds(new Set(systemNodes.map(n => n.id)));
                      }
                    }}
                    className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors border-2 ${
                      examMode === 'historical_only'
                        ? 'border-amber-500 bg-amber-50 text-amber-700'
                        : 'border-slate-200 text-slate-600 hover:border-amber-300'
                    }`}
                  >
                    <span className="block font-bold">考古題模擬考</span>
                    <span className="text-xs opacity-75">100% 歷年真題</span>
                  </button>
                </div>

                {/* Spec 19 §「題目排列模式」 */}
                <label className="block text-sm font-medium text-slate-700 mb-3">題目排列模式</label>
                <div className="grid grid-cols-3 gap-2 mb-6">
                  {[
                    { v: 'interleaved' as const, label: '交錯', desc: '跨節點輪流（預設）', emoji: '🔀' },
                    { v: 'grouped' as const, label: '分組', desc: '同節點集中', emoji: '📦' },
                    { v: 'sequential' as const, label: '依難度', desc: '由易到難', emoji: '📈' },
                  ].map((m) => (
                    <button
                      key={m.v}
                      onClick={() => setOrderMode(m.v)}
                      className={`px-3 py-2.5 rounded-xl text-xs transition-colors border-2 ${
                        orderMode === m.v
                          ? 'border-blue-500 bg-blue-50 text-blue-700 font-bold'
                          : 'border-slate-200 text-slate-600 hover:border-blue-300'
                      }`}
                    >
                      <span className="block text-lg mb-0.5">{m.emoji}</span>
                      <span className="block font-bold">{m.label}</span>
                      <span className="block text-[10px] opacity-75">{m.desc}</span>
                    </button>
                  ))}
                </div>

                <label className="block text-sm font-medium text-slate-700 mb-3">題數選擇</label>
                <div className="grid grid-cols-4 gap-2">
                  {QUESTION_COUNTS.map(count => {
                    // 考古題模式不消耗 AI API，解鎖所有題數
                    const isLocked = examMode === 'historical_only' ? false : count > tierLimit.max;
                    return (
                      <button
                        key={count}
                        onClick={() => !isLocked && setQuestionCount(count)}
                        disabled={isLocked}
                        className={`py-2 rounded-lg text-sm font-medium transition-colors relative ${
                          isLocked
                            ? 'border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed'
                            : questionCount === count
                            ? 'border-2 border-emerald-500 bg-emerald-50 text-emerald-700 font-bold'
                            : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {isLocked && <Lock className="h-3 w-3 inline-block mr-1" />}
                        {count} 題
                      </button>
                    );
                  })}
                </div>
                {examMode !== 'historical_only' && tierLimit.upgradeMessage && (
                  <p className="text-xs text-amber-600 mt-2">{tierLimit.upgradeMessage}</p>
                )}
              </div>

              {/* Difficulty */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">難度分配</label>
                <input
                  type="range"
                  min="1"
                  max="3"
                  value={difficulty}
                  onChange={e => setDifficulty(Number(e.target.value) as 1 | 2 | 3)}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-2">
                  {difficultyLabels.map((label, i) => (
                    <span key={label} className={difficulty === i + 1 ? 'font-medium text-emerald-600' : ''}>
                      {label}
                    </span>
                  ))}
                </div>
              </div>

              {/* Question Types */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">題型偏好 (可複選)</label>
                <div className="flex flex-wrap gap-2">
                  {(Object.entries(qtLabels) as [QuestionType, string][]).map(([qt, label]) => {
                    const isActive = questionTypes.has(qt);
                    return (
                      <button
                        key={qt}
                        onClick={() => toggleQuestionType(qt)}
                        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium cursor-pointer transition-colors ${
                          isActive
                            ? 'border border-emerald-500 bg-emerald-50 text-emerald-700'
                            : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Advanced Recipe Panel — ULTRA tier 用戶；管理者帳號（ADMIN/SUPER_ADMIN）亦自動含 */}
              {(isUltra || isAdmin) && (
                <div className="border-t border-slate-200 pt-6">
                  <button
                    type="button"
                    onClick={() => setShowAdvancedRecipe(!showAdvancedRecipe)}
                    className="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-emerald-600 transition-colors w-full"
                  >
                    <Sparkles className="h-4 w-4 text-amber-500" />
                    <span>進階出題配方</span>
                    <ChevronDown className={`h-4 w-4 ml-auto transition-transform ${showAdvancedRecipe ? 'rotate-180' : ''}`} />
                  </button>

                  {showAdvancedRecipe && (
                    <div className="mt-4 space-y-6 animate-in slide-in-from-top-2 duration-200">
                      {/* Historical stats button */}
                      <button
                        type="button"
                        onClick={loadHistoricalStats}
                        disabled={loadingHistoricalStats || selectedNodeIds.size === 0}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border-2 border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed w-full justify-center"
                      >
                        <RotateCcw className={`h-4 w-4 ${loadingHistoricalStats ? 'animate-spin' : ''}`} />
                        {loadingHistoricalStats ? '載入中...' : '套用考古題分佈'}
                      </button>

                      {/* Node point ratio sliders */}
                      {selectedNodeIds.size > 0 && Object.keys(customPointRatio).length > 0 && (
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-3">
                            知識節點出題比例
                            <span className="text-xs text-slate-400 ml-2">
                              (總計 {Object.values(customPointRatio).reduce((s, v) => s + v, 0)}%)
                            </span>
                          </label>
                          <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                            {systemNodes.filter(n => selectedNodeIds.has(n.id)).map(node => (
                              <div key={node.id} className="flex items-center gap-3">
                                <span className="text-xs text-slate-600 w-28 truncate flex-shrink-0" title={node.name}>
                                  {node.name}
                                </span>
                                <input
                                  type="range"
                                  min="0"
                                  max="100"
                                  value={customPointRatio[node.id] || 0}
                                  onChange={e => updatePointRatio(node.id, Number(e.target.value))}
                                  className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                />
                                <span className="text-xs font-mono text-slate-700 w-10 text-right">
                                  {customPointRatio[node.id] || 0}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Bloom taxonomy ratio sliders */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                          Bloom 認知層次配比
                          <span className="text-xs text-slate-400 ml-2">
                            (總計 {Object.values(customBloomRatio).reduce((s, v) => s + v, 0)}%)
                          </span>
                        </label>
                        <div className="space-y-3">
                          {[
                            { key: 'remember', label: '記憶', color: 'text-blue-600' },
                            { key: 'understand', label: '理解', color: 'text-cyan-600' },
                            { key: 'apply', label: '應用', color: 'text-green-600' },
                            { key: 'analyze', label: '分析', color: 'text-yellow-600' },
                            { key: 'evaluate', label: '評鑑', color: 'text-orange-600' },
                            { key: 'create', label: '創造', color: 'text-red-600' },
                          ].map(({ key, label, color }) => (
                            <div key={key} className="flex items-center gap-3">
                              <span className={`text-xs font-medium w-10 flex-shrink-0 ${color}`}>
                                {label}
                              </span>
                              <input
                                type="range"
                                min="0"
                                max="100"
                                value={customBloomRatio[key] || 0}
                                onChange={e => updateBloomRatio(key, Number(e.target.value))}
                                className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                              />
                              <span className="text-xs font-mono text-slate-700 w-10 text-right">
                                {customBloomRatio[key] || 0}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Footer */}
        <div className="bg-slate-900 p-6 flex items-center justify-between">
          <div className="text-slate-300 text-sm">
            {validationError ? (
              <span className="text-red-400">{validationError}</span>
            ) : selectedDocIds.size === 0 && selectedNodeIds.size === 0 ? (
              <span className="text-amber-400">請先選擇至少一份學習資源</span>
            ) : selectedNodeIds.size > 0 && selectedDocIds.size === 0 ? (
              <>已選 <span className="text-white font-medium">{selectedNodeIds.size}</span> 個知識範圍 • 預計生成時間：<span className="text-white font-medium">約 15 秒</span></>
            ) : (
              <>已選 <span className="text-white font-medium">{selectedDocIds.size}</span> 份資源 • 預計生成時間：<span className="text-white font-medium">約 15 秒</span></>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <button
              onClick={examGuard.is_blocked ? undefined : handleGenerate}
              disabled={isGenerating || examGuard.is_blocked}
              className={`px-6 sm:px-8 py-3 rounded-xl font-bold transition-colors flex items-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${
                examGuard.is_blocked
                  ? 'bg-rose-500 hover:bg-rose-500 text-white shadow-rose-500/20'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-emerald-500/20'
              }`}
            >
              <Play className="h-5 w-5 fill-current" />
              {examGuard.is_blocked ? '本月測驗額度已用完' : '生成專屬模擬考'}
            </button>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500">本月模擬測驗：</span>
              <QuotaBadge quotaKey="monthly_exams" variant="pill" />
              {examGuard.is_blocked && (
                <Link href="/account" className="text-emerald-600 hover:text-emerald-700 underline font-medium">升級解鎖 →</Link>
              )}
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
    </div>
  );
}
