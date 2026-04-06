'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft, Brain, TrendingUp, TrendingDown, Minus, Sparkles,
  Target, Clock, Trash2, AlertTriangle, BarChart3, FileText,
  BookOpen, Calendar, Lightbulb, Download, ClipboardList,
  ChevronDown, ChevronUp, XCircle, CheckCircle2,
} from 'lucide-react';

import { useAuth } from '@/lib/auth-context';
import { adminService } from '@/lib/api/services';
import type { Student } from '@/types';

// ─── Types ───────────────────────────────────────────────────────────────────

interface CompetencyItem {
  label: string;
  score: number;
  color: string;
}

interface AiSuggestion {
  topic: string;
  suggestion: string;
  action_type: 'review' | 'quiz' | 'explore';
}

interface WrongAnswer {
  question_number: number;
  content: string;
  student_answer: string;
  correct_answer: string;
  explanation: string;
  difficulty: string | null;
}

interface ExamHistoryItem {
  exam_id: string;
  score: number | null;
  total_questions: number;
  correct_count: number | null;
  wrong_count: number;
  submitted_at: string | null;
  wrong_answers: WrongAnswer[];
}

interface StudentReport {
  student_id: string;
  name: string;
  email: string;
  exam_count: number;
  average_score: number | null;
  strengths: string[];
  weaknesses: string[];
  recent_activity: unknown[];
  exam_history?: ExamHistoryItem[];
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function TrendIcon({ trend }: { trend: Student['trend'] }) {
  if (trend === 'up') return <TrendingUp className="h-4 w-4 text-emerald-500" />;
  if (trend === 'down') return <TrendingDown className="h-4 w-4 text-rose-500" />;
  return <Minus className="h-4 w-4 text-slate-400" />;
}

function StatusBadge({ status }: { status: Student['status'] }) {
  const map = {
    active: 'bg-emerald-100 text-emerald-800',
    needs_attention: 'bg-rose-100 text-rose-700',
    inactive: 'bg-slate-100 text-slate-600',
  } as const;
  const labels = { active: '活躍', needs_attention: '需關注', inactive: '未啟用' } as const;
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium ${map[status]}`}>
      {labels[status]}
    </span>
  );
}

function CompetencyBar({ label, score, color }: { label: string; score: number; color?: string }) {
  const barColor = color
    ? (color === 'green' ? 'bg-emerald-500' : color === 'orange' ? 'bg-amber-400' : 'bg-rose-500')
    : (score >= 70 ? 'bg-emerald-500' : score >= 40 ? 'bg-amber-400' : 'bg-rose-500');
  const dotColor = color
    ? (color === 'green' ? 'bg-emerald-400' : color === 'orange' ? 'bg-amber-400' : 'bg-rose-400')
    : (score >= 70 ? 'bg-emerald-400' : score >= 40 ? 'bg-amber-400' : 'bg-rose-400');
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className={`h-2 w-2 rounded-full ${dotColor} shrink-0`} />
      <span className="w-32 text-slate-600 truncate shrink-0 font-medium">{label}</span>
      <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className="w-10 text-right font-bold text-slate-700">{score}</span>
    </div>
  );
}

function SuggestionCard({ suggestion }: { suggestion: AiSuggestion }) {
  const iconMap = {
    review: { icon: BookOpen, color: 'bg-blue-50 text-blue-500', label: '複習' },
    quiz: { icon: ClipboardList, color: 'bg-amber-50 text-amber-500', label: '練習' },
    explore: { icon: Lightbulb, color: 'bg-emerald-50 text-emerald-500', label: '探索' },
  };
  const { icon: Icon, color, label } = iconMap[suggestion.action_type] || iconMap.review;
  return (
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
      <div className="flex items-start gap-3">
        <div className={`h-9 w-9 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-bold text-slate-900">{suggestion.topic}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-500 font-medium">{label}</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">{suggestion.suggestion}</p>
        </div>
      </div>
    </div>
  );
}

function ExamCard({ exam }: { exam: ExamHistoryItem }) {
  const [expanded, setExpanded] = useState(false);
  const date = exam.submitted_at ? new Date(exam.submitted_at) : null;
  const dateStr = date
    ? `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    : '未知日期';
  const scoreColor = (exam.score || 0) >= 70 ? 'text-emerald-600' : (exam.score || 0) >= 50 ? 'text-amber-600' : 'text-rose-600';
  const wrongCount = exam.wrong_answers.length;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Exam summary row */}
      <div
        className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
          <FileText className="h-5 w-5 text-indigo-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-900">{dateStr}</span>
            <span className="text-xs text-slate-400">共 {exam.total_questions} 題</span>
          </div>
          <div className="flex items-center gap-3 mt-0.5 text-xs">
            <span className="flex items-center gap-1 text-emerald-600">
              <CheckCircle2 className="h-3 w-3" /> {exam.correct_count ?? 0} 題正確
            </span>
            {wrongCount > 0 && (
              <span className="flex items-center gap-1 text-rose-500">
                <XCircle className="h-3 w-3" /> {wrongCount} 題錯誤
              </span>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className={`text-2xl font-extrabold ${scoreColor}`}>
            {exam.score ?? '—'}
          </div>
          <div className="text-[10px] text-slate-400">分</div>
        </div>
        {wrongCount > 0 && (
          expanded
            ? <ChevronUp className="h-4 w-4 text-slate-400 shrink-0" />
            : <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
        )}
      </div>

      {/* Wrong answers detail */}
      {expanded && wrongCount > 0 && (
        <div className="border-t border-slate-100 bg-rose-50/30">
          <div className="px-5 py-3">
            <h4 className="text-xs font-bold text-rose-700 mb-3 flex items-center gap-1.5">
              <XCircle className="h-3.5 w-3.5" />
              錯題詳情（{wrongCount} 題）
            </h4>
            <div className="space-y-3">
              {exam.wrong_answers.map((wa, i) => (
                <div key={i} className="bg-white rounded-lg border border-rose-100 p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-bold text-rose-500 bg-rose-100 rounded-full h-6 w-6 flex items-center justify-center shrink-0">
                      {wa.question_number}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-800 leading-relaxed mb-2">{wa.content}</p>
                      <div className="flex items-center gap-4 text-xs mb-2">
                        <span className="text-rose-600">
                          學生作答：<span className="font-bold">{wa.student_answer || '未作答'}</span>
                        </span>
                        <span className="text-emerald-600">
                          正確答案：<span className="font-bold">{wa.correct_answer}</span>
                        </span>
                        {wa.difficulty && (
                          <span className="text-slate-400">
                            難度：{wa.difficulty === 'easy' ? '簡單' : wa.difficulty === 'medium' ? '中等' : '困難'}
                          </span>
                        )}
                      </div>
                      {wa.explanation && (
                        <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
                          <div className="flex items-center gap-1.5 mb-1">
                            <Lightbulb className="h-3 w-3 text-blue-500" />
                            <span className="text-[10px] font-bold text-blue-700">解析</span>
                          </div>
                          <p className="text-xs text-blue-800 leading-relaxed">{wa.explanation}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function StudentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;
  const { loading: authLoading, isAuthenticated } = useAuth();

  const [student, setStudent] = useState<Student | null>(null);
  const [report, setReport] = useState<StudentReport | null>(null);
  const [competencies, setCompetencies] = useState<CompetencyItem[]>([]);
  const [suggestions, setSuggestions] = useState<AiSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  const [removeInput, setRemoveInput] = useState('');
  const [removing, setRemoving] = useState(false);
  const [showRemediation, setShowRemediation] = useState(false);
  const [remediationWeights, setRemediationWeights] = useState<Record<string, number>>({});
  const [remediationCount, setRemediationCount] = useState(20);
  const [remediationGenerating, setRemediationGenerating] = useState(false);
  const [remediationResult, setRemediationResult] = useState<{ exam_id: string; question_count: number; distribution: { label: string; count: number }[] } | null>(null);
  const [remediationError, setRemediationError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (authLoading || !isAuthenticated || !studentId) return;

    const fetchAll = async () => {
      setIsLoading(true);
      setError(null);

      const [reportResult, competencyResult, studentListResult] = await Promise.allSettled([
        adminService.getStudentReport(studentId),
        adminService.getStudentCompetency(studentId),
        adminService.getStudentList(),
      ]);

      if (reportResult.status === 'fulfilled' && reportResult.value && !reportResult.value.error) {
        setReport(reportResult.value);
      }

      if (competencyResult.status === 'fulfilled' && competencyResult.value?.competencies) {
        setCompetencies(competencyResult.value.competencies);
      }

      if (studentListResult.status === 'fulfilled' && studentListResult.value?.students) {
        const found = studentListResult.value.students.find((s: Student) => s.id === studentId);
        if (found) {
          setStudent(found);
        } else {
          setError('找不到此學員');
        }
      } else {
        setError('無法載入學員資料');
      }

      setIsLoading(false);
    };
    fetchAll();
  }, [studentId, authLoading, isAuthenticated]);

  // Fetch remediation defaults from API when panel opens; fall back to local calculation
  useEffect(() => {
    if (!showRemediation || !studentId) return;
    let cancelled = false;

    const fetchDefaults = async () => {
      try {
        const res = await adminService.getRemediationDefaults(studentId) as { defaults?: { label: string; weight: number }[] };
        if (cancelled) return;
        if (res?.defaults && Array.isArray(res.defaults)) {
          const weights: Record<string, number> = {};
          res.defaults.forEach((d: { label: string; weight: number }) => {
            weights[d.label] = d.weight;
          });
          setRemediationWeights(weights);
          return;
        }
      } catch {
        // API failed — fall through to local calculation
      }
      if (cancelled) return;
      // Fallback: compute from competency scores
      if (competencies.length > 0) {
        const weights: Record<string, number> = {};
        competencies.forEach(c => {
          weights[c.label] = c.score < 40 ? 50 : c.score < 70 ? 30 : 20;
        });
        const total = Object.values(weights).reduce((a, b) => a + b, 0);
        if (total > 0) {
          Object.keys(weights).forEach(k => {
            weights[k] = Math.round((weights[k] / total) * 100);
          });
        }
        setRemediationWeights(weights);
      }
    };

    fetchDefaults();
    return () => { cancelled = true; };
  }, [showRemediation, studentId, competencies]);

  const handleGenerateRemediation = async () => {
    setRemediationGenerating(true);
    try {
      const competencyWeights = Object.entries(remediationWeights).map(([label, weight]) => ({
        label,
        weight,
      }));
      const result = await adminService.createStudentRemediation(studentId, {
        question_count: remediationCount,
        competency_weights: competencyWeights,
      }) as { exam_id: string; question_count: number; distribution: { label: string; count: number }[] };

      setRemediationResult(result);
      setRemediationError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : '生成補考失敗，請稍後再試';
      setRemediationError(message);
    } finally {
      setRemediationGenerating(false);
    }
  };

  const handleRequestSuggestions = async () => {
    setSuggestionsLoading(true);
    try {
      const result = await adminService.getAiSuggestions(studentId);
      if (result?.suggestions) {
        setSuggestions(result.suggestions);
      }
    } catch {
      alert('無法取得 AI 建議，請稍後再試');
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const handleRemoveStudent = async () => {
    if (!student || removeInput !== student.name) return;
    setRemoving(true);
    try {
      await adminService.removeStudent(student.id);
      router.replace('/edu-console');
    } catch {
      alert('移除學員失敗，請稍後再試');
    } finally {
      setRemoving(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center h-[calc(100vh-64px)] bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500" />
          <p className="text-slate-500 font-medium">載入學員資料中...</p>
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="flex-1 flex items-center justify-center h-[calc(100vh-64px)] bg-slate-50">
        <div className="text-center space-y-4">
          <AlertTriangle className="h-12 w-12 text-amber-400 mx-auto" />
          <p className="text-slate-600 font-medium">{error || '找不到此學員'}</p>
          <button
            onClick={() => router.push('/edu-console')}
            className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
          >
            返回管理中心
          </button>
        </div>
      </div>
    );
  }

  const examCount = report?.exam_count ?? 0;
  const examHistory = report?.exam_history ?? [];
  const strengths = report?.strengths ?? [];
  const weaknesses = report?.weaknesses ?? [];

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-slate-50">
      {/* Header */}
      <header className="bg-slate-900 text-white px-6 py-4 flex items-center gap-4 shrink-0 shadow-md z-10">
        <button
          onClick={() => router.push('/edu-console')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          <span className="text-sm font-medium">返回</span>
        </button>
        <div className="h-5 w-px bg-slate-700" />
        <div className="flex-1">
          <h1 className="text-lg font-bold">{student.name}</h1>
          <p className="text-xs text-slate-400">{student.email}</p>
        </div>
        <button
          onClick={() => alert('匯出功能即將推出！')}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors bg-slate-800 px-3 py-2 rounded-lg border border-slate-700"
        >
          <Download className="h-3.5 w-3.5" />
          匯出報告
        </button>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="max-w-5xl mx-auto space-y-6">

          {/* ❶ Profile Card */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-start gap-5 flex-wrap md:flex-nowrap">
              <div className="h-16 w-16 rounded-2xl bg-indigo-100 flex items-center justify-center shrink-0">
                <span className="text-2xl font-bold text-indigo-600">{student.name[0]}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1 flex-wrap">
                  <h2 className="text-xl font-bold text-slate-900">{student.name}</h2>
                  <TrendIcon trend={student.trend} />
                  <StatusBadge status={student.status} />
                </div>
                <p className="text-sm text-slate-500">{student.email}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                  {student.group && (
                    <span>群組：<span className="font-medium text-slate-600">{student.group}</span></span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    最後活躍：{student.lastActiveLabel || '無紀錄'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ❷ Stats Grid (3 cards — removed 能力面向) */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-4 w-4 text-indigo-500" />
                <span className="text-xs text-slate-500 font-medium">平均分數</span>
              </div>
              <div className={`text-3xl font-extrabold ${(student.averageScore || 0) >= 70 ? 'text-emerald-600' : (student.averageScore || 0) >= 50 ? 'text-amber-600' : 'text-slate-400'}`}>
                {report?.average_score ?? student.averageScore ?? '—'}
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-emerald-500" />
                <span className="text-xs text-slate-500 font-medium">學習進度</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{student.progress}%</div>
              <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${student.progress >= 70 ? 'bg-emerald-500' : student.progress >= 40 ? 'bg-amber-400' : 'bg-slate-300'}`} style={{ width: `${student.progress}%` }} />
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-violet-500" />
                <span className="text-xs text-slate-500 font-medium">完成考試</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{examCount}</div>
              <div className="text-xs text-slate-400 mt-1">次模擬考</div>
            </div>
          </div>

          {/* ❸ Competency Analysis */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-indigo-500" />
                <h2 className="text-base font-bold text-slate-900">能力分析</h2>
              </div>
              {competencies.length > 0 && (
                <div className="flex items-center gap-3 text-[10px] text-slate-400">
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-400" /> 精熟 (≥70)</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400" /> 普通 (40-69)</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-rose-400" /> 弱點 (&lt;40)</span>
                </div>
              )}
            </div>
            {competencies.length > 0 ? (
              <div className="space-y-3">
                {competencies.map(c => (
                  <CompetencyBar key={c.label} label={c.label} score={c.score} color={c.color} />
                ))}
              </div>
            ) : student.competencies && student.competencies.length > 0 ? (
              <div className="space-y-3">
                {student.competencies.map(c => (
                  <CompetencyBar key={c.label} label={c.label} score={c.score} />
                ))}
              </div>
            ) : (
              <p className="text-center py-8 text-slate-400 text-sm">尚無能力分析資料</p>
            )}
          </div>

          {/* ❹ Exam History with Wrong Answers */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center gap-2 mb-5">
              <ClipboardList className="h-5 w-5 text-violet-500" />
              <h2 className="text-base font-bold text-slate-900">考試歷程</h2>
              {examHistory.length > 0 && (
                <span className="text-xs text-slate-400 ml-auto">共 {examHistory.length} 次考試</span>
              )}
            </div>
            {examHistory.length > 0 ? (
              <div className="space-y-3">
                {examHistory.map(exam => (
                  <ExamCard key={exam.exam_id} exam={exam} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-8 w-8 text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400">此學員尚無考試記錄</p>
              </div>
            )}
          </div>

          {/* ❺ Strengths & Weaknesses */}
          {(strengths.length > 0 || weaknesses.length > 0) && (
            <div className="grid md:grid-cols-2 gap-4">
              {strengths.length > 0 && (
                <div className="bg-emerald-50 rounded-2xl p-5 border border-emerald-100">
                  <h3 className="text-sm font-bold text-emerald-800 mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" /> 強項領域
                  </h3>
                  <div className="space-y-2">
                    {strengths.map(s => (
                      <div key={s} className="text-sm text-emerald-700 bg-white/60 rounded-lg px-3 py-2">{s}</div>
                    ))}
                  </div>
                </div>
              )}
              {weaknesses.length > 0 && (
                <div className="bg-rose-50 rounded-2xl p-5 border border-rose-100">
                  <h3 className="text-sm font-bold text-rose-800 mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" /> 弱點領域
                  </h3>
                  <div className="space-y-2">
                    {weaknesses.map(w => (
                      <div key={w} className="text-sm text-rose-700 bg-white/60 rounded-lg px-3 py-2">{w}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ❻ AI Suggestions */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-violet-500" />
                <h2 className="text-base font-bold text-slate-900">AI 個人化補強建議</h2>
              </div>
              {suggestions.length === 0 && (
                <button
                  onClick={handleRequestSuggestions}
                  disabled={suggestionsLoading}
                  className="flex items-center gap-2 text-xs font-bold text-violet-600 hover:text-violet-500 bg-violet-50 hover:bg-violet-100 px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {suggestionsLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-violet-500" />
                      分析中...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      生成建議
                    </>
                  )}
                </button>
              )}
            </div>
            {suggestions.length > 0 ? (
              <div className="space-y-3">
                {suggestions.map((s, i) => (
                  <SuggestionCard key={i} suggestion={s} />
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <Lightbulb className="h-8 w-8 text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400">點擊「生成建議」，AI 將根據弱點分析提供個人化學習建議</p>
              </div>
            )}
          </div>

          {/* ❼ Remediation Exam */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            {!showRemediation ? (
              <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
                <button
                  onClick={() => setShowRemediation(true)}
                  className="p-5 hover:bg-slate-50 transition-colors flex items-center gap-4 text-left"
                >
                  <div className="h-11 w-11 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
                    <Target className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">指派補考</h3>
                    <p className="text-xs text-slate-500 mt-0.5">設定各能力比例，生成個人化補救試卷</p>
                  </div>
                </button>
                <button
                  onClick={() => alert('複習排程功能即將推出！')}
                  className="p-5 hover:bg-slate-50 transition-colors flex items-center gap-4 text-left"
                >
                  <div className="h-11 w-11 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                    <Calendar className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">複習排程</h3>
                    <p className="text-xs text-slate-500 mt-0.5">查看此學員的艾賓浩斯複習日程</p>
                  </div>
                </button>
              </div>
            ) : (
              <div className="p-6">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-2">
                    <Target className="h-5 w-5 text-amber-500" />
                    <h2 className="text-base font-bold text-slate-900">指派補考 — 出題比例設定</h2>
                  </div>
                  <button
                    onClick={() => setShowRemediation(false)}
                    className="text-xs text-slate-400 hover:text-slate-600"
                  >
                    取消
                  </button>
                </div>

                <p className="text-xs text-slate-500 mb-4">
                  調整各能力領域的出題比例，弱點領域預設分配較高比重。總和需為 100%。
                </p>

                {/* Question count */}
                <div className="flex items-center gap-3 mb-5">
                  <span className="text-sm font-medium text-slate-700">出題數量：</span>
                  <div className="flex items-center gap-1">
                    {[10, 20, 30, 50].map(n => (
                      <button
                        key={n}
                        onClick={() => setRemediationCount(n)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                          remediationCount === n
                            ? 'bg-amber-500 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {n} 題
                      </button>
                    ))}
                  </div>
                </div>

                {/* Weight sliders */}
                <div className="space-y-4 mb-6">
                  {competencies.map(c => {
                    const weight = remediationWeights[c.label] ?? 0;
                    const dotColor = c.color === 'green' ? 'bg-emerald-400' : c.color === 'orange' ? 'bg-amber-400' : 'bg-rose-400';
                    const questionCount = Math.round((weight / 100) * remediationCount);
                    return (
                      <div key={c.label}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <div className={`h-2 w-2 rounded-full ${dotColor}`} />
                            <span className="text-sm font-medium text-slate-700">{c.label}</span>
                            <span className="text-[10px] text-slate-400">能力 {c.score}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">{questionCount} 題</span>
                            <span className="text-sm font-bold text-slate-900 w-10 text-right">{weight}%</span>
                          </div>
                        </div>
                        <input
                          type="range"
                          min={0}
                          max={100}
                          value={weight}
                          onChange={e => {
                            const newVal = parseInt(e.target.value);
                            const others = Object.entries(remediationWeights).filter(([k]) => k !== c.label);
                            const othersTotal = others.reduce((a, [, v]) => a + v, 0);
                            const remaining = 100 - newVal;

                            const updated = { ...remediationWeights, [c.label]: newVal };
                            // Proportionally redistribute remaining to others
                            if (othersTotal > 0) {
                              others.forEach(([k, v]) => {
                                updated[k] = Math.round((v / othersTotal) * remaining);
                              });
                            } else {
                              // Edge case: all others are 0
                              const perOther = Math.round(remaining / others.length);
                              others.forEach(([k], i) => {
                                updated[k] = i === others.length - 1
                                  ? remaining - perOther * (others.length - 1)
                                  : perOther;
                              });
                            }
                            // Fix rounding so total = 100
                            const sum = Object.values(updated).reduce((a, b) => a + b, 0);
                            if (sum !== 100 && others.length > 0) {
                              updated[others[0][0]] += 100 - sum;
                            }
                            setRemediationWeights(updated);
                          }}
                          className="w-full h-2 bg-slate-100 rounded-full appearance-none cursor-pointer accent-amber-500"
                        />
                      </div>
                    );
                  })}
                </div>

                {/* Total check */}
                {(() => {
                  const total = Object.values(remediationWeights).reduce((a, b) => a + b, 0);
                  return total !== 100 ? (
                    <div className="text-xs text-rose-500 mb-3">
                      目前比例總和為 {total}%，需調整至 100%
                    </div>
                  ) : null;
                })()}

                {/* Preview distribution */}
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 mb-5">
                  <div className="text-xs font-bold text-slate-600 mb-2">出題分配預覽</div>
                  <div className="flex h-4 rounded-full overflow-hidden">
                    {competencies.map(c => {
                      const weight = remediationWeights[c.label] ?? 0;
                      if (weight === 0) return null;
                      const bgColor = c.color === 'green' ? 'bg-emerald-500' : c.color === 'orange' ? 'bg-amber-400' : 'bg-rose-500';
                      return (
                        <div
                          key={c.label}
                          className={`${bgColor} relative group`}
                          style={{ width: `${weight}%` }}
                          title={`${c.label}: ${Math.round((weight / 100) * remediationCount)} 題`}
                        />
                      );
                    })}
                  </div>
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    {competencies.map(c => {
                      const weight = remediationWeights[c.label] ?? 0;
                      if (weight === 0) return null;
                      const dotColor = c.color === 'green' ? 'bg-emerald-400' : c.color === 'orange' ? 'bg-amber-400' : 'bg-rose-400';
                      return (
                        <span key={c.label} className="flex items-center gap-1 text-[10px] text-slate-500">
                          <span className={`h-2 w-2 rounded-full ${dotColor}`} />
                          {c.label} {Math.round((weight / 100) * remediationCount)} 題
                        </span>
                      );
                    })}
                  </div>
                </div>

                <button
                  onClick={handleGenerateRemediation}
                  disabled={remediationGenerating || competencies.length === 0}
                  className="w-full bg-amber-500 hover:bg-amber-400 disabled:bg-slate-200 disabled:text-slate-400 text-white py-3 rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2"
                >
                  {remediationGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <Target className="h-4 w-4" />
                      生成 {remediationCount} 題補考試卷
                    </>
                  )}
                </button>

                {remediationResult && (
                  <div className="mt-4 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                    <p className="text-sm font-semibold text-emerald-700 mb-2">✅ 已成功生成 {remediationResult.question_count} 題補考試卷</p>
                    <div className="space-y-1">
                      {remediationResult.distribution.map(d => (
                        <div key={d.label} className="flex justify-between text-xs text-emerald-600">
                          <span>{d.label}</span>
                          <span>{d.count} 題</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {remediationError && (
                  <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl">
                    <p className="text-sm text-rose-600">{remediationError}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ❽ Danger Zone */}
          <div className="bg-white rounded-2xl shadow-sm border border-rose-200 p-6">
            <h2 className="text-base font-bold text-rose-700 mb-1">危險操作</h2>
            <p className="text-xs text-slate-500 mb-4">移除學員後，該學員將失去機構權限，此操作無法復原。</p>

            {showRemoveConfirm ? (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-3">
                <p className="text-sm text-rose-700">
                  請輸入學員姓名「<span className="font-bold">{student.name}</span>」以確認移除：
                </p>
                <input
                  autoFocus
                  value={removeInput}
                  onChange={e => setRemoveInput(e.target.value)}
                  placeholder={student.name}
                  className="w-full px-3 py-2 border border-rose-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-400"
                />
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleRemoveStudent}
                    disabled={removeInput !== student.name || removing}
                    className="bg-rose-600 hover:bg-rose-500 disabled:bg-slate-200 disabled:text-slate-400 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
                  >
                    {removing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                        移除中...
                      </>
                    ) : (
                      <>
                        <Trash2 className="h-4 w-4" />
                        確認移除
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => { setShowRemoveConfirm(false); setRemoveInput(''); }}
                    className="text-sm text-slate-500 hover:text-slate-700"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowRemoveConfirm(true)}
                className="flex items-center gap-2 text-sm text-rose-600 hover:text-rose-500 font-medium px-4 py-2 rounded-lg hover:bg-rose-50 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                移除此學生
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
