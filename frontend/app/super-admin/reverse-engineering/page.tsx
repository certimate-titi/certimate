/**
 * @file 路由 `/super-admin/reverse-engineering` — 考綱逆向工程操作頁（Spec 26）。
 *
 * Super Admin 為某科目觸發 LLM 從考古題反推知識結構：
 * - 全量 extract（重建整棵知識樹）
 * - 增量 incremental（只處理新增考古題）
 * - 預覽當前知識樹（遞迴展開 3 層）
 * - Markdown 匯出（下載）/ 匯入（覆寫現有結構）
 */
'use client';

import { useEffect, useState } from 'react';
import { Wrench, Loader2, RefreshCw, AlertCircle, CheckCircle2, Download, Upload, ChevronRight, ChevronDown } from 'lucide-react';
import { reverseEngineeringService, subjectService } from '@/lib/api/services';

interface TreeNode {
  id?: string;
  name?: string;
  depth?: number;
  children?: TreeNode[];
  [key: string]: unknown;
}

function TreeNodeRow({ node, level = 0 }: { node: TreeNode; level?: number }) {
  const [open, setOpen] = useState(level < 1); // depth=1 默認展開，depth=2 收合
  const children = (node.children as TreeNode[] | undefined) || [];
  const hasChildren = children.length > 0;
  const colorByDepth = ['text-slate-900 font-bold', 'text-slate-700 font-medium', 'text-slate-500'];
  const cls = colorByDepth[Math.min(level, 2)] || 'text-slate-400';

  return (
    <li>
      <div
        className="flex items-center gap-1 hover:bg-slate-50 rounded px-1 py-0.5 cursor-pointer"
        style={{ paddingLeft: `${level * 16}px` }}
        onClick={() => hasChildren && setOpen(!open)}
      >
        {hasChildren ? (
          open ? <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" /> : <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
        ) : (
          <span className="w-3 inline-block shrink-0" />
        )}
        <span className={`${cls} truncate`}>{String(node.name || '(未命名)')}</span>
        {hasChildren && (
          <span className="text-[10px] text-slate-400 ml-1">({children.length})</span>
        )}
      </div>
      {hasChildren && open && (
        <ul className="text-xs">
          {children.map((c, i) => (
            <TreeNodeRow key={c.id ? String(c.id) : `${level}-${i}`} node={c} level={level + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function ReverseEngineeringPage() {
  const [subjects, setSubjects] = useState<Array<{ id: string; name: string }>>([]);
  const [selected, setSelected] = useState<string>('');
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [tree, setTree] = useState<TreeNode[] | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState('');

  useEffect(() => {
    subjectService.getUserSubjects().then((res) => {
      const list = (res.subjects || []).map((s) => ({ id: s.subjectId || s.id, name: s.subjectName || s.id }));
      setSubjects(list);
      if (list.length) setSelected(list[0].id);
    }).catch(() => { /* silent */ });
  }, []);

  const run = async (action: 'extract' | 'incremental' | 'preview') => {
    if (!selected) return;
    setBusy(action);
    setMsg(null);
    try {
      if (action === 'extract') {
        const res = await reverseEngineeringService.extract(selected);
        setMsg({ ok: true, text: `✅ 全量萃取完成：${res.nodes_created} 個知識節點` });
      } else if (action === 'incremental') {
        const res = await reverseEngineeringService.incremental(selected);
        setMsg({ ok: true, text: `✅ 增量處理完成：新增 ${res.added} 個節點` });
      } else {
        const res = await reverseEngineeringService.getKnowledgeTree(selected);
        setTree((res.tree || []) as TreeNode[]);
        // 計算總節點數（含 children）
        const countAll = (nodes: TreeNode[]): number => nodes.reduce(
          (acc, n) => acc + 1 + countAll((n.children as TreeNode[]) || []), 0,
        );
        const total = countAll((res.tree || []) as TreeNode[]);
        setMsg({ ok: true, text: `✅ 載入完成（共 ${total} 節點，${res.tree?.length || 0} 個 root）` });
      }
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg({ ok: false, text: `❌ ${err?.message || '操作失敗'}` });
    } finally {
      setBusy(null);
    }
  };

  const handleExport = async () => {
    if (!selected) return;
    setBusy('export');
    setMsg(null);
    try {
      const res = await reverseEngineeringService.exportMarkdown(selected);
      const blob = new Blob([res.markdown || ''], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const subjName = subjects.find((s) => s.id === selected)?.name || selected;
      a.href = url;
      a.download = `knowledge-tree-${subjName}-${new Date().toISOString().slice(0, 10)}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setMsg({ ok: true, text: '✅ Markdown 已下載' });
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg({ ok: false, text: `❌ ${err?.message || '匯出失敗'}` });
    } finally {
      setBusy(null);
    }
  };

  const handleImport = async () => {
    if (!selected || !importText.trim()) return;
    if (!confirm('匯入會覆寫現有知識樹，確定繼續？')) return;
    setBusy('import');
    setMsg(null);
    try {
      const res = await reverseEngineeringService.importMarkdown(selected, importText);
      setMsg({ ok: true, text: `✅ 匯入完成：${res.nodes_created} 個節點寫入` });
      setShowImport(false);
      setImportText('');
      // 重新載入樹
      const treeRes = await reverseEngineeringService.getKnowledgeTree(selected);
      setTree((treeRes.tree || []) as TreeNode[]);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg({ ok: false, text: `❌ ${err?.message || '匯入失敗'}` });
    } finally {
      setBusy(null);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setImportText(String(ev.target?.result || ''));
    };
    reader.readAsText(file);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Wrench className="w-6 h-6 text-indigo-500" />
        <h1 className="text-2xl font-bold text-slate-900">考綱逆向工程</h1>
      </div>
      <p className="text-sm text-slate-500 mb-6 leading-relaxed">
        Spec 26 §考綱逆向工程：對某科目觸發 LLM 從考古題反推知識結構。
        全量會重建整棵樹（耗時 1-3 分鐘），增量只處理新增考古題。可匯出 Markdown 編輯後再匯入覆寫。
      </p>

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
        <label className="block text-xs text-slate-600 mb-2">選擇科目</label>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full px-3 py-2 border border-slate-200 rounded text-sm mb-4"
        >
          {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>

        <div className="grid grid-cols-3 gap-2 mb-3">
          <button
            onClick={() => run('extract')}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-rose-500 text-white rounded text-xs font-medium hover:bg-rose-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {busy === 'extract' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            全量萃取
          </button>
          <button
            onClick={() => run('incremental')}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-emerald-500 text-white rounded text-xs font-medium hover:bg-emerald-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {busy === 'incremental' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            增量處理
          </button>
          <button
            onClick={() => run('preview')}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-slate-500 text-white rounded text-xs font-medium hover:bg-slate-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            預覽知識樹
          </button>
        </div>

        {/* Spec 26 §匯入匯出 Markdown */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={handleExport}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-blue-500 text-white rounded text-xs font-medium hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {busy === 'export' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
            匯出 Markdown
          </button>
          <button
            onClick={() => setShowImport((v) => !v)}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-amber-500 text-white rounded text-xs font-medium hover:bg-amber-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            <Upload className="w-3 h-3" />
            匯入 Markdown
          </button>
        </div>

        {msg && (
          <div className={`mt-3 flex items-start gap-2 p-3 rounded text-xs ${
            msg.ok ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
          }`}>
            {msg.ok ? <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />}
            <div>{msg.text}</div>
          </div>
        )}
      </div>

      {/* 匯入區塊（展開式） */}
      {showImport && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-4">
          <h2 className="text-sm font-bold text-amber-900 mb-2">匯入 Markdown 知識樹</h2>
          <p className="text-xs text-amber-700 mb-3">
            ⚠️ 匯入會覆寫該科目現有的知識樹結構。建議先匯出備份。
          </p>
          <input
            type="file"
            accept=".md,text/markdown"
            onChange={handleFileUpload}
            className="text-xs mb-2 block"
          />
          <textarea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder="貼上或選擇 Markdown 巢狀列表（# / ## / ### 三層）..."
            className="w-full h-40 p-2 border border-amber-300 rounded text-xs font-mono"
          />
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleImport}
              disabled={!importText.trim() || busy !== null}
              className="px-3 py-1.5 bg-amber-600 text-white rounded text-xs hover:bg-amber-700 disabled:opacity-50 flex items-center gap-1"
            >
              {busy === 'import' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
              確認匯入
            </button>
            <button
              onClick={() => { setShowImport(false); setImportText(''); }}
              className="px-3 py-1.5 bg-slate-200 text-slate-700 rounded text-xs hover:bg-slate-300"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {tree && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-slate-700 mb-3">知識樹預覽（遞迴展開）</h2>
          {tree.length === 0 ? (
            <p className="text-xs text-slate-400">（尚無資料 — 請先觸發萃取）</p>
          ) : (
            <ul className="text-xs space-y-0.5 max-h-[500px] overflow-y-auto">
              {tree.map((n, i) => (
                <TreeNodeRow key={n.id ? String(n.id) : `root-${i}`} node={n} level={0} />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
