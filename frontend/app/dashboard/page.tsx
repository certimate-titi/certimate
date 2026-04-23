'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Upload, Youtube, FileText, Image as ImageIcon, Clock, TrendingUp, BookOpen, Calendar as CalendarIcon, ChevronLeft, ChevronRight, Play, AlertCircle, Sparkles, Lock, CheckCircle2, XCircle, RefreshCw, MessageSquare, Loader2 } from 'lucide-react';
import { dashboardService, documentService, subjectService, resourceParseService } from '@/lib/api/services';
import type { GetDashboardResponse, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import StreakCounter from '@/components/StreakCounter';
import DailyQuestCard from '@/components/DailyQuestCard';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import SubjectPickerModal from '@/components/SubjectPickerModal';
import AnnouncementBanner from '@/components/AnnouncementBanner';
import PendingJourneysBanner from '@/components/PendingJourneysBanner';
import StudyBuddyBanner from '@/components/StudyBuddyBanner';
import DomainRadarChart from '@/components/DomainRadarChart';
import type { SelectedSubject } from '@/components/onboarding/SelectedSubjectCard';

export default function DashboardPage() {
  const { user, isAuthenticated, loading: authLoading, onboardingCompleted, isProPlus, isUltra, subscriptionTier } = useAuth();
  const router = useRouter();
  const [showModeTooltip, setShowModeTooltip] = useState(false);

  const [data, setData] = useState<GetDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'pending' | 'processing' | 'completed' | 'failed'>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadErrorMessage, setUploadErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Calendar state
  const [calendarMonth, setCalendarMonth] = useState(new Date().getMonth() + 1); // 1-12
  const [calendarYear, setCalendarYear] = useState(new Date().getFullYear());

  // Subject state
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');
  const [showAddSubject, setShowAddSubject] = useState(false);

  // Onboarding guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (!onboardingCompleted) {
      router.replace('/onboarding');
    }
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load subjects
  useEffect(() => {
    if (authLoading || !isAuthenticated || !onboardingCompleted) return;
    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects || []);
      if (res.subjects && res.subjects.length > 0) {
        const saved = localStorage.getItem('certimate_active_subject_id');
        const match = saved && res.subjects.find((s: UserSubject) => s.id === saved);
        setActiveSubjectId(match ? saved : res.subjects[0].id);
      }
    }).catch(() => setSubjects([]));
  }, [authLoading, isAuthenticated, onboardingCompleted]);

  // Merge main dashboard response with quests + review-calendar endpoints.
  const loadDashboardData = useCallback(async (subjectId?: string) => {
    const [d, questsRes, calRes] = await Promise.all([
      dashboardService.get(subjectId),
      dashboardService.getDailyQuests().catch(() => ({ quests: [] })),
      dashboardService.getReviewCalendar().catch(() => ({ calendar: [], subject: null, month: null })),
    ]);
    const quests = (questsRes.quests || []).map((q: any) => ({
      id: q.id,
      type: (q.type as 'review' | 'explore' | 'quiz') || 'review',
      description: q.title,
      completed: q.status === 'completed',
      xpReward: 0,
      progress: typeof q.progress === 'number' ? q.progress : undefined,
      target: typeof q.target === 'number' ? q.target : undefined,
    }));
    const calendar = (calRes.calendar || []).map((c) => ({
      date: c.date,
      reviewCount: c.count,
      topics: [] as string[],
    }));
    return {
      ...d,
      dailyQuests: quests,
      reviewCalendar: calendar,
    };
  }, []);

  // Load dashboard data
  useEffect(() => {
    if (authLoading || !isAuthenticated) return;
    if (!onboardingCompleted || !activeSubjectId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    loadDashboardData(activeSubjectId)
      .then((merged) => { setData(merged); setLoading(false); })
      .catch(() => {
        setData({
          user: null as any,
          streak: { currentStreak: 0, longestStreak: 0, freezesRemaining: 0, freezesPerWeek: 0, lastActiveDate: new Date().toISOString() },
          dailyQuests: [],
          activityItems: [],
          reviewCalendar: [],
          stats: { overallAccuracy: 0, totalMocksCompleted: 0, totalQuestionsAnswered: 0, predictedPassRate: 0, examCountdown: null },
          domainStrengths: [],
        });
        setLoading(false);
      });
  }, [activeSubjectId, isAuthenticated, onboardingCompleted, loadDashboardData]);

  const handleFileUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!activeSubjectId) {
      alert('請先選擇或新增備考科目後再上傳資源');
      return;
    }

    // 依檔案類型分級大小限制
    const file = files[0];
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const docExts = ['pdf', 'docx', 'pptx', 'xlsx', 'doc', 'ppt', 'xls', 'md', 'txt'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    const audioExts = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'wma', 'aac'];
    const videoExts = ['mp4', 'mov', 'avi', 'mkv', 'webm'];

    let maxSizeMB = 50; // 預設文件類
    let typeLabel = '文件';
    if (imageExts.includes(ext)) {
      maxSizeMB = 20;
      typeLabel = '圖片';
    } else if (audioExts.includes(ext)) {
      maxSizeMB = 100;
      typeLabel = '音訊';
    } else if (videoExts.includes(ext)) {
      maxSizeMB = 500;
      typeLabel = '影片';
    } else if (!docExts.includes(ext)) {
      alert('不支援的檔案格式');
      return;
    }

    if (file.size > maxSizeMB * 1024 * 1024) {
      alert(`${typeLabel}檔案大小不可超過 ${maxSizeMB}MB`);
      return;
    }

    setUploading(true);
    setUploadStatus('pending');
    setUploadProgress(0);
    const progressInterval = setInterval(() => {
      setUploadProgress(p => {
        if (p >= 20 && uploadStatus !== 'processing') {
          setUploadStatus('processing');
        }
        return Math.min(p + 10, 90);
      });
    }, 300);
    try {
      setUploadErrorMessage(null);
      const uploadRes = await documentService.upload({ file: files[0], title: files[0].name, subjectId: activeSubjectId });
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('completed');
      setData(await loadDashboardData(activeSubjectId));
      // EPIC-035：上傳成功後自動觸發 LLM 解析（非阻塞）
      const resourceId = uploadRes?.document?.id;
      if (resourceId) {
        try { await resourceParseService.triggerParse(resourceId); } catch { /* 忽略配額錯誤，使用者可在資源庫手動觸發 */ }
      }
    } catch (err) {
      clearInterval(progressInterval);
      setUploadErrorMessage(err instanceof Error ? err.message : String(err));
      setUploadStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [activeSubjectId, loadDashboardData]);

  const handleYoutubeSubmit = useCallback(async () => {
    if (!youtubeUrl.trim()) return;
    if (!activeSubjectId) {
      alert('請先選擇或新增備考科目後再上傳資源');
      return;
    }
    setUploading(true);
    setUploadStatus('pending');
    setUploadProgress(0);
    const progressInterval = setInterval(() => {
      setUploadProgress(p => {
        if (p >= 20 && uploadStatus !== 'processing') {
          setUploadStatus('processing');
        }
        return Math.min(p + 8, 90);
      });
    }, 400);
    try {
      setUploadErrorMessage(null);
      const uploadRes = await documentService.upload({ youtubeUrl: youtubeUrl.trim(), subjectId: activeSubjectId });
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('completed');
      setYoutubeUrl('');
      setData(await loadDashboardData(activeSubjectId));
      const resourceId = uploadRes?.document?.id;
      if (resourceId) {
        try { await resourceParseService.triggerParse(resourceId); } catch { /* noop */ }
      }
    } catch (err) {
      clearInterval(progressInterval);
      setUploadErrorMessage(err instanceof Error ? err.message : String(err));
      setUploadStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [youtubeUrl, activeSubjectId, loadDashboardData]);


  const handleAddSubject = useCallback(async (selected: SelectedSubject[]) => {
    const failures: string[] = [];
    for (const s of selected) {
      try {
        await subjectService.addSubject({
          subjectId: s.subjectId,
          subjectName: s.subjectName,
          examDate: s.examDate,
          resultDate: s.resultDate,
          selfAssessment: s.selfAssessment,
        });
      } catch (e: any) {
        const msg = e?.response?.data?.detail?.message || e?.response?.data?.message || e?.message || '未知錯誤';
        failures.push(`${s.subjectName}：${msg}`);
      }
    }
    try {
      const res = await subjectService.getUserSubjects();
      setSubjects(res.subjects);
      if (res.subjects.length > 0 && !activeSubjectId) {
        setActiveSubjectId(res.subjects[0].id);
      }
    } catch { /* silent */ }
    if (failures.length > 0) {
      alert(`部分科目新增失敗：\n\n${failures.join('\n')}`);
    }
    if (failures.length < selected.length) {
      setShowAddSubject(false);
    }
  }, [activeSubjectId]);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // User logged in but hasn't picked a subject yet — show an explicit CTA
  // instead of an infinite skeleton. Uses the in-app SubjectPickerModal
  // (NOT /onboarding) because onboardingCompleted may already be true
  // for admin users — navigating to /onboarding would just bounce back.
  if (!activeSubjectId || subjects.length === 0) {
    return (
      <>
        <div className="min-h-screen flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white rounded-3xl shadow-sm border border-slate-200 p-8 text-center">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-xl font-bold text-slate-800 mb-2">歡迎使用 TiTi</h2>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed">
              你還沒有選擇備考科目。請先新增一個科目，我們會為你準備考古題題庫、
              知識心智圖與 AI 教練。
            </p>
            <button
              onClick={() => setShowAddSubject(true)}
              className="w-full bg-emerald-500 text-white py-3 rounded-full font-medium hover:bg-emerald-600 transition-colors"
            >
              開始選擇科目
            </button>
          </div>
        </div>
        {showAddSubject && (
          <SubjectPickerModal
            excludeSubjectIds={subjects.map(s => s.subjectId)}
            onConfirm={handleAddSubject}
            onClose={() => setShowAddSubject(false)}
          />
        )}
      </>
    );
  }

  if (loading || !data) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-slate-200 rounded w-48" />
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              <div className="h-48 bg-slate-200 rounded-3xl" />
              <div className="h-32 bg-slate-200 rounded-3xl" />
            </div>
            <div className="h-96 bg-slate-200 rounded-3xl" />
          </div>
        </div>
      </div>
    );
  }

  const reviewDates = new Set(data.reviewCalendar.map(r => {
    const d = new Date(r.date);
    return d.getDate();
  }));

  return (
    <>
      {/* System Announcements */}
      <AnnouncementBanner />

      {/* Study buddy (ULTRA only) */}
      <StudyBuddyBanner />

      {/* Pending exam result confirmations */}
      <PendingJourneysBanner />

      {/* No-subject prompt */}
      {subjects.length === 0 && isAuthenticated && onboardingCompleted && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-3">
          <div className="container mx-auto max-w-6xl flex items-center justify-between">
            <span className="text-sm text-amber-800">尚未建立備考科目，請先新增科目以開始學習</span>
            <button onClick={() => setShowAddSubject(true)} className="text-sm font-bold text-amber-700 hover:text-amber-900 underline">新增科目</button>
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header — Row 1: Greeting + Mode Badge / StreakCounter */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-4">
          <div className="min-w-0">
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 truncate">早安，{user?.displayName || '學習者'}！</h1>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <p className="text-sm text-slate-500">今天想從哪裡開始複習？</p>
              {data.stats.examCountdown && (() => {
                const days = data.stats.examCountdown.daysRemaining;
                const mode = days < 14 ? { icon: '🔥', label: 'Sprint 衝刺', color: 'bg-rose-50 text-rose-700 border-rose-200', desc: '距離考試不到 14 天，系統已自動切換至衝刺狀態。', strategy: '重點加強曾答錯的高頻題目與未觸及的盲點。', weights: '未考知識 40% / 曾錯盲點 50% / 其他 10%' }
                  : days <= 90 ? { icon: '🏃', label: 'Standard 正常', color: 'bg-blue-50 text-blue-700 border-blue-200', desc: '1~3 個月備考期，開拓與鞏固並行。', strategy: '兼顧新知識點探索與已有觀念的深化鞏固。', weights: '新知識 40% / 鞏固複習 40% / 弱點 20%' }
                  : { icon: '🌳', label: 'Mastery 長期', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', desc: '超過 3 個月的長久學習，追求抗遺忘與跨域關聯。', strategy: '建立深層記憶與概念串聯，低壓穩步推進。', weights: '跨域關聯 30% / 新知識 40% / 鞏固 30%' };
                return (
                  <div className="relative">
                    <button
                      onClick={() => setShowModeTooltip(!showModeTooltip)}
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border cursor-pointer hover:shadow-sm transition-all ${mode.color}`}
                    >
                      {mode.icon} {mode.label}
                    </button>
                    {showModeTooltip && (
                      <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 p-4 z-30">
                        <h4 className="font-bold text-slate-900 text-sm mb-2">{mode.icon} {mode.label}</h4>
                        <p className="text-xs text-slate-600 mb-2">{mode.desc}</p>
                        <p className="text-xs text-slate-500 mb-2"><strong>策略：</strong>{mode.strategy}</p>
                        <div className="bg-slate-50 rounded-lg p-2">
                          <p className="text-[10px] text-slate-500 font-medium mb-1">配題權重</p>
                          <p className="text-xs text-slate-700">{mode.weights}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0" title={data.streak.freezeConsumedToday ? '休息也是學習的一部分，歡迎回來！' : undefined}>
            <StreakCounter streak={data.streak} />
            {data.streak.freezesRemaining > 0 && (
              <span className="text-xs text-blue-500 whitespace-nowrap">❄️ {data.streak.freezesRemaining}</span>
            )}
          </div>
        </div>

        {/* Header — Row 2: Subject Switcher (full width tab bar) */}
        {subjects.length > 0 && (
          <div className="mb-6">
            <SubjectSwitcher
              subjects={subjects}
              activeSubjectId={activeSubjectId}
              onSwitch={(id) => { setActiveSubjectId(id); localStorage.setItem('certimate_active_subject_id', id); }}
              onAddSubject={() => setShowAddSubject(true)}
              variant="compact"
            />
          </div>
        )}

        {/* Ultra: Co-study counter — requires backend /community/online-count API */}

        {/* Core Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 text-center">
            <Clock className="h-5 w-5 text-amber-500 mx-auto mb-2" />
            <span className="block text-2xl font-extrabold text-slate-900">{data.stats.examCountdown?.daysRemaining ?? '--'}</span>
            <span className="text-xs text-slate-500">距離考試天數</span>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 text-center">
            <BookOpen className="h-5 w-5 text-indigo-500 mx-auto mb-2" />
            <span className="block text-2xl font-extrabold text-slate-900">{data.stats.totalQuestionsAnswered ?? 0}</span>
            <span className="text-xs text-slate-500">累積答題數</span>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 text-center">
            <TrendingUp className="h-5 w-5 text-emerald-500 mx-auto mb-2" />
            <span className="block text-2xl font-extrabold text-slate-900">{data.stats.overallAccuracy}%</span>
            <span className="text-xs text-slate-500">整體答對率</span>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 text-center">
            <Sparkles className="h-5 w-5 text-purple-500 mx-auto mb-2" />
            <span className="block text-2xl font-extrabold text-slate-900">{data.stats.predictedPassRate ?? '--'}%</span>
            <span className="text-xs text-slate-500">預測及格率</span>
          </div>
        </div>

        {/* V3: 有機生長 — 無 decay 提醒，改用進度稀釋 Toast（由 WebSocket 觸發） */}

        <div className="grid lg:grid-cols-3 gap-8 items-start">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Upload Widget */}
            <section className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
              <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                <Upload className="h-5 w-5 text-emerald-500" /> 快速匯入學習資源
              </h2>

              {!activeSubjectId && (
                <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
                  尚未選擇備考科目，請先{' '}
                  <button onClick={() => setShowAddSubject(true)} className="font-bold underline">新增科目</button>{' '}
                  後再上傳資源。
                </div>
              )}

              {/* Upload Status Feedback */}
              {uploadStatus === 'pending' && (
                <div className="mb-4 flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
                  <Clock className="h-4 w-4 text-slate-500 shrink-0" />
                  <p className="text-sm text-slate-600 font-medium">等待處理...</p>
                </div>
              )}
              {uploadStatus === 'processing' && (
                <div className="mb-4">
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      AI 解析中...
                    </span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                  </div>
                  <div className="h-8 bg-slate-100 rounded-lg mt-2 animate-pulse" />
                </div>
              )}
              {uploadStatus === 'completed' && (
                <div className="mb-4 flex items-center justify-between bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    <p className="text-sm text-emerald-800 font-medium">解析完成</p>
                    <Link href="/knowledge" className="text-sm font-bold text-emerald-600 underline underline-offset-2 ml-1">立即查看</Link>
                  </div>
                  <button onClick={() => setUploadStatus('idle')} className="text-emerald-400 hover:text-emerald-600 transition-colors">
                    <XCircle className="h-4 w-4" />
                  </button>
                </div>
              )}
              {uploadStatus === 'failed' && (
                <div className="mb-4 flex items-start justify-between bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
                  <div className="flex items-start gap-2 min-w-0">
                    <XCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-rose-800">解析失敗</p>
                      {uploadErrorMessage && (
                        <p className="text-xs text-rose-700 mt-0.5 break-words whitespace-pre-wrap">{uploadErrorMessage}</p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => { setUploadStatus('idle'); setUploadErrorMessage(null); fileInputRef.current?.click(); }}
                    className="flex items-center gap-1 text-xs font-medium text-rose-600 hover:text-rose-800 ml-2 shrink-0"
                  >
                    <RefreshCw className="h-3 w-3" /> 重試
                  </button>
                </div>
              )}

              <div className="grid sm:grid-cols-2 gap-4">
                {/* File Upload */}
                <div className="space-y-2">
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-2xl p-5 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group ${
                      uploading ? 'border-emerald-400 bg-emerald-50/50' : 'border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/50'
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.md,.txt,.docx,.pptx,.xlsx,.doc,.ppt,.xls,.mp3,.wav,.m4a,.flac,.ogg,.wma,.aac,.mp4,.mov,.avi,.mkv,.webm,.jpg,.jpeg,.png,.gif,.webp"
                      className="hidden"
                      onChange={e => handleFileUpload(e.target.files)}
                      disabled={uploading}
                    />
                    {uploading && (uploadStatus === 'pending' || uploadStatus === 'processing') ? (
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
                        <p className="font-medium text-emerald-700">上傳中...</p>
                      </div>
                    ) : (
                      <>
                        <FileText className="h-8 w-8 text-slate-400 group-hover:text-emerald-500 transition-colors mb-3" />
                        <p className="font-medium text-slate-700 mb-1">上傳實體檔案</p>
                        <p className="text-xs text-slate-500">PDF、Office、文字、音訊、影片、圖片</p>
                      </>
                    )}
                  </div>
                  {/* Vision OCR 已移除 — 實體檔案上傳即可 */}
                </div>

                {/* YouTube Import */}
                <div className="border border-slate-200 rounded-2xl p-5 flex flex-col justify-center bg-slate-50 hover:bg-white transition-colors">
                  <div className="flex items-center gap-2 mb-3">
                    <Youtube className="h-6 w-6 text-red-500" />
                    <span className="font-medium text-slate-700">影音連結解析</span>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={youtubeUrl}
                      onChange={e => setYoutubeUrl(e.target.value)}
                      placeholder="貼上 YouTube 網址..."
                      className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      onKeyDown={e => e.key === 'Enter' && handleYoutubeSubmit()}
                    />
                    <button
                      onClick={handleYoutubeSubmit}
                      disabled={uploading || !youtubeUrl.trim()}
                      className="bg-slate-900 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-50"
                    >
                      解析
                    </button>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-2">所有方案皆可使用，Pro 以上無時長限制</p>
                </div>
              </div>

              {/* Implicit Copyright Consent */}
              <p className="text-[10px] text-slate-400 text-center mt-3">
                *點擊上傳即代表您保證擁有此檔案／影片的合法使用授權，且同意不公開散佈生成的內容。*
              </p>
            </section>

            {/* Daily Quests */}
            <section>
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-500" /> 每日任務
              </h2>
              <div className="space-y-2">
                {(data.dailyQuests || []).map(quest => (
                  <DailyQuestCard key={quest.id} quest={quest} />
                ))}
              </div>
            </section>

            {/* Activity Items */}
            <section>
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-indigo-500" /> 待辦提醒
              </h2>
              <div className="space-y-3">
                {(data.activityItems || []).map(item => {
                  const iconMap = {
                    error_review: TrendingUp,
                    incomplete_exam: BookOpen,
                    new_resource: FileText,
                    achievement: Sparkles,
                  };
                  const colorMap = {
                    error_review: 'bg-rose-100 text-rose-600',
                    incomplete_exam: 'bg-blue-100 text-blue-600',
                    new_resource: 'bg-emerald-100 text-emerald-600',
                    achievement: 'bg-amber-100 text-amber-600',
                  };
                  const Icon = iconMap[item.type];
                  const colorClass = colorMap[item.type];

                  return (
                    <div key={item.id} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 flex items-center justify-between hover:shadow-md transition-shadow cursor-pointer">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-full flex items-center justify-center ${colorClass}`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <h4 className="font-medium text-slate-900">{item.title}</h4>
                          <p className="text-sm text-slate-500">{item.description}</p>
                        </div>
                      </div>
                      <Link href={item.link} className="text-sm font-medium text-emerald-600 hover:text-emerald-700 shrink-0">
                        {item.linkLabel} &rarr;
                      </Link>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Ebbinghaus Review Calendar */}
            <section className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <CalendarIcon className="h-5 w-5 text-blue-500" /> 複習日曆
                </h2>
                <div className="flex items-center gap-1">
                  <button onClick={() => { if (calendarMonth === 1) { setCalendarMonth(12); setCalendarYear(calendarYear - 1); } else { setCalendarMonth(calendarMonth - 1); } }} className="p-1 rounded-full hover:bg-slate-100 transition-colors"><ChevronLeft className="h-4 w-4 text-slate-600" /></button>
                  <span className="text-sm font-medium text-slate-700">{calendarYear !== new Date().getFullYear() ? `${calendarYear}年${calendarMonth}月` : `${calendarMonth}月`}</span>
                  <button onClick={() => { if (calendarMonth === 12) { setCalendarMonth(1); setCalendarYear(calendarYear + 1); } else { setCalendarMonth(calendarMonth + 1); } }} className="p-1 rounded-full hover:bg-slate-100 transition-colors"><ChevronRight className="h-4 w-4 text-slate-600" /></button>
                </div>
              </div>

              <div className="grid grid-cols-7 gap-1 text-center mb-1">
                {['日', '一', '二', '三', '四', '五', '六'].map(day => (
                  <div key={day} className="text-[10px] font-medium text-slate-400 py-1">{day}</div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1">
                {Array.from({ length: new Date(calendarYear, calendarMonth, 0).getDate() }).map((_, i) => {
                  const day = i + 1;
                  const now = new Date();
                  const isToday = day === now.getDate() && calendarMonth === now.getMonth() + 1 && calendarYear === now.getFullYear();
                  const hasReview = reviewDates.has(day);
                  const calendarDay = data.reviewCalendar.find(r => new Date(r.date).getDate() === day);
                  const reviewCount = calendarDay?.reviewCount ?? 0;

                  return (
                    <div
                      key={day}
                      className={`
                        relative flex flex-col items-center justify-center p-1 rounded-lg border
                        ${isToday ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-transparent hover:border-slate-200 hover:bg-slate-50'}
                        ${hasReview && !isToday ? 'bg-slate-50/50' : ''}
                        cursor-pointer transition-all aspect-square
                      `}
                      title={calendarDay ? calendarDay.topics.join(', ') : undefined}
                    >
                      <span className={`text-xs font-medium ${isToday ? 'text-blue-700' : 'text-slate-700'}`}>
                        {day}
                      </span>
                      {hasReview && (
                        <div className="flex gap-0.5 mt-0.5">
                          {Array.from({ length: Math.min(reviewCount, 3) }).map((_, j) => (
                            <div key={j} className={`w-1 h-1 rounded-full ${isToday ? 'bg-blue-500' : 'bg-emerald-400'}`} />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Today's Tasks — dynamic based on study mode */}
              <div className="mt-4 pt-4 border-t border-slate-100">
                <h3 className="text-xs font-bold text-slate-900 mb-2">
                  今日特訓 ({new Date().getMonth() + 1}月{new Date().getDate()}日)
                </h3>
                <div className="space-y-1.5">
                  {(data.todayTasks || []).length > 0 ? (
                    (data.todayTasks as Array<{title: string; type: string}>).slice(0, 3).map((task, idx) => {
                      const typeConfig: Record<string, {color: string; label: string; labelColor: string}> = {
                        wrong: { color: 'bg-rose-500', label: '錯題', labelColor: 'bg-rose-100 text-rose-600' },
                        unseen: { color: 'bg-amber-500', label: '新題', labelColor: 'bg-amber-100 text-amber-600' },
                        review: { color: 'bg-emerald-500', label: '複習', labelColor: 'bg-emerald-100 text-emerald-600' },
                      };
                      const cfg = typeConfig[task.type] || typeConfig.review;
                      return (
                        <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 hover:border-blue-200 transition-colors cursor-pointer">
                          <div className="flex items-center gap-2 truncate pr-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${cfg.color} shrink-0`} />
                            <span className="text-xs font-medium text-slate-700 truncate">{task.title}</span>
                          </div>
                          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded shrink-0 ${cfg.labelColor}`}>
                            {cfg.label}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-center py-3 text-xs text-slate-400">
                      {(data.todo_reminders?.wrong_answers || 0) > 0
                        ? `有 ${data.todo_reminders?.wrong_answers} 題錯題待複習`
                        : '今日無特訓任務，保持複習節奏！'}
                    </div>
                  )}
                </div>
                <Link href={(data.todo_reminders?.wrong_answers ?? 0) > 0 ? '/review' : '/exam/setup'} className="w-full mt-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors shadow-md shadow-blue-500/20 flex items-center justify-center gap-1.5">
                  <Play className="h-3 w-3" /> {(data.todo_reminders?.wrong_answers ?? 0) > 0 ? '複習錯題' : '開始特訓'}
                </Link>
              </div>
            </section>

            {/* Learning Stats */}
            <section className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-900 mb-4">學習狀態</h2>

              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-500">整體答對率</span>
                  <span className="font-bold text-slate-900">{data.stats.overallAccuracy}%</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${data.stats.overallAccuracy}%` }} />
                </div>
              </div>

              <DomainRadarChart
                domains={data.domainStrengths}
                onDomainClick={activeSubjectId ? (_d, nodeId) => {
                  const qs = nodeId ? `?focus=${nodeId}` : '';
                  window.location.href = `/subjects/${activeSubjectId}/canvas${qs}`;
                } : undefined}
              />

              {activeSubjectId && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <Link
                    href={`/subjects/${activeSubjectId}/canvas`}
                    className="flex items-center justify-center gap-1.5 text-xs text-emerald-600 hover:text-emerald-800 py-2 rounded-lg hover:bg-emerald-50 transition"
                  >
                    🗺️ 開啟知識地圖 Canvas
                  </Link>
                </div>
              )}
            </section>
          </div>
        </div>
      </div>

      {/* Feedback Link */}
      <div className="container mx-auto px-4 max-w-6xl pb-8">
        <div className="flex justify-center">
          <Link href="/feedback" className="text-sm text-slate-500 hover:text-emerald-600 flex items-center gap-1">
            <MessageSquare className="h-4 w-4" /> 意見反饋
          </Link>
        </div>
      </div>

      {/* Add Subject Modal */}
      {showAddSubject && (
        <SubjectPickerModal
          excludeSubjectIds={subjects.map(s => s.subjectId)}
          onConfirm={handleAddSubject}
          onClose={() => setShowAddSubject(false)}
        />
      )}
    </>
  );
}
