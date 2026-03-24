'use client';

import { useState, useEffect, useMemo } from 'react';
import { Search, Star } from 'lucide-react';
import { addMonths, format } from 'date-fns';
import type { SubjectCatalogItem, SubjectCategory } from '@/types';
import { onboardingService } from '@/lib/api/services';
import SelectedSubjectCard, { type SelectedSubject } from './SelectedSubjectCard';

const categories: { value: SubjectCategory | 'ALL'; label: string }[] = [
  { value: 'ALL', label: '全部' },
  { value: 'IT', label: 'IT' },
  { value: '金融', label: '金融' },
  { value: '語言', label: '語言' },
  { value: '醫療', label: '醫療' },
  { value: '公務員', label: '公務員' },
  { value: '其他', label: '其他' },
];

interface SubjectPickerProps {
  mode: 'onboarding' | 'add';
  initialSelected?: SelectedSubject[];
  excludeSubjectIds?: string[];
  onConfirm: (subjects: SelectedSubject[]) => void;
  onCancel?: () => void;
}

export default function SubjectPicker({
  mode,
  initialSelected = [],
  excludeSubjectIds = [],
  onConfirm,
  onCancel,
}: SubjectPickerProps) {
  const [catalog, setCatalog] = useState<SubjectCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<SubjectCategory | 'ALL'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selected, setSelected] = useState<SelectedSubject[]>(initialSelected);

  useEffect(() => {
    onboardingService.getSubjectCatalog().then(res => {
      setCatalog(res.subjects);
      setLoading(false);
    });
  }, []);

  const defaultExamDate = format(addMonths(new Date(), 3), 'yyyy-MM-dd');

  const filteredSubjects = useMemo(() => {
    return catalog.filter(s => {
      if (excludeSubjectIds.includes(s.id)) return false;
      if (activeCategory !== 'ALL' && s.category !== activeCategory) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [catalog, activeCategory, searchQuery, excludeSubjectIds]);

  // In onboarding mode, sync selected subjects back to parent on every change
  useEffect(() => {
    if (mode === 'onboarding') {
      onConfirm(selected);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, mode]);

  const isSelected = (subjectId: string) => selected.some(s => s.subjectId === subjectId);

  const toggleSubject = (item: SubjectCatalogItem) => {
    if (isSelected(item.id)) {
      setSelected(prev => prev.filter(s => s.subjectId !== item.id));
    } else {
      setSelected(prev => [
        ...prev,
        {
          subjectId: item.id,
          subjectName: item.name,
          examDate: defaultExamDate,
          selfAssessment: 'beginner' as const,
        },
      ]);
    }
  };

  const updateSelected = (index: number, updated: SelectedSubject) => {
    setSelected(prev => prev.map((s, i) => (i === index ? updated : s)));
  };

  const removeSelected = (index: number) => {
    setSelected(prev => prev.filter((_, i) => i !== index));
  };

  const handleConfirm = () => {
    onConfirm(selected);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className={mode === 'onboarding' ? '' : 'max-h-[80vh] overflow-y-auto'}>
      {/* Category tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide">
        {categories.map(cat => (
          <button
            key={cat.value}
            onClick={() => setActiveCategory(cat.value)}
            className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeCategory === cat.value
                ? 'bg-emerald-500 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="搜尋科目名稱（中英文皆可）..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
      </div>

      <div className={mode === 'onboarding' ? 'grid lg:grid-cols-2 gap-6' : ''}>
        {/* Subject cards grid */}
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {filteredSubjects.map(subject => {
              const active = isSelected(subject.id);
              return (
                <button
                  key={subject.id}
                  onClick={() => toggleSubject(subject)}
                  className={`text-left p-3 rounded-xl border-2 transition-all ${
                    active
                      ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                      : 'border-slate-200 hover:border-emerald-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className="font-bold text-sm text-slate-900">{subject.name}</span>
                    {subject.isPopular && (
                      <Star className="h-3.5 w-3.5 text-amber-400 fill-amber-400 shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{subject.description}</p>
                  <span className="inline-block text-[10px] font-medium mt-1.5 px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                    {subject.category}
                  </span>
                </button>
              );
            })}
          </div>
          {filteredSubjects.length === 0 && (
            <p className="text-center text-slate-400 py-8">找不到符合的科目</p>
          )}
        </div>

        {/* Selected subjects panel */}
        {mode === 'onboarding' ? (
          <div>
            <h3 className="text-sm font-bold text-slate-700 mb-3">
              已選科目 ({selected.length})
            </h3>
            {selected.length === 0 ? (
              <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center">
                <p className="text-sm text-slate-400">點擊左側卡片選擇備考科目</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {selected.map((subj, i) => (
                  <SelectedSubjectCard
                    key={subj.subjectId}
                    subject={subj}
                    onUpdate={updated => updateSelected(i, updated)}
                    onRemove={() => removeSelected(i)}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {selected.length > 0 && (
              <div className="mt-4 space-y-3">
                <h3 className="text-sm font-bold text-slate-700">
                  已選科目 ({selected.length})
                </h3>
                {selected.map((subj, i) => (
                  <SelectedSubjectCard
                    key={subj.subjectId}
                    subject={subj}
                    onUpdate={updated => updateSelected(i, updated)}
                    onRemove={() => removeSelected(i)}
                  />
                ))}
              </div>
            )}
            <div className="flex gap-3 mt-4 pt-4 border-t border-slate-200">
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
              )}
              <button
                onClick={handleConfirm}
                disabled={selected.length === 0}
                className="flex-1 py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-bold hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                確認新增
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
