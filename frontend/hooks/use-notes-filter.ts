'use client';

/**
 * @file use-notes-filter.ts
 * 管理 /notes 頁面的篩選狀態：subjectId / kindFilter / searchQuery / sortOrder
 * 同時處理「最近搜尋」localStorage (最多 3 條)。
 */

import { useCallback, useEffect, useState } from 'react';

export type NoteKind = 'note' | 'annotation' | 'scaffold';
export type SortOrder = 'desc' | 'asc' | 'group';

const RECENT_SEARCH_KEY = 'certimate_notes_recent_searches';
const MAX_RECENT = 3;

function loadRecentSearches(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(RECENT_SEARCH_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function saveRecentSearches(list: string[]) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(RECENT_SEARCH_KEY, JSON.stringify(list));
  } catch {
    // ignore
  }
}

export interface NotesFilterState {
  /** 目前選定的 UserSubject.id（非 subjectId UUID） */
  activeUserSubjectId: string;
  /** 類型篩選，null = 全部 */
  kindFilter: NoteKind | null;
  /** 搜尋關鍵字 */
  searchQuery: string;
  /** 排序方式 */
  sortOrder: SortOrder;
  /** 最近搜尋 (localStorage) */
  recentSearches: string[];
}

export interface NotesFilterActions {
  setActiveUserSubjectId: (id: string) => void;
  setKindFilter: (kind: NoteKind | null) => void;
  setSearchQuery: (q: string) => void;
  setSortOrder: (order: SortOrder) => void;
  /** 提交搜尋關鍵字：執行 setSearchQuery 並存入最近搜尋 */
  commitSearch: (q: string) => void;
  resetFilters: () => void;
}

export function useNotesFilter(
  subjects: Array<{ id: string; subjectId: string; subjectName: string }>,
): NotesFilterState & NotesFilterActions {
  const [activeUserSubjectId, setActiveUserSubjectIdRaw] = useState('');
  const [kindFilter, setKindFilter] = useState<NoteKind | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // 初始化：選第一個科目 + 讀 localStorage
  useEffect(() => {
    setRecentSearches(loadRecentSearches());
  }, []);

  useEffect(() => {
    if (subjects.length > 0 && !activeUserSubjectId) {
      setActiveUserSubjectIdRaw(subjects[0].id);
    }
  }, [subjects, activeUserSubjectId]);

  const setActiveUserSubjectId = useCallback((id: string) => {
    setActiveUserSubjectIdRaw(id);
    // 切換科目時重置 kind filter 但保留 search
    setKindFilter(null);
  }, []);

  const commitSearch = useCallback((q: string) => {
    setSearchQuery(q);
    if (!q.trim()) return;
    setRecentSearches((prev) => {
      const next = [q, ...prev.filter((s) => s !== q)].slice(0, MAX_RECENT);
      saveRecentSearches(next);
      return next;
    });
  }, []);

  const resetFilters = useCallback(() => {
    setKindFilter(null);
    setSearchQuery('');
    setSortOrder('desc');
  }, []);

  return {
    activeUserSubjectId,
    kindFilter,
    searchQuery,
    sortOrder,
    recentSearches,
    setActiveUserSubjectId,
    setKindFilter,
    setSearchQuery,
    setSortOrder,
    commitSearch,
    resetFilters,
  };
}
