/**
 * @file 回報 AI 補洞鷹架不準確的 Modal 元件。
 *
 * 提供 5 個原因選項（A-E）與選填補充說明（100 字內），
 * 送出後內部呼叫 API 並通知父元件隱藏鷹架。
 */
'use client';

import { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { orphanScaffoldService } from '@/lib/api/services';
import type { OrphanReasonCode } from '@/types/api';

const REASON_OPTIONS: { code: OrphanReasonCode; label: string }[] = [
  { code: 'definition_wrong', label: 'A. 定義有誤' },
  { code: 'example_wrong', label: 'B. 範例不符科目' },
  { code: 'answer_wrong', label: 'C. 練習題答案錯誤' },
  { code: 'unrelated', label: 'D. 與節點名稱無關' },
  { code: 'other', label: 'E. 其他（請於下方說明）' },
];

/**
 * ReportInaccurateModal 的 props。
 */
export interface ReportInaccurateModalProps {
  /** 要回報的鷹架 UUID */
  scaffoldId: string;
  /** 關閉 modal 的回呼 */
  onClose: () => void;
  /** 回報成功後的回呼（通知父元件隱藏鷹架） */
  onReported: () => void;
}

/**
 * 回報 AI 補洞鷹架不準確的 Modal。
 *
 * 選擇原因後送出 → API 呼叫 → 成功後通知父元件隱藏。
 * 若 API 回 409（已回報過），以友善文字告知用戶。
 */
export default function ReportInaccurateModal({
  scaffoldId,
  onClose,
  onReported,
}: ReportInaccurateModalProps) {
  const [selectedReason, setSelectedReason] = useState<OrphanReasonCode | null>(null);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!selectedReason) return;
    setSubmitting(true);
    setError(null);
    try {
      await orphanScaffoldService.reportInaccurate(
        scaffoldId,
        selectedReason,
        note.trim() || undefined,
      );
      onReported();
    } catch (err) {
      const e = err as { status?: number; message?: string };
      if (e.status === 409) {
        setError('您已回報過此鷹架，感謝您的回饋！');
      } else {
        setError(e.message || '送出失敗，請稍後再試');
      }
    } finally {
      setSubmitting(false);
    }
  }

  const noteOverLimit = note.length > 100;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-label="回報 AI 鷹架不準確"
    >
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <h2 className="text-sm font-bold text-slate-800">回報內容不準確</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="關閉"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Reason Selection */}
        <div className="px-5 pt-4 pb-2">
          <p className="text-[11px] text-slate-500 mb-3">請選擇最符合的原因（必選）</p>
          <div className="space-y-2">
            {REASON_OPTIONS.map(({ code, label }) => (
              <label
                key={code}
                className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 cursor-pointer transition-colors ${
                  selectedReason === code
                    ? 'border-amber-400 bg-amber-50'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="reason"
                  value={code}
                  checked={selectedReason === code}
                  onChange={() => setSelectedReason(code)}
                  className="accent-amber-500"
                />
                <span className="text-xs text-slate-700">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Note */}
        <div className="px-5 pb-4">
          <label className="block text-[11px] text-slate-500 mb-1">
            補充說明（選填，100 字內）
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="請描述具體問題..."
            rows={3}
            className={`w-full rounded-lg border px-3 py-2 text-xs text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-amber-400 ${
              noteOverLimit ? 'border-rose-400 bg-rose-50' : 'border-slate-200 bg-slate-50'
            }`}
            disabled={submitting}
          />
          <div className="flex justify-between items-center mt-1">
            {noteOverLimit ? (
              <p className="text-[10px] text-rose-500">超過 100 字上限</p>
            ) : (
              <span />
            )}
            <span className={`text-[10px] ml-auto ${noteOverLimit ? 'text-rose-500' : 'text-slate-400'}`}>
              {note.length}/100
            </span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-5 mb-3 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2">
            <p className="text-[11px] text-rose-600">{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 px-5 pb-5">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-slate-200 py-2 text-xs text-slate-600 hover:bg-slate-50 transition-colors"
            disabled={submitting}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedReason || submitting || noteOverLimit}
            className="flex-1 rounded-lg bg-amber-500 py-2 text-xs font-bold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
          >
            {submitting ? '送出中...' : '送出回報'}
          </button>
        </div>
      </div>
    </div>
  );
}
