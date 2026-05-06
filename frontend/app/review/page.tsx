/**
 * @file 路由 `/review` — 錯題複習簿頁。
 *
 * 列出使用者標記為「需要複習」的題目並支援與蘇格拉底教練對話；
 * 透過 `reviewService` / `subjectService` 載入資料。
 */
'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ChevronLeft, FileText, Lock, Sparkles, Send, RefreshCw, BookOpen } from 'lucide-react';
import TiTiLogo from '@/components/TiTiLogo';
import MathContent from '@/components/MathContent';
import Link from 'next/link';
import { reviewService, subjectService, examService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import type { GetReviewQuestionsResponse, ChatMessage, UserSubject } from '@/types';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import QuotaBadge from '@/components/QuotaBadge';
import WrongAnswerExamModal from '@/components/WrongAnswerExamModal';
import { useQuotaGuard, invalidateQuotaCache } from '@/hooks/use-quota';
import { useRouter } from 'next/navigation';

export default function ReviewBookPageWrapper() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
      <ReviewBookPage />
    </Suspense>
  );
}

function ReviewBookPage() {
  const searchParams = useSearchParams();
  const examId = searchParams.get('examId');
  const { isPro, isProPlus, isAdmin, isAuthenticated, loading: authLoading, onboardingCompleted, subscriptionTier } = useAuth();
  const router = useRouter();

  // Subject state
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');

  const [data, setData] = useState<GetReviewQuestionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  // Layer 3：當無錯題時查最近失敗的測驗，區分「真全答對」vs「測驗生成失敗」
  const [recentFailures, setRecentFailures] = useState<Array<{ exam_id: string }>>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showCitation, setShowCitation] = useState(false);
  // 手機/平板版：底部 tab 切換 panel；desktop (lg+) 永遠三欄並排
  const [mobileTab, setMobileTab] = useState<'list' | 'detail' | 'coach'>('detail');
  // 錯題考試 modal
  const [showWrongAnswerExam, setShowWrongAnswerExam] = useState(false);

  // 管理者帳號（ADMIN/SUPER_ADMIN）自動含所有 user-facing tier 功能
  const isFreeUser = subscriptionTier === 'FREE' && !isAdmin;
  const isPro199Only = subscriptionTier === 'PRO_199' && !isAdmin;
  const canChat = isPro || isProPlus || isAdmin; // PRO, PRO_PLUS, ULTRA, ADMIN, SUPER_ADMIN

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

  useEffect(() => {
    if (!activeSubjectId) return;

    // Dev-only mock mode：?mock=1 注入假資料以驗證 UI 排版
    // production build 時 NODE_ENV !== 'development'，此分支會被 Next.js 在 build 時 dead-code-eliminated
    if (
      process.env.NODE_ENV === 'development' &&
      typeof window !== 'undefined' &&
      new URLSearchParams(window.location.search).get('mock') === '1'
    ) {
      setData({
        examTitle: 'Mock 測驗 — 防制洗錢與打擊資恐',
        wrongQuestions: [
          { question: { id:'mock-q1', contentText:'某航空公司導入生成式 AI 聲控客服，提供航班與票務查詢。有人員透過惡意提示，試圖讓系統洩漏內部安檢流程。在此情境中，下列何者為降低提示攻擊(Prompt Injection)風險的最佳策略？',
            options:[{label:'A',text:'導入輸入檢測與回應審核流程，防止敏感指令被執行'},{label:'B',text:'限制 AI 可回應的主題範圍'},{label:'C',text:'每次提問前確認密碼'},{label:'D',text:'移除生成式 AI 改用傳統聊天機器人'}],
            correctAnswer:'A', explanationMarkdown:'本題考核 LLM 安全治理。Prompt Injection 是當前生成式 AI 主要攻擊向量。輸入檢測搭配 RAI 政策可有效阻斷。', tags:['AI 安全'],
            citationChunkId:null, citationDocTitle:null, citationPage:null }, userAnswer:{userChoice:'B'} },
          { question: { id:'mock-q2', contentText:'金融科技公司在信貸決策系統導入反事實解釋(Counterfactual)，主要好處？',
            options:[{label:'A',text:'加快模型訓練速度'},{label:'B',text:'讓被拒客戶知道需要做什麼改變才能核准'},{label:'C',text:'降低運算資源消耗'},{label:'D',text:'自動推薦商品'}],
            correctAnswer:'B', explanationMarkdown:'反事實解釋符合 GDPR 第 22 條對於可解釋性的要求。', tags:['可解釋 AI'],
            citationChunkId:null, citationDocTitle:null, citationPage:null }, userAnswer:{userChoice:'A'} },
          { question: { id:'mock-q3', contentText:'某零售業專案在收集訓練資料時，發現原始客戶分布有性別不平衡，下列何者為合理的偏誤緩解策略？',
            options:[{label:'A',text:'忽略不處理，假設模型會自動修正'},{label:'B',text:'使用 SMOTE 等 oversampling 技術平衡少數類別'},{label:'C',text:'丟棄少數類別資料'},{label:'D',text:'改用更大的模型'}],
            correctAnswer:'B', explanationMarkdown:'資料不平衡是 ML 公平性的關鍵議題。', tags:['ML 公平性'],
            citationChunkId:null, citationDocTitle:null, citationPage:null }, userAnswer:{userChoice:'D'} },
        ],
      } as unknown as GetReviewQuestionsResponse);
      setLoading(false);
      return;
    }

    setLoading(true);
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    // 有 examId 時只用 examId 查（考試可能屬於不同科目）；無 examId 時用 subjectId 查
    reviewService.getWrongQuestions(examId || undefined, examId ? undefined : targetSubjectId).then(res => {
      setData(res);
      setLoading(false);
      // Layer 3：若無錯題，查最近失敗的測驗
      if (res.wrongQuestions.length === 0) {
        examService.getRecentFailures()
          .then(r => setRecentFailures(r.failures || []))
          .catch(() => setRecentFailures([]));
      } else {
        setRecentFailures([]);
      }
    }).catch(() => setLoading(false));
  }, [examId, activeSubjectId, subjects]);

  // Load chat history for current question
  useEffect(() => {
    setShowCitation(false);
    if (!data || data.wrongQuestions.length === 0) return;
    const questionId = data.wrongQuestions[currentIndex].question.id;
    reviewService.getChatHistory(questionId).then(setMessages).catch(() => {});
  }, [data, currentIndex]);

  // L-quota: AI 教練配額守門
  const aiChatGuard = useQuotaGuard('daily_ai_chats');

  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || !data || sending) return;
    if (aiChatGuard.is_blocked) return; // 達上限不送
    const questionId = data.wrongQuestions[currentIndex].question.id;

    const userMsg: ChatMessage = {
      id: `msg_user_${Date.now()}`,
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setSending(true);

    try {
      const res = await reviewService.sendMessage({
        questionId,
        message: userMsg.content,
        conversationHistory: [...messages, userMsg],
      });
      setMessages(prev => [...prev, res.reply]);
      invalidateQuotaCache(); // L-quota: AI 對話 +1
    } finally {
      setSending(false);
    }
  }, [chatInput, data, currentIndex, messages, sending, aiChatGuard.is_blocked]);

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="flex-1 flex flex-col h-screen bg-slate-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (data.wrongQuestions.length === 0) {
    const hasRecentFailures = recentFailures.length > 0;
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className="mx-auto mb-4"><TiTiLogo size={64} /></div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              {hasRecentFailures ? '無錯題記錄' : '全部答對！'}
            </h2>
            <p className="text-slate-500 mb-6">
              {hasRecentFailures
                ? '目前該學科沒有錯題記錄。'
                : '目前該學科沒有錯題，太厲害了！'}
            </p>
            {hasRecentFailures && (
              <div className="mb-6 mx-auto text-left bg-rose-50 border border-rose-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-rose-700 mb-1">⚠️ 偵測到 {recentFailures.length} 個最近失敗的測驗，可能是 AI 出題失敗導致無錯題記錄：</p>
                <ul className="text-xs text-rose-600 space-y-1">
                  {recentFailures.slice(0, 3).map(f => (
                    <li key={f.exam_id}>• 測驗 {f.exam_id.slice(0, 8)}…（生成失敗）</li>
                  ))}
                </ul>
              </div>
            )}
            <Link href="/dashboard" className="bg-emerald-500 text-white px-6 py-3 rounded-xl font-bold hover:bg-emerald-600 transition-colors">
              回到儀表板
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const current = data.wrongQuestions[currentIndex];
  const { question, userAnswer } = current;
  const correctOption = question.options.find(o => o.label === question.correctAnswer);
  const wrongOption = question.options.find(o => o.label === userAnswer.userChoice);

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between shrink-0 gap-2 sm:gap-3">
        <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
          <Link href="/dashboard" className="text-slate-400 hover:text-slate-600 transition-colors shrink-0">
            <ChevronLeft className="h-5 w-5" />
          </Link>
          <div className="min-w-0">
            <h1 className="text-base sm:text-xl font-bold text-slate-900 truncate">錯題本與 AI 教練</h1>
            <p className="text-xs sm:text-sm text-slate-500 truncate">{data.examTitle} • 第 {currentIndex + 1}/{data.wrongQuestions.length} 題</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* 錯題考試入口（4 階段智能挑題） */}
          <button
            onClick={() => setShowWrongAnswerExam(true)}
            disabled={data.wrongQuestions.length === 0}
            className="bg-emerald-500 hover:bg-emerald-600 text-white px-3 sm:px-4 py-1.5 rounded-full text-xs sm:text-sm font-bold shadow-sm flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
            title="從錯題本智能挑題進行考試"
          >
            🎯<span className="hidden sm:inline">考錯題</span>
          </button>
          {subjects.length > 0 && (
            <SubjectSwitcher
              subjects={subjects}
              activeSubjectId={activeSubjectId}
              onSwitch={(id) => { setActiveSubjectId(id); localStorage.setItem('certimate_active_subject_id', id); }}
              onAddSubject={() => router.push('/onboarding')}
              allowAdd={false}
              variant="compact"
            />
          )}
        </div>
      </header>

      {/* 錯題考試 Modal */}
      {showWrongAnswerExam && (
        <WrongAnswerExamModal
          subjectId={subjects.find(s => s.id === activeSubjectId)?.subjectId || activeSubjectId}
          onClose={() => setShowWrongAnswerExam(false)}
        />
      )}

      <div className="flex-1 flex overflow-hidden pb-14 lg:pb-0">
        {/* Left Sidebar: Wrong Questions List */}
        <div className={`${mobileTab === 'list' ? 'flex' : 'hidden'} lg:flex w-full lg:w-56 border-r border-slate-200 bg-white flex-col shrink-0`}>
          <div className="p-3 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">錯題列表</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {data.wrongQuestions.map((wq, idx) => (
              <button
                key={wq.question.id}
                onClick={() => { setCurrentIndex(idx); setMobileTab('detail'); }}
                className={`w-full text-left p-3 border-b border-slate-100 transition-colors ${
                  idx === currentIndex ? 'bg-emerald-50 border-l-2 border-l-emerald-500' : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                    idx === currentIndex ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                  }`}>
                    Q{idx + 1}
                  </span>
                  <span className="text-[10px] text-slate-400">選了 {wq.userAnswer.userChoice}</span>
                  {wq.isMastered && (
                    <span className="ml-auto text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-bold">✓ 已掌握</span>
                  )}
                </div>
                <p className="text-xs text-slate-600 line-clamp-2">{wq.question.contentText.slice(0, 50)}...</p>
                <div className="flex items-center justify-between mt-1">
                  {wq.question.tags[0] && (
                    <span className="text-[10px] text-slate-400">{wq.question.tags[0]}</span>
                  )}
                  {/* Streak 進度小圓點 */}
                  {!wq.isMastered && typeof wq.correctStreak === 'number' && (
                    <span className="flex items-center gap-0.5 text-[10px] text-slate-400" title={`連續答對 ${wq.correctStreak}/${wq.streakTarget ?? 2} 次後自動消除`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${(wq.correctStreak ?? 0) >= 1 ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                      <span className={`w-1.5 h-1.5 rounded-full ${(wq.correctStreak ?? 0) >= 2 ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Center Panel: Question & Answer */}
        <div className={`${mobileTab === 'detail' ? 'flex' : 'hidden'} lg:flex flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 border-r border-slate-200 bg-white flex-col`}>
          <div className="max-w-3xl mx-auto w-full">
            {/* Question */}
            <div className="mb-8">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 text-rose-700 text-xs font-bold uppercase tracking-wider border border-rose-100">
                  答錯
                </div>
                {/* 已掌握 toggle 按鈕 */}
                <button
                  onClick={async () => {
                    try {
                      if (current.isMastered) {
                        await reviewService.unmarkMastered(question.id);
                      } else {
                        await reviewService.markMastered(question.id);
                      }
                      // 更新本地 state
                      setData(prev => prev ? {
                        ...prev,
                        wrongQuestions: prev.wrongQuestions.map((wq, i) => i === currentIndex
                          ? { ...wq, isMastered: !wq.isMastered }
                          : wq),
                      } : prev);
                    } catch (e) {
                      console.warn('Mark mastered failed:', e);
                    }
                  }}
                  className={`text-xs font-bold px-3 py-1 rounded-full border transition-colors ${
                    current.isMastered
                      ? 'bg-emerald-100 text-emerald-700 border-emerald-200 hover:bg-emerald-200'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-emerald-400 hover:text-emerald-600'
                  }`}
                  title={current.isMastered ? '取消已掌握標記' : '標記為已掌握，從錯題本移除'}
                >
                  {current.isMastered ? '✓ 已掌握（取消）' : '☐ 標記已掌握'}
                </button>
              </div>
              {/* Streak 進度提示 */}
              {!current.isMastered && (current.correctStreak ?? 0) < (current.streakTarget ?? 2) && (
                <p className="text-xs text-slate-500 mb-3 italic">
                  💪 再連續答對 {(current.streakTarget ?? 2) - (current.correctStreak ?? 0)} 次此題就會自動從錯題本消除
                </p>
              )}
              <MathContent className="text-lg text-slate-900 leading-relaxed font-medium">
                {question.contentText}
              </MathContent>
            </div>

            {/* User's Wrong Answer */}
            {wrongOption && (
              <div className="mb-6 p-5 rounded-2xl border-2 border-rose-200 bg-rose-50 relative">
                <div className="absolute -top-3 left-4 bg-rose-100 text-rose-700 px-2 py-0.5 rounded text-xs font-bold border border-rose-200">
                  你的答案
                </div>
                <div className="flex items-start gap-4">
                  <div className="flex items-center justify-center h-6 w-6 rounded-full border-2 border-rose-500 bg-rose-500 mt-0.5 shrink-0">
                    <span className="text-xs font-bold text-white">{userAnswer.userChoice}</span>
                  </div>
                  <span className="text-rose-900 font-medium">{wrongOption.text}</span>
                </div>
              </div>
            )}

            {/* Correct Answer */}
            {correctOption && (
              <div className="p-5 rounded-2xl border-2 border-emerald-500 bg-emerald-50 relative">
                <div className="absolute -top-3 left-4 bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded text-xs font-bold border border-emerald-200">
                  正確解答
                </div>
                <div className="flex items-start gap-4">
                  <div className="flex items-center justify-center h-6 w-6 rounded-full border-2 border-emerald-500 bg-emerald-500 mt-0.5 shrink-0">
                    <span className="text-xs font-bold text-white">{question.correctAnswer}</span>
                  </div>
                  <span className="text-emerald-900 font-medium">{correctOption.text}</span>
                </div>
              </div>
            )}

            {/* Citation */}
            {question.citationChunkId && (
              <div className="mt-6 rounded-xl border border-slate-200 overflow-hidden">
                <div className="bg-slate-50 px-3 py-2 border-b border-slate-200 flex items-center gap-2 text-xs font-medium text-slate-600">
                  <FileText className="h-3 w-3 text-blue-500" /> 溯源來源
                </div>
                <div className="p-4 bg-yellow-50/30">
                  <p className="text-sm text-slate-700 italic border-l-2 border-yellow-400 pl-3">
                    {question.explanationMarkdown.slice(0, 150)}
                  </p>
                </div>
              </div>
            )}

            {/* Detailed Explanation */}
            {question.explanationMarkdown && (
              <div className="mt-8 rounded-xl border border-slate-200 overflow-hidden relative">
                <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-bold text-slate-700">
                    <Sparkles className="h-4 w-4 text-emerald-500" /> 詳細解析
                  </div>
                  {/* Citation button (visible to PRO_199+) */}
                  {isPro && question.citationChunkId && (
                    <div className="relative">
                      <button
                        onClick={() => setShowCitation(prev => !prev)}
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors font-medium px-2 py-1 rounded-md hover:bg-blue-50"
                      >
                        <BookOpen className="h-3 w-3" /> 查看來源
                      </button>
                      {showCitation && (
                        <div className="absolute right-0 top-full mt-1 z-20 w-72 bg-white border border-slate-200 rounded-xl shadow-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <FileText className="h-4 w-4 text-blue-500 shrink-0" />
                            <span className="text-sm font-semibold text-slate-800">{question.citationDocTitle || '來源文件'}</span>
                          </div>
                          {question.citationPage && (
                            <p className="text-xs text-slate-500">第 {question.citationPage} 頁</p>
                          )}
                          {!question.citationDocTitle && !question.citationPage && (
                            <p className="text-xs text-slate-500">來源區塊 ID: {question.citationChunkId}</p>
                          )}
                          <button
                            onClick={() => setShowCitation(false)}
                            className="mt-3 text-xs text-slate-400 hover:text-slate-600 transition-colors"
                          >
                            關閉
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="p-5 bg-white prose prose-sm prose-slate max-w-none relative">
                  <div className={`text-sm text-slate-700 leading-relaxed whitespace-pre-line ${isFreeUser ? 'select-none' : ''}`}>
                    {question.explanationMarkdown}
                  </div>
                  {/* FREE user glassmorphism paywall over explanation */}
                  {isFreeUser && (
                    <div className="absolute inset-0 backdrop-blur-md bg-white/60 z-10 flex items-center justify-center p-6">
                      <div className="bg-white p-6 rounded-2xl shadow-xl border border-slate-100 max-w-sm text-center">
                        <div className="mx-auto h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center mb-4">
                          <Lock className="h-6 w-6 text-indigo-500" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 mb-2">升級 PRO 方案，解鎖完整詳解與 AI 教練</h3>
                        <p className="text-sm text-slate-500 mb-5">
                          完整的詳細解析與 AI 教練深度對話，助你徹底掌握每道錯題。
                        </p>
                        <Link href="/account" className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold transition-colors shadow-md">
                          <Sparkles className="h-4 w-4" /> 立即升級
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: AI Tutor */}
        <div className={`${mobileTab === 'coach' ? 'flex' : 'hidden'} lg:flex w-full lg:w-[400px] bg-slate-50 flex-col shrink-0 relative`}>
          <div className="p-4 border-b border-slate-200 bg-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-emerald-500" />
            <h2 className="font-bold text-slate-900">AI 蘇格拉底教練</h2>
            <span className="ml-auto"><QuotaBadge quotaKey="daily_ai_chats" variant="pill" /></span>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 relative">
            {messages.map(msg => (
              msg.role === 'ai' ? (
                <div key={msg.id} className="flex gap-4">
                  <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                    <Sparkles className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-slate-200 text-sm text-slate-700 leading-relaxed">
                    <MathContent>{msg.content}</MathContent>
                    {msg.citationSource && (
                      <p className="mt-2 text-slate-500 italic text-xs">
                        來源：{msg.citationSource.label}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div key={msg.id} className="flex gap-4 flex-row-reverse">
                  <div className="h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0">
                    <span className="text-sm font-bold text-slate-600">U</span>
                  </div>
                  <div className="bg-emerald-500 text-white p-4 rounded-2xl rounded-tr-none shadow-sm text-sm leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              )
            ))}

            {sending && (
              <div className="flex gap-4">
                <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                  <Sparkles className="h-5 w-5 text-emerald-600" />
                </div>
                <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-slate-200">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.1s]" />
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            )}

            {/* FREE: 簡化提示（主要升級卡已在解析區域，這裡只放輕量提示避免重複） */}
            {isFreeUser && messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center px-6 opacity-60">
                <Lock className="h-8 w-8 text-slate-300 mb-3" />
                <p className="text-sm text-slate-400">升級 PRO 方案即可使用 AI 教練</p>
              </div>
            )}

            {/* PRO_199: can see explanation but AI chat is locked */}
            {isPro199Only && (
              <div className="absolute inset-x-0 bottom-0 top-32 bg-white/90 z-10 flex flex-col items-center justify-center p-8 text-center">
                <div className="bg-white p-6 rounded-3xl shadow-xl border border-slate-100 max-w-sm">
                  <div className="mx-auto h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center mb-4">
                    <Lock className="h-6 w-6 text-indigo-500" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mb-2">AI 教練深度對話為 PRO+ 專屬功能</h3>
                  <p className="text-sm text-slate-500 mb-6">
                    升級至 PRO_PLUS 方案，解鎖 AI 教練無限追問與深度對話。
                  </p>
                  <Link href="/account" className="w-full bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold transition-colors flex items-center justify-center gap-2 shadow-md">
                    <Sparkles className="h-4 w-4" /> 升級 PRO_PLUS (NT$399/月)
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="p-4 bg-white border-t border-slate-200">
            {/* PRO_199 lockout message */}
            {isPro199Only && (
              <div className="text-center py-3">
                <p className="text-sm text-slate-500 font-medium mb-1">AI 教練深度對話為 PRO+ 專屬功能</p>
                <Link href="/account" className="text-xs text-emerald-600 hover:text-emerald-700 underline transition-colors">
                  升級至 PRO_PLUS 解鎖
                </Link>
              </div>
            )}
            {/* FREE lockout - input hidden */}
            {isFreeUser && (
              <div className="text-center py-3 opacity-50">
                <p className="text-sm text-slate-400">升級方案以使用 AI 教練</p>
              </div>
            )}
            {/* Functional chat input for PRO_PLUS / ULTRA */}
            {canChat && (
              <>
                {aiChatGuard.is_blocked && !aiChatGuard.isUnlimited && (
                  <div className="mb-2 px-3 py-2 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center justify-between gap-2">
                    <span>今日 AI 教練對話已達上限</span>
                    <Link href="/account" className="text-emerald-600 hover:text-emerald-700 underline font-medium shrink-0">升級解鎖</Link>
                  </div>
                )}
                <div className="relative">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                    placeholder={aiChatGuard.is_blocked && !aiChatGuard.isUnlimited ? '今日已達上限...' : '向 AI 教練追問...'}
                    className="w-full pl-4 pr-12 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all text-sm disabled:bg-slate-100 disabled:cursor-not-allowed"
                    disabled={sending || (aiChatGuard.is_blocked && !aiChatGuard.isUnlimited)}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={sending || !chatInput.trim() || (aiChatGuard.is_blocked && !aiChatGuard.isUnlimited)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 bg-emerald-500 text-white rounded-lg flex items-center justify-center hover:bg-emerald-600 transition-colors disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-2 flex justify-between items-center px-1">
                  <span className="text-[10px] text-slate-400">支援 KaTeX 數學公式渲染（行內 $x^2$、區塊 $$...$$）</span>
                  {sending && (
                    <span className="text-[10px] text-emerald-600 flex items-center gap-1">
                      <RefreshCw className="h-3 w-3 animate-spin" /> 思考中...
                    </span>
                  )}
                </div>
                {/* Legal disclaimer */}
                <p className="text-xs text-slate-400 italic mt-2">
                  *AI 生成內容僅供參考，請隨時自行查證重要資訊。*
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Mobile / Tablet bottom tab bar — only visible < lg */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-slate-200 grid grid-cols-3 shadow-[0_-2px_8px_rgba(0,0,0,0.04)]">
        {([
          { id: 'list' as const, label: '錯題列表', icon: '📋', count: data.wrongQuestions.length as number | undefined },
          { id: 'detail' as const, label: '題目解析', icon: '📝', count: undefined as number | undefined },
          { id: 'coach' as const, label: 'AI 教練', icon: '✨', count: undefined as number | undefined },
        ]).map(t => (
          <button
            key={t.id}
            onClick={() => setMobileTab(t.id)}
            className={`flex flex-col items-center justify-center py-2.5 gap-0.5 text-[11px] font-medium transition-colors min-h-[56px] ${
              mobileTab === t.id ? 'text-emerald-600 bg-emerald-50' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <span className="text-base leading-none">{t.icon}</span>
            <span className="leading-tight">{t.label}{t.count !== undefined ? ` (${t.count})` : ''}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
