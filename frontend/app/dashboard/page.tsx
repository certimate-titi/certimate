'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Upload, Youtube, FileText, Image as ImageIcon, Clock, TrendingUp, BookOpen, Calendar as CalendarIcon, ChevronLeft, ChevronRight, Play, AlertCircle, Sparkles, Lock, CheckCircle2, XCircle, RefreshCw, MessageSquare, Loader2 } from 'lucide-react';
import { dashboardService, documentService, subjectService } from '@/lib/api/services';
import type { GetDashboardResponse, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import StreakCounter from '@/components/StreakCounter';
import DailyQuestCard from '@/components/DailyQuestCard';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import SubjectPickerModal from '@/components/SubjectPickerModal';
import AnnouncementBanner from '@/components/AnnouncementBanner';
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
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    if (!isAuthenticated || !onboardingCompleted) return;
    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects || []);
      if (res.subjects && res.subjects.length > 0) {
        setActiveSubjectId(res.subjects[0].id);
      }
    }).catch(() => setSubjects([]));
  }, [isAuthenticated, onboardingCompleted]);

  // Load dashboard data
  useEffect(() => {
    if (!isAuthenticated || !onboardingCompleted) return;
    dashboardService.get().then(d => {
      // Ensure all expected fields have defaults for backend compatibility
      setData({
        ...d,
        streak: d.streak || { currentStreak: 0, freezeCount: 2, lastActiveDate: new Date().toISOString() },
        dailyQuests: d.dailyQuests || [],
        activityItems: d.activityItems || [],
        reviewCalendar: d.reviewCalendar || [],
        stats: d.stats || { overallAccuracy: 0, totalMocksCompleted: 0, totalQuestionsAnswered: 0, predictedPassRate: 0, examCountdown: null },
        domainStrengths: d.domainStrengths || [],
      });
      setLoading(false);
    }).catch(() => {
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
  }, [activeSubjectId, isAuthenticated, onboardingCompleted]);

  const handleFileUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
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
        return Math.min(p + 10, 90);
      });
    }, 300);
    try {
      await documentService.upload({ file: files[0], title: files[0].name, subjectId: activeSubjectId });
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('completed');
      const d = await dashboardService.get();
      setData({
        ...d,
        streak: d.streak || { currentStreak: 0, freezeCount: 2, lastActiveDate: new Date().toISOString() },
        dailyQuests: d.dailyQuests || [],
        activityItems: d.activityItems || [],
        reviewCalendar: d.reviewCalendar || [],
        stats: d.stats || { overallAccuracy: 0, totalMocksCompleted: 0, totalQuestionsAnswered: 0, predictedPassRate: 0, examCountdown: null },
        domainStrengths: d.domainStrengths || [],
      });
      setTimeout(() => setUploadStatus('idle'), 4000);
    } catch {
      clearInterval(progressInterval);
      setUploadStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [activeSubjectId]);

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
      await documentService.upload({ youtubeUrl: youtubeUrl.trim(), subjectId: activeSubjectId });
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('completed');
      setYoutubeUrl('');
      const d = await dashboardService.get();
      setData({
        ...d,
        streak: d.streak || { currentStreak: 0, freezeCount: 2, lastActiveDate: new Date().toISOString() },
        dailyQuests: d.dailyQuests || [],
        activityItems: d.activityItems || [],
        reviewCalendar: d.reviewCalendar || [],
        stats: d.stats || { overallAccuracy: 0, totalMocksCompleted: 0, totalQuestionsAnswered: 0, predictedPassRate: 0, examCountdown: null },
        domainStrengths: d.domainStrengths || [],
      });
      setTimeout(() => setUploadStatus('idle'), 4000);
    } catch {
      clearInterval(progressInterval);
      setUploadStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [youtubeUrl, activeSubjectId]);


  const handleAddSubject = useCallback(async (selected: SelectedSubject[]) => {
    for (const s of selected) {
      await subjectService.addSubject({
        subjectId: s.subjectId,
        subjectName: s.subjectName,
        examDate: s.examDate,
        selfAssessment: s.selfAssessment,
      });
    }
    // Reload subjects from backend
    try {
      const res = await subjectService.getUserSubjects();
      setSubjects(res.subjects);
      if (res.subjects.length > 0 && !activeSubjectId) {
        setActiveSubjectId(res.subjects[0].id);
      }
    } catch { /* silent */ }
    setShowAddSubject(false);
  }, [activeSubjectId]);

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
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

      {/* Subject Switcher */}
      {subjects.length > 0 ? (
        <SubjectSwitcher
          subjects={subjects}
          activeSubjectId={activeSubjectId}
          onSwitch={setActiveSubjectId}
          onAddSubject={() => setShowAddSubject(true)}
        />
      ) : isAuthenticated && onboardingCompleted ? (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-3">
          <div className="container mx-auto max-w-6xl flex items-center justify-between">
            <span className="text-sm text-amber-800">尚未建立備考科目，請先新增科目以開始學習</span>
            <button onClick={() => setShowAddSubject(true)} className="text-sm font-bold text-amber-700 hover:text-amber-900 underline">新增科目</button>
          </div>
        </div>
      ) : null}

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">早安，{user?.displayName || '學習者'}！</h1>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-slate-500">今天想從哪裡開始複習？</p>
              {/* Task Mode Badge */}
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
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end gap-1">
              <StreakCounter streak={data.streak} />
              {data.streak.freezesRemaining > 0 && (
                <span className="text-xs text-blue-500">❄️ {data.streak.freezesRemaining} 次補救機會</span>
              )}
              {data.streak.freezeConsumedToday && (
                <span className="text-xs text-slate-500 italic">休息也是學習的一部分，歡迎回來！</span>
              )}
            </div>
            {data.stats.examCountdown && (
              <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-full shadow-sm border border-slate-200">
                <Clock className="h-5 w-5 text-amber-500" />
                <span className="text-sm font-medium text-slate-700">
                  距離 {data.stats.examCountdown.examName} 還有 <strong className="text-amber-600">{data.stats.examCountdown.daysRemaining}</strong> 天
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Ultra: Co-study counter */}
        {isUltra && (
          <div className="mb-6 flex items-center gap-2 bg-purple-50 border border-purple-100 rounded-xl px-4 py-2">
            <span className="text-sm text-purple-700">目前有 <strong>368</strong> 位考生一起奮鬥中</span>
          </div>
        )}

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

        <div className="grid lg:grid-cols-3 gap-8">
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
                <div className="mb-4 flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <p className="text-sm text-emerald-800 font-medium">解析完成</p>
                  <Link href="/knowledge" className="text-sm font-bold text-emerald-600 underline underline-offset-2 ml-1">立即查看</Link>
                </div>
              )}
              {uploadStatus === 'failed' && (
                <div className="mb-4 flex items-center justify-between bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-rose-600 shrink-0" />
                    <p className="text-sm text-rose-800">解析失敗</p>
                  </div>
                  <button
                    onClick={() => { setUploadStatus('idle'); fileInputRef.current?.click(); }}
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
                      accept=".pdf,.md,.txt"
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
                        <p className="text-xs text-slate-500">PDF、Markdown、TXT</p>
                      </>
                    )}
                  </div>
                  {/* Image upload — Pro Plus only */}
                  {isProPlus ? (
                    <button
                      onClick={() => {
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = '.png,.jpg,.jpeg,.webp';
                        input.onchange = e => handleFileUpload((e.target as HTMLInputElement).files);
                        input.click();
                      }}
                      disabled={uploading}
                      className="w-full flex items-center gap-2 justify-center border border-purple-200 bg-purple-50 hover:bg-purple-100 rounded-xl px-4 py-2 text-sm font-medium text-purple-700 transition-colors disabled:opacity-50"
                    >
                      <ImageIcon className="h-4 w-4" /> 上傳圖片（Vision OCR）
                    </button>
                  ) : (
                    <div className="group relative w-full flex items-center gap-2 justify-center border border-slate-200 bg-slate-50 rounded-xl px-4 py-2 text-sm text-slate-400 cursor-default">
                      <Lock className="h-3.5 w-3.5" />
                      <span>圖片上傳需 PRO+ 以上方案</span>
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-slate-900 text-white text-xs rounded-lg px-3 py-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-center">
                        手寫/圖片辨識需要多模態算力，升級 PRO+ 解鎖 Vision OCR
                      </div>
                    </div>
                  )}
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
                  <button className="p-1 rounded-full hover:bg-slate-100 transition-colors"><ChevronLeft className="h-4 w-4 text-slate-600" /></button>
                  <span className="text-sm font-medium text-slate-700">3月</span>
                  <button className="p-1 rounded-full hover:bg-slate-100 transition-colors"><ChevronRight className="h-4 w-4 text-slate-600" /></button>
                </div>
              </div>

              <div className="grid grid-cols-7 gap-1 text-center mb-1">
                {['日', '一', '二', '三', '四', '五', '六'].map(day => (
                  <div key={day} className="text-[10px] font-medium text-slate-400 py-1">{day}</div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1">
                {Array.from({ length: 31 }).map((_, i) => {
                  const day = i + 1;
                  const isToday = day === 19;
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
                        ? `有 ${data.todo_reminders.wrong_answers} 題錯題待複習`
                        : '今日無特訓任務，保持複習節奏！'}
                    </div>
                  )}
                </div>
                <Link href={data.todo_reminders?.wrong_answers > 0 ? '/review' : '/exam/setup'} className="w-full mt-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors shadow-md shadow-blue-500/20 flex items-center justify-center gap-1.5">
                  <Play className="h-3 w-3" /> {data.todo_reminders?.wrong_answers > 0 ? '複習錯題' : '開始特訓'}
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

              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">能力分佈</h3>
                <div className="aspect-square w-full bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-center relative overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-3/4 h-3/4 border border-slate-200 rounded-full" />
                    <div className="w-1/2 h-1/2 border border-slate-200 rounded-full absolute" />
                    <div className="w-1/4 h-1/4 border border-slate-200 rounded-full absolute" />
                    <div className="w-full h-px bg-slate-200 absolute" />
                    <div className="h-full w-px bg-slate-200 absolute" />
                    <div className="w-full h-px bg-slate-200 absolute rotate-45" />
                    <div className="w-full h-px bg-slate-200 absolute -rotate-45" />
                    {data.domainStrengths.length > 0 && (
                      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
                        <polygon points="50,15 80,40 70,80 30,75 15,45" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" strokeWidth="2" />
                      </svg>
                    )}
                  </div>
                  {data.domainStrengths.length === 0 ? (
                    <span className="absolute text-xs text-slate-400">尚無測驗資料</span>
                  ) : (
                    data.domainStrengths.slice(0, 4).map((d, i) => {
                      const positions = [
                        'top-2 left-1/2 -translate-x-1/2',
                        'bottom-2 left-1/2 -translate-x-1/2',
                        'left-2 top-1/2 -translate-y-1/2',
                        'right-2 top-1/2 -translate-y-1/2',
                      ];
                      return (
                        <span key={i} className={`absolute ${positions[i]} text-[10px] font-medium text-slate-500`}>
                          {d.domain.split(' ')[0]}
                        </span>
                      );
                    })
                  )}
                </div>
              </div>
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
