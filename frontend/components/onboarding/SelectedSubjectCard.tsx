'use client';

import { X } from 'lucide-react';
import type { SelfAssessmentLevel } from '@/types';

export interface SelectedSubject {
  subjectId: string;
  subjectName: string;
  examDate: string;
  selfAssessment: SelfAssessmentLevel;
}

interface SelectedSubjectCardProps {
  subject: SelectedSubject;
  onUpdate: (updated: SelectedSubject) => void;
  onRemove: () => void;
}

const assessmentOptions: { value: SelfAssessmentLevel; label: string }[] = [
  { value: 'beginner', label: '初學者' },
  { value: 'intermediate', label: '有基礎' },
  { value: 'advanced', label: '進階複習' },
];

export default function SelectedSubjectCard({ subject, onUpdate, onRemove }: SelectedSubjectCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-bold text-slate-900">{subject.subjectName}</h4>
        <button
          onClick={onRemove}
          className="p-1 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
          aria-label={`移除 ${subject.subjectName}`}
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-3">
        {/* Exam date */}
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">預計考試日期</label>
          <input
            type="date"
            value={subject.examDate}
            onChange={e => onUpdate({ ...subject, examDate: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        {/* Self assessment */}
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">自評程度</label>
          <div className="flex gap-1">
            {assessmentOptions.map(opt => (
              <button
                key={opt.value}
                onClick={() => onUpdate({ ...subject, selfAssessment: opt.value })}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-colors ${
                  subject.selfAssessment === opt.value
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
