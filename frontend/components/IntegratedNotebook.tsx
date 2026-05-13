/**
 * @file 「我的筆記」三區整合視圖。
 *
 * 區 1 — 自由筆記（userNoteService CRUD）
 * 區 2 — AI 對話標記（chatAnnotationService list / update / remove）
 * 區 3 — 鷹架深讀（knowledgeService getNode/ResourceScaffolds + updateScaffold）
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Edit2,
  MessageSquare,
  NotebookPen,
  Plus,
  Sparkles,
  Trash2,
  X,
  Check,
} from 'lucide-react';
import {
  chatAnnotationService,
  knowledgeService,
  userNoteService,
  type NodeScaffoldItem,
} from '@/lib/api/services';
import type {
  AnnotationType,
  ChatAnnotation,
  UserNote,
} from '@/types/api';

// ─────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────

export interface IntegratedNotebookProps {
  /** 當前節點 ID（為 null 時三區各自空態） */
  nodeId: string | null;
  /** fallback 資源 ID，供鷹架查詢退回資源層級 */
  fallbackResourceId?: string | null;
  /** 節點顯示名稱 */
  nodeLabel: string | null;
  /** 所屬科目 UUID（userNoteService create 必填） */
  subjectId: string | null;
  /** 是否為 PRO 訂戶（paywall 判斷） */
  isPro: boolean;
  /** 點擊「升級 PRO」按鈕的回呼 */
  onUpgradeClick?: () => void;
}

// ─────────────────────────────────────────────
// Utility
// ─────────────────────────────────────────────

const ANNOTATION_LABELS: Record<AnnotationType, string> = {
  note: '筆記',
  key_insight: '關鍵洞察',
  challenge: '挑戰',
  example: '範例',
  application: '應用',
};

const ANNOTATION_COLORS: Record<AnnotationType, string> = {
  note: 'bg-slate-100 text-slate-600',
  key_insight: 'bg-amber-100 text-amber-700',
  challenge: 'bg-rose-100 text-rose-700',
  example: 'bg-blue-100 text-blue-700',
  application: 'bg-emerald-100 text-emerald-700',
};

function SectionHeader({
  icon,
  title,
  count,
  open,
  onToggle,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
  open: boolean;
  onToggle: () => void;
  action?: React.ReactNode;
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onToggle}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggle(); }}
      className="w-full flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors border-b border-slate-200 text-left cursor-pointer select-none"
    >
      {open ? (
        <ChevronDown className="h-3.5 w-3.5 text-slate-400 shrink-0" />
      ) : (
        <ChevronRight className="h-3.5 w-3.5 text-slate-400 shrink-0" />
      )}
      <span className="text-slate-500 shrink-0">{icon}</span>
      <span className="text-xs font-semibold text-slate-700 flex-1">
        {title}{' '}
        <span className="font-normal text-slate-400">({count})</span>
      </span>
      {action && (
        <span
          onClick={(e) => e.stopPropagation()}
          className="shrink-0"
        >
          {action}
        </span>
      )}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="p-3 space-y-2">
      {[1, 2].map((i) => (
        <div key={i} className="rounded-lg border border-slate-100 p-3 animate-pulse bg-slate-50 h-16" />
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="px-4 py-5 text-center text-[11px] text-slate-400">{message}</div>
  );
}

function ToastError({ msg, onClose }: { msg: string; onClose: () => void }) {
  return (
    <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 text-rose-700 text-[11px] px-3 py-2 rounded-lg mx-3 mb-2">
      <span className="flex-1">{msg}</span>
      <button onClick={onClose} className="shrink-0 hover:text-rose-900">
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────
// Section 1 — 自由筆記
// ─────────────────────────────────────────────

function FreeNoteSection({
  nodeId,
  subjectId,
}: {
  nodeId: string | null;
  subjectId: string | null;
}) {
  const [open, setOpen] = useState(true);
  const [notes, setNotes] = useState<UserNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Creating
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [saving, setSaving] = useState(false);

  // Editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  const fetchNotes = useCallback(async () => {
    if (!subjectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await userNoteService.list({
        subject_id: subjectId,
        node_id: nodeId || undefined,
        limit: 50,
      });
      // Sort by updated_at desc
      const sorted = [...res.items].sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
      setNotes(sorted);
    } catch (e) {
      const err = e as { message?: string };
      setError(err.message || '載入自由筆記失敗');
    } finally {
      setLoading(false);
    }
  }, [subjectId, nodeId]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  async function handleCreate() {
    if (!subjectId || !newContent.trim()) return;
    setSaving(true);
    try {
      const note = await userNoteService.create({
        subject_id: subjectId,
        node_id: nodeId || null,
        title: newTitle.trim() || null,
        content: newContent.trim(),
      });
      setNotes((prev) => [note, ...prev]);
      setCreating(false);
      setNewTitle('');
      setNewContent('');
    } catch (e) {
      const err = e as { message?: string };
      setError(err.message || '新增筆記失敗');
    } finally {
      setSaving(false);
    }
  }

  function startEdit(note: UserNote) {
    setEditingId(note.id);
    setEditTitle(note.title || '');
    setEditContent(note.content);
  }

  async function handleUpdate(id: string) {
    setEditSaving(true);
    const original = notes.find((n) => n.id === id);
    // Optimistic update
    setNotes((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, title: editTitle.trim() || null, content: editContent.trim(), updated_at: new Date().toISOString() } : n
      )
    );
    setEditingId(null);
    try {
      const updated = await userNoteService.update(id, {
        title: editTitle.trim() || null,
        content: editContent.trim(),
      });
      setNotes((prev) => prev.map((n) => (n.id === id ? updated : n)));
    } catch (e) {
      // Rollback
      if (original) {
        setNotes((prev) => prev.map((n) => (n.id === id ? original : n)));
      }
      const err = e as { message?: string };
      setError(err.message || '儲存筆記失敗');
    } finally {
      setEditSaving(false);
    }
  }

  async function handleDelete(id: string) {
    const original = notes.find((n) => n.id === id);
    // Optimistic remove
    setNotes((prev) => prev.filter((n) => n.id !== id));
    try {
      await userNoteService.remove(id);
    } catch (e) {
      if (original) setNotes((prev) => [original, ...prev]);
      const err = e as { message?: string };
      setError(err.message || '刪除筆記失敗');
    }
  }

  return (
    <div className="border-b border-slate-200">
      <SectionHeader
        icon={<NotebookPen className="h-3.5 w-3.5" />}
        title="自由筆記"
        count={notes.length}
        open={open}
        onToggle={() => setOpen((o) => !o)}
        action={
          subjectId && (
            <button
              type="button"
              onClick={() => { setOpen(true); setCreating(true); }}
              className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 hover:text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded-full transition-colors"
            >
              <Plus className="h-3 w-3" /> 新增筆記
            </button>
          )
        }
      />
      {open && (
        <div>
          {error && <ToastError msg={error} onClose={() => setError(null)} />}
          {loading ? (
            <Skeleton />
          ) : (
            <ul className="p-3 space-y-2">
              {/* 新增卡 */}
              {creating && (
                <li className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 space-y-2">
                  <input
                    type="text"
                    placeholder="標題（選填）"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-emerald-300 bg-white"
                  />
                  <textarea
                    placeholder="筆記內容（必填）"
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    rows={3}
                    className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-emerald-300 resize-none bg-white"
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      type="button"
                      onClick={() => { setCreating(false); setNewTitle(''); setNewContent(''); }}
                      className="text-[10px] px-2 py-1 rounded text-slate-500 hover:bg-slate-100"
                    >
                      取消
                    </button>
                    <button
                      type="button"
                      disabled={!newContent.trim() || saving}
                      onClick={handleCreate}
                      className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-emerald-500 text-white font-semibold hover:bg-emerald-600 disabled:opacity-50"
                    >
                      <Check className="h-3 w-3" /> 儲存
                    </button>
                  </div>
                </li>
              )}

              {notes.length === 0 && !creating && (
                <EmptyState message="尚無筆記，點「+ 新增筆記」開始寫" />
              )}

              {notes.map((note) =>
                editingId === note.id ? (
                  <li key={note.id} className="rounded-lg border border-blue-200 bg-blue-50/50 p-3 space-y-2">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="標題（選填）"
                      className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-300 bg-white"
                    />
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      rows={3}
                      className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-300 resize-none bg-white"
                    />
                    <div className="flex gap-2 justify-end">
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="text-[10px] px-2 py-1 rounded text-slate-500 hover:bg-slate-100"
                      >
                        取消
                      </button>
                      <button
                        type="button"
                        disabled={!editContent.trim() || editSaving}
                        onClick={() => handleUpdate(note.id)}
                        className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-blue-500 text-white font-semibold hover:bg-blue-600 disabled:opacity-50"
                      >
                        <Check className="h-3 w-3" /> 儲存
                      </button>
                    </div>
                  </li>
                ) : (
                  <li key={note.id} className="rounded-lg border border-slate-200 bg-white p-3 group">
                    {note.title && (
                      <p className="text-[10px] font-semibold text-slate-700 mb-0.5">{note.title}</p>
                    )}
                    <p className="text-[11px] text-slate-600 line-clamp-3 whitespace-pre-line">{note.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-[10px] text-slate-400">
                        {new Date(note.updated_at).toLocaleDateString('zh-TW')}
                      </span>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          type="button"
                          onClick={() => startEdit(note)}
                          className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                          title="編輯"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(note.id)}
                          className="p-1 rounded hover:bg-rose-50 text-slate-400 hover:text-rose-500"
                          title="刪除"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </li>
                )
              )}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Section 2 — AI 對話標記
// ─────────────────────────────────────────────

function ChatAnnotationSection({ nodeId }: { nodeId: string | null }) {
  const [open, setOpen] = useState(true);
  const [annotations, setAnnotations] = useState<ChatAnnotation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editAnnotation, setEditAnnotation] = useState('');
  const [editType, setEditType] = useState<AnnotationType>('note');
  const [editSaving, setEditSaving] = useState(false);

  const fetchAnnotations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await chatAnnotationService.list({ limit: 50 });
      setAnnotations(res.items);
    } catch (e) {
      const err = e as { message?: string };
      setError(err.message || '載入 AI 對話標記失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnnotations();
  }, [fetchAnnotations]);

  function startEdit(ann: ChatAnnotation) {
    setEditingId(ann.id);
    setEditAnnotation(ann.user_annotation);
    setEditType(ann.annotation_type);
  }

  async function handleUpdate(id: string) {
    setEditSaving(true);
    const original = annotations.find((a) => a.id === id);
    // Optimistic update
    setAnnotations((prev) =>
      prev.map((a) =>
        a.id === id ? { ...a, user_annotation: editAnnotation, annotation_type: editType } : a
      )
    );
    setEditingId(null);
    try {
      const updated = await chatAnnotationService.update(id, {
        user_annotation: editAnnotation,
        annotation_type: editType,
      });
      setAnnotations((prev) => prev.map((a) => (a.id === id ? updated : a)));
    } catch (e) {
      if (original) {
        setAnnotations((prev) => prev.map((a) => (a.id === id ? original : a)));
      }
      const err = e as { message?: string };
      setError(err.message || '儲存標記失敗');
    } finally {
      setEditSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('確定要刪除此標記？')) return;
    const original = annotations.find((a) => a.id === id);
    setAnnotations((prev) => prev.filter((a) => a.id !== id));
    try {
      await chatAnnotationService.remove(id);
    } catch (e) {
      if (original) setAnnotations((prev) => [original, ...prev]);
      const err = e as { message?: string };
      setError(err.message || '刪除標記失敗');
    }
  }

  const TYPES: AnnotationType[] = ['note', 'key_insight', 'challenge', 'example', 'application'];

  return (
    <div className="border-b border-slate-200">
      <SectionHeader
        icon={<MessageSquare className="h-3.5 w-3.5" />}
        title="AI 對話標記"
        count={annotations.length}
        open={open}
        onToggle={() => setOpen((o) => !o)}
      />
      {open && (
        <div>
          {error && <ToastError msg={error} onClose={() => setError(null)} />}
          {loading ? (
            <Skeleton />
          ) : annotations.length === 0 ? (
            <EmptyState message="尚無標記，在 AI 問答頁選取文字即可新增" />
          ) : (
            <ul className="p-3 space-y-2">
              {annotations.map((ann) =>
                editingId === ann.id ? (
                  <li key={ann.id} className="rounded-lg border border-blue-200 bg-blue-50/50 p-3 space-y-2">
                    {/* Type picker */}
                    <div className="flex flex-wrap gap-1">
                      {TYPES.map((t) => (
                        <button
                          key={t}
                          type="button"
                          onClick={() => setEditType(t)}
                          className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full border transition-colors ${
                            editType === t
                              ? ANNOTATION_COLORS[t] + ' border-current'
                              : 'border-slate-200 text-slate-400 bg-white'
                          }`}
                        >
                          {ANNOTATION_LABELS[t]}
                        </button>
                      ))}
                    </div>
                    <textarea
                      value={editAnnotation}
                      onChange={(e) => setEditAnnotation(e.target.value)}
                      rows={3}
                      placeholder="評語（至少 10 字）"
                      className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-300 resize-none bg-white"
                    />
                    <div className="flex gap-2 justify-end">
                      <button type="button" onClick={() => setEditingId(null)} className="text-[10px] px-2 py-1 rounded text-slate-500 hover:bg-slate-100">取消</button>
                      <button
                        type="button"
                        disabled={editAnnotation.length < 10 || editSaving}
                        onClick={() => handleUpdate(ann.id)}
                        className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-blue-500 text-white font-semibold hover:bg-blue-600 disabled:opacity-50"
                      >
                        <Check className="h-3 w-3" /> 儲存
                      </button>
                    </div>
                  </li>
                ) : (
                  <li key={ann.id} className="rounded-lg border border-slate-200 bg-white p-3 group">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${ANNOTATION_COLORS[ann.annotation_type]}`}>
                        {ANNOTATION_LABELS[ann.annotation_type]}
                      </span>
                    </div>
                    {ann.highlighted_text && (
                      <blockquote className="text-[10px] text-slate-500 italic border-l-2 border-slate-300 pl-2 mb-1.5 line-clamp-2">
                        {ann.highlighted_text}
                      </blockquote>
                    )}
                    <p className="text-[11px] text-slate-700 whitespace-pre-line">{ann.user_annotation}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-[10px] text-slate-400">
                        {new Date(ann.created_at).toLocaleDateString('zh-TW')}
                      </span>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button type="button" onClick={() => startEdit(ann)} className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600" title="編輯">
                          <Edit2 className="h-3 w-3" />
                        </button>
                        <button type="button" onClick={() => handleDelete(ann.id)} className="p-1 rounded hover:bg-rose-50 text-slate-400 hover:text-rose-500" title="刪除">
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </li>
                )
              )}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Section 3 — 鷹架深讀
// ─────────────────────────────────────────────

function ScaffoldSection({
  nodeId,
  fallbackResourceId,
}: {
  nodeId: string | null;
  fallbackResourceId?: string | null;
}) {
  const [open, setOpen] = useState(true);
  const [scaffolds, setScaffolds] = useState<NodeScaffoldItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editResponse, setEditResponse] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  useEffect(() => {
    if (!nodeId && !fallbackResourceId) {
      setScaffolds([]);
      return;
    }
    setLoading(true);
    setError(null);

    const fetchPromise = nodeId
      ? knowledgeService.getNodeScaffolds(nodeId).then((res) => {
          const withResp = (res.scaffolds || []).filter((s) => s.user_response);
          if (withResp.length === 0 && fallbackResourceId) {
            return knowledgeService.getResourceScaffolds(fallbackResourceId);
          }
          return res;
        })
      : knowledgeService.getResourceScaffolds(fallbackResourceId!);

    fetchPromise
      .then((res) => {
        const withResponses = (res.scaffolds || []).filter((s) => s.user_response);
        setScaffolds(withResponses);
      })
      .catch((e) => {
        const err = e as { message?: string };
        setError(err.message || '載入鷹架深讀失敗');
      })
      .finally(() => setLoading(false));
  }, [nodeId, fallbackResourceId ?? null]);

  function startEdit(scaffold: NodeScaffoldItem) {
    setEditingId(scaffold.id);
    setEditResponse(scaffold.user_response || '');
  }

  async function handleUpdate(id: string) {
    setEditSaving(true);
    const original = scaffolds.find((s) => s.id === id);
    // Optimistic update
    setScaffolds((prev) =>
      prev.map((s) => (s.id === id ? { ...s, user_response: editResponse } : s))
    );
    setEditingId(null);
    try {
      const updated = await knowledgeService.updateScaffold(id, { user_response: editResponse });
      setScaffolds((prev) => prev.map((s) => (s.id === id ? updated : s)));
    } catch (e) {
      if (original) {
        setScaffolds((prev) => prev.map((s) => (s.id === id ? original : s)));
      }
      const err = e as { message?: string };
      setError(err.message || '儲存鷹架回應失敗');
    } finally {
      setEditSaving(false);
    }
  }

  return (
    <div>
      <SectionHeader
        icon={<BookOpen className="h-3.5 w-3.5" />}
        title="鷹架深讀"
        count={scaffolds.length}
        open={open}
        onToggle={() => setOpen((o) => !o)}
      />
      {open && (
        <div>
          {error && <ToastError msg={error} onClose={() => setError(null)} />}
          {loading ? (
            <Skeleton />
          ) : scaffolds.length === 0 ? (
            <EmptyState message="尚無深讀筆記，至「教材」深讀模式回答提問後自動建立" />
          ) : (
            <ul className="p-3 space-y-2">
              {scaffolds.map((s) =>
                editingId === s.id ? (
                  <li key={s.id} className="rounded-lg border border-blue-200 bg-blue-50/50 p-3 space-y-2">
                    {s.chapter_heading && (
                      <p className="text-[10px] font-semibold text-emerald-600">{s.chapter_heading}</p>
                    )}
                    <p className="text-[11px] font-semibold text-slate-700">{s.content}</p>
                    <textarea
                      value={editResponse}
                      onChange={(e) => setEditResponse(e.target.value)}
                      rows={3}
                      className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-300 resize-none bg-white"
                    />
                    <div className="flex gap-2 justify-end">
                      <button type="button" onClick={() => setEditingId(null)} className="text-[10px] px-2 py-1 rounded text-slate-500 hover:bg-slate-100">取消</button>
                      <button
                        type="button"
                        disabled={!editResponse.trim() || editSaving}
                        onClick={() => handleUpdate(s.id)}
                        className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-blue-500 text-white font-semibold hover:bg-blue-600 disabled:opacity-50"
                      >
                        <Check className="h-3 w-3" /> 儲存
                      </button>
                    </div>
                  </li>
                ) : (
                  <li key={s.id} className="rounded-lg border border-slate-200 bg-white p-3 group">
                    {s.chapter_heading && (
                      <div className="text-[10px] font-semibold text-emerald-600 mb-0.5">{s.chapter_heading}</div>
                    )}
                    <p className="text-[11px] font-semibold text-slate-700 mb-1">{s.content}</p>
                    <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1.5">
                      <p className="text-[11px] text-slate-700 whitespace-pre-line leading-relaxed">{s.user_response}</p>
                    </div>
                    {s.responded_at && (
                      <div className="mt-1.5 text-[10px] text-slate-400">
                        {new Date(s.responded_at).toLocaleString('zh-TW')}
                      </div>
                    )}
                    <div className="flex justify-end mt-1">
                      <button
                        type="button"
                        onClick={() => startEdit(s)}
                        className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="編輯"
                      >
                        <Edit2 className="h-3 w-3" />
                      </button>
                    </div>
                  </li>
                )
              )}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Main Export
// ─────────────────────────────────────────────

export default function IntegratedNotebook({
  nodeId,
  fallbackResourceId,
  nodeLabel,
  subjectId,
  isPro,
  onUpgradeClick,
}: IntegratedNotebookProps) {
  if (!nodeId && !fallbackResourceId && !subjectId) {
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        <NotebookPen className="h-6 w-6 mx-auto mb-2 text-slate-300" />
        點擊節點以查看筆記
      </div>
    );
  }

  if (!isPro) {
    return (
      <div className="p-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-center">
          <Sparkles className="h-6 w-6 text-amber-500 mx-auto mb-2" />
          <p className="text-xs text-slate-700 font-semibold mb-1">筆記本為 PRO 專屬</p>
          <button
            onClick={onUpgradeClick}
            className="inline-flex items-center gap-1 bg-emerald-500 text-white px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-600"
          >
            升級 PRO
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <FreeNoteSection nodeId={nodeId} subjectId={subjectId} />
      <ChatAnnotationSection nodeId={nodeId} />
      <ScaffoldSection nodeId={nodeId} fallbackResourceId={fallbackResourceId} />
    </div>
  );
}
