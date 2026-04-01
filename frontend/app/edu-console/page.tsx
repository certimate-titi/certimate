'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Users, FileSpreadsheet, Send, BarChart3, Search, MoreVertical,
  ShieldCheck, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Sparkles, ChevronRight, Brain, Target, Clock, CheckCircle2,
  Upload, Download, X, FileText, AlertCircle
} from 'lucide-react';

import { adminService } from '@/lib/api/services';
import type { Student, GetStudentListResponse } from '@/types';

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

// ─── CSV Import Modal ────────────────────────────────────────────────────────

const CSV_TEMPLATE = `姓名,電子郵件,群組
王小明,student01@school.com,AWS 雲端基礎班 A
李大華,student02@school.com,PMP 衝刺班 B`;

const REQUIRED_COLUMNS = ['姓名', '電子郵件', '群組'];

interface CsvRow { 姓名: string; 電子郵件: string; 群組: string; }

function ImportStudentModal({
  open,
  onClose,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CsvRow[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{
    total_rows: number;
    created_users: number;
    added_members: number;
    skipped_duplicates: number;
    groups: string[];
  } | null>(null);
  const [consent, setConsent] = useState(false);

  const reset = useCallback(() => {
    setFile(null);
    setPreview([]);
    setParseError(null);
    setUploading(false);
    setResult(null);
    setConsent(false);
  }, []);

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleFileSelect = (f: File) => {
    setParseError(null);
    setResult(null);
    setConsent(false);

    if (!f.name.endsWith('.csv')) {
      setParseError('請選擇 .csv 格式的檔案');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.trim().split('\n');
      if (lines.length < 2) {
        setParseError('CSV 檔案至少需要標題列與一筆資料');
        return;
      }

      const headers = lines[0].split(',').map(h => h.trim().replace(/^\uFEFF/, ''));
      const missing = REQUIRED_COLUMNS.filter(c => !headers.includes(c));
      if (missing.length > 0) {
        setParseError(`缺少必要欄位：${missing.join('、')}。CSV 格式必須包含：姓名、電子郵件、群組`);
        return;
      }

      const rows: CsvRow[] = [];
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',').map(c => c.trim());
        if (cols.length < 3 || cols.every(c => !c)) continue;
        const nameIdx = headers.indexOf('姓名');
        const emailIdx = headers.indexOf('電子郵件');
        const groupIdx = headers.indexOf('群組');
        rows.push({
          姓名: cols[nameIdx] || '',
          電子郵件: cols[emailIdx] || '',
          群組: cols[groupIdx] || '',
        });
      }

      if (rows.length === 0) {
        setParseError('CSV 不包含任何有效資料列');
        return;
      }

      const emptyRow = rows.findIndex(r => !r.姓名 || !r.電子郵件 || !r.群組);
      if (emptyRow >= 0) {
        setParseError(`第 ${emptyRow + 2} 行資料不完整：姓名、電子郵件、群組皆為必填`);
        return;
      }

      setFile(f);
      setPreview(rows);
    };
    reader.readAsText(f);
  };

  const handleUpload = async () => {
    if (!file || !consent) return;
    setUploading(true);
    try {
      const res = await adminService.importStudents(file);
      setResult(res);
    } catch (err) {
      setParseError(err instanceof Error ? err.message : '匯入失敗，請稍後再試');
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadTemplate = () => {
    const blob = new Blob([CSV_TEMPLATE], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'student-import-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center">
              <FileSpreadsheet className="h-5 w-5 text-indigo-500" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">匯入學生名單</h2>
              <p className="text-xs text-slate-500">上傳 CSV 檔案批量新增學員</p>
            </div>
          </div>
          <button onClick={handleClose} className="text-slate-400 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Success result */}
          {result ? (
            <div className="space-y-4">
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  <h3 className="font-bold text-emerald-800">匯入完成</h3>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-white rounded-lg p-3 border border-emerald-100">
                    <div className="text-2xl font-bold text-slate-900">{result.total_rows}</div>
                    <div className="text-xs text-slate-500">總處理筆數</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-emerald-100">
                    <div className="text-2xl font-bold text-indigo-600">{result.created_users}</div>
                    <div className="text-xs text-slate-500">新建帳號</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-emerald-100">
                    <div className="text-2xl font-bold text-emerald-600">{result.added_members}</div>
                    <div className="text-xs text-slate-500">加入群組</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-emerald-100">
                    <div className="text-2xl font-bold text-slate-400">{result.skipped_duplicates}</div>
                    <div className="text-xs text-slate-500">略過（已存在）</div>
                  </div>
                </div>
                {result.groups.length > 0 && (
                  <div className="mt-3 text-xs text-slate-600">
                    <span className="font-medium">群組：</span>{result.groups.join('、')}
                  </div>
                )}
              </div>
              <button
                onClick={() => { handleClose(); onSuccess(); }}
                className="w-full bg-indigo-500 hover:bg-indigo-400 text-white py-3 rounded-xl font-bold text-sm transition-colors"
              >
                完成
              </button>
            </div>
          ) : (
            <>
              {/* CSV Format Spec */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                <h3 className="text-sm font-bold text-slate-700 mb-2">CSV 格式說明</h3>
                <p className="text-xs text-slate-500 mb-3">
                  檔案必須為 UTF-8 編碼的 CSV 格式，包含以下三個必填欄位：
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100">
                        <th className="border border-slate-200 px-3 py-2 text-left font-bold text-slate-700">欄位名稱</th>
                        <th className="border border-slate-200 px-3 py-2 text-left font-bold text-slate-700">說明</th>
                        <th className="border border-slate-200 px-3 py-2 text-left font-bold text-slate-700">範例</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="border border-slate-200 px-3 py-2 font-medium text-indigo-600">姓名</td>
                        <td className="border border-slate-200 px-3 py-2 text-slate-600">學員姓名</td>
                        <td className="border border-slate-200 px-3 py-2 text-slate-500">王小明</td>
                      </tr>
                      <tr>
                        <td className="border border-slate-200 px-3 py-2 font-medium text-indigo-600">電子郵件</td>
                        <td className="border border-slate-200 px-3 py-2 text-slate-600">學員登入 Email</td>
                        <td className="border border-slate-200 px-3 py-2 text-slate-500">student@school.com</td>
                      </tr>
                      <tr>
                        <td className="border border-slate-200 px-3 py-2 font-medium text-indigo-600">群組</td>
                        <td className="border border-slate-200 px-3 py-2 text-slate-600">所屬群組名稱（不存在會自動建立）</td>
                        <td className="border border-slate-200 px-3 py-2 text-slate-500">AWS 雲端基礎班 A</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <button
                  onClick={handleDownloadTemplate}
                  className="mt-3 flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-500 font-medium"
                >
                  <Download className="h-3.5 w-3.5" />
                  下載 CSV 範本
                </button>
              </div>

              {/* File Upload */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
                  file ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                }`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const f = e.dataTransfer.files[0];
                  if (f) handleFileSelect(f);
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFileSelect(f);
                  }}
                />
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="h-8 w-8 text-indigo-500" />
                    <div className="text-left">
                      <p className="text-sm font-bold text-slate-900">{file.name}</p>
                      <p className="text-xs text-slate-500">{preview.length} 筆學員資料</p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); reset(); }}
                      className="ml-4 text-slate-400 hover:text-rose-500"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                    <p className="text-sm text-slate-600 font-medium">點擊選擇或拖曳 CSV 檔案到此處</p>
                    <p className="text-xs text-slate-400 mt-1">支援 .csv 格式，UTF-8 編碼</p>
                  </>
                )}
              </div>

              {/* Parse Error */}
              {parseError && (
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-rose-800">格式錯誤</p>
                    <p className="text-xs text-rose-600 mt-1">{parseError}</p>
                  </div>
                </div>
              )}

              {/* Preview Table */}
              {preview.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold text-slate-700 mb-2">
                    資料預覽（前 {Math.min(preview.length, 5)} 筆，共 {preview.length} 筆）
                  </h3>
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-slate-50">
                          <th className="px-3 py-2 text-left font-bold text-slate-600">#</th>
                          <th className="px-3 py-2 text-left font-bold text-slate-600">姓名</th>
                          <th className="px-3 py-2 text-left font-bold text-slate-600">電子郵件</th>
                          <th className="px-3 py-2 text-left font-bold text-slate-600">群組</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {preview.slice(0, 5).map((row, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="px-3 py-2 text-slate-400">{i + 1}</td>
                            <td className="px-3 py-2 text-slate-900 font-medium">{row.姓名}</td>
                            <td className="px-3 py-2 text-slate-600">{row.電子郵件}</td>
                            <td className="px-3 py-2 text-slate-600">{row.群組}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {preview.length > 5 && (
                    <p className="text-xs text-slate-400 mt-1 text-right">...及其他 {preview.length - 5} 筆</p>
                  )}
                </div>
              )}

              {/* Consent + Submit */}
              {preview.length > 0 && (
                <div className="space-y-3">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={consent}
                      onChange={(e) => setConsent(e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-xs text-slate-600">
                      我確認已取得上述學員的同意，允許將其資料匯入系統並建立帳號。
                      新建帳號將使用預設密碼，學員首次登入時應自行修改。
                    </span>
                  </label>
                  <button
                    onClick={handleUpload}
                    disabled={!consent || uploading}
                    className="w-full bg-indigo-500 hover:bg-indigo-400 disabled:bg-slate-200 disabled:text-slate-400 text-white py-3 rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2"
                  >
                    {uploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                        匯入中...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4" />
                        確認匯入 {preview.length} 位學員
                      </>
                    )}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EduConsolePage() {
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  
  const [students, setStudents] = useState<Student[]>([]);
  const [classStats, setClassStats] = useState<GetStudentListResponse['classStats']>({
    averageScore: 0,
    scoreChange: 0,
    topWeaknesses: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeGroup, setActiveGroup] = useState<string>('all');

  // 獲取學員資料（B2B dashboard 直接回傳機構學員）
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setIsEmpty(false);
      try {
        const res = await adminService.getStudentList();
        const fetchedStudents = res?.students ?? [];
        const fetchedStats = res?.classStats ?? { averageScore: 0, scoreChange: 0, topWeaknesses: [] };
        setStudents(fetchedStudents);
        setClassStats(fetchedStats);
        setIsEmpty(fetchedStudents.length === 0);
      } catch (error) {
        console.error('EduConsole: Fetch error:', error);
        setStudents([]);
        setIsEmpty(true);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [refreshKey]);


  // 從學員資料提取群組列表
  const groups = [...new Set(students.map(s => s.group).filter(Boolean))] as string[];

  // 根據群組 + 搜尋篩選
  const groupFiltered = activeGroup === 'all' ? students : students.filter(s => s.group === activeGroup);
  const filtered = groupFiltered.filter(
    s =>
      s.name.includes(search) ||
      s.email.toLowerCase().includes(search.toLowerCase()),
  );

  const atRiskStudents = groupFiltered.filter(s => s.status === 'needs_attention');
  const activeCount    = groupFiltered.filter(s => s.status === 'active').length;
  const avgScore       = classStats.averageScore;

  const refreshData = useCallback(() => {
    setRefreshKey(k => k + 1);
  }, []);

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
            <span className="text-white">{students.length} / 200</span>
          </div>
          <button className="bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-2 rounded-full text-sm font-bold transition-colors"
            onClick={() => setImportModalOpen(true)}>
            + 匯入學生名單
          </button>
        </div>
      </header>
      
      {/* Group Switcher */}
      {groups.length > 0 && (
        <div className="bg-white border-b border-slate-200">
          <div className="container mx-auto max-w-6xl px-4">
            <div className="flex items-center gap-1 overflow-x-auto py-2 scrollbar-hide">
              <button
                onClick={() => setActiveGroup('all')}
                className={`shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeGroup === 'all'
                    ? 'bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                全部群組
                <span className="ml-1.5 text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full">
                  {students.length}
                </span>
              </button>
              {groups.map(group => {
                const count = students.filter(s => s.group === group).length;
                return (
                  <button
                    key={group}
                    onClick={() => setActiveGroup(group)}
                    className={`shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeGroup === group
                        ? 'bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold'
                        : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {group}
                    <span className="ml-1.5 text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500" />
              <p className="text-slate-500 font-medium">資料載入中...</p>
            </div>
          ) : isEmpty ? (
            <div className="flex flex-col items-center justify-center h-96 space-y-6">
              <div className="h-20 w-20 rounded-full bg-indigo-50 flex items-center justify-center">
                <Users className="h-10 w-10 text-indigo-400" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-xl font-bold text-slate-900">尚未匯入任何學員</h2>
                <p className="text-slate-500 text-sm max-w-md">
                  請先透過 CSV 匯入學生名單，開始管理您的教育機構。
                </p>
              </div>
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm max-w-lg w-full">
                <h3 className="text-sm font-bold text-slate-700 mb-4">快速開始三步驟</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm font-bold shrink-0">1</div>
                    <span className="text-sm text-slate-600">建立學員群組（如：AWS 基礎班）</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm font-bold shrink-0">2</div>
                    <span className="text-sm text-slate-600">上傳 CSV 匯入學員名單</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm font-bold shrink-0">3</div>
                    <span className="text-sm text-slate-600">派發模擬考卷給群組</span>
                  </div>
                </div>
              </div>
              <button
                className="bg-indigo-500 hover:bg-indigo-400 text-white px-6 py-3 rounded-xl font-bold transition-colors text-sm"
                onClick={() => setImportModalOpen(true)}
              >
                <FileSpreadsheet className="h-4 w-4 inline-block mr-2" />
                匯入學生名單
              </button>
            </div>
          ) : (
            <>
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-indigo-50 rounded-2xl p-5 shadow-sm border border-indigo-100">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-4 w-4 text-indigo-500" />
                <span className="text-xs text-slate-500 font-medium">已註冊學員</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{groupFiltered.length}</div>
              <div className="text-xs text-slate-400 font-medium mt-1">活躍 {activeCount} 人</div>
            </div>
            <div className="bg-emerald-50 rounded-2xl p-5 shadow-sm border border-emerald-100">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-4 w-4 text-emerald-500" />
                <span className="text-xs text-slate-500 font-medium">活躍率</span>
              </div>
              <div className="text-3xl font-extrabold text-emerald-600">{groupFiltered.length > 0 ? Math.round((activeCount / groupFiltered.length) * 100) : 0}%</div>
              <div className="text-xs text-slate-400 font-medium mt-1">{activeCount} / {groupFiltered.length} 人</div>
            </div>
            <div className="bg-amber-50 rounded-2xl p-5 shadow-sm border border-amber-100">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <span className="text-xs text-slate-500 font-medium">需關注學員</span>
              </div>
              <div className="text-3xl font-extrabold text-amber-600">{atRiskStudents.length}</div>
              <div className="text-xs text-slate-400 font-medium mt-1">低於預警閾值</div>
            </div>
            <div className="bg-blue-50 rounded-2xl p-5 shadow-sm border border-blue-100">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-blue-500" />
                <span className="text-xs text-slate-500 font-medium">班級平均</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{avgScore || '—'}</div>
              {classStats.scoreChange !== 0 && (
                <div className={`text-xs font-medium mt-1 ${classStats.scoreChange > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {classStats.scoreChange > 0 ? '+' : ''}{classStats.scoreChange} 分
                </div>
              )}
            </div>
          </div>

          {/* ── 預警中心 ── */}
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-rose-500" />
              <h2 className="text-base font-bold text-rose-800">預警中心</h2>
              <span className="text-xs text-rose-400 ml-auto">{atRiskStudents.length} 位學員需關注</span>
            </div>
            <div className="space-y-3">
              {atRiskStudents.length === 0 ? (
                <div className="text-center py-6 text-slate-400 text-sm">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-emerald-400" />
                  目前沒有需要關注的學員
                </div>
              ) : (
                atRiskStudents.map((s) => (
                  <div key={s.id} className="bg-white rounded-xl p-4 border border-rose-100 flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900 text-sm">{s.name}</span>
                        <TrendIcon trend={s.trend} />
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {(s.averageScore ?? 0) < 60 && <span className="text-rose-600 font-medium">平均分 {s.averageScore}</span>}
                        {s.lastActiveLabel && <span className="text-slate-400"> · 最後活躍: {s.lastActiveLabel}</span>}
                      </p>
                    </div>
                    <button className="shrink-0 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                      onClick={() => alert('此功能即將推出，敬請期待！')}>
                      查看詳情
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ── 班級弱點分析 ── */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="h-5 w-5 text-rose-500" />
              <h2 className="text-base font-bold text-slate-900">班級弱點分析</h2>
            </div>
            <div className="space-y-4">
              {classStats.topWeaknesses.length === 0 ? (
                <p className="text-center py-4 text-slate-400 text-sm">尚無足夠測驗資料進行弱點分析</p>
              ) : (
                classStats.topWeaknesses.map((item) => (
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
                ))
              )}
            </div>
          </div>

          {/* ── Quick Actions ── */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4"
              onClick={() => setImportModalOpen(true)}>
              <div className="h-11 w-11 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
                <FileSpreadsheet className="h-5 w-5 text-indigo-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">批量匯入名單</h3>
                <p className="text-xs text-slate-500 mt-0.5">上傳 CSV，自動發送邀請</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400 ml-auto" />
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4"
              onClick={() => alert('此功能即將推出，敬請期待！')}>
              <div className="h-11 w-11 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                <Send className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">派發模擬考卷</h3>
                <p className="text-xs text-slate-500 mt-0.5">統一生成並設定期限</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400 ml-auto" />
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow cursor-pointer flex items-center gap-4"
              onClick={() => alert('此功能即將推出，敬請期待！')}>
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
                        onClick={e => { e.stopPropagation(); alert('此功能即將推出，敬請期待！'); }}
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
                            <button className="flex items-center gap-1.5 bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-bold px-3 py-2 rounded-lg transition-colors"
                              onClick={() => alert('此功能即將推出，敬請期待！')}>
                              <Sparkles className="h-3.5 w-3.5" />
                              AI 個人化補強建議
                            </button>
                            <button className="flex items-center gap-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold px-3 py-2 rounded-lg transition-colors"
                              onClick={() => alert('此功能即將推出，敬請期待！')}>
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
              <button className="w-full bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-3 rounded-xl font-bold transition-colors text-sm relative z-10"
                onClick={() => alert('此功能即將推出，敬請期待！')}>
                匯出詳細報告
              </button>
            </div>

          </div>

            </>
          )}
        </div>
      </div>

      {/* CSV Import Modal */}
      <ImportStudentModal
        open={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onSuccess={refreshData}
      />
    </div>
  );
}
