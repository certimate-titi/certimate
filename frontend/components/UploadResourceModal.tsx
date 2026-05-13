/**
 * @file UploadResourceModal — 快速匯入學習資源 Modal。
 *
 * 抽自 /dashboard 的「快速匯入學習資源」section，掛在 /knowledge「新增資源」按鈕。
 * Props:
 *   open            - 控制顯示/隱藏
 *   onClose         - 關閉 callback
 *   activeSubjectId - 目前選中科目（傳入可為空字串）
 *   subjects        - 使用者科目列表（用於判斷是否需要先選科目）
 *   onUploadComplete - 上傳完成 callback（帶 resourceId），可選
 */
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import {
  Upload, Youtube, FileText, Clock, XCircle,
  CheckCircle2, RefreshCw, Loader2, X,
} from 'lucide-react';
import { documentService, resourceParseService } from '@/lib/api/services';
import QuotaBadge from '@/components/QuotaBadge';
import { invalidateQuotaCache, useQuotaGuard } from '@/hooks/use-quota';
import type { UserSubject } from '@/types';

interface UploadResourceModalProps {
  open: boolean;
  onClose: () => void;
  activeSubjectId: string | null;
  subjects: UserSubject[];
  onUploadComplete?: (resourceId: string) => void;
}

export default function UploadResourceModal({
  open,
  onClose,
  activeSubjectId,
  subjects,
  onUploadComplete,
}: UploadResourceModalProps) {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'pending' | 'processing' | 'completed' | 'failed'>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadErrorMessage, setUploadErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadGuard = useQuotaGuard('monthly_uploads');

  // 關閉時重置狀態
  useEffect(() => {
    if (!open) {
      setUploadStatus('idle');
      setUploadProgress(0);
      setUploadErrorMessage(null);
      setYoutubeUrl('');
      setUploading(false);
    }
  }, [open]);

  // ESC 關閉
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  const pollParseUntilDone = useCallback(async (resourceId: string) => {
    const startedAt = Date.now();
    const timeoutMs = 90_000;
    while (Date.now() - startedAt < timeoutMs) {
      try {
        const job = await resourceParseService.getStatus(resourceId);
        if (job.status === 'COMPLETED') {
          setUploadStatus('completed');
          onUploadComplete?.(resourceId);
          return;
        }
        if (job.status === 'FAILED') {
          setUploadErrorMessage(job.failure_reason || '解析失敗（後端未提供原因）');
          setUploadStatus('failed');
          return;
        }
      } catch {
        // job 尚未建立或暫時不可達 — 繼續等下一輪
      }
      await new Promise((r) => setTimeout(r, 3000));
    }
    // 超時 → 視為 completed（背景仍在跑）
    setUploadStatus('completed');
    onUploadComplete?.(resourceId);
  }, [onUploadComplete]);

  const handleFileUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!activeSubjectId) {
      alert('請先選擇或新增備考科目後再上傳資源');
      return;
    }

    const file = files[0];
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const docExts = ['pdf', 'docx', 'pptx', 'xlsx', 'doc', 'ppt', 'xls', 'md', 'txt'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    const audioExts = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'wma', 'aac'];
    const videoExts = ['mp4', 'mov', 'avi', 'mkv', 'webm'];

    let maxSizeMB = 50;
    let typeLabel = '文件';
    if (imageExts.includes(ext)) {
      maxSizeMB = 20; typeLabel = '圖片';
    } else if (audioExts.includes(ext)) {
      maxSizeMB = 100; typeLabel = '音訊';
    } else if (videoExts.includes(ext)) {
      maxSizeMB = 500; typeLabel = '影片';
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
        if (p >= 20) setUploadStatus('processing');
        return Math.min(p + 10, 90);
      });
    }, 300);
    try {
      setUploadErrorMessage(null);
      const uploadRes = await documentService.upload({ file: files[0], title: files[0].name, subjectId: activeSubjectId });
      clearInterval(progressInterval);
      setUploadProgress(100);
      invalidateQuotaCache();
      await pollParseUntilDone(uploadRes.document.id);
    } catch (err) {
      clearInterval(progressInterval);
      setUploadErrorMessage(err instanceof Error ? err.message : String(err));
      setUploadStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [activeSubjectId, pollParseUntilDone]);

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
        if (p >= 20) setUploadStatus('processing');
        return Math.min(p + 8, 90);
      });
    }, 400);
    try {
      setUploadErrorMessage(null);
      const uploadRes = await documentService.upload({ youtubeUrl: youtubeUrl.trim(), subjectId: activeSubjectId });
      clearInterval(progressInterval);
      setUploadProgress(100);
      setYoutubeUrl('');
      invalidateQuotaCache();
      await pollParseUntilDone(uploadRes.document.id);
    } catch (err) {
      clearInterval(progressInterval);
      setUploadErrorMessage(err instanceof Error ? err.message : String(err));
      setUploadStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [youtubeUrl, activeSubjectId, pollParseUntilDone]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="快速匯入學習資源"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Card */}
      <div className="relative z-10 w-full max-w-lg bg-white rounded-3xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          <Upload className="h-5 w-5 text-emerald-500 shrink-0" />
          <h2 className="text-xl font-bold text-slate-900 flex-1">快速匯入學習資源</h2>
          <span><QuotaBadge quotaKey="monthly_uploads" variant="pill" /></span>
          <button
            type="button"
            onClick={onClose}
            className="ml-2 p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="關閉"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">本月可上傳資源檔案數，超過上限請升級方案。</p>

        {/* 無科目提示 */}
        {subjects.length === 0 && (
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
            尚未選擇備考科目，請先前往{' '}
            <Link href="/dashboard" className="font-bold underline" onClick={onClose}>儀表板</Link>{' '}
            新增科目後再上傳資源。
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
              <Link href="/knowledge" className="text-sm font-bold text-emerald-600 underline underline-offset-2 ml-1" onClick={onClose}>
                立即查看
              </Link>
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

        {/* Upload Inputs */}
        <div className="grid sm:grid-cols-2 gap-4">
          {/* File Upload */}
          <div className="space-y-2">
            <div
              onClick={() => { if (!uploadGuard.is_blocked) fileInputRef.current?.click(); }}
              className={`border-2 border-dashed rounded-2xl p-5 flex flex-col items-center justify-center text-center transition-colors group ${
                uploadGuard.is_blocked ? 'border-rose-200 bg-rose-50/40 cursor-not-allowed opacity-60' :
                uploading ? 'border-emerald-400 bg-emerald-50/50 cursor-pointer' :
                'border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/50 cursor-pointer'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.md,.txt,.docx,.pptx,.xlsx,.doc,.ppt,.xls,.mp3,.wav,.m4a,.flac,.ogg,.wma,.aac,.mp4,.mov,.avi,.mkv,.webm,.jpg,.jpeg,.png,.gif,.webp"
                className="hidden"
                onChange={e => handleFileUpload(e.target.files)}
                disabled={uploading || uploadGuard.is_blocked}
              />
              {uploading && (uploadStatus === 'pending' || uploadStatus === 'processing') ? (
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
                  <p className="font-medium text-emerald-700">上傳中...</p>
                </div>
              ) : uploadGuard.is_blocked ? (
                <>
                  <FileText className="h-8 w-8 text-rose-400 mb-3" />
                  <p className="font-bold text-rose-700 mb-1">本月上傳次數已用完</p>
                  <Link href="/account" className="text-xs text-emerald-600 underline font-medium" onClick={(e) => e.stopPropagation()}>
                    升級方案解鎖更多 →
                  </Link>
                </>
              ) : (
                <>
                  <FileText className="h-8 w-8 text-slate-400 group-hover:text-emerald-500 transition-colors mb-3" />
                  <p className="font-medium text-slate-700 mb-1">上傳實體檔案</p>
                  <p className="text-xs text-slate-500">PDF、Office、文字、音訊、影片、圖片</p>
                </>
              )}
            </div>
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

        <p className="text-[10px] text-slate-400 text-center mt-3">
          *點擊上傳即代表您保證擁有此檔案／影片的合法使用授權，且同意不公開散佈生成的內容。*
        </p>
      </div>
    </div>
  );
}
