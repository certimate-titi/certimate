'use client';

import React, { useEffect, useState } from 'react';
import { anomalyService, type AnomalyItem } from '@/lib/api/services';
import { AlertTriangle, Wrench, Calendar, Power } from 'lucide-react';

const STATUS_LABELS: Record<string, { text: string; bg: string }> = {
  open: { text: '未處理', bg: 'bg-rose-50 text-rose-700' },
  assigned: { text: '已指派', bg: 'bg-amber-50 text-amber-700' },
  in_progress: { text: '處理中', bg: 'bg-blue-50 text-blue-700' },
  resolved: { text: '已解決', bg: 'bg-emerald-50 text-emerald-700' },
  closed: { text: '已關閉', bg: 'bg-slate-100 text-slate-600' },
};

export default function AnomalyPage() {
  const [items, setItems] = useState<AnomalyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskForm, setTaskForm] = useState({ name: '', priority: 'P1', related_error: '', estimated_hours: 1 });

  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleForm, setScheduleForm] = useState({ name: '', starts_at: '', ends_at: '', notify_channels: 'email' });

  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [maintenanceForm, setMaintenanceForm] = useState({ reason: '', estimated_recovery: '' });

  const [msg, setMsg] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    anomalyService.listAnomalies()
      .then(res => setItems(res.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleUpdateStatus = async (errorId: string, nextStatus: string) => {
    setBusy(errorId);
    try {
      await anomalyService.updateAnomaly(errorId, nextStatus);
      load();
    } catch (e) {
      alert(`更新失敗：${e instanceof Error ? e.message : '未知錯誤'}`);
    } finally {
      setBusy(null);
    }
  };

  const handleAssign = async (errorId: string) => {
    const who = prompt('指派給（填入 email 或姓名）：');
    if (!who) return;
    setBusy(errorId);
    try {
      await anomalyService.updateAnomaly(errorId, 'assigned', who);
      load();
    } catch (e) {
      alert(`指派失敗：${e instanceof Error ? e.message : '未知錯誤'}`);
    } finally {
      setBusy(null);
    }
  };

  const handleCreateTask = async () => {
    if (!taskForm.name) { setMsg('請填寫任務名稱'); return; }
    try {
      await anomalyService.createMaintenanceTask({
        name: taskForm.name,
        priority: taskForm.priority,
        related_error: taskForm.related_error || undefined,
        estimated_hours: taskForm.estimated_hours,
      });
      setMsg('✓ 維修任務已建立');
      setShowTaskModal(false);
      setTaskForm({ name: '', priority: 'P1', related_error: '', estimated_hours: 1 });
    } catch (e) {
      setMsg(`建立失敗：${e instanceof Error ? e.message : '未知錯誤'}`);
    }
  };

  const handleCreateSchedule = async () => {
    if (!scheduleForm.name || !scheduleForm.starts_at || !scheduleForm.ends_at) { setMsg('請填寫完整資訊'); return; }
    try {
      await anomalyService.createMaintenanceSchedule(scheduleForm);
      setMsg('✓ 維修排程已建立');
      setShowScheduleModal(false);
      setScheduleForm({ name: '', starts_at: '', ends_at: '', notify_channels: 'email' });
    } catch (e) {
      setMsg(`建立失敗：${e instanceof Error ? e.message : '未知錯誤'}`);
    }
  };

  const handleActivateMaintenance = async () => {
    if (!maintenanceForm.reason || !maintenanceForm.estimated_recovery) { setMsg('請填寫完整資訊'); return; }
    if (!confirm(`⚠️ 確定要啟動維修模式？\n原因：${maintenanceForm.reason}\n預計恢復：${maintenanceForm.estimated_recovery}`)) return;
    try {
      await anomalyService.activateMaintenanceMode(maintenanceForm.reason, maintenanceForm.estimated_recovery);
      setMsg('✓ 維修模式已啟動');
      setShowMaintenanceModal(false);
      setMaintenanceForm({ reason: '', estimated_recovery: '' });
    } catch (e) {
      setMsg(`啟動失敗：${e instanceof Error ? e.message : '未知錯誤'}`);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">異常維修管理</h1>
          <p className="text-slate-500">追蹤系統異常、排程維修任務與啟動維修模式</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowTaskModal(true)} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 flex items-center gap-2">
            <Wrench className="h-4 w-4" /> 建立維修任務
          </button>
          <button onClick={() => setShowScheduleModal(true)} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 flex items-center gap-2">
            <Calendar className="h-4 w-4" /> 排程維修
          </button>
          <button onClick={() => setShowMaintenanceModal(true)} className="px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700 flex items-center gap-2">
            <Power className="h-4 w-4" /> 啟動維修模式
          </button>
        </div>
      </div>

      {msg && (
        <div className={`rounded-xl px-4 py-3 text-sm ${msg.startsWith('✓') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
          {msg}
        </div>
      )}

      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          <h2 className="text-lg font-bold text-slate-900">異常清單</h2>
          <span className="text-xs text-slate-500">（共 {items.length} 筆）</span>
        </div>

        {loading ? (
          <p className="text-sm text-slate-500">載入中…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">目前沒有異常紀錄。</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-2 text-left">錯誤 ID</th>
                  <th className="px-4 py-2 text-left">類型</th>
                  <th className="px-4 py-2 text-right">發生次數</th>
                  <th className="px-4 py-2 text-left">影響範圍</th>
                  <th className="px-4 py-2 text-left">指派</th>
                  <th className="px-4 py-2 text-left">最近發生</th>
                  <th className="px-4 py-2 text-center">狀態</th>
                  <th className="px-4 py-2 text-right">動作</th>
                </tr>
              </thead>
              <tbody>
                {items.map(r => (
                  <tr key={r.error_id} className="border-t border-slate-100">
                    <td className="px-4 py-2 font-mono text-xs">{r.error_id}</td>
                    <td className="px-4 py-2">{r.error_type}{r.classified && <span className="ml-1 text-xs text-amber-600">·重複</span>}</td>
                    <td className="px-4 py-2 text-right font-semibold">{r.occurrence_count}</td>
                    <td className="px-4 py-2 text-slate-600">{r.impact_scope || '—'}</td>
                    <td className="px-4 py-2 text-slate-600">{r.assigned_to || '—'}</td>
                    <td className="px-4 py-2 text-slate-600 text-xs">{r.last_seen_at ? new Date(r.last_seen_at).toLocaleString() : '—'}</td>
                    <td className="px-4 py-2 text-center">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_LABELS[r.status]?.bg || 'bg-slate-100 text-slate-600'}`}>
                        {STATUS_LABELS[r.status]?.text || r.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <div className="flex gap-1 justify-end">
                        {r.status === 'open' && (
                          <button disabled={busy === r.error_id} onClick={() => handleAssign(r.error_id)} className="px-2 py-1 text-xs bg-amber-600 text-white rounded hover:bg-amber-700 disabled:opacity-50">指派</button>
                        )}
                        {(r.status === 'open' || r.status === 'assigned') && (
                          <button disabled={busy === r.error_id} onClick={() => handleUpdateStatus(r.error_id, 'in_progress')} className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">處理中</button>
                        )}
                        {r.status !== 'resolved' && r.status !== 'closed' && (
                          <button disabled={busy === r.error_id} onClick={() => handleUpdateStatus(r.error_id, 'resolved')} className="px-2 py-1 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50">解決</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Task Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4" onClick={() => setShowTaskModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4">建立維修任務</h3>
            <div className="space-y-3">
              <input placeholder="任務名稱" value={taskForm.name} onChange={e => setTaskForm({ ...taskForm, name: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <select value={taskForm.priority} onChange={e => setTaskForm({ ...taskForm, priority: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm">
                <option value="P0">P0 — 緊急</option>
                <option value="P1">P1 — 高</option>
                <option value="P2">P2 — 中</option>
                <option value="P3">P3 — 低</option>
              </select>
              <input placeholder="關聯異常 ID（選填）" value={taskForm.related_error} onChange={e => setTaskForm({ ...taskForm, related_error: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <input type="number" step="0.5" placeholder="預估工時" value={taskForm.estimated_hours} onChange={e => setTaskForm({ ...taskForm, estimated_hours: Number(e.target.value) })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <div className="flex gap-2 justify-end pt-2">
                <button onClick={() => setShowTaskModal(false)} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">取消</button>
                <button onClick={handleCreateTask} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">建立</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4" onClick={() => setShowScheduleModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4">排程維修</h3>
            <div className="space-y-3">
              <input placeholder="排程名稱" value={scheduleForm.name} onChange={e => setScheduleForm({ ...scheduleForm, name: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <label className="block text-xs text-slate-500">開始時間</label>
              <input type="datetime-local" value={scheduleForm.starts_at} onChange={e => setScheduleForm({ ...scheduleForm, starts_at: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <label className="block text-xs text-slate-500">結束時間</label>
              <input type="datetime-local" value={scheduleForm.ends_at} onChange={e => setScheduleForm({ ...scheduleForm, ends_at: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <select value={scheduleForm.notify_channels} onChange={e => setScheduleForm({ ...scheduleForm, notify_channels: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm">
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="email,sms">Email + SMS</option>
              </select>
              <div className="flex gap-2 justify-end pt-2">
                <button onClick={() => setShowScheduleModal(false)} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">取消</button>
                <button onClick={handleCreateSchedule} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">建立</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Maintenance Mode Modal */}
      {showMaintenanceModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4" onClick={() => setShowMaintenanceModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4 text-rose-700">⚠️ 啟動維修模式</h3>
            <p className="text-sm text-slate-600 mb-3">啟動後所有使用者將看到維修頁面，請謹慎操作。</p>
            <div className="space-y-3">
              <input placeholder="維修原因（例：資料庫升級）" value={maintenanceForm.reason} onChange={e => setMaintenanceForm({ ...maintenanceForm, reason: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <input placeholder="預計恢復時間（例：2026-04-20 03:00）" value={maintenanceForm.estimated_recovery} onChange={e => setMaintenanceForm({ ...maintenanceForm, estimated_recovery: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              <div className="flex gap-2 justify-end pt-2">
                <button onClick={() => setShowMaintenanceModal(false)} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">取消</button>
                <button onClick={handleActivateMaintenance} className="px-4 py-2 text-sm bg-rose-600 text-white rounded-lg hover:bg-rose-700">確認啟動</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
