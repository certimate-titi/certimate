'use client';

import { Plus } from 'lucide-react';
import { differenceInDays, parseISO } from 'date-fns';
import type { UserSubject } from '@/types';

interface SubjectSwitcherProps {
  subjects: UserSubject[];
  activeSubjectId: string;
  onSwitch: (subjectId: string) => void;
  onAddSubject: () => void;
  allowAdd?: boolean;
}

export default function SubjectSwitcher({
  subjects,
  activeSubjectId,
  onSwitch,
  onAddSubject,
  allowAdd = true,
}: SubjectSwitcherProps) {
  return (
    <div className="bg-white border-b border-slate-200">
      <div className="container mx-auto max-w-6xl px-4">
        <div className="flex items-center gap-1 overflow-x-auto py-2 scrollbar-hide">
          {subjects.filter(s => s && s.id).map(subject => {
            const isActive = subject.id === activeSubjectId;
            const daysLeft = subject.examDate ? differenceInDays(parseISO(subject.examDate), new Date()) : -1;

            return (
              <button
                key={subject.id}
                onClick={() => onSwitch(subject.id)}
                className={`shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span className={isActive ? 'font-bold' : ''}>{subject.subjectName}</span>
                {daysLeft > 0 && (
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                    daysLeft <= 7
                      ? 'bg-rose-100 text-rose-700'
                      : daysLeft <= 30
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-slate-100 text-slate-500'
                  }`}>
                    {daysLeft}天
                  </span>
                )}
              </button>
            );
          })}

          {/* Add subject button */}
          {allowAdd && (
            <button
              onClick={onAddSubject}
              className="shrink-0 flex items-center justify-center w-8 h-8 rounded-full border-2 border-dashed border-slate-300 hover:border-emerald-400 text-slate-400 hover:text-emerald-500 transition-colors ml-1"
              aria-label="新增備考科目"
            >
              <Plus className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
