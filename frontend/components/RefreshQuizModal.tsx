'use client';

import { useState } from 'react';
import { X, Zap, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api/client';

interface Question {
  id: string;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

interface RefreshQuizModalProps {
  topicId: string;
  topicName: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete: (result: { allCorrect: boolean; effectiveProgress: number }) => void;
}

export default function RefreshQuizModal({
  topicId,
  topicName,
  isOpen,
  onClose,
  onComplete,
}: RefreshQuizModalProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    allCorrect: boolean;
    effectiveProgress: number;
    message: string;
  } | null>(null);

  const startQuiz = async () => {
    setLoading(true);
    setResult(null);
    setAnswers({});
    try {
      const res = await apiClient.get<{ questions: Question[] }>(
        `/topics/${topicId}/refresh-quiz`
      );
      setQuestions(res.questions || []);
    } catch {
      setQuestions([]);
    } finally {
      setLoading(false);
    }
  };

  const submitQuiz = async () => {
    setSubmitting(true);
    try {
      const answerList = Object.entries(answers).map(([qid, ans]) => ({
        question_id: qid,
        selected_answer: ans,
      }));
      const res = await apiClient.post<{
        all_correct: boolean;
        effective_progress: number;
        message: string;
      }>(`/topics/${topicId}/refresh-quiz/submit`, { answers: answerList });

      setResult({
        allCorrect: res.all_correct,
        effectiveProgress: res.effective_progress,
        message: res.message,
      });
      onComplete({
        allCorrect: res.all_correct,
        effectiveProgress: res.effective_progress,
      });
    } catch {
      setResult({ allCorrect: false, effectiveProgress: 0, message: '提交失敗' });
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b bg-amber-50">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-500" />
            <h3 className="font-bold text-slate-900">記憶喚醒</h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-amber-100 rounded-lg">
            <X className="h-5 w-5 text-slate-500" />
          </button>
        </div>

        <div className="p-5">
          {/* 初始狀態 */}
          {questions.length === 0 && !loading && !result && (
            <div className="text-center py-6">
              <div className="text-4xl mb-3">🧠</div>
              <p className="text-slate-700 font-medium mb-1">「{topicName}」記憶已衰退</p>
              <p className="text-sm text-slate-500 mb-5">
                完成迷你測驗即可恢復進度，全部答對可延長複習間隔！
              </p>
              <button
                onClick={startQuiz}
                className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
              >
                開始喚醒測驗
              </button>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-amber-500" />
              <span className="ml-2 text-slate-500">載入題目中...</span>
            </div>
          )}

          {/* 題目列表 */}
          {questions.length > 0 && !result && (
            <div className="space-y-5">
              {questions.map((q, idx) => (
                <div key={q.id} className="space-y-2">
                  <p className="text-sm font-medium text-slate-800">
                    {idx + 1}. {q.content}
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {['A', 'B', 'C', 'D'].map((letter) => {
                      const optionText = q[`option_${letter.toLowerCase()}` as keyof Question] as string;
                      const isSelected = answers[q.id] === letter;
                      return (
                        <button
                          key={letter}
                          onClick={() => setAnswers(prev => ({ ...prev, [q.id]: letter }))}
                          className={`text-left px-3 py-2 rounded-lg text-sm border transition-colors ${
                            isSelected
                              ? 'border-amber-500 bg-amber-50 text-amber-800'
                              : 'border-slate-200 hover:border-amber-300 text-slate-600'
                          }`}
                        >
                          <span className="font-medium">{letter}.</span> {optionText}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              <button
                onClick={submitQuiz}
                disabled={Object.keys(answers).length < questions.length || submitting}
                className="w-full bg-amber-500 hover:bg-amber-600 disabled:bg-slate-300 text-white py-2.5 rounded-xl font-medium transition-colors"
              >
                {submitting ? '批改中...' : `提交 (${Object.keys(answers).length}/${questions.length})`}
              </button>
            </div>
          )}

          {/* 結果 */}
          {result && (
            <div className="text-center py-6">
              {result.allCorrect ? (
                <>
                  <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
                  <p className="text-lg font-bold text-emerald-700">記憶喚醒成功！</p>
                  <p className="text-sm text-slate-500 mt-1">
                    進度已恢復至 {Math.round(result.effectiveProgress * 100)}%
                  </p>
                </>
              ) : (
                <>
                  <XCircle className="h-12 w-12 text-amber-500 mx-auto mb-3" />
                  <p className="text-lg font-bold text-amber-700">部分答錯</p>
                  <p className="text-sm text-slate-500 mt-1">{result.message}</p>
                </>
              )}
              <button
                onClick={onClose}
                className="mt-5 bg-slate-900 hover:bg-slate-800 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
              >
                關閉
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
