'use client';

/**
 * @file NotesTimeline.tsx
 * 右側 Unified Timeline：
 *  - 整合三源（userNote / chatAnnotation / scaffold）
 *  - Toolbar：排序下拉 / active filter chip / 重置篩選
 *  - 每筆 card：type 色塊 + 來源 badge + 內容 preview + edit/delete
 *  - Inline edit mode（自由筆記 & AI 標記 & 鷹架只可編輯不可刪）
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  BookOpen,
  Check,
  ChevronDown,
  Edit2,
  NotebookPen,
  RotateCcw,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react';
import {
  chatAnnotationService,
  knowledgeService,
  userNoteService,
  type NodeScaffoldItem,
} from '@/lib/api/services';
import type { AnnotationType, ChatAnnotation, UserNote } from '@/types/api';
import type { NoteKind, SortOrder } from '@/hooks/use-notes-filter';

// ─── Types ───────────────────────────────────────────────────────────────────

interface BaseItem {
  _id: string;
  _kind: NoteKind;
  _sortTime: number; // unix ms for sorting
  _subjectName?: string;
}

interface NoteItem extends BaseItem {
  _kind: 'note';
  data: UserNote;
}

interface AnnotationItem extends BaseItem {
  _kind: 'annotation';
  data: ChatAnnotation;
}

interface ScaffoldItem extends BaseItem {
  _kind: 'scaffold';
  data: NodeScaffoldItem & { resource_id?: string | null };
}

type TimelineItem = NoteItem | AnnotationItem | ScaffoldItem;

// ─── Props ───────────────────────────────────────────────────────────────────

export interface NotesTimelineProps {
  /** UserSubject.subjectId（後端 UUID），用於 API 查詢 */
  subjectId: string | null;
  kindFilter: NoteKind | null;
  searchQuery: string;
  sortOrder: SortOrder;
  onSortChange: (order: SortOrder) => void;
  onKindFilterChange: (kind: NoteKind | null) => void;
  onResetFilters: () => void;
  /** 回報各 kind 數量給父層（供 sidebar 顯示 badge） */
  onCountsUpdate?: (counts: { note: number; annotation: number; scaffold: number }) => void;
  isPro: boolean;
  onUpgradeClick: () => void;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const KIND_META: Record<NoteKind, { label: string; icon: string; dot: string; chip: string; border: string }> = {
  note: {
    label: '自由筆記',
    icon: '📝',
    dot: 'bg-emerald-400',
    chip: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    border: 'border-l-emerald-400',
  },
  annotation: {
    label: 'AI 標記',
    icon: '✨',
    dot: 'bg-violet-400',
    chip: 'bg-violet-50 text-violet-700 border-violet-200',
    border: 'border-l-violet-400',
  },
  scaffold: {
    label: '鷹架深讀',
    icon: '🦅',
    dot: 'bg-amber-400',
    chip: 'bg-amber-50 text-amber-700 border-amber-200',
    border: 'border-l-amber-400',
  },
};

const ANNOTATION_LABELS: Record<AnnotationType, string> = {
  note: '筆記',
  key_insight: '關鍵洞察',
  challenge: '挑戰',
  example: '範例',
  application: '應用',
};

const SORT_LABELS: Record<SortOrder, string> = {
  desc: '最新優先',
  asc: '最舊優先',
  group: '依類型分組',
};

// ─── Relative time ────────────────────────────────────────────────────────────

function relativeTime(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return '剛剛';
  if (minutes < 60) return `${minutes} 分鐘前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小時前`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} 天前`;
  return new Date(isoStr).toLocaleDateString('zh-TW');
}

// ─── Inline Edit Forms ────────────────────────────────────────────────────────

function NoteEditForm({
  note,
  onSave,
  onCancel,
}: {
  note: UserNote;
  onSave: (title: string | null, content: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(note.title ?? '');
  const [content, setContent] = useState(note.content);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    await onSave(title.trim() || null, content.trim());
    setSaving(false);
  }

  return (
    <div className="space-y-2 pt-2">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="標題（選填）"
        className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-emerald-300 bg-white"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={3}
        className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-emerald-300 resize-none bg-white"
      />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="text-xs px-3 py-1 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors">取消</button>
        <button
          type="button"
          disabled={!content.trim() || saving}
          onClick={handleSave}
          className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-lg bg-emerald-500 text-white font-semibold hover:bg-emerald-600 disabled:opacity-50 transition-colors"
        >
          <Check className="h-3 w-3" /> 儲存
        </button>
      </div>
    </div>
  );
}

function AnnotationEditForm({
  ann,
  onSave,
  onCancel,
}: {
  ann: ChatAnnotation;
  onSave: (annotation: string, type: AnnotationType) => Promise<void>;
  onCancel: () => void;
}) {
  const [text, setText] = useState(ann.user_annotation);
  const [annType, setAnnType] = useState<AnnotationType>(ann.annotation_type);
  const [saving, setSaving] = useState(false);

  const TYPES: AnnotationType[] = ['note', 'key_insight', 'challenge', 'example', 'application'];

  async function handleSave() {
    setSaving(true);
    await onSave(text, annType);
    setSaving(false);
  }

  return (
    <div className="space-y-2 pt-2">
      <div className="flex flex-wrap gap-1">
        {TYPES.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setAnnType(t)}
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border transition-colors ${
              annType === t
                ? 'bg-violet-100 text-violet-700 border-violet-300'
                : 'border-slate-200 text-slate-400 bg-white hover:bg-slate-50'
            }`}
          >
            {ANNOTATION_LABELS[t]}
          </button>
        ))}
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="評語（至少 10 字）"
        className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-violet-300 resize-none bg-white"
      />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="text-xs px-3 py-1 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors">取消</button>
        <button
          type="button"
          disabled={text.length < 10 || saving}
          onClick={handleSave}
          className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-lg bg-violet-500 text-white font-semibold hover:bg-violet-600 disabled:opacity-50 transition-colors"
        >
          <Check className="h-3 w-3" /> 儲存
        </button>
      </div>
    </div>
  );
}

function ScaffoldEditForm({
  scaffold,
  onSave,
  onCancel,
}: {
  scaffold: NodeScaffoldItem;
  onSave: (response: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [response, setResponse] = useState(scaffold.user_response ?? '');
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    await onSave(response);
    setSaving(false);
  }

  return (
    <div className="space-y-2 pt-2">
      <p className="text-xs font-semibold text-amber-700">{scaffold.content}</p>
      <textarea
        value={response}
        onChange={(e) => setResponse(e.target.value)}
        rows={3}
        className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-amber-300 resize-none bg-white"
      />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="text-xs px-3 py-1 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors">取消</button>
        <button
          type="button"
          disabled={!response.trim() || saving}
          onClick={handleSave}
          className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-lg bg-amber-500 text-white font-semibold hover:bg-amber-600 disabled:opacity-50 transition-colors"
        >
          <Check className="h-3 w-3" /> 儲存
        </button>
      </div>
    </div>
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────

function TimelineCard({
  item,
  onUpdate,
  onDelete,
}: {
  item: TimelineItem;
  onUpdate: (item: TimelineItem, payload: unknown) => Promise<void>;
  onDelete: (item: TimelineItem) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const meta = KIND_META[item._kind];

  async function handleDelete() {
    if (!window.confirm('確定要刪除此筆記？')) return;
    setDeleting(true);
    await onDelete(item);
    setDeleting(false);
  }

  return (
    <div className={`rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow bg-white overflow-hidden border-l-4 ${meta.border}`}>
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start gap-2 mb-2">
          <span className="text-base leading-none mt-0.5">{meta.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full border ${meta.chip}`}>
                {meta.label}
              </span>
              {/* annotation type badge */}
              {item._kind === 'annotation' && (
                <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded-full">
                  {ANNOTATION_LABELS[item.data.annotation_type]}
                </span>
              )}
              {/* scaffold chapter */}
              {item._kind === 'scaffold' && item.data.chapter_heading && (
                <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded-full truncate max-w-[120px]">
                  {item.data.chapter_heading}
                </span>
              )}
            </div>
          </div>
          {/* Actions */}
          <div className="flex gap-1 shrink-0">
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
              title="編輯"
            >
              <Edit2 className="h-3.5 w-3.5" />
            </button>
            {/* 鷹架不可刪 */}
            {item._kind !== 'scaffold' && (
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="p-1.5 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-500 transition-colors disabled:opacity-50"
                title="刪除"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Content preview */}
        {!editing && (
          <>
            {item._kind === 'note' && (
              <div>
                {item.data.title && (
                  <p className="text-xs font-semibold text-slate-800 mb-0.5">{item.data.title}</p>
                )}
                <p className="text-sm text-slate-700 line-clamp-3 whitespace-pre-line leading-relaxed">{item.data.content}</p>
              </div>
            )}
            {item._kind === 'annotation' && (
              <div>
                {item.data.highlighted_text && (
                  <blockquote className="text-xs text-slate-500 italic border-l-2 border-slate-300 pl-2 mb-1.5 line-clamp-2">
                    {item.data.highlighted_text}
                  </blockquote>
                )}
                <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed line-clamp-3">{item.data.user_annotation}</p>
              </div>
            )}
            {item._kind === 'scaffold' && (
              <div>
                <p className="text-xs font-semibold text-slate-600 mb-1 line-clamp-2">{item.data.content}</p>
                {item.data.user_response && (
                  <div className="rounded-lg bg-amber-50/60 border border-amber-100 px-3 py-2">
                    <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed line-clamp-3">{item.data.user_response}</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Inline edit */}
        {editing && item._kind === 'note' && (
          <NoteEditForm
            note={item.data}
            onSave={async (title, content) => {
              await onUpdate(item, { title, content });
              setEditing(false);
            }}
            onCancel={() => setEditing(false)}
          />
        )}
        {editing && item._kind === 'annotation' && (
          <AnnotationEditForm
            ann={item.data}
            onSave={async (annotation, type) => {
              await onUpdate(item, { user_annotation: annotation, annotation_type: type });
              setEditing(false);
            }}
            onCancel={() => setEditing(false)}
          />
        )}
        {editing && item._kind === 'scaffold' && (
          <ScaffoldEditForm
            scaffold={item.data}
            onSave={async (response) => {
              await onUpdate(item, { user_response: response });
              setEditing(false);
            }}
            onCancel={() => setEditing(false)}
          />
        )}

        {/* Timestamp */}
        {!editing && (
          <p className="mt-2 text-[10px] text-slate-400">
            {relativeTime(
              item._kind === 'annotation' ? item.data.created_at : item._kind === 'note' ? item.data.updated_at : (item.data.responded_at ?? '')
            )}
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function NotesTimeline({
  subjectId,
  kindFilter,
  searchQuery,
  sortOrder,
  onSortChange,
  onKindFilterChange,
  onResetFilters,
  onCountsUpdate,
  isPro,
  onUpgradeClick,
}: NotesTimelineProps) {
  const [items, setItems] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSortMenu, setShowSortMenu] = useState(false);

  // 穩定 onCountsUpdate ref，避免因外層每次 render 產新 function 而觸發 fetchData 無限 loop
  const onCountsUpdateRef = useRef(onCountsUpdate);
  useEffect(() => { onCountsUpdateRef.current = onCountsUpdate; });

  const fetchData = useCallback(async () => {
    if (!subjectId) {
      setItems([]);
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const [noteRes, annRes, scaffoldRes] = await Promise.allSettled([
        userNoteService.list({ subject_id: subjectId, limit: 100 }),
        chatAnnotationService.list({ limit: 200 }),
        knowledgeService.getSubjectScaffolds(subjectId, { user_response_only: true, limit: 100 }),
      ]);

      const merged: TimelineItem[] = [];

      if (noteRes.status === 'fulfilled') {
        noteRes.value.items.forEach((n) => {
          merged.push({
            _id: n.id,
            _kind: 'note',
            _sortTime: new Date(n.updated_at).getTime(),
            data: n,
          });
        });
      }

      if (annRes.status === 'fulfilled') {
        annRes.value.items.forEach((a) => {
          merged.push({
            _id: a.id,
            _kind: 'annotation',
            _sortTime: new Date(a.created_at).getTime(),
            data: a,
          });
        });
      }

      if (scaffoldRes.status === 'fulfilled') {
        (scaffoldRes.value.scaffolds ?? []).forEach((s) => {
          merged.push({
            _id: s.id,
            _kind: 'scaffold',
            _sortTime: s.responded_at ? new Date(s.responded_at).getTime() : 0,
            data: s,
          });
        });
      }

      setItems(merged);

      // 回報 counts（用 ref 避免觸發 loop）
      if (onCountsUpdateRef.current) {
        onCountsUpdateRef.current({
          note: noteRes.status === 'fulfilled' ? noteRes.value.items.length : 0,
          annotation: annRes.status === 'fulfilled' ? annRes.value.items.length : 0,
          scaffold: scaffoldRes.status === 'fulfilled' ? (scaffoldRes.value.scaffolds?.length ?? 0) : 0,
        });
      }
    } catch (e) {
      const err = e as { message?: string };
      setError(err.message || '載入筆記失敗');
    } finally {
      setLoading(false);
    }
  }, [subjectId]); // onCountsUpdate 透過 ref 存取，不列入 dep 以免 loop

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ─ Filter ──────────────────────────────────────────────────────────────────

  const filtered = items.filter((item) => {
    if (kindFilter && item._kind !== kindFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      if (item._kind === 'note') {
        return (
          item.data.content.toLowerCase().includes(q) ||
          (item.data.title?.toLowerCase() ?? '').includes(q)
        );
      }
      if (item._kind === 'annotation') {
        return (
          item.data.user_annotation.toLowerCase().includes(q) ||
          (item.data.highlighted_text?.toLowerCase() ?? '').includes(q)
        );
      }
      if (item._kind === 'scaffold') {
        return (
          (item.data.user_response?.toLowerCase() ?? '').includes(q) ||
          item.data.content.toLowerCase().includes(q)
        );
      }
    }
    return true;
  });

  // ─ Sort ────────────────────────────────────────────────────────────────────

  let sorted: TimelineItem[];
  if (sortOrder === 'group') {
    const groups: NoteKind[] = ['note', 'annotation', 'scaffold'];
    sorted = groups.flatMap((k) =>
      filtered.filter((i) => i._kind === k).sort((a, b) => b._sortTime - a._sortTime)
    );
  } else if (sortOrder === 'asc') {
    sorted = [...filtered].sort((a, b) => a._sortTime - b._sortTime);
  } else {
    sorted = [...filtered].sort((a, b) => b._sortTime - a._sortTime);
  }

  // ─ Update handlers ─────────────────────────────────────────────────────────

  async function handleUpdate(item: TimelineItem, payload: unknown) {
    if (item._kind === 'note') {
      const p = payload as { title: string | null; content: string };
      const updated = await userNoteService.update(item._id, p);
      setItems((prev) =>
        prev.map((i) =>
          i._id === item._id
            ? ({ ...i, _sortTime: new Date(updated.updated_at).getTime(), data: updated } as NoteItem)
            : i
        )
      );
    } else if (item._kind === 'annotation') {
      const p = payload as { user_annotation: string; annotation_type: AnnotationType };
      const updated = await chatAnnotationService.update(item._id, p);
      setItems((prev) =>
        prev.map((i) => (i._id === item._id ? ({ ...i, data: updated } as AnnotationItem) : i))
      );
    } else if (item._kind === 'scaffold') {
      const p = payload as { user_response: string };
      const updated = await knowledgeService.updateScaffold(item._id, p);
      setItems((prev) =>
        prev.map((i) => (i._id === item._id ? ({ ...i, data: updated } as ScaffoldItem) : i))
      );
    }
  }

  async function handleDelete(item: TimelineItem) {
    if (item._kind === 'note') {
      await userNoteService.remove(item._id);
    } else if (item._kind === 'annotation') {
      await chatAnnotationService.remove(item._id);
    }
    setItems((prev) => prev.filter((i) => i._id !== item._id));
  }

  // ─ Paywall ─────────────────────────────────────────────────────────────────

  if (!isPro) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-8 text-center max-w-sm mx-auto">
          <Sparkles className="h-8 w-8 text-amber-500 mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-800 mb-1">筆記本為 PRO 專屬</p>
          <p className="text-xs text-slate-500 mb-4">升級 PRO 以解鎖三合一筆記中心</p>
          <button
            onClick={onUpgradeClick}
            className="inline-flex items-center gap-1.5 bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-emerald-600 transition-colors"
          >
            升級 PRO
          </button>
        </div>
      </div>
    );
  }

  // ─ Render ──────────────────────────────────────────────────────────────────

  const isFiltered = kindFilter !== null || searchQuery.trim() !== '';

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-200 bg-white flex-wrap gap-y-2">
        {/* Sort dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowSortMenu((v) => !v)}
            className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-medium transition-colors"
          >
            <span>{SORT_LABELS[sortOrder]}</span>
            <ChevronDown className="h-3 w-3 text-slate-400" />
          </button>
          {showSortMenu && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-20 overflow-hidden min-w-[140px]">
              {(Object.keys(SORT_LABELS) as SortOrder[]).map((order) => (
                <button
                  key={order}
                  type="button"
                  onClick={() => { onSortChange(order); setShowSortMenu(false); }}
                  className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                    sortOrder === order
                      ? 'bg-emerald-50 text-emerald-700 font-semibold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {SORT_LABELS[order]}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Active filter chips */}
        {kindFilter && (
          <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border ${KIND_META[kindFilter].chip}`}>
            {KIND_META[kindFilter].icon} {KIND_META[kindFilter].label}
            <button
              type="button"
              onClick={() => onKindFilterChange(null)}
              className="ml-0.5 hover:opacity-70"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}
        {searchQuery.trim() && (
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border bg-slate-50 text-slate-700 border-slate-200">
            「{searchQuery}」
            <button
              type="button"
              onClick={() => onResetFilters()}
              className="ml-0.5 hover:opacity-70"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        )}

        {/* Reset button */}
        {isFiltered && (
          <button
            type="button"
            onClick={onResetFilters}
            className="ml-auto inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors border border-slate-200"
          >
            <RotateCcw className="h-3 w-3" />
            重置
          </button>
        )}

        {/* Item count */}
        <span className="text-xs text-slate-400 ml-auto">
          {sorted.length} 筆
        </span>
      </div>

      {/* Timeline list */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        {!loading && error && (
          <div className="flex items-center justify-center py-12">
            <p className="text-sm text-rose-500">{error}</p>
          </div>
        )}
        {!loading && !error && sorted.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
            <NotebookPen className="h-10 w-10 text-slate-300" />
            <p className="text-sm text-slate-500 font-medium">
              {isFiltered ? '找不到符合條件的筆記' : '尚無筆記'}
            </p>
            {!isFiltered && (
              <p className="text-xs text-slate-400">
                前往{' '}
                <a href="/knowledge" className="text-emerald-600 hover:underline">
                  知識地圖
                </a>{' '}
                開始學習並寫筆記
              </p>
            )}
          </div>
        )}
        {!loading && !error && sorted.length > 0 && (
          <div className="space-y-3">
            {/* Group headers for 'group' sort */}
            {sortOrder === 'group' ? (
              (['note', 'annotation', 'scaffold'] as NoteKind[]).map((kind) => {
                const group = sorted.filter((i) => i._kind === kind);
                if (group.length === 0) return null;
                return (
                  <div key={kind}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-base">{KIND_META[kind].icon}</span>
                      <span className="text-xs font-semibold text-slate-600">{KIND_META[kind].label}</span>
                      <div className="flex-1 border-t border-slate-200" />
                      <span className="text-[10px] text-slate-400">{group.length} 筆</span>
                    </div>
                    <div className="space-y-3">
                      {group.map((item) => (
                        <TimelineCard
                          key={item._id}
                          item={item}
                          onUpdate={handleUpdate}
                          onDelete={handleDelete}
                        />
                      ))}
                    </div>
                  </div>
                );
              })
            ) : (
              sorted.map((item) => (
                <TimelineCard
                  key={item._id}
                  item={item}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
