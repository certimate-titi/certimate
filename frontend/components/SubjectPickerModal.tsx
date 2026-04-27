/**
 * @file 新增備考科目 Modal——包裝 SubjectPicker 並提供「自訂考科」入口（PRD-033 §8）。
 */
'use client';

import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import SubjectPicker from '@/components/onboarding/SubjectPicker';
import type { SelectedSubject } from '@/components/onboarding/SelectedSubjectCard';
import { subjectService } from '@/lib/api/services';

/**
 * SubjectPickerModal 的 props。
 */
interface SubjectPickerModalProps {
  /** 不允許再次選取的科目 ID（已加入帳號） */
  excludeSubjectIds: string[];
  /** 確認新增時觸發 */
  onConfirm: (subjects: SelectedSubject[]) => void;
  /** 關閉 Modal 時觸發 */
  onClose: () => void;
}

/**
 * 新增備考科目 Modal。
 *
 * 主體為 SubjectPicker（add 模式），底部提供「+ 新增自訂考科」展開區，
 * 自訂科目透過 `subjectService.addSubject` 寫入後端（僅本人可見）。
 *
 * @param props.excludeSubjectIds - 排除的科目 ID
 * @param props.onConfirm - 確認回呼
 * @param props.onClose - 關閉回呼
 */
export default function SubjectPickerModal({
  excludeSubjectIds,
  onConfirm,
  onClose,
}: SubjectPickerModalProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customName, setCustomName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateCustom = async () => {
    const name = customName.trim();
    if (!name) return;
    setBusy(true);
    setError(null);
    try {
      await subjectService.addSubject({
        subjectName: name,
        subjectId: name,
        selfAssessment: 'beginner',
      } as never);
      setCustomName('');
      setShowCustom(false);
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '建立失敗');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-900">新增備考科目</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto flex-1">
          <SubjectPicker
            mode="add"
            excludeSubjectIds={excludeSubjectIds}
            onConfirm={onConfirm}
            onCancel={onClose}
          />
        </div>

        {/* PRD-033 §8：底部「+ 新增自訂考科」入口 */}
        <div className="border-t border-slate-200 bg-slate-50 p-4">
          {!showCustom ? (
            <button
              onClick={() => setShowCustom(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border-2 border-dashed border-slate-300 text-sm text-slate-600 hover:border-slate-400 hover:bg-white transition"
            >
              <Plus className="w-4 h-4" /> 找不到？新增自訂考科（僅你可見）
            </button>
          ) : (
            <div className="space-y-2">
              <input
                autoFocus
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateCustom()}
                placeholder="例如：我的化學複習"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm"
              />
              {error && <div className="text-xs text-red-600">{error}</div>}
              <div className="flex gap-2">
                <button
                  onClick={handleCreateCustom}
                  disabled={busy || !customName.trim()}
                  className="flex-1 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm disabled:opacity-50"
                >
                  建立
                </button>
                <button
                  onClick={() => {
                    setShowCustom(false);
                    setCustomName('');
                    setError(null);
                  }}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600"
                >
                  取消
                </button>
              </div>
              <p className="text-xs text-slate-500">
                自訂考科僅你自己可見，可於「帳號設定 → 我的自建考科」管理。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
