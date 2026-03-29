'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, FileText, Youtube, BrainCircuit, Play, Lock } from 'lucide-react';
import { documentService, examService, subjectService } from '@/lib/api/services';
import type { Document, QuestionType, UserSubject, SubscriptionTier } from '@/types';
import ExamLoadingOverlay from '@/components/ExamLoadingOverlay';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import { useAuth } from '@/lib/auth-context';

const QUESTION_COUNTS = [10, 20, 50, 100] as const;

const TIER_QUESTION_LIMITS: Record<SubscriptionTier, { max: number; upgradeMessage: string | null }> = {
  FREE: { max: 10, upgradeMessage: 'FREE 方案每次測驗最多 10 題，升級 PRO 最多可出 50 題' },
  PRO_199: { max: 50, upgradeMessage: 'PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上' },
  PRO_PLUS_399: { max: 50, upgradeMessage: 'PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上' },
  ULTRA_1599: { max: Infinity, upgradeMessage: null },
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

export default function ExamSetupPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, onboardingCompleted, subscriptionTier } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Subject state
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');

  // Setup state
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const [questionCount, setQuestionCount] = useState<typeof QUESTION_COUNTS[number]>(20);
  const [difficulty, setDifficulty] = useState<1 | 2 | 3>(2);
  const [questionTypes, setQuestionTypes] = useState<Set<QuestionType>>(
    new Set(['MULTIPLE_CHOICE'])
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedExamId, setGeneratedExamId] = useState<string | null>(null);

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
      if (res.subjects.length > 0) setActiveSubjectId(res.subjects[0].id);
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load & filter docs by active subject
  useEffect(() => {
    if (!activeSubjectId) return;

    setLoadingDocs(true);
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    documentService.list().then(res => {
      setDocuments(res.documents.filter(d =>
        d.status === 'COMPLETED' && d.subjectId === targetSubjectId
      ));
      setLoadingDocs(false);
    }).catch(() => setLoadingDocs(false));
  }, [activeSubjectId, subjects]);

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

  const handleGenerate = useCallback(async () => {
    if (selectedDocIds.size === 0) {
      setValidationError('請至少選擇一個知識範圍');
      return;
    }
    setValidationError(null);
    setIsGenerating(true);

    try {
      const result = await examService.create({
        config: {
          selectedDocumentIds: Array.from(selectedDocIds),
          questionCount,
          difficulty,
          questionTypes: Array.from(questionTypes),
        },
      });
      const examId = result.exam?.id || result.exam_id || result.examId;
      setGeneratedExamId(examId);
    } catch (e) {
      console.error('Exam generation failed:', e);
      setIsGenerating(false);
    }
  }, [selectedDocIds, questionCount, difficulty, questionTypes]);

  const handleLoadingComplete = useCallback(() => {
    if (generatedExamId) {
      router.push(`/exam/workspace?examId=${generatedExamId}`);
    }
  }, [generatedExamId, router]);

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
      <SubjectSwitcher
        subjects={subjects}
        activeSubjectId={activeSubjectId}
        onSwitch={setActiveSubjectId}
        onAddSubject={() => router.push('/onboarding')}
        allowAdd={false}
      />
      
      <div className="flex-1 overflow-y-auto py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <ExamLoadingOverlay
            stages={LOADING_STAGES}
            onComplete={handleLoadingComplete}
            isVisible={isGenerating}
          />

      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-slate-900 mb-4">自訂模擬考卷</h1>
        <p className="text-slate-600">選擇你想測驗的範圍與難度，AI 將為你動態生成專屬考題。</p>
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="grid md:grid-cols-2">
          {/* Left Column: Scope Selection */}
          <div className="p-8 border-b md:border-b-0 md:border-r border-slate-200 bg-slate-50/50">
            <h2 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 text-sm">1</span>
              選擇測驗範圍
            </h2>

            {loadingDocs ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-20 bg-slate-200 rounded-2xl animate-pulse" />
                ))}
              </div>
            ) : (
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
            )}
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
                <label className="block text-sm font-medium text-slate-700 mb-3">題數選擇</label>
                <div className="grid grid-cols-4 gap-2">
                  {QUESTION_COUNTS.map(count => {
                    const isLocked = count > tierLimit.max;
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
                {tierLimit.upgradeMessage && (
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
            </div>
          </div>
        </div>

        {/* Action Footer */}
        <div className="bg-slate-900 p-6 flex items-center justify-between">
          <div className="text-slate-300 text-sm">
            {validationError ? (
              <span className="text-red-400">{validationError}</span>
            ) : selectedDocIds.size === 0 ? (
              <span className="text-amber-400">請先選擇至少一份學習資源</span>
            ) : (
              <>已選 <span className="text-white font-medium">{selectedDocIds.size}</span> 份資源 • 預計生成時間：<span className="text-white font-medium">約 15 秒</span></>
            )}
          </div>
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="bg-emerald-500 hover:bg-emerald-400 text-white px-8 py-3 rounded-xl font-bold transition-colors flex items-center gap-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="h-5 w-5 fill-current" /> 生成專屬模擬考
          </button>
        </div>
        </div>
      </div>
    </div>
    </div>
  );
}
