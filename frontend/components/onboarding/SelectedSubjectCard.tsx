'use client';

import { useMemo } from 'react';
import { X } from 'lucide-react';
import { differenceInCalendarDays } from 'date-fns';
import type { SelfAssessmentLevel } from '@/types';

export interface SelectedSubject {
  subjectId: string;
  subjectName: string;
  examDate: string;
  resultDate: string;
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

export function getModeBadge(examDate: string): { label: string; className: string } | null {
  if (!examDate) return null;
  const days = differenceInCalendarDays(new Date(examDate), new Date());
  if (days < 0) return null;
  if (days <= 30) {
    return { label: '短期衝刺', className: 'bg-rose-100 text-rose-700' };
  }
  if (days <= 90) {
    return { label: '穩步前進', className: 'bg-blue-100 text-blue-700' };
  }
  return { label: '長期備戰', className: 'bg-green-100 text-green-700' };
}

export default function SelectedSubjectCard({ subject, onUpdate, onRemove }: SelectedSubjectCardProps) {
  const badge = useMemo(() => getModeBadge(subject.examDate), [subject.examDate]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h4 className="font-bold text-slate-900">{subject.subjectName}</h4>
          {badge && (
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${badge.className}`}>
              {badge.label}
            </span>
          )}
        </div>
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

        {/* Result date */}
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">預計放榜日期</label>
          <input
            type="date"
            value={subject.resultDate}
            onChange={e => onUpdate({ ...subject, resultDate: e.target.value })}
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
