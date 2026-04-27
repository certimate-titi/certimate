/**
 * @file 路由 `/practice` — 自由練習模式頁。
 *
 * 以特定知識節點為主題的自由刷題，提示與蘇格拉底教練互動；
 * 透過 query string `nodeId` / `subjectId` 帶入練習主題。
 */
'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  BookOpen,
  ChevronRight,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Lightbulb,
  BarChart3,
  TrendingUp,
  Network,
} from 'lucide-react';
import { practiceService, knowledgeService, subjectService, blindInferenceService } from '@/lib/api/services';
import type { PracticeQuestion, PracticeSubmitResponse } from '@/lib/api/services';
import type { InferenceJudgment } from '@/types/api';
import type { UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import SubjectSwitcher from '@/components/SubjectSwitcher';

export default function PracticePageWrapper() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center min-h-screen"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
      <PracticePage />
    </Suspense>
  );
}

type PracticePhase = 'select-node' | 'answering' | 'feedback' | 'no-questions';

function PracticePage() {
  const searchParams = useSearchParams();
  const preselectedNodeId = searchParams.get('nodeId');
  const preselectedNodeName = searchParams.get('nodeName');
  const { isAuthenticated, loading: authLoading, onboardingCompleted } = useAuth();
  const router = useRouter();

  // Subject
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');

  // Node selection — API returns tree { name, parent_id, children, ... }
  interface ApiNode {
    id: string;
    name: string;
    label?: string;
    parent_id: string | null;
    parentId?: string | null;
    depth: number;
    mastery_level?: string;
    masteryLevel?: string;
    mastery_rate?: number;
    color?: string;
    mastery_color?: string;
    children?: ApiNode[];
  }
  const [nodes, setNodes] = useState<ApiNode[]>([]);
  const [loadingNodes, setLoadingNodes] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(preselectedNodeId || null);
  const [selectedNodeName, setSelectedNodeName] = useState<string>(preselectedNodeName || '');

  // Questions
  const [questions, setQuestions] = useState<PracticeQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Answer state
  const [phase, setPhase] = useState<PracticePhase>(preselectedNodeId ? 'answering' : 'select-node');
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<PracticeSubmitResponse | null>(null);
  const [judgmentSet, setJudgmentSet] = useState(false);

  // Stats
  const [correctCount, setCorrectCount] = useState(0);
  const [totalAnswered, setTotalAnswered] = useState(0);

  // Auth guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (!onboardingCompleted) { router.replace('/onboarding'); return; }

    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects);
      if (res.subjects.length > 0) {
        const saved = localStorage.getItem('certimate_active_subject_id');
        const match = saved && res.subjects.find((s: UserSubject) => s.id === saved);
        setActiveSubjectId(match ? saved : res.subjects[0].id);
      }
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load knowledge nodes for selected subject
  useEffect(() => {
    if (!activeSubjectId) return;
    setLoadingNodes(true);
    knowledgeService.getMap(activeSubjectId).then((res: Record<string, unknown>) => {
      setNodes((res.nodes as ApiNode[]) || []);
    }).catch(() => {
      setNodes([]);
    }).finally(() => setLoadingNodes(false));
  }, [activeSubjectId]);

  // Auto-load questions if preselected node
  useEffect(() => {
    if (preselectedNodeId && phase === 'answering') {
      loadQuestions(preselectedNodeId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preselectedNodeId]);

  const loadQuestions = useCallback(async (nodeId: string) => {
    setLoadingQuestions(true);
    try {
      const res = await practiceService.getNodeQuestions(nodeId);
      setQuestions(res.questions);
      setCurrentIdx(0);
      setSelectedAnswer(null);
      setFeedback(null);
      if (res.questions.length === 0) {
        setPhase('no-questions');
      } else {
        setPhase('answering');
      }
    } catch {
      setQuestions([]);
      setPhase('no-questions');
    } finally {
      setLoadingQuestions(false);
    }
  }, []);

  const handleSelectNode = (node: ApiNode) => {
    setSelectedNodeId(node.id);
    setSelectedNodeName(node.name || node.label || '');
    setCorrectCount(0);
    setTotalAnswered(0);
    loadQuestions(node.id);
  };

  const handleSelectAnswer = (answer: string) => {
    if (phase !== 'answering' || submitting) return;
    setSelectedAnswer(answer);
  };

  const handleSubmit = async () => {
    if (!selectedAnswer || !questions[currentIdx]) return;
    setSubmitting(true);
    try {
      const res = await practiceService.submitAnswer(questions[currentIdx].id, selectedAnswer);
      setFeedback(res);
      setPhase('feedback');
      setJudgmentSet(false);
      setTotalAnswered(prev => prev + 1);
      if (res.is_correct) setCorrectCount(prev => prev + 1);
    } catch {
      // handle error silently
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = async () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(prev => prev + 1);
      setSelectedAnswer(null);
      setFeedback(null);
      setPhase('answering');
    } else {
      // All questions done — await refresh mastery state BEFORE switching phase
      // so the node list renders fresh data instead of stale "未測" tags.
      setLoadingNodes(true);
      if (activeSubjectId) {
        try {
          const res = await knowledgeService.getMap(activeSubjectId) as Record<string, unknown>;
          setNodes((res.nodes as ApiNode[]) || []);
        } catch {
          // leave stale nodes on error — user can refresh manually
        }
      }
      setLoadingNodes(false);
      setPhase('select-node');
    }
  };

  const currentQuestion = questions[currentIdx];
  const options = currentQuestion
    ? [
        { key: 'A', text: currentQuestion.option_a },
        { key: 'B', text: currentQuestion.option_b },
        { key: 'C', text: currentQuestion.option_c },
        { key: 'D', text: currentQuestion.option_d },
      ]
    : [];

  // Flatten tree → only show leaf nodes (no children or children=[])
  const flattenTree = (tree: ApiNode[]): ApiNode[] => {
    const result: ApiNode[] = [];
    const walk = (list: ApiNode[]) => {
      for (const n of list) {
        if (!n.children || n.children.length === 0) {
          result.push(n);
        } else {
          walk(n.children);
        }
      }
    };
    walk(tree);
    return result;
  };
  const leafNodes = flattenTree(nodes);

  if (authLoading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <BookOpen className="h-5 w-5 text-emerald-600 shrink-0" />
            <h1 className="text-sm sm:text-lg font-bold text-slate-800 truncate">
              {phase === 'select-node' ? '節點練習' : selectedNodeName || '練習模式'}
            </h1>
            {totalAnswered > 0 && (
              <span className="text-[10px] sm:text-xs bg-emerald-50 text-emerald-700 px-1.5 sm:px-2 py-0.5 rounded-full border border-emerald-200 shrink-0 whitespace-nowrap">
                {correctCount}/{totalAnswered} 正確
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <SubjectSwitcher
              subjects={subjects}
              activeSubjectId={activeSubjectId}
              onSwitch={(id) => {
                setActiveSubjectId(id);
                localStorage.setItem('certimate_active_subject_id', id);
                setPhase('select-node');
                setQuestions([]);
                setSelectedNodeId(null);
              }}
              onAddSubject={() => router.push('/onboarding')}
              allowAdd={false}
              variant="compact"
            />
            <Link
              href="/knowledge"
              className="text-xs text-slate-500 hover:text-emerald-600 flex items-center gap-1"
            >
              <Network className="h-3.5 w-3.5" />
              知識圖譜
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* Phase: Select Node */}
        {phase === 'select-node' && (
          <div>
            {/* Summary if just finished */}
            {totalAnswered > 0 && (
              <div className="mb-6 p-4 bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl border border-emerald-100">
                <div className="flex items-center gap-3 mb-2">
                  <BarChart3 className="h-5 w-5 text-emerald-600" />
                  <h2 className="font-bold text-slate-800">練習完成</h2>
                </div>
                <div className="flex gap-4 sm:gap-6 text-sm flex-wrap">
                  <div>
                    <span className="text-slate-500">答對</span>
                    <span className="ml-1 font-bold text-emerald-700">{correctCount}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">答錯</span>
                    <span className="ml-1 font-bold text-rose-600">{totalAnswered - correctCount}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">正確率</span>
                    <span className="ml-1 font-bold text-blue-700">
                      {totalAnswered > 0 ? Math.round((correctCount / totalAnswered) * 100) : 0}%
                    </span>
                  </div>
                </div>
              </div>
            )}

            <h2 className="text-sm font-semibold text-slate-600 mb-3">選擇知識節點開始練習</h2>

            {loadingNodes ? (
              <div className="flex justify-center py-12">
                <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : leafNodes.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">尚無知識節點</p>
                <p className="text-slate-400 text-xs mt-1">請先上傳學習資源並生成知識圖譜</p>
                <Link
                  href="/knowledge"
                  className="mt-4 inline-block text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  前往知識庫 <ChevronRight className="inline h-4 w-4" />
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
                {leafNodes.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => handleSelectNode(node)}
                    className="p-4 bg-white rounded-xl border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all text-left group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-slate-800 truncate group-hover:text-emerald-700">
                          {node.name || node.label}
                        </h3>
                        {(() => {
                          const rate = node.mastery_rate ?? 0;
                          const color = node.mastery_color || node.color || 'gray';
                          return (
                            <span
                              className={`mt-1 inline-block text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                                color === 'green'
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  : color === 'yellow'
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : color === 'red'
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : 'bg-slate-50 text-slate-500 border-slate-200'
                              }`}
                            >
                              {rate > 0 ? `${rate}%` : '未測'}
                            </span>
                          );
                        })()}
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-emerald-500 shrink-0" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Phase: No Questions — preselected node has no questions yet */}
        {phase === 'no-questions' && !loadingQuestions && (
          <div className="max-w-xl mx-auto text-center py-16">
            <BookOpen className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <h2 className="text-base font-semibold text-slate-700 mb-1">
              「{selectedNodeName || '此節點'}」尚無練習題
            </h2>
            <p className="text-sm text-slate-500 mb-4">
              此知���節點還沒有可用題目，請先透過測驗產生題目���或選擇其他節點練習。
            </p>
            <p className="text-xs text-slate-400 mb-6">
              提示：若已建立過測驗但仍無題目，可能是 AI 出題任務尚未完成或已失敗，請至測驗頁重新產生。
            </p>
            <div className="flex gap-3 justify-center flex-wrap">
              <Link
                href={selectedNodeId ? `/exam/setup?nodeId=${selectedNodeId}` : '/exam/setup'}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                前往出題
              </Link>
              <button
                onClick={() => {
                  setSelectedNodeId(null);
                  setSelectedNodeName('');
                  setPhase('select-node');
                  router.replace('/practice');
                }}
                className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                選擇其他��點
              </button>
              <Link
                href="/knowledge"
                className="px-4 py-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100"
              >
                回知識圖譜
              </Link>
            </div>
          </div>
        )}

        {/* Phase: Loading Questions */}
        {loadingQuestions && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-sm text-slate-500">載入練習題...</p>
          </div>
        )}

        {/* Phase: Answering */}
        {phase === 'answering' && currentQuestion && !loadingQuestions && (
          <div className="max-w-2xl mx-auto">
            {/* Progress bar */}
            <div className="mb-4 flex items-center gap-3">
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                  style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
                />
              </div>
              <span className="text-xs text-slate-400 shrink-0">
                {currentIdx + 1} / {questions.length}
              </span>
            </div>

            {/* Question card */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-6 mb-4">
              <div className="flex items-center gap-2 mb-4">
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                    currentQuestion.difficulty === 'easy'
                      ? 'bg-green-50 text-green-700 border-green-200'
                      : currentQuestion.difficulty === 'hard'
                      ? 'bg-red-50 text-red-700 border-red-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}
                >
                  {currentQuestion.difficulty === 'easy' ? '簡單' : currentQuestion.difficulty === 'hard' ? '困難' : '中等'}
                </span>
                <span className="text-[10px] text-slate-400">
                  {currentQuestion.type === 'single_choice' ? '單選題' : currentQuestion.type}
                </span>
              </div>

              <p className="text-sm text-slate-800 leading-relaxed mb-4 whitespace-pre-line">
                {currentQuestion.content}
              </p>

              {currentQuestion.figure_urls && currentQuestion.figure_urls.length > 0 && (
                <div className="mb-6 space-y-2">
                  {currentQuestion.figure_urls.map((url, i) => {
                    const src = url.startsWith('http')
                      ? url
                      : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/v1\/?$/, '')}${url}`;
                    return (
                      <img
                        key={i}
                        src={src}
                        alt={currentQuestion.figure_description || `題目附圖 ${i + 1}`}
                        className="max-w-full rounded-lg border border-slate-200"
                        loading="lazy"
                      />
                    );
                  })}
                  {currentQuestion.figure_description && (
                    <p className="text-xs text-slate-500 italic">
                      圖說：{currentQuestion.figure_description}
                    </p>
                  )}
                </div>
              )}

              {/* Options */}
              <div className="space-y-2.5">
                {options.map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() => handleSelectAnswer(opt.key)}
                    disabled={submitting}
                    className={`w-full text-left p-3.5 rounded-lg border-2 transition-all text-sm ${
                      selectedAnswer === opt.key
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
                        : 'border-slate-200 hover:border-slate-300 text-slate-700'
                    } ${submitting ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <span className="font-bold mr-2 text-xs">{opt.key}.</span>
                    {opt.text}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit button */}
            <button
              onClick={handleSubmit}
              disabled={!selectedAnswer || submitting}
              className={`w-full py-3 rounded-xl font-medium text-sm transition-all ${
                selectedAnswer && !submitting
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              }`}
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  提交中...
                </span>
              ) : (
                '確認作答'
              )}
            </button>
          </div>
        )}

        {/* Phase: Feedback */}
        {phase === 'feedback' && feedback && (
          <div className="max-w-2xl mx-auto">
            {/* Result banner */}
            <div
              className={`p-4 rounded-xl border-2 mb-4 ${
                feedback.is_correct
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-rose-50 border-rose-200'
              }`}
            >
              <div className="flex items-center gap-3">
                {feedback.is_correct ? (
                  <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="h-6 w-6 text-rose-600 shrink-0" />
                )}
                <div>
                  <h3
                    className={`font-bold text-sm ${
                      feedback.is_correct ? 'text-emerald-800' : 'text-rose-800'
                    }`}
                  >
                    {feedback.is_correct ? '答對了！' : '答錯了'}
                  </h3>
                  {!feedback.is_correct && (
                    <p className="text-xs text-rose-600 mt-0.5">
                      正確答案：<span className="font-bold">{feedback.correct_answer}</span>
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Question recap with answer highlights */}
            {currentQuestion && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-6 mb-4">
                <p className="text-sm text-slate-800 leading-relaxed mb-5 whitespace-pre-line">
                  {currentQuestion.content}
                </p>
                <div className="space-y-2.5">
                  {options.map((opt) => {
                    const isCorrect = opt.key === feedback.correct_answer;
                    const isUserPick = opt.key === selectedAnswer;
                    const isWrongPick = isUserPick && !feedback.is_correct;
                    const baseClass = 'w-full text-left p-3.5 rounded-lg border-2 text-sm flex items-start gap-2';
                    const stateClass = isCorrect
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-900'
                      : isWrongPick
                      ? 'border-rose-500 bg-rose-50 text-rose-900'
                      : 'border-slate-200 text-slate-600';
                    return (
                      <div key={opt.key} className={`${baseClass} ${stateClass}`}>
                        <span className="font-bold text-xs shrink-0 mt-0.5">{opt.key}.</span>
                        <span className="flex-1">{opt.text}</span>
                        {isCorrect && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-600 text-white shrink-0">
                            正確答案
                          </span>
                        )}
                        {isWrongPick && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-600 text-white shrink-0">
                            你的選擇
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Explanation */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <h4 className="text-sm font-bold text-slate-700">詳解</h4>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                {feedback.explanation || '本題暫無詳解，若需進一步說明可詢問 AI 教練。'}
              </p>
            </div>

            {/* EPIC-035: AI 推論揭示（僅 ai_inferred 題目顯示） */}
            {currentQuestion && feedback.answer_source === 'ai_inferred' && (
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="h-4 w-4 text-amber-600" />
                  <h4 className="text-sm font-bold text-amber-800">這是 AI 推論的答案</h4>
                </div>
                <div className="text-xs text-amber-700 space-y-1">
                  <div>
                    AI 推論：<span className="font-bold">{feedback.correct_answer}</span>
                    {typeof feedback.confidence === 'number' && (
                      <span className="ml-2">（信心度 {(feedback.confidence * 100).toFixed(0)}%）</span>
                    )}
                  </div>
                  <p className="text-amber-600 italic">
                    此題無官方正解，AI 僅提供推論。你可以保留自己的答案或採信 AI。
                  </p>
                </div>
                {!judgmentSet && (
                  <div className="mt-3 flex gap-2">
                    {([
                      { k: 'keep_mine' as InferenceJudgment, label: '保留我的答案' },
                      { k: 'accept_ai' as InferenceJudgment, label: '採信 AI' },
                      { k: 'skip' as InferenceJudgment, label: '略過' },
                    ]).map((b) => (
                      <button
                        key={b.k}
                        onClick={async () => {
                          try {
                            await blindInferenceService.submitJudgment(currentQuestion.id, b.k);
                            setJudgmentSet(true);
                          } catch (e: any) {
                            alert(`記錄失敗：${e?.message}`);
                          }
                        }}
                        className="px-3 py-1 text-xs bg-white border border-amber-300 text-amber-700 rounded-lg hover:bg-amber-100"
                      >
                        {b.label}
                      </button>
                    ))}
                  </div>
                )}
                {judgmentSet && (
                  <p className="mt-2 text-xs text-amber-600 font-medium">已記錄你的判定 ✓</p>
                )}
              </div>
            )}

            {/* EPIC-035: never_for_scoring 隔離提示 */}
            {feedback.never_for_scoring && !feedback.progress && (
              <div className="bg-slate-50 rounded-xl border border-slate-200 p-3 mb-4 text-xs text-slate-600">
                <span className="font-semibold">個人題庫隔離：</span>
                本題為個人題庫題目，作答結果不影響節點掌握度統計。
              </div>
            )}

            {/* Progress update */}
            {feedback.progress && (
              <div className="bg-blue-50 rounded-xl border border-blue-100 p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <h4 className="text-sm font-bold text-blue-800">進度更新</h4>
                </div>
                <div className="flex items-center gap-4 text-xs text-blue-700">
                  <div>
                    掌握度：
                    <span className="font-bold">
                      {Math.round((feedback.progress.old_progress ?? 0) * 100)}%
                    </span>
                    <ArrowRight className="inline h-3 w-3 mx-1" />
                    <span className="font-bold">
                      {Math.round((feedback.progress.new_progress ?? 0) * 100)}%
                    </span>
                  </div>
                  <div>
                    狀態：<span className="font-bold">{feedback.progress.status}</span>
                  </div>
                </div>

                {/* Propagation */}
                {feedback.propagation && feedback.propagation.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-blue-200">
                    <p className="text-[10px] text-blue-600 mb-1">父節點進度傳播：</p>
                    {feedback.propagation.map((p, i) => (
                      <div key={i} className="text-[10px] text-blue-600">
                        → {Math.round((p.new_progress ?? 0) * 100)}%
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Next button */}
            <button
              onClick={handleNext}
              className="w-full py-3 rounded-xl font-medium text-sm bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm transition-all flex items-center justify-center gap-2"
            >
              {currentIdx < questions.length - 1 ? (
                <>
                  下一題 <ArrowRight className="h-4 w-4" />
                </>
              ) : (
                '完成練習'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
