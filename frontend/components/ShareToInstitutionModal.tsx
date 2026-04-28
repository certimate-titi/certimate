/**
 * @file 分享資源給機構 Modal（Spec 11 §ShareModal）。
 *
 * 取代舊版 prompt() 直接輸入 UUID 的不安全流程。提供：
 * 1. 從「我可分享的機構列表」選一個（顯示名稱 + 學生數，避免誤分享）
 * 2. 確認步驟顯示「該機構 N 名學生可看到此資源」
 * 3. inline 錯誤呈現、loading state、disabled 防重複送出
 *
 * 注意：EDU 用戶定位是學生，所以 UI 文案強調「分享給機構 → 該機構學生可看到」，
 * 而不是「分享給 EDU 用戶」。
 */
'use client';

import { useEffect, useState } from 'react';
import { Share2, X, Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { resourceShareService, type ShareableInstitution } from '@/lib/api/services';

export interface ShareToInstitutionModalProps {
  /** 要分享的資源 ID */
  resourceId: string;
  /** 資源名稱（顯示於確認區） */
  resourceName: string;
  /** 關閉 modal */
  onClose: () => void;
  /** 分享成功後 callback（觸發列表 refresh） */
  onSuccess?: () => void;
}

export default function ShareToInstitutionModal({
  resourceId,
  resourceName,
  onClose,
  onSuccess,
}: ShareToInstitutionModalProps) {
  const [institutions, setInstitutions] = useState<ShareableInstitution[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ShareableInstitution | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    resourceShareService.listShareable()
      .then((res) => setInstitutions(res.institutions || []))
      .catch((e: unknown) => {
        const err = e as { message?: string };
        setError(err?.message || '載入機構列表失敗');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async () => {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      await resourceShareService.shareToInstitution(resourceId, selected.id);
      setDone(true);
      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1200);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setError(err?.message || '分享失敗');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-2xl p-5 max-w-md w-full mx-4 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Share2 className="h-5 w-5 text-blue-500" />
            分享資源給機構
          </h3>
          <button onClick={onClose} disabled={submitting}>
            <X className="w-5 h-5 text-slate-400 hover:text-slate-700" />
          </button>
        </div>

        <p className="text-xs text-slate-500 mb-3 leading-relaxed">
          選擇要分享的機構。該機構**所有學生**將能在學習庫看到此資源。
        </p>

        {/* 資源名稱 */}
        <div className="px-3 py-2 bg-slate-50 rounded text-xs text-slate-700 mb-3 break-all">
          📎 {resourceName}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
          </div>
        ) : error && institutions.length === 0 ? (
          <div className="flex items-start gap-2 p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        ) : institutions.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-400">
            目前沒有可分享的機構（需機構先簽署 DPA）
          </div>
        ) : (
          <>
            <ul className="max-h-60 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 mb-3">
              {institutions.map((inst) => (
                <li key={inst.id}>
                  <button
                    onClick={() => setSelected(inst)}
                    disabled={submitting || done}
                    className={`w-full text-left px-3 py-2.5 hover:bg-slate-50 flex items-center gap-2 ${
                      selected?.id === inst.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-900 truncate">{inst.name}</div>
                      <div className="text-[11px] text-slate-500">
                        {inst.student_count} 名學生
                      </div>
                    </div>
                    {selected?.id === inst.id && <CheckCircle2 className="w-4 h-4 text-blue-500" />}
                  </button>
                </li>
              ))}
            </ul>

            {selected && (
              <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900 mb-3 leading-relaxed">
                確認：將「<b>{resourceName.length > 40 ? resourceName.slice(0, 40) + '...' : resourceName}</b>」
                分享給「<b>{selected.name}</b>」，該機構 <b>{selected.student_count}</b> 名學生將能看到此資源。
              </div>
            )}
          </>
        )}

        {error && institutions.length > 0 && (
          <div className="flex items-start gap-2 p-2 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs mb-2">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        {done ? (
          <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded text-emerald-700 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4" />
            ✅ 分享成功！
          </div>
        ) : (
          <div className="flex gap-2 justify-end">
            <button
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-sm font-medium text-slate-700 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-50"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={!selected || submitting}
              className="px-4 py-2 text-sm font-bold text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
              確定分享
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
