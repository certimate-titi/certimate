'use client';

import { X } from 'lucide-react';
import SubjectPicker from '@/components/onboarding/SubjectPicker';
import type { SelectedSubject } from '@/components/onboarding/SelectedSubjectCard';

interface SubjectPickerModalProps {
  excludeSubjectIds: string[];
  onConfirm: (subjects: SelectedSubject[]) => void;
  onClose: () => void;
}

export default function SubjectPickerModal({
  excludeSubjectIds,
  onConfirm,
  onClose,
}: SubjectPickerModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-900">新增備考科目</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto max-h-[calc(90vh-80px)]">
          <SubjectPicker
            mode="add"
            excludeSubjectIds={excludeSubjectIds}
            onConfirm={onConfirm}
            onCancel={onClose}
          />
        </div>
      </div>
    </div>
  );
}
