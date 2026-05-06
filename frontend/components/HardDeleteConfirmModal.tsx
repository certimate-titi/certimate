'use client';

/**
 * @file HardDeleteConfirmModal — 硬刪除二次確認 Modal。
 *
 * 用戶必須在輸入框鍵入「確認刪除」四字才能啟用「永久刪除」按鈕。
 * 顯示連帶刪除筆數預覽，強化不可逆警示。
 */

import { useState } from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

export interface CascadeCount {
  // 科目刪除
  knowledge_nodes?: number;
  exams?: number;
  questions?: number;
  answers?: number;
  wrong_answers?: number;
  resources?: number;
  resource_chunks?: number;
  resource_scaffolds?: number;
  node_mastery?: number;
  learning_journeys?: number;
  // 資源刪除
  resource_parse_jobs?: number;
  question_candidates?: number;
}

interface HardDeleteConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  entityName: string;
  cascadeCount: CascadeCount;
  loading?: boolean;
}

const CASCADE_LABELS: { key: keyof CascadeCount; label: string }[] = [
  { key: 'knowledge_nodes',    label: '知識節點' },
  { key: 'exams',              label: '考試' },
  { key: 'questions',          label: '題目' },
  { key: 'answers',            label: '答題紀錄' },
  { key: 'wrong_answers',      label: '錯題紀錄' },
  { key: 'resources',          label: '學習資源' },
  { key: 'resource_chunks',    label: '知識切塊' },
  { key: 'resource_scaffolds', label: '學習鷹架' },
  { key: 'resource_parse_jobs',label: '解析任務' },
  { key: 'question_candidates',label: '題目候選' },
  { key: 'node_mastery',       label: '掌握度紀錄' },
  { key: 'learning_journeys',  label: '學習旅程' },
];

const CONFIRM_PHRASE = '確認刪除';

export default function HardDeleteConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  entityName,
  cascadeCount,
  loading = false,
}: HardDeleteConfirmModalProps) {
  const [inputValue, setInputValue] = useState('');

  if (!open) return null;

  const canDelete = inputValue === CONFIRM_PHRASE;

  const relevantItems = CASCADE_LABELS.filter(
    ({ key }) => (cascadeCount[key] ?? 0) > 0
  );

  const handleClose = () => {
    setInputValue('');
    onClose();
  };

  const handleConfirm = async () => {
    if (!canDelete || loading) return;
    await onConfirm();
    setInputValue('');
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl border border-rose-200 w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-rose-100 bg-rose-50">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
              <AlertTriangle className="h-5 w-5 text-rose-600" />
            </div>
            <div>
              <h2 className="text-base font-bold text-rose-900">{title}</h2>
              <p className="text-xs text-rose-700 mt-0.5 font-mono truncate max-w-xs">{entityName}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 disabled:opacity-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Warning text */}
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-sm text-rose-800">
            <span className="font-semibold">此操作將永久刪除以下資料，無法復原：</span>
          </div>

          {/* Cascade count list */}
          {relevantItems.length > 0 ? (
            <ul className="space-y-1.5">
              {relevantItems.map(({ key, label }) => (
                <li key={key} className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-slate-50 text-sm">
                  <span className="text-slate-700">{label}</span>
                  <span className="font-bold text-rose-600 tabular-nums">
                    {(cascadeCount[key] ?? 0).toLocaleString()} 筆
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500 px-1">（無連帶資料，僅刪除主體本身）</p>
          )}

          {/* Confirmation input */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-700">
              請輸入「<span className="font-bold text-rose-700">{CONFIRM_PHRASE}</span>」以確認操作
            </label>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onPaste={(e) => e.preventDefault()}
              placeholder="請手動輸入確認文字"
              disabled={loading}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 focus:border-transparent disabled:opacity-50"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-5 pb-5">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-4 py-2 rounded-lg text-sm font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canDelete || loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            {loading ? '刪除中…' : '永久刪除'}
          </button>
        </div>
      </div>
    </div>
  );
}
