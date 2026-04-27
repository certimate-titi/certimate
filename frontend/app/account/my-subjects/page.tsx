/**
 * @file 路由 `/account/my-subjects` — 我的自訂科目頁。
 *
 * 列出使用者建立的自訂科目並提供刪除功能；未登入時不發 API 請求。
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Trash2, BookOpen } from 'lucide-react';
import { subjectService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

interface CustomSubject {
  id: string;
  name: string;
  description?: string;
  created_at?: string;
}

/**
 * 我的自訂科目頁。
 *
 * 透過 `subjectService.getMyCustomSubjects` 載入清單，支援單筆刪除。
 */
export default function MySubjectsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [subjects, setSubjects] = useState<CustomSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || !isAuthenticated) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await subjectService.getMyCustomSubjects();
        if (!cancelled) setSubjects(res.subjects || []);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : '無法載入自建考科');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authLoading, isAuthenticated]);

  const handleDelete = async (id: string) => {
    if (!confirm('確定要刪除此自建考科？相關學習歷程會被封存。')) return;
    setDeletingId(id);
    try {
      await subjectService.deleteSubject(id);
      setSubjects((prev) => prev.filter((s) => s.id !== id));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : '刪除失敗');
    } finally {
      setDeletingId(null);
    }
  };

  if (authLoading || loading) {
    return <div className="p-8 text-slate-500">載入中…</div>;
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link
        href="/account"
        className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-4"
      >
        <ArrowLeft className="w-4 h-4" /> 返回帳號設定
      </Link>

      <h1 className="text-2xl font-bold text-slate-900 mb-2">我的自建考科</h1>
      <p className="text-sm text-slate-600 mb-6">
        這裡列出你自行建立的考科，僅你自己可見，不會出現在其他用戶的選單中。
      </p>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
      )}

      {subjects.length === 0 ? (
        <div className="border-2 border-dashed border-slate-200 rounded-2xl p-10 text-center">
          <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-500">尚未建立自訂考科</p>
          <p className="text-xs text-slate-400 mt-1">
            於儀表板「+ 新增考科」Modal 底部可建立自訂考科
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {subjects.map((s) => (
            <div
              key={s.id}
              className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 hover:border-slate-300 transition"
            >
              <div className="min-w-0 flex-1">
                <div className="font-medium text-slate-900 truncate">{s.name}</div>
                {s.description && (
                  <div className="text-xs text-slate-500 mt-0.5 truncate">{s.description}</div>
                )}
                {s.created_at && (
                  <div className="text-xs text-slate-400 mt-1">
                    建立於 {new Date(s.created_at).toLocaleDateString('zh-TW')}
                  </div>
                )}
              </div>
              <button
                onClick={() => handleDelete(s.id)}
                disabled={deletingId === s.id}
                className="ml-3 p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 disabled:opacity-50"
                title="刪除"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
