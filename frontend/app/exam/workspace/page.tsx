'use client';

import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Clock, Flag, ChevronLeft, ChevronRight, LayoutGrid, Pause, Play } from 'lucide-react';
import { examService } from '@/lib/api/services';
import type { Question } from '@/types';

const STORAGE_KEY_PREFIX = 'certimate_exam_';

interface ExamState {
  answers: Record<string, string>;
  markedForReview: string[];
  timeRemaining: number;
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function MockExamWorkspacePageWrapper() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center bg-slate-900"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
      <MockExamWorkspacePage />
    </Suspense>
  );
}

function MockExamWorkspacePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const examId = searchParams.get('examId') || 'exam_001';

  const [questions, setQuestions] = useState<Question[]>([]);
  const [examTitle, setExamTitle] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [markedForReview, setMarkedForReview] = useState<Set<string>>(new Set());
  const [timeRemaining, setTimeRemaining] = useState(7200);
  const [loading, setLoading] = useState(true);
  const [showGrid, setShowGrid] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const submitCalledRef = useRef(false);

  // Load exam data
  useEffect(() => {
    const storageKey = `${STORAGE_KEY_PREFIX}${examId}`;
    examService.getExam(examId).then(res => {
      setQuestions(res.questions);
      setExamTitle(res.exam.title);

      // Restore from localStorage if exists
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          const state: ExamState = JSON.parse(saved);
          setAnswers(state.answers || {});
          setMarkedForReview(new Set(state.markedForReview || []));
          setTimeRemaining(state.timeRemaining || res.exam.timeLimit);
        } catch {
          setTimeRemaining(res.exam.timeLimit);
        }
      } else {
        setTimeRemaining(res.exam.timeLimit);
      }

      setLoading(false);
    });
  }, [examId]);

  // Auto-save to localStorage (debounced)
  useEffect(() => {
    if (loading) return;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      const state: ExamState = {
        answers,
        markedForReview: Array.from(markedForReview),
        timeRemaining,
      };
      localStorage.setItem(`${STORAGE_KEY_PREFIX}${examId}`, JSON.stringify(state));
    }, 500);
  }, [answers, markedForReview, timeRemaining, examId, loading]);

  // Warn user before closing/refreshing the page during an active exam
  useEffect(() => {
    if (loading || submitCalledRef.current) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [loading]);

  const handleSubmit = useCallback(async () => {
    if (submitCalledRef.current) return;
    submitCalledRef.current = true;
    localStorage.removeItem(`${STORAGE_KEY_PREFIX}${examId}`);
    const answerArray = questions.map(q => ({
      questionId: q.id,
      userChoice: answers[q.id] || '',
    }));
    await examService.submit({
      examId,
      answers: answerArray,
      timeSpentSeconds: 7200 - timeRemaining,
    });
    router.push(`/exam/results?examId=${examId}`);
  }, [answers, examId, questions, timeRemaining, router]);

  // Countdown timer (pauses when isPaused is true)
  useEffect(() => {
    if (loading || isPaused) return;
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [loading, isPaused, handleSubmit]);

  const selectAnswer = (questionId: string, optionLabel: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionLabel }));
  };

  const confirmSubmit = useCallback(() => {
    const unansweredCount = questions.filter(q => !answers[q.id]).length;
    if (unansweredCount > 0) {
      setShowSubmitConfirm(true);
    } else {
      handleSubmit();
    }
  }, [questions, answers, handleSubmit]);

  const toggleMark = (questionId: string) => {
    setMarkedForReview(prev => {
      const next = new Set(prev);
      if (next.has(questionId)) next.delete(questionId);
      else next.add(questionId);
      return next;
    });
  };

  if (loading || questions.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-900">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const isTimeLow = timeRemaining < 300;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50">
      {/* Top Bar */}
      <header className="bg-slate-900 text-slate-300 px-6 py-3 flex items-center justify-between shrink-0 shadow-md z-10">
        <div className="flex items-center gap-6">
          <h1 className="text-lg font-bold text-white tracking-wider">{examTitle}</h1>
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex items-center gap-2 text-sm font-medium">
            <span className="text-slate-400">Question</span>
            <span className="text-white text-base">{currentIndex + 1}</span>
            <span className="text-slate-500">of {questions.length}</span>
          </div>
        </div>

        <div className="flex items-center gap-8">
          <div className={`flex items-center gap-2 bg-slate-800 px-4 py-1.5 rounded-full border border-slate-700 ${isTimeLow ? 'animate-pulse' : ''}`}>
            <Clock className={`h-4 w-4 ${isTimeLow ? 'text-rose-600' : 'text-emerald-400'}`} />
            <span className={`font-mono font-bold tracking-wider ${isTimeLow ? 'text-rose-600' : 'text-emerald-400'}`}>
              {formatTime(timeRemaining)}
            </span>
          </div>

          <button
            onClick={() => setShowGrid(!showGrid)}
            className="text-sm font-medium hover:text-white transition-colors flex items-center gap-2"
          >
            <LayoutGrid className="h-4 w-4" /> 總覽
          </button>
          <button
            onClick={() => setIsPaused(true)}
            className="text-sm font-medium hover:text-white transition-colors flex items-center gap-2"
          >
            <Pause className="h-4 w-4" /> 暫停測驗
          </button>
          <button
            onClick={confirmSubmit}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-1.5 rounded-full text-sm font-bold transition-colors"
          >
            交卷 ({answeredCount}/{questions.length})
          </button>
        </div>
      </header>

      {/* Main */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Question Navigation */}
        <div className="w-64 border-r border-slate-200 bg-white flex flex-col shrink-0">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">題號導覽</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="grid grid-cols-4 gap-2">
              {questions.map((q, i) => {
                const isCurrent = i === currentIndex;
                const isAnswered = !!answers[q.id];
                const isMarked = markedForReview.has(q.id);

                let stateClass = 'bg-slate-200 border-slate-200 text-slate-600 hover:border-emerald-300';
                if (isCurrent) stateClass = 'bg-slate-900 border-slate-900 text-white font-bold shadow-md';
                else if (isMarked) stateClass = 'bg-yellow-400 border-yellow-400 text-slate-900';
                else if (isAnswered) stateClass = 'bg-emerald-500 border-emerald-500 text-white';

                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(i)}
                    className={`h-10 w-10 rounded-lg border flex items-center justify-center text-sm transition-colors relative ${stateClass}`}
                  >
                    {i + 1}
                    {isMarked && !isCurrent && (
                      <Flag className="absolute -top-1 -right-1 h-3 w-3 text-amber-500 fill-amber-500" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="p-4 border-t border-slate-200 bg-slate-50 text-xs text-slate-500 space-y-2">
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-slate-900" /> 目前題目</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-emerald-500" /> 已作答</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-slate-200" /> 未作答</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-yellow-400" /> 標記複習</div>
          </div>
        </div>

        {/* Center: Question Content */}
        <div className="flex-1 flex flex-col bg-white relative">
          <div className="flex-1 overflow-y-auto p-8 md:p-12 lg:px-24">
            {/* Question Header */}
            <div className="flex items-start justify-between mb-8">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold uppercase tracking-wider border border-blue-100">
                {currentQuestion.tags[0] || '一般題'}
              </div>
              <button
                onClick={() => toggleMark(currentQuestion.id)}
                className={`flex items-center gap-2 transition-colors ${
                  markedForReview.has(currentQuestion.id) ? 'text-amber-600' : 'text-slate-500 hover:text-amber-600'
                }`}
              >
                <Flag className={`h-5 w-5 ${markedForReview.has(currentQuestion.id) ? 'fill-amber-500' : ''}`} />
                <span className="text-sm font-medium">
                  {markedForReview.has(currentQuestion.id) ? '已標記' : '標記以供複習'}
                </span>
              </button>
            </div>

            {/* Question Text */}
            <div className="prose prose-slate max-w-none mb-10">
              <p className="text-xl text-slate-900 leading-relaxed font-medium whitespace-pre-line">
                {currentQuestion.contentText}
              </p>
            </div>

            {/* Options */}
            <div className="space-y-4">
              {currentQuestion.options.map(option => {
                const isSelected = answers[currentQuestion.id] === option.label;
                return (
                  <button
                    key={option.label}
                    onClick={() => selectAnswer(currentQuestion.id, option.label)}
                    className={`w-full text-left flex items-start gap-4 p-5 rounded-2xl border-2 transition-all ${
                      isSelected
                        ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                        : 'border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/30'
                    }`}
                  >
                    <div className={`flex items-center justify-center h-6 w-6 rounded-full border-2 mt-0.5 shrink-0 ${
                      isSelected ? 'border-emerald-500 bg-emerald-500' : 'border-slate-300'
                    }`}>
                      {isSelected ? (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      ) : (
                        <span className="text-xs font-bold text-slate-500">{option.label}</span>
                      )}
                    </div>
                    <span className={`text-lg ${isSelected ? 'font-medium text-emerald-900' : 'text-slate-700'}`}>
                      {option.text}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bottom Navigation */}
          <div className="bg-slate-50 border-t border-slate-200 p-4 flex items-center justify-between shrink-0">
            <button
              onClick={() => setCurrentIndex(i => Math.max(0, i - 1))}
              disabled={currentIndex === 0}
              className="flex items-center gap-2 px-6 py-3 rounded-xl font-medium text-slate-600 hover:bg-slate-200 transition-colors disabled:opacity-30"
            >
              <ChevronLeft className="h-5 w-5" /> 上一題
            </button>
            <button
              onClick={() => setCurrentIndex(i => Math.min(questions.length - 1, i + 1))}
              disabled={currentIndex === questions.length - 1}
              className="flex items-center gap-2 px-8 py-3 rounded-xl font-bold text-white bg-slate-900 hover:bg-slate-800 transition-colors shadow-md disabled:opacity-30"
            >
              下一題 <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Pause Modal */}
      {isPaused && (
        <div className="fixed inset-0 z-50 bg-slate-900/80 flex items-center justify-center">
          <div className="bg-white rounded-3xl p-10 max-w-sm w-full shadow-2xl text-center">
            <div className="flex items-center justify-center w-16 h-16 mx-auto mb-6 rounded-full bg-amber-50 border-2 border-amber-200">
              <Pause className="h-8 w-8 text-amber-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">測驗已暫停</h2>
            <p className="text-slate-500 mb-8">計時器已停止，按下按鈕繼續作答。</p>
            <button
              onClick={() => setIsPaused(false)}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition-colors flex items-center justify-center gap-2"
            >
              <Play className="h-5 w-5" /> 繼續作答
            </button>
          </div>
        </div>
      )}

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
          <div className="bg-white rounded-3xl p-10 max-w-sm w-full shadow-2xl text-center">
            <h2 className="text-xl font-bold text-slate-900 mb-4">確認交卷</h2>
            <p className="text-slate-600 mb-8">
              你還有 {questions.filter(q => !answers[q.id]).length} 題未作答，確定要交卷嗎？
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowSubmitConfirm(false)}
                className="flex-1 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-300 transition-colors"
              >
                繼續作答
              </button>
              <button
                onClick={() => { setShowSubmitConfirm(false); handleSubmit(); }}
                className="flex-1 py-3 bg-rose-600 text-white rounded-xl font-bold hover:bg-rose-500 transition-colors"
              >
                確定交卷
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Overview Modal */}
      {showGrid && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center" onClick={() => setShowGrid(false)}>
          <div className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-bold text-slate-900 mb-6">作答總覽</h2>
            <div className="grid grid-cols-5 sm:grid-cols-10 gap-3 mb-6">
              {questions.map((q, i) => {
                const isAnswered = !!answers[q.id];
                const isMarked = markedForReview.has(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => { setCurrentIndex(i); setShowGrid(false); }}
                    className={`h-10 w-10 rounded-xl flex items-center justify-center font-bold text-sm relative ${
                      isMarked
                        ? 'bg-yellow-400 border-2 border-yellow-400 text-slate-900'
                        : isAnswered
                        ? 'bg-emerald-500 border-2 border-emerald-500 text-white'
                        : 'bg-slate-200 border-2 border-slate-200 text-slate-500'
                    }`}
                  >
                    {i + 1}
                    {isMarked && <Flag className="absolute -top-1 -right-1 h-3 w-3 text-amber-500 fill-amber-500" />}
                  </button>
                );
              })}
            </div>
            <div className="flex justify-between text-sm text-slate-500">
              <span>已作答：{answeredCount}/{questions.length}</span>
              <span>標記複習：{markedForReview.size}</span>
            </div>
            <button
              onClick={() => setShowGrid(false)}
              className="w-full mt-6 py-3 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition-colors"
            >
              關閉
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
