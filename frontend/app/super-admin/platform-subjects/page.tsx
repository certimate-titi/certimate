'use client';

import { useEffect, useState } from 'react';
import { Save, Rocket, Undo2, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import {
  platformSubjectAdminService,
  type PlatformSubjectVersionInfo,
} from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';

interface Subject {
  id: string;
  name: string;
  scope?: string;
  version?: number;
  published_at?: string | null;
}

interface Resource {
  id: string;
  name: string;
  scope?: string;
}

export default function PlatformSubjectsAdminPage() {
  const { isAdmin, loading: authLoading } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [platformResources, setPlatformResources] = useState<Resource[]>([]);
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());
  const [versionInfo, setVersionInfo] = useState<PlatformSubjectVersionInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || !isAdmin) return;
    void loadSubjects();
    void loadResources();
  }, [authLoading, isAdmin]);

  useEffect(() => {
    if (!selectedId) return;
    void loadVersions(selectedId);
  }, [selectedId]);

  const loadSubjects = async () => {
    try {
      const res = await apiClient.get<{
        subjects?: Subject[];
        categories?: Array<{ subjects: Subject[] }>;
      }>('/subjects/available');
      const flat =
        res.subjects || (res.categories || []).flatMap((c) => c.subjects || []);
      setSubjects(flat.filter((s) => s.scope === 'platform' || !s.scope));
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '載入考科失敗');
    }
  };

  const loadResources = async () => {
    try {
      const res = await apiClient.get<{ resources?: Resource[] }>('/resources');
      setPlatformResources((res.resources || []).filter((r) => r.scope === 'platform'));
    } catch {
      /* ignore */
    }
  };

  const loadVersions = async (subjectId: string) => {
    try {
      const res = await platformSubjectAdminService.listVersions(subjectId);
      setVersionInfo(res);
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '載入版本失敗');
    }
  };

  const toggle = (id: string) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const saveDraft = async () => {
    if (!selectedId) return;
    setBusy(true);
    setMsg(null);
    try {
      await platformSubjectAdminService.updateDraft(selectedId, Array.from(checkedIds));
      setMsg('草稿已儲存');
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '儲存失敗');
    } finally {
      setBusy(false);
    }
  };

  const publish = async () => {
    if (!selectedId) return;
    if (!confirm('發布後新選科用戶將取得此版本（已 fork 用戶不受影響），確認？')) return;
    setBusy(true);
    setMsg(null);
    try {
      const r = await platformSubjectAdminService.publish(selectedId);
      setMsg(`已發布 v${r.version}`);
      await loadVersions(selectedId);
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '發布失敗');
    } finally {
      setBusy(false);
    }
  };

  const rollback = async () => {
    if (!selectedId) return;
    if (!confirm('回滾至前一版本？此操作僅調整版本號，既有資源內容不會被還原。')) return;
    setBusy(true);
    setMsg(null);
    try {
      const r = await platformSubjectAdminService.rollback(selectedId);
      setMsg(`已回滾至 v${r.version}`);
      await loadVersions(selectedId);
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '回滾失敗');
    } finally {
      setBusy(false);
    }
  };

  if (authLoading) return <div className="p-8 text-slate-500">載入中…</div>;
  if (!isAdmin) return <div className="p-8 text-red-600">需要管理員權限</div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-1">平台預載科目版本管理</h1>
      <p className="text-sm text-slate-600 mb-6">
        PRD-034 US-03：編輯草稿、發布新版、回滾。已 fork 用戶不受新版本影響（解耦式 Fork）。
      </p>

      <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6">
        <label className="block text-xs text-slate-600 mb-1">選擇平台科目</label>
        <select
          value={selectedId}
          onChange={(e) => {
            setSelectedId(e.target.value);
            setCheckedIds(new Set());
            setMsg(null);
          }}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-sm"
        >
          <option value="">— 選擇科目 —</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
              {s.version ? `（v${s.version}）` : ''}
            </option>
          ))}
        </select>
      </div>

      {selectedId && (
        <>
          <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-slate-900">草稿資源清單</h2>
              <button
                onClick={saveDraft}
                disabled={busy}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-sm disabled:opacity-50"
              >
                <Save className="w-4 h-4" /> 儲存草稿
              </button>
            </div>
            {platformResources.length === 0 ? (
              <p className="text-sm text-slate-400">尚無 scope=platform 的資源</p>
            ) : (
              <div className="space-y-1.5 max-h-80 overflow-auto">
                {platformResources.map((r) => (
                  <label
                    key={r.id}
                    className="flex items-center gap-3 p-2 rounded-md hover:bg-slate-50 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={checkedIds.has(r.id)}
                      onChange={() => toggle(r.id)}
                    />
                    <span>{r.name}</span>
                    <span className="ml-auto text-xs text-slate-400">{r.id.slice(0, 8)}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6">
            <h2 className="font-semibold text-slate-900 mb-3">版本操作</h2>
            <div className="flex gap-2">
              <button
                onClick={publish}
                disabled={busy}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm disabled:opacity-50"
              >
                <Rocket className="w-4 h-4" /> 發布新版
              </button>
              <button
                onClick={rollback}
                disabled={busy}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-600 text-white text-sm disabled:opacity-50"
              >
                <Undo2 className="w-4 h-4" /> 回滾至前一版
              </button>
              <button
                onClick={() => loadVersions(selectedId)}
                disabled={busy}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-300 text-sm text-slate-700"
              >
                <RefreshCw className="w-4 h-4" /> 重新載入
              </button>
            </div>
            {msg && <div className="mt-3 text-sm text-slate-600">{msg}</div>}
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-900 mb-3">目前版本</h2>
            {!versionInfo ? (
              <p className="text-sm text-slate-400">載入中…</p>
            ) : (
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 text-sm">
                <span className="font-medium">v{versionInfo.current_version}</span>
                <span className="text-slate-500">
                  {versionInfo.published_at
                    ? `已發布：${new Date(versionInfo.published_at).toLocaleString()}`
                    : '尚未發布'}
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
