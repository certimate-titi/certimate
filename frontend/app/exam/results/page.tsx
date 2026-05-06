/**
 * @file 路由 `/exam/results` — 考試結果頁。
 *
 * 顯示模擬考成績、答對率、領域強弱、錯題回顧；及格時播 Confetti 動畫，
 * 並用 ForceGraph 視覺化作答涉及的知識節點。透過 query string `examId` 取得結果。
 */
'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle2, XCircle, ArrowRight, BrainCircuit, Trophy, Target, Clock, TrendingUp, TrendingDown, Flag, Share2, Download, Sparkles, FileText } from 'lucide-react';
import { examService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import type { GetExamResultsResponse } from '@/types';
import Confetti from '@/components/Confetti';
import ForceGraph, { type GraphNode } from '@/components/ForceGraph';
import ShareBadgeModal from '@/components/ShareBadgeModal';
import type { ShareBadgeResponse } from '@/types/api';

/**
 * 考試結果頁外層 Suspense 包裝（`useSearchParams` 需在 Suspense 內使用）。
 */
export default function ExamResultsPageWrapper() {
  return (
    <Suspense fallback={<div className="container mx-auto px-4 py-12 max-w-5xl"><div className="animate-pulse space-y-8"><div className="h-10 bg-slate-200 rounded w-64 mx-auto" /></div></div>}>
      <ExamResultsPage />
    </Suspense>
  );
}

function ExamResultsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const examId = searchParams.get('examId') || 'exam_001';
  const { user, loading: authLoading, isAuthenticated, subscriptionTier, isAdmin } = useAuth();
  const isFreeUser = subscriptionTier === 'FREE' && !isAdmin;

  const [data, setData] = useState<GetExamResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [confidenceData, setConfidenceData] = useState<any>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);
  const [showConfetti, setShowConfetti] = useState(false);
  // L-share-badge: 徽章資料 + 分享 modal
  const [badgeData, setBadgeData] = useState<ShareBadgeResponse | null>(null);
  const [showBadgeModal, setShowBadgeModal] = useState(false);

  useEffect(() => {
    examService.getResults(examId).then(async (res) => {
      setData(res);
      setLoading(false);
      examService.getConfidenceAnalysis(examId).then(setConfidenceData).catch(() => {});
      // L-share-badge: 預載徽章資料（成功則在頁面下方顯示徽章 + 分享按鈕）
      examService.getShareBadge(examId).then(setBadgeData).catch(() => setBadgeData(null));
      if (res.exam.score !== null && res.exam.score >= 80) {
        setTimeout(() => setShowConfetti(true), 300);
      }

      // 載入完整知識圖譜
      try {
        const { apiClient } = await import('@/lib/api/client');
        const { subjectService } = await import('@/lib/api/services');
        const subjectsRes = await subjectService.getUserSubjects();
        if (subjectsRes.subjects.length > 0) {
          const subjectId = subjectsRes.subjects[0].subjectId || subjectsRes.subjects[0].id;
          const mapRes = await apiClient.get<{ nodes?: Array<{ id: string; name: string; depth: number; parent_id: string | null; mastery_rate: number; color: string; children?: Array<{ id: string; name: string; depth: number; parent_id: string | null; mastery_rate: number; color: string; available_questions?: number }> }> }>(`/knowledge-map/subjects/${subjectId}/nodes`);
          const flat: GraphNode[] = [];
          const flattenNodes = (nodes: typeof mapRes.nodes) => {
            for (const n of (nodes || [])) {
              flat.push({ id: n.id, name: n.name, depth: n.depth, progress: n.mastery_rate || 0, color: n.color || 'gray', parentId: n.parent_id, status: 'UNSEEN', availableQuestions: 0 });
              if (n.children) flattenNodes(n.children);
            }
          };
          flattenNodes(mapRes.nodes);
          setGraphNodes(flat);
        }
      } catch { /* knowledge map optional */ }
    }).catch(() => setLoading(false));
  }, [examId]);

  if (loading || !data) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-5xl">
        <div className="animate-pulse space-y-8">
          <div className="h-10 bg-slate-200 rounded w-64 mx-auto" />
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="h-80 bg-slate-200 rounded-3xl" />
            <div className="lg:col-span-2 h-80 bg-slate-200 rounded-3xl" />
          </div>
        </div>
      </div>
    );
  }

  const { exam, questions, userAnswers, domainAnalysis, aiSummary, bloomBreakdown } = data;
  const score = exam.score ?? 0;
  const correctCount = userAnswers.filter(a => a.isCorrect).length;
  const wrongCount = userAnswers.filter(a => !a.isCorrect && a.userChoice).length;
  const unanswered = userAnswers.filter(a => !a.userChoice).length;

  const isPass = score >= 70;
  const scoreMessage = score >= 90
    ? '太厲害了！幾近完美！'
    : score >= 80
    ? '恭喜通過！表現優異！'
    : score >= 70
    ? '通過了！繼續加油！'
    : score >= 50
    ? '差一點點，再練習一下！'
    : '別灰心，學習就是這樣一步步來的！';

  // Previous score comparison (from API data when available)
  const extData = data as GetExamResultsResponse & { previousScore?: number; consecutiveDeclines?: number; totalTimeMinutes?: number };
  const previousScore = extData.previousScore ?? null;
  const scoreDiff = previousScore !== null ? score - previousScore : 0;

  // Consecutive decline detection (from API data when available)
  const showAiCoachIntervention = extData.consecutiveDeclines ? extData.consecutiveDeclines >= 2 : false;

  // Completion stats — exam.timeSpent is time_spent_seconds from backend
  const timeSpentSeconds = data.exam.timeSpent || 0;
  const totalTimeMinutes = timeSpentSeconds > 0 ? Math.round(timeSpentSeconds / 60) : 0;
  const avgTimePerQuestion = questions.length > 0 && timeSpentSeconds > 0 ? Math.round(timeSpentSeconds / questions.length) : 0;
  const markedQuestions = userAnswers.filter(a => a.isMarkedForReview);
  const markedCorrectRate = markedQuestions.length > 0
    ? Math.round((markedQuestions.filter(a => a.isCorrect).length / markedQuestions.length) * 100)
    : 0;

  return (
    <div className="container mx-auto px-4 py-12 max-w-5xl">
      <Confetti trigger={showConfetti} />

      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-4">測驗結果分析</h1>
        <p className="text-lg text-slate-600">{exam.title} • {exam.createdAt ? new Date(exam.createdAt).toLocaleDateString('zh-TW') : new Date().toLocaleDateString('zh-TW')}</p>
        {/* Feature 19: 交錯練習模式標籤 */}
        {exam.questionOrderMode === 'interleaved' && (
          <div className="mt-3 inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full px-4 py-1.5 text-sm font-medium">
            <span>🔀</span>
            <span>交錯練習</span>
          </div>
        )}
        {exam.questionOrderMode === 'interleaved' && (
          <p className="mt-2 text-sm text-indigo-500">交錯練習有助於長期記憶，持續使用效果更佳</p>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column: Score Overview */}
        <div className="lg:col-span-1 space-y-8">
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 text-center relative overflow-hidden">
            <div className={`absolute top-0 left-0 w-full h-2 ${isPass ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            <div className={`inline-flex items-center justify-center h-20 w-20 rounded-full mb-6 ${
              isPass ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'
            }`}>
              <Trophy className="h-10 w-10" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">{scoreMessage}</h2>
            <div className="flex items-end justify-center gap-2 mb-6">
              <span className="text-6xl font-extrabold text-slate-900">{score}</span>
              <span className="text-xl font-medium text-slate-500 mb-1">/ 100</span>
            </div>
            {/* Progress comparison */}
            {previousScore !== null && scoreDiff !== 0 && (
              <div className={`flex items-center justify-center gap-2 mb-4 px-4 py-2 rounded-lg ${
                scoreDiff > 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
              }`}>
                {scoreDiff > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                <span className="text-sm font-bold">
                  {scoreDiff > 0 ? `↑ 提升 ${scoreDiff} 分，幹得好！` : `↓ 較上次下降 ${Math.abs(scoreDiff)} 分，別氣餒！`}
                </span>
              </div>
            )}

            {/* AI Coach Intervention — triggered on 2+ consecutive score declines */}
            {showAiCoachIntervention && (
              <Link href="/review" className="block mb-4 bg-amber-50 border border-amber-200 rounded-xl p-4 hover:bg-amber-100 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
                    <BrainCircuit className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-amber-800">連續退步？讓 AI 教練幫你找出盲點</p>
                    <p className="text-xs text-amber-600 mt-0.5">AI 教練已準備好個人化學習策略建議</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-amber-500 flex-shrink-0 ml-auto" />
                </div>
              </Link>
            )}

            <div className="flex items-center justify-between text-sm text-slate-500 bg-slate-50 rounded-xl p-4 border border-slate-100">
              <div className="text-center">
                <span className="block font-bold text-emerald-600 text-lg">{correctCount}</span>
                答對
              </div>
              <div className="w-px h-8 bg-slate-200" />
              <div className="text-center">
                <span className="block font-bold text-rose-500 text-lg">{wrongCount}</span>
                答錯
              </div>
              <div className="w-px h-8 bg-slate-200" />
              <div className="text-center">
                <span className="block font-bold text-slate-400 text-lg">{unanswered}</span>
                未答
              </div>
            </div>
          </div>

          {/* Completion Stats */}
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Clock className="h-5 w-5 text-indigo-500" /> 完賽數據
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-3 bg-slate-50 rounded-xl">
                <span className="block text-lg font-bold text-slate-900">{totalTimeMinutes} 分</span>
                <span className="text-xs text-slate-500">作答總時間</span>
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-xl">
                <span className="block text-lg font-bold text-slate-900">{avgTimePerQuestion} 秒</span>
                <span className="text-xs text-slate-500">平均每題</span>
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-xl">
                <span className="block text-lg font-bold text-slate-900 flex items-center justify-center gap-1">
                  <Flag className="h-4 w-4 text-amber-500" /> {markedCorrectRate}%
                </span>
                <span className="text-xs text-slate-500">標記題答對率</span>
              </div>
            </div>
          </div>

          {/* AI Summary — Feature 06: FREE 用戶不顯示 AI 考後總評，改顯示升級提示 */}
          {isFreeUser ? (
            <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-3xl p-6 shadow-sm border border-slate-200">
              <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-slate-400" />
                <BrainCircuit className="h-5 w-5 text-slate-400" />
                AI 分析摘要
              </h3>
              <div className="text-center py-4">
                <p className="text-sm text-slate-500 mb-3">升級至 PRO_199 方案即可解鎖 AI 考後總評分析</p>
                <Link href="/pricing" className="inline-flex items-center gap-2 bg-indigo-500 hover:bg-indigo-400 text-white px-5 py-2.5 rounded-xl font-bold text-sm transition-colors">
                  <Sparkles className="h-4 w-4" /> 查看升級方案
                </Link>
              </div>
            </div>
          ) : (
            <div className="bg-gradient-to-br from-indigo-50 to-emerald-50 rounded-3xl p-6 shadow-sm border border-indigo-100">
              <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-500" />
                <BrainCircuit className="h-5 w-5 text-emerald-500" />
                AI 分析摘要
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed">{aiSummary}</p>
            </div>
          )}

          {/* Action Card */}
          <div className="bg-slate-900 rounded-3xl p-8 text-white shadow-lg shadow-slate-900/20 relative overflow-hidden group">
            <div className="absolute -right-10 -top-10 h-40 w-40 bg-emerald-500/20 rounded-full blur-3xl group-hover:bg-emerald-500/30 transition-colors" />
            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
              <BrainCircuit className="h-6 w-6 text-emerald-400" /> 深度檢討
            </h3>
            <p className="text-slate-300 text-sm mb-8 leading-relaxed">
              AI 教練已為你準備好錯題解析，包含盲點痛擊與記憶口訣。
            </p>
            <Link href={`/review?examId=${examId}`} className="w-full bg-emerald-500 hover:bg-emerald-400 text-white px-6 py-4 rounded-xl font-bold transition-colors flex items-center justify-center gap-2 shadow-md mb-3">
              進入錯題本（AI 解析 + 教練）<ArrowRight className="h-5 w-5" />
            </Link>
            <Link href={`/review?examId=${examId}&all=1`} className="w-full bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2 border border-white/10 text-sm">
              <FileText className="h-4 w-4" /> 逐題解析（含答對題）
            </Link>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Spec 18 §Bloom 各層次答對率 */}
          {bloomBreakdown && bloomBreakdown.length > 0 && bloomBreakdown.some(b => b.total > 0) && (
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
                <BrainCircuit className="h-6 w-6 text-purple-500" /> Bloom 認知層次分析
              </h3>
              <p className="text-xs text-slate-500 mb-5 leading-relaxed">
                依教育心理學 Bloom 分類法，分析你在記憶 / 理解 / 應用 / 分析 / 評估 / 創造六個層次的答對率。
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {bloomBreakdown.filter(b => b.total > 0).map(b => {
                  const tone = b.rate < 50 ? 'rose' : b.rate >= 80 ? 'emerald' : 'amber';
                  const colors = {
                    rose: 'bg-rose-50 border-rose-200 text-rose-700',
                    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
                    amber: 'bg-amber-50 border-amber-200 text-amber-700',
                  } as const;
                  return (
                    <div key={b.category} className={`p-3 rounded-xl border-2 ${colors[tone]}`}>
                      <div className="text-xs font-medium opacity-75 mb-1">{b.label}</div>
                      <div className="text-2xl font-extrabold">{b.rate}%</div>
                      <div className="text-[10px] opacity-60">{b.correct} / {b.total}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 信心度四象限分析 */}
          {confidenceData && confidenceData.quadrants && (
            <div data-testid="confidence-quadrant-analysis" className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
                <BrainCircuit className="h-6 w-6 text-indigo-500" /> 信心度四象限分析
              </h3>
              <p className="text-xs text-slate-500 mb-5 leading-relaxed">
                依作答信心與正確性，將題目分為四個象限，找出認知盲點與幸運猜對的題目。
              </p>
              <div className="grid grid-cols-2 gap-3 mb-6">
                {/* 真正掌握 — confident_correct */}
                {confidenceData.quadrants.confident_correct && (
                  <div className="p-4 rounded-xl border-2 border-emerald-200 bg-emerald-50">
                    <div className="text-xs font-medium text-emerald-600 mb-1">{confidenceData.quadrants.confident_correct.label}</div>
                    <div className="text-3xl font-extrabold text-emerald-700">{confidenceData.quadrants.confident_correct.count}</div>
                    <div className="text-[10px] text-emerald-500 mt-1">有把握且答對</div>
                  </div>
                )}
                {/* 危險盲點 — confident_incorrect */}
                {confidenceData.quadrants.confident_incorrect && (
                  <div className="p-4 rounded-xl border-2 border-rose-200 bg-rose-50">
                    <div className="text-xs font-medium text-rose-600 mb-1">{confidenceData.quadrants.confident_incorrect.label}</div>
                    <div className="text-3xl font-extrabold text-rose-700">{confidenceData.quadrants.confident_incorrect.count}</div>
                    <div className="text-[10px] text-rose-500 mt-1">有把握但答錯</div>
                  </div>
                )}
                {/* 幸運猜對 — guessing_correct */}
                {confidenceData.quadrants.guessing_correct && (
                  <div className="p-4 rounded-xl border-2 border-amber-200 bg-amber-50">
                    <div className="text-xs font-medium text-amber-600 mb-1">{confidenceData.quadrants.guessing_correct.label}</div>
                    <div className="text-3xl font-extrabold text-amber-700">{confidenceData.quadrants.guessing_correct.count}</div>
                    <div className="text-[10px] text-amber-500 mt-1">猜對的題目</div>
                  </div>
                )}
                {/* 預期中的弱點 — guessing_incorrect */}
                {confidenceData.quadrants.guessing_incorrect && (
                  <div className="p-4 rounded-xl border-2 border-slate-200 bg-slate-50">
                    <div className="text-xs font-medium text-slate-600 mb-1">{confidenceData.quadrants.guessing_incorrect.label}</div>
                    <div className="text-3xl font-extrabold text-slate-700">{confidenceData.quadrants.guessing_incorrect.count}</div>
                    <div className="text-[10px] text-slate-500 mt-1">不確定且答錯</div>
                  </div>
                )}
              </div>

              {/* Calibration Rate */}
              <div className="mb-5">
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium text-slate-700">校準率（Calibration Rate）</span>
                  <span className="font-bold text-indigo-600">{Math.round(confidenceData.calibration_rate * 100)}%</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-indigo-500 transition-all" style={{ width: `${Math.round(confidenceData.calibration_rate * 100)}%` }} />
                </div>
                <p className="text-[10px] text-slate-400 mt-1">校準率越高代表你對自己的掌握度判斷越準確</p>
              </div>

              {/* AI Coach Alerts */}
              {confidenceData.quadrants.confident_incorrect && confidenceData.quadrants.confident_incorrect.count > 0 && confidenceData.ai_coach_messages?.confident_incorrect && (
                <div className="flex items-start gap-3 bg-rose-50 border border-rose-200 rounded-xl p-4 mb-3">
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-rose-100 flex items-center justify-center mt-0.5">
                    <XCircle className="h-4 w-4 text-rose-600" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-rose-800 mb-0.5">危險盲點提醒</p>
                    <p className="text-xs text-rose-600 leading-relaxed">{confidenceData.ai_coach_messages.confident_incorrect}</p>
                  </div>
                </div>
              )}
              {confidenceData.quadrants.guessing_correct && confidenceData.quadrants.guessing_correct.count > 0 && confidenceData.ai_coach_messages?.guessing_correct && (
                <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center mt-0.5">
                    <Sparkles className="h-4 w-4 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-amber-800 mb-0.5">幸運猜對提醒</p>
                    <p className="text-xs text-amber-600 leading-relaxed">{confidenceData.ai_coach_messages.guessing_correct}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Domain Analysis */}
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
            <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
              <Target className="h-6 w-6 text-indigo-500" /> 知識點弱點分析
            </h3>
            <div className="space-y-6">
              {domainAnalysis.map(d => {
                const barColor = d.percentage < 60 ? 'bg-rose-500' : d.percentage >= 80 ? 'bg-emerald-500' : 'bg-amber-500';
                const textColor = d.percentage < 60 ? 'text-rose-600' : d.percentage >= 80 ? 'text-emerald-600' : 'text-amber-600';
                return (
                  <div key={d.domain}>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-medium text-slate-700 flex items-center gap-2">
                        {d.domain}
                        {d.percentage < 60 && (
                          <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-700 text-xs font-bold">需加強</span>
                        )}
                      </span>
                      <span className={`font-bold ${textColor}`}>
                        {d.percentage}% ({d.correct}/{d.total})
                      </span>
                    </div>
                    <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${d.percentage}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 知識圖譜 */}
          {graphNodes.length > 0 && (
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                <BrainCircuit className="h-6 w-6 text-emerald-500" /> 知識圖譜
              </h3>
              <ForceGraph
                nodes={graphNodes.map(n => {
                  // 標示本次考試涉及的節點
                  const examDomain = domainAnalysis.find(d => d.domain === n.name);
                  if (examDomain) {
                    return {
                      ...n,
                      progress: examDomain.percentage,
                      color: examDomain.percentage < 60 ? 'red' : examDomain.percentage >= 80 ? 'green' : 'yellow',
                    };
                  }
                  return n;
                })}
                onNodeClick={() => {}}
                width={700}
                height={400}
              />
              <div className="flex items-center gap-4 mt-3 text-[10px] text-slate-400 justify-center">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />本次精通</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />本次部分</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" />本次需加強</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300" />未涉及</span>
              </div>
            </div>
          )}
          {graphNodes.length === 0 && domainAnalysis.length > 0 && (
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                <BrainCircuit className="h-6 w-6 text-emerald-500" /> 弱點圖譜
              </h3>
              <ForceGraph
                nodes={domainAnalysis.map((d, i) => ({
                  id: `domain-${i}`, name: d.domain, depth: 1,
                  progress: d.percentage,
                  color: d.percentage < 60 ? 'red' : d.percentage >= 80 ? 'green' : 'yellow',
                  parentId: null, status: 'UNSEEN', availableQuestions: d.total,
                }))}
                onNodeClick={() => {}}
                width={700}
                height={300}
              />
            </div>
          )}

          {/* Question Grid */}
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
            <h3 className="text-xl font-bold text-slate-900 mb-6">作答明細</h3>
            <div className="grid grid-cols-5 sm:grid-cols-10 gap-3">
              {questions.map((q, i) => {
                const ua = userAnswers.find(a => a.questionId === q.id);
                const isWrong = ua && !ua.isCorrect;
                return (
                  <div key={q.id} className="flex flex-col items-center gap-1">
                    <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                      isWrong
                        ? 'bg-rose-50 border-2 border-rose-200 text-rose-700'
                        : 'bg-emerald-50 border-2 border-emerald-200 text-emerald-700'
                    }`}>
                      {i + 1}
                    </div>
                    {isWrong ? (
                      <XCircle className="h-4 w-4 text-rose-500" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* L-share-badge: 學習徽章區（不顯示絕對分數，A+B+D 三種正向指標） */}
      {badgeData && (
        <div className="mt-10 bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm">
          <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
            <div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-500" />
                你的學習徽章
              </h3>
              <p className="text-xs text-slate-500 mt-1">展現成長與堅持，不揭露分數，分享無壓力</p>
            </div>
            <button
              onClick={() => setShowBadgeModal(true)}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-5 py-2 rounded-full text-sm font-bold transition-colors flex items-center gap-2 shadow-sm shadow-emerald-500/30"
            >
              <Share2 className="h-4 w-4" /> 分享徽章
            </button>
          </div>
          {/* 簡略預覽：三項正向指標一行 */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
            <div className="bg-emerald-50 rounded-xl p-3 text-center">
              <p className="text-[10px] uppercase tracking-wider text-emerald-700 font-bold mb-1">本次表現</p>
              <p className="text-sm font-bold text-slate-900">{badgeData.improvement.message}</p>
            </div>
            <div className="bg-amber-50 rounded-xl p-3 text-center">
              <p className="text-[10px] uppercase tracking-wider text-amber-700 font-bold mb-1">累積里程</p>
              <p className="text-sm font-bold text-slate-900">
                {badgeData.cumulative.total_exams} 測驗 · {badgeData.cumulative.total_questions} 題 · 連 {badgeData.cumulative.streak_days} 天
              </p>
            </div>
            <div className="bg-indigo-50 rounded-xl p-3 text-center">
              <p className="text-[10px] uppercase tracking-wider text-indigo-700 font-bold mb-1">學習風格</p>
              <p className="text-sm font-bold text-slate-900">
                {badgeData.learning_style.emoji} {badgeData.learning_style.label}
              </p>
            </div>
          </div>
        </div>
      )}

      {showBadgeModal && badgeData && (
        <ShareBadgeModal data={badgeData} onClose={() => setShowBadgeModal(false)} />
      )}

      {/* Legal Disclaimer */}
      <p className="text-xs text-slate-400 italic text-center mt-6">
        *本模擬考試結果僅反映當前熟悉度，並不保證實測通過率及 AI 解析結果的絕對正確性。*
      </p>
    </div>
  );
}
