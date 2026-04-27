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
import Link from 'next/link';
import { reviewService, subjectService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import type { GetReviewQuestionsResponse, ChatMessage, UserSubject } from '@/types';
import SubjectSwitcher from '@/components/SubjectSwitcher';
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
  const [currentIndex, setCurrentIndex] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showCitation, setShowCitation] = useState(false);

  const isFreeUser = subscriptionTier === 'FREE' && !isAdmin;
  const isPro199Only = subscriptionTier === 'PRO_199' && !isAdmin;
  const canChat = isPro || isProPlus || isAdmin; // PRO, PRO_PLUS, ULTRA, ADMIN

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

    setLoading(true);
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    // 有 examId 時只用 examId 查（考試可能屬於不同科目）；無 examId 時用 subjectId 查
    reviewService.getWrongQuestions(examId || undefined, examId ? undefined : targetSubjectId).then(res => {
      setData(res);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [examId, activeSubjectId, subjects]);

  // Load chat history for current question
  useEffect(() => {
    setShowCitation(false);
    if (!data || data.wrongQuestions.length === 0) return;
    const questionId = data.wrongQuestions[currentIndex].question.id;
    reviewService.getChatHistory(questionId).then(setMessages).catch(() => {});
  }, [data, currentIndex]);

  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || !data || sending) return;
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
    } finally {
      setSending(false);
    }
  }, [chatInput, data, currentIndex, messages, sending]);

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
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4"><TiTiLogo size={64} /></div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">全部答對！</h2>
            <p className="text-slate-500 mb-6">目前該學科沒有錯題，太厲害了！</p>
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
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0 gap-3">
        <div className="flex items-center gap-4 min-w-0">
          <Link href="/dashboard" className="text-slate-400 hover:text-slate-600 transition-colors shrink-0">
            <ChevronLeft className="h-5 w-5" />
          </Link>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-slate-900 truncate">錯題本與 AI 教練</h1>
            <p className="text-sm text-slate-500 truncate">{data.examTitle} • 第 {currentIndex + 1}/{data.wrongQuestions.length} 題</p>
          </div>
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

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Wrong Questions List */}
        <div className="w-56 border-r border-slate-200 bg-white flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">錯題列表</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {data.wrongQuestions.map((wq, idx) => (
              <button
                key={wq.question.id}
                onClick={() => setCurrentIndex(idx)}
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
                </div>
                <p className="text-xs text-slate-600 line-clamp-2">{wq.question.contentText.slice(0, 50)}...</p>
                {wq.question.tags[0] && (
                  <span className="text-[10px] text-slate-400 mt-1 block">{wq.question.tags[0]}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Center Panel: Question & Answer */}
        <div className="flex-1 overflow-y-auto p-8 border-r border-slate-200 bg-white">
          <div className="max-w-3xl mx-auto">
            {/* Question */}
            <div className="mb-8">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 text-rose-700 text-xs font-bold uppercase tracking-wider border border-rose-100 mb-4">
                答錯
              </div>
              <p className="text-lg text-slate-900 leading-relaxed font-medium whitespace-pre-line">
                {question.contentText}
              </p>
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
        <div className="w-[400px] bg-slate-50 flex flex-col shrink-0 relative">
          <div className="p-4 border-b border-slate-200 bg-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-emerald-500" />
            <h2 className="font-bold text-slate-900">AI 蘇格拉底教練</h2>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 relative">
            {messages.map(msg => (
              msg.role === 'ai' ? (
                <div key={msg.id} className="flex gap-4">
                  <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                    <Sparkles className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-slate-200 text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                    {msg.content}
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
                <div className="relative">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                    placeholder="向 AI 教練追問..."
                    className="w-full pl-4 pr-12 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all text-sm"
                    disabled={sending}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={sending || !chatInput.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 bg-emerald-500 text-white rounded-lg flex items-center justify-center hover:bg-emerald-600 transition-colors disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-2 flex justify-between items-center px-1">
                  <span className="text-[10px] text-slate-400">支援 KaTeX 數學公式渲染</span>
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
    </div>
  );
}
