'use client';

/**
 * @file NotesClassifyTree.tsx
 * 左側分類樹 sidebar：
 *  - 搜尋框（即時 filter + 最近搜尋 dropdown）
 *  - 科目樹（subject 點擊 → timeline filter）
 *  - type chip：📝 自由 / ✨ AI / 🦅 鷹架
 *  - 底部「全部筆記」toggle 重置篩選
 */

import { useEffect, useRef, useState } from 'react';
import { BookOpen, ChevronDown, ChevronRight, Clock, NotebookPen, Search, Sparkles, X } from 'lucide-react';
import type { NoteKind, NotesFilterActions, NotesFilterState } from '@/hooks/use-notes-filter';

export interface NotesClassifyTreeProps {
  subjects: Array<{ id: string; subjectId: string; subjectName: string }>;
  filterState: NotesFilterState;
  filterActions: NotesFilterActions;
  /** counts: 每個 userSubjectId 下各 kind 的數量（可選，顯示 badge） */
  counts?: Record<string, { note: number; annotation: number; scaffold: number }>;
}

const KIND_CONFIG: Array<{
  kind: NoteKind;
  label: string;
  icon: string;
  color: string;
  activeColor: string;
}> = [
  { kind: 'note', label: '自由筆記', icon: '📝', color: 'text-emerald-600', activeColor: 'bg-emerald-100 text-emerald-700 border-emerald-300' },
  { kind: 'annotation', label: 'AI 標記', icon: '✨', color: 'text-violet-600', activeColor: 'bg-violet-100 text-violet-700 border-violet-300' },
  { kind: 'scaffold', label: '鷹架深讀', icon: '🦅', color: 'text-amber-600', activeColor: 'bg-amber-100 text-amber-700 border-amber-300' },
];

export default function NotesClassifyTree({
  subjects,
  filterState,
  filterActions,
  counts,
}: NotesClassifyTreeProps) {
  const { activeUserSubjectId, kindFilter, searchQuery, recentSearches } = filterState;
  const { setActiveUserSubjectId, setKindFilter, commitSearch, setSearchQuery, resetFilters } = filterActions;

  const [inputValue, setInputValue] = useState(searchQuery);
  const [showRecent, setShowRecent] = useState(false);
  const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());
  const searchRef = useRef<HTMLInputElement>(null);
  const recentRef = useRef<HTMLDivElement>(null);

  // 同步外部 searchQuery → inputValue
  useEffect(() => {
    setInputValue(searchQuery);
  }, [searchQuery]);

  // 關閉 recent dropdown（點外部）
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (recentRef.current && !recentRef.current.contains(e.target as Node)) {
        setShowRecent(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function handleSearchKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      commitSearch(inputValue);
      setShowRecent(false);
      searchRef.current?.blur();
    } else if (e.key === 'Escape') {
      setInputValue('');
      setSearchQuery('');
      setShowRecent(false);
    }
  }

  function handleSearchChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value;
    setInputValue(v);
    // 即時 filter（不存 recent）
    setSearchQuery(v);
  }

  function toggleSubject(id: string) {
    setExpandedSubjects((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function selectSubject(id: string) {
    setActiveUserSubjectId(id);
  }

  function selectKind(kind: NoteKind) {
    setKindFilter(kindFilter === kind ? null : kind);
  }

  const isFiltered = kindFilter !== null || searchQuery.trim() !== '';

  return (
    <div className="flex flex-col h-full bg-white border-r border-slate-200">
      {/* 搜尋框 */}
      <div className="p-3 border-b border-slate-100">
        <div className="relative" ref={recentRef}>
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
            <input
              ref={searchRef}
              type="text"
              value={inputValue}
              onChange={handleSearchChange}
              onKeyDown={handleSearchKeyDown}
              onFocus={() => recentSearches.length > 0 && setShowRecent(true)}
              placeholder="搜尋筆記..."
              className="w-full pl-7 pr-7 py-1.5 text-xs border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-300 focus:border-emerald-400 bg-slate-50 transition-all"
            />
            {inputValue && (
              <button
                type="button"
                onClick={() => { setInputValue(''); setSearchQuery(''); }}
                className="absolute right-2 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* 最近搜尋 dropdown */}
          {showRecent && recentSearches.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-md z-20 overflow-hidden">
              <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-slate-100">
                <Clock className="h-3 w-3 text-slate-400" />
                <span className="text-[10px] text-slate-400 font-medium">最近搜尋</span>
              </div>
              {recentSearches.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => {
                    setInputValue(s);
                    commitSearch(s);
                    setShowRecent(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 科目樹 */}
      <div className="flex-1 overflow-y-auto py-2">
        <p className="px-3 pb-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">科目</p>
        {subjects.length === 0 && (
          <p className="px-3 py-3 text-xs text-slate-400">尚未加入科目</p>
        )}
        {subjects.map((sub) => {
          const isActive = activeUserSubjectId === sub.id;
          const isExpanded = expandedSubjects.has(sub.id);
          const subCounts = counts?.[sub.id];

          return (
            <div key={sub.id}>
              {/* Subject row */}
              <div
                className={`flex items-center gap-1.5 px-3 py-2 cursor-pointer transition-colors rounded-lg mx-1 ${
                  isActive ? 'bg-emerald-50 text-emerald-700' : 'hover:bg-slate-50 text-slate-700'
                }`}
              >
                <button
                  type="button"
                  onClick={() => toggleSubject(sub.id)}
                  className="shrink-0 p-0.5 rounded hover:bg-slate-200 transition-colors"
                  aria-label={isExpanded ? '收合' : '展開'}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-3 w-3 text-slate-400" />
                  ) : (
                    <ChevronRight className="h-3 w-3 text-slate-400" />
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => selectSubject(sub.id)}
                  className="flex-1 text-left text-xs font-medium truncate"
                >
                  {sub.subjectName}
                </button>
                {subCounts && (
                  <span className="shrink-0 text-[10px] text-slate-400">
                    {subCounts.note + subCounts.annotation + subCounts.scaffold}
                  </span>
                )}
              </div>

              {/* Type chips (展開後顯示) */}
              {isExpanded && (
                <div className="ml-6 mr-2 mb-1 space-y-0.5">
                  {KIND_CONFIG.map((cfg) => {
                    const isKindActive = isActive && kindFilter === cfg.kind;
                    const count = subCounts?.[cfg.kind] ?? null;
                    return (
                      <button
                        key={cfg.kind}
                        type="button"
                        onClick={() => {
                          selectSubject(sub.id);
                          selectKind(cfg.kind);
                        }}
                        className={`w-full flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs transition-colors border ${
                          isKindActive
                            ? cfg.activeColor + ' border-opacity-60'
                            : 'bg-transparent border-transparent text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <span>{cfg.icon}</span>
                        <span className="flex-1 text-left">{cfg.label}</span>
                        {count !== null && (
                          <span className="text-[10px] text-slate-400">{count}</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 底部：重置篩選 */}
      {isFiltered && (
        <div className="px-3 py-3 border-t border-slate-100">
          <button
            type="button"
            onClick={resetFilters}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 border border-slate-200 transition-colors"
          >
            <NotebookPen className="h-3.5 w-3.5" />
            全部筆記（重置篩選）
          </button>
        </div>
      )}
      {!isFiltered && (
        <div className="px-3 py-3 border-t border-slate-100">
          <div className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-emerald-50 border border-emerald-200">
            <BookOpen className="h-3.5 w-3.5 text-emerald-500" />
            <span className="text-xs font-medium text-emerald-700">全部筆記</span>
            <Sparkles className="h-3 w-3 text-emerald-400 ml-auto" />
          </div>
        </div>
      )}
    </div>
  );
}
