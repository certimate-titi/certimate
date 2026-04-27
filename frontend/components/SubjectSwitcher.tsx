/**
 * @file 備考科目切換 Tab——含距考天數徽章與「+ 新增科目」入口。
 */
'use client';

import { Plus } from 'lucide-react';
import { differenceInDays, parseISO } from 'date-fns';
import type { UserSubject } from '@/types';

/**
 * SubjectSwitcher 的 props。
 */
interface SubjectSwitcherProps {
  /** 使用者已加入的備考科目 */
  subjects: UserSubject[];
  /** 當前 active 科目 ID */
  activeSubjectId: string;
  /** 切換科目時觸發 */
  onSwitch: (subjectId: string) => void;
  /** 點擊「+」新增科目按鈕時觸發 */
  onAddSubject: () => void;
  /** 是否顯示新增按鈕（預設 true） */
  allowAdd?: boolean;
  /** 顯示樣式：default 含外層 container，compact 僅 tabs */
  variant?: 'default' | 'compact';
}

/**
 * 備考科目切換 Tab。
 *
 * 每個 tab 顯示科目名稱與距考剩餘天數徽章（≤7 紅 / ≤30 黃 / 其餘灰）；
 * compact 模式只回傳 tabs 本體，default 模式包覆白底 container。
 *
 * @param props.subjects - 備考科目清單
 * @param props.activeSubjectId - 當前科目 ID
 * @param props.onSwitch - 切換回呼
 * @param props.onAddSubject - 新增回呼
 * @param props.allowAdd - 是否允許新增
 * @param props.variant - 顯示樣式
 */
export default function SubjectSwitcher({
  subjects,
  activeSubjectId,
  onSwitch,
  onAddSubject,
  allowAdd = true,
  variant = 'default',
}: SubjectSwitcherProps) {
  const tabs = (
    <div className={`flex items-center gap-1 overflow-x-auto scrollbar-hide ${variant === 'compact' ? '' : 'py-2'}`}>
      {subjects.filter(s => s && s.id).map(subject => {
        const isActive = subject.id === activeSubjectId;
        const daysLeft = subject.examDate ? differenceInDays(parseISO(subject.examDate), new Date()) : -1;

        return (
          <button
            key={subject.id}
            onClick={() => onSwitch(subject.id)}
            className={`shrink-0 flex items-center gap-1.5 ${variant === 'compact' ? 'px-3 py-1' : 'px-4 py-2'} rounded-lg text-sm font-medium transition-colors ${
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
  );

  if (variant === 'compact') {
    return tabs;
  }

  return (
    <div className="bg-white border-b border-slate-200">
      <div className="container mx-auto max-w-6xl px-4">
        {tabs}
      </div>
    </div>
  );
}
