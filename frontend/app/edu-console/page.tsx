'use client';

import { useEffect, useState } from 'react';
import {
  Users, FileSpreadsheet, Send, BarChart3, Search, MoreVertical,
  ShieldCheck, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Sparkles, ChevronRight, Brain, Target, Clock, CheckCircle2
} from 'lucide-react';

import { adminService, subjectService } from '@/lib/api/services';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import type { Student, UserSubject, GetStudentListResponse } from '@/types';

// ─── Sub-components ──────────────────────────────────────────────────────────

function TrendIcon({ trend }: { trend: Student['trend'] }) {
  if (trend === 'up') return <TrendingUp className="h-4 w-4 text-emerald-500" />;
  if (trend === 'down') return <TrendingDown className="h-4 w-4 text-rose-500" />;
  return <Minus className="h-4 w-4 text-slate-400" />;
}

function StatusBadge({ status }: { status: Student['status'] }) {
  const map = {
    active:   'bg-emerald-100 text-emerald-800',
    'needs_attention': 'bg-rose-100 text-rose-700',
    inactive: 'bg-slate-100 text-slate-600',
  } as const;
  const labels = { active: '活躍', 'needs_attention': '需關注', inactive: '未啟用' } as const;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${map[status]}`}>
      {labels[status]}
    </span>
  );
}

function CompetencyBar({ label, score }: { label: string; score: number }) {
  const color =
    score >= 70 ? 'bg-emerald-500' :
    score >= 40 ? 'bg-amber-400' :
    'bg-rose-500';
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-slate-500 truncate shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${score}%` }} />
      </div>
      <span className="w-8 text-right font-medium text-slate-600">{score || '—'}</span>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EduConsolePage() {
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  
  // ─── Subject Switching State ───────────────────────────────────────────────
  const [userSubjects, setUserSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');
  const [students, setStudents] = useState<Student[]>([]);
  const [classStats, setClassStats] = useState<GetStudentListResponse['classStats']>({
    averageScore: 0,
    scoreChange: 0,
    topWeaknesses: [],
  });
  const [isLoading, setIsLoading] = useState(true);

  // 1. 初始獲取用戶關聯的學科
  useEffect(() => {
    const fetchSubjects = async () => {
      const { subjects } = await subjectService.getUserSubjects();
      setUserSubjects(subjects);
      if (subjects.length > 0) {
        // 設定初始 activeSubjectId 為 UserSubject 的 id
        setActiveSubjectId(subjects[0].id);
      }
    };
    fetchSubjects();
  }, []);

  // 2. 當切換學科或搜尋文字改變時，獲取對應的學員資料
  useEffect(() => {
    const fetchData = async () => {
      // 從 userSubjects 中找到對應的實際學科 ID (如 subj_pmp)
      const currentSub = userSubjects.find(s => s.id === activeSubjectId);
      const targetId = currentSub ? currentSub.subjectId : activeSubjectId;

      setIsLoading(true);
      try {
        const { students: fetchedStudents, classStats: fetchedStats } = await adminService.getStudentList(targetId);
        setStudents(fetchedStudents);
        setClassStats(fetchedStats);
      } catch (error) {
        console.error('EduConsole: Fetch error:', error);
      } finally {
        setIsLoading(false);
      }
    };
    if (activeSubjectId) {
      fetchData();
    }
  }, [activeSubjectId, userSubjects]);


  const filtered = students.filter(
    s =>
      s.name.includes(search) ||
      s.email.toLowerCase().includes(search.toLowerCase()),
  );

  const atRiskStudents = students.filter(s => s.status === 'needs_attention');
  const activeCount    = students.filter(s => s.status === 'active').length;
  const avgScore       = classStats.averageScore;

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-slate-50">

      {/* Header */}
      <header className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0 shadow-md z-10">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-6 w-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold tracking-wider">教育機構管理中心</h1>
            <p className="text-xs text-slate-400">Ultra 方案專屬 • 教育訓練管理</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-slate-800 px-4 py-2 rounded-full border border-slate-700 text-sm font-medium">
            <span className="text-slate-400">已授權人數：</span>
            <span className="text-white">142 / 200</span>
          </div>
          <button className="bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-2 rounded-full text-sm font-bold transition-colors">
            + 匯入學生名單
          </button>
        </div>
      </header>
      
      {/* Subject Switcher */}
      <SubjectSwitcher 
        subjects={userSubjects}
        activeSubjectId={activeSubjectId}
        onSwitch={setActiveSubjectId}
        onAddSubject={() => {}} // 教育管理中心暫不提供新增學科，或連至設定
        allowAdd={false}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500" />
              <p className="text-slate-500 font-medium">資料載入中...</p>
            </div>
          ) : (
            <>
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-indigo-50 rounded-2xl p-5 shadow-sm border border-indigo-100">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-4 w-4 text-indigo-500" />
                <span className="text-xs text-slate-500 font-medium">日活躍用戶</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">32</div>
              <div className="text-xs text-emerald-600 font-medium mt-1">+5 vs 昨日</div>
            </div>
            <div className="bg-emerald-50 rounded-2xl p-5 shadow-sm border border-emerald-100">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-4 w-4 text-emerald-500" />
                <span className="text-xs text-slate-500 font-medium">活躍率</span>
              </div>
              <div className="text-3xl font-extrabold text-emerald-600">78%</div>
              <div className="text-xs text-emerald-600 font-medium mt-1">+3%</div>
            </div>
            <div className="bg-amber-50 rounded-2xl p-5 shadow-sm border border-amber-100">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <span className="text-xs text-slate-500 font-medium">需關注學員</span>
              </div>
              <div className="text-3xl font-extrabold text-amber-600">4</div>
              <div className="text-xs text-emerald-600 font-medium mt-1">-1</div>
            </div>
            <div className="bg-blue-50 rounded-2xl p-5 shadow-sm border border-blue-100">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-blue-500" />
                <span className="text-xs text-slate-500 font-medium">班級平均</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">72.5</div>
              <div className="text-xs text-emerald-600 font-medium mt-1">+2.1</div>
            </div>
          </div>

          {/* ── 預警中心 ── */}
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-rose-500" />
              <h2 className="text-base font-bold text-rose-800">預警中心</h2>
            </div>
            <div className="space-y-3">
              {[
                { name: '王小明', reason: '平均分低於 60', score: 45, action: 'AI 補強建議' },
                { name: '李大華', reason: '連續 3 次退步', trend: 'down' as const, action: '查看詳情' },
                { name: '張美玲', reason: '超過 5 天未登入', lastActive: '7 天前', action: '發送提醒' },
              ].map((item) => (
                <div key={item.name} className="bg-white rounded-xl p-4 border border-rose-100 flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900 text-sm">{item.name}</span>
                      {item.trend === 'down' && <TrendingDown className="h-4 w-4 text-rose-500" />}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {item.reason}
                      {item.score !== undefined && <span className="text-rose-600 font-medium"> (分數: {item.score})</span>}
                      {item.lastActive && <span className="text-slate-400"> · 最後活躍: {item.lastActive}</span>}
                    </p>
                  </div>
                  <button className="shrink-0 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                    {item.action}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* ── 班級弱點分析 ── */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="h-5 w-5 text-rose-500" />
              <h2 className="text-base font-bold text-slate-900">班級弱點分析</h2>
            </div>
            <div className="space-y-4">
              {[
                { topic: '風險管理 - 風險回應策略', errorRate: 68 },
                { topic: '品質管理 - 品質控制工具', errorRate: 55 },
                { topic: '採購管理 - 合約類型', errorRate: 48 },
              ].map((item) => (
                <div key={item.topic}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-700 font-medium">{item.topic}</span>
                    <span className="text-rose-600 font-bold">{item.errorRate}%</span>
                  </div>
                  <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-rose-500 rounded-full"
                      style={{ width: `${item.errorRate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Quick Actions ── */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4">
              <div className="h-11 w-11 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
                <FileSpreadsheet className="h-5 w-5 text-indigo-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">批量匯入名單</h3>
                <p className="text-xs text-slate-500 mt-0.5">上傳 CSV，自動發送邀請</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400 ml-auto" />
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4">
              <div className="h-11 w-11 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                <Send className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">派發模擬考卷</h3>
                <p className="text-xs text-slate-500 mt-0.5">統一生成並設定期限</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400 ml-auto" />
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4">
              <div className="h-11 w-11 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
                <BarChart3 className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">全局弱點分析</h3>
                <p className="text-xs text-slate-500 mt-0.5">找出班級共同知識盲區</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400 ml-auto" />
            </div>
          </div>

          {/* ── Student Competency Table + Class Stats ── */}
          <div className="grid lg:grid-cols-3 gap-6">

            {/* Student List with Competency Profiles (Redmenta: competency profiles) */}
            <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
              <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Brain className="h-5 w-5 text-indigo-500" /> 學生能力檔案
                </h2>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="搜尋姓名或信箱..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="pl-9 pr-4 py-2 rounded-full border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 w-56"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                {filtered.map(s => (
                  <div key={s.id}>
                    {/* Row */}
                    <div
                      className="flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors cursor-pointer"
                      onClick={() => setExpandedId(expandedId === s.id ? null : s.id)}
                    >
                      {/* Avatar */}
                      <div className="h-9 w-9 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 text-sm font-bold text-indigo-600">
                        {s.name[0]}
                      </div>

                      {/* Name + email */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-semibold text-slate-900 text-sm">{s.name}</span>
                          <TrendIcon trend={s.trend} />
                        </div>
                        <span className="text-xs text-slate-400">{s.email}</span>
                      </div>

                      {/* Progress bar */}
                      <div className="hidden sm:flex items-center gap-2 w-28">
                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${s.progress >= 70 ? 'bg-emerald-500' : s.progress >= 40 ? 'bg-amber-400' : 'bg-slate-300'}`}
                            style={{ width: `${s.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500 w-8 text-right">{s.progress}%</span>
                      </div>

                      {/* Score */}
                      <div className="w-10 text-right">
                        <span className={`text-sm font-bold ${(s.averageScore || 0) >= 70 ? 'text-emerald-600' : (s.averageScore || 0) >= 50 ? 'text-amber-600' : 'text-slate-400'}`}>
                          {s.averageScore || '—'}
                        </span>
                      </div>

                      {/* Status */}
                      <div className="w-16 flex justify-center">
                        <StatusBadge status={s.status} />
                      </div>

                      {/* More */}
                      <button
                        className="text-slate-400 hover:text-slate-600 shrink-0"
                        onClick={e => e.stopPropagation()}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </button>
                    </div>

                    {/* ── Expanded: Competency Profile (Redmenta: per-student skill breakdown) ── */}
                    {expandedId === s.id && (
                      <div className="bg-slate-50 px-5 py-4 border-t border-slate-100">
                        <div className="flex items-start gap-6">
                          {/* Competency bars */}
                          <div className="flex-1 space-y-2">
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">能力分析</p>
                            {s.competencies.map(c => (
                              <CompetencyBar key={c.label} {...c} />
                            ))}
                          </div>
                          {/* Actions */}
                          <div className="shrink-0 flex flex-col gap-2 items-end">
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">操作</p>
                            <button className="flex items-center gap-1.5 bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-bold px-3 py-2 rounded-lg transition-colors">
                              <Sparkles className="h-3.5 w-3.5" />
                              AI 個人化補強建議
                            </button>
                            <button className="flex items-center gap-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold px-3 py-2 rounded-lg transition-colors">
                              <Send className="h-3.5 w-3.5" />
                              指派補考
                            </button>
                            <span className="text-xs text-slate-400 mt-1">最後活躍：{s.lastActiveLabel}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Class Stats + Weak Areas */}
            <div className="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6 text-white relative overflow-hidden flex flex-col gap-5">
              <div className="absolute top-0 right-0 w-40 h-40 bg-indigo-500/20 rounded-bl-full blur-2xl pointer-events-none" />

              <h2 className="text-base font-bold flex items-center gap-2 relative z-10">
                <BarChart3 className="h-5 w-5 text-indigo-400" /> 班級學習概況
              </h2>

              {/* Avg score */}
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 relative z-10">
                <div className="text-xs text-slate-400 mb-1">平均測驗分數</div>
                <div className="text-3xl font-extrabold">{avgScore}</div>
                <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" /> 較上週提升 {classStats.scoreChange} 分
                </div>
              </div>

              {/* Common weak spots */}
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 relative z-10">
                <div className="text-xs text-slate-400 mb-3">共同弱點 Top 3</div>
                <ul className="space-y-3">
                  {classStats.topWeaknesses.map((w, idx) => {
                    const colors = [
                      { color: 'bg-rose-500', text: 'text-rose-300' },
                      { color: 'bg-amber-500', text: 'text-amber-300' },
                      { color: 'bg-yellow-500', text: 'text-yellow-300' },
                    ];
                    const { color, text } = colors[idx % colors.length];
                    return (
                      <li key={w.topic}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className={text}>{w.topic}</span>
                          <span className="text-slate-400">答錯率 {w.errorRate}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-700 rounded-full overflow-hidden">
                          <div className={`h-full ${color} rounded-full`} style={{ width: `${w.errorRate}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>

              {/* Export */}
              <button className="w-full bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-3 rounded-xl font-bold transition-colors text-sm relative z-10">
                匯出詳細報告
              </button>
            </div>

          </div>

            </>
          )}
        </div>
      </div>
    </div>
  );
}
