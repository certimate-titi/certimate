'use client';

import React, { useState } from 'react';
import {
  Settings,
  Cpu,
  Zap,
  Bell,
  Flag,
  ShieldCheck,
  Save,
  RefreshCw,
  Plus,
  Trash2,
  ChevronRight,
  Info,
  User,
  Mail,
  Shield,
  MoreVertical,
  Server,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { logAdminAction, AdminAction } from '@/firebase';
import { superAdminService } from '@/lib/api/services';
import { BUILD_INFO } from '@/lib/build-info';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('ai');
  const [isSaving, setIsSaving] = useState(false);

  const tabs = [
    { id: 'ai', name: 'AI 模型路由', icon: Cpu },
    { id: 'plans', name: '方案限額', icon: Zap },
    { id: 'announcements', name: '公告管理', icon: Bell },
    { id: 'flags', name: 'Feature Flags', icon: Flag },
    { id: 'admins', name: '管理員帳號', icon: ShieldCheck },
    { id: 'version', name: '版本資訊', icon: Server },
  ];

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      // Save AI routing
      if (activeTab === 'ai') {
        await superAdminService.updateModelRouting('FREE', 'basic', aiRouting.freeBasic);
        await superAdminService.updateModelRouting('FREE', 'fallback', aiRouting.freeFallback);
        await superAdminService.updateModelRouting('PRO', 'advanced', aiRouting.proBasic);
        await superAdminService.updateModelRouting('PRO', 'fallback', aiRouting.proFallback);
      }
      // Save plan quotas
      if (activeTab === 'plans') {
        const planUpdates: Record<string, Record<string, number>> = { FREE: {}, PRO: {}, PRO_PLUS: {}, ULTRA: {} };
        for (const row of planQuotas) {
          planUpdates['FREE'][row.key] = Number(row.free) || 0;
          planUpdates['PRO'][row.key] = Number(row.pro) || 0;
          planUpdates['PRO_PLUS'][row.key] = Number(row.pro_plus) || 0;
          planUpdates['ULTRA'][row.key] = Number(row.ultra) || 0;
        }
        for (const [plan, updates] of Object.entries(planUpdates)) {
          await superAdminService.updatePlanQuota(plan, updates);
        }
      }
      // Save feature flags
      if (activeTab === 'flags') {
        for (const flag of featureFlags) {
          await superAdminService.updateFeatureFlag(flag.id, flag.enabled);
        }
      }
      // Save announcements
      if (activeTab === 'announcements' && announcementForm.title) {
        await superAdminService.createAnnouncement({
          title: announcementForm.title,
          content: announcementForm.content,
          display_mode: announcementForm.displayMode,
          schedule_date: announcementForm.scheduleDate || undefined,
        });
        setAnnouncementForm({ title: '', content: '', displayMode: 'banner', scheduleDate: '' });
      }
      await logAdminAction(
        AdminAction.UPDATE_SETTINGS,
        activeTab,
        `更新了 ${tabs.find(t => t.id === activeTab)?.name} 的系統設定`
      );
      alert('設定已儲存');
    } catch (error) {
      console.error(error);
      alert('儲存失敗，請稍後再試');
    } finally {
      setIsSaving(false);
    }
  };

  const [featureFlags, setFeatureFlags] = useState<{ id: string; name: string; description: string; enabled: boolean }[]>([]);

  const toggleFlag = (flagId: string) => {
    setFeatureFlags(prev => prev.map(f => f.id === flagId ? { ...f, enabled: !f.enabled } : f));
  };

  const [announcementForm, setAnnouncementForm] = useState({
    title: '',
    content: '',
    displayMode: 'banner',
    scheduleDate: '',
  });

  const [admins, setAdmins] = useState<{ id: string; name: string; email: string; role: string; joined: string }[]>([]);
  const [planQuotas, setPlanQuotas] = useState<{ label: string; key: string; free: number | string; pro: number | string; pro_plus: number | string; ultra: number | string }[]>([]);
  const [announcements, setAnnouncements] = useState<{ id: string; title: string; content: string; display_mode: string; created_at: string }[]>([]);
  const [aiRouting, setAiRouting] = useState({
    freeBasic: 'gemini-1.5-flash', freeFallback: 'llama-3-8b',
    proBasic: 'claude-3.5-sonnet', proFallback: 'gpt-4o',
    timeout: 3000, retries: 2,
  });

  const [versionInfo, setVersionInfo] = useState<{
    backend_version: string;
    backend_commit: string;
    api_prefix: string;
    python_version: string;
    alembic_head: string;
    deployed_at: string;
    environment: string;
  } | null>(null);
  const [versionLoading, setVersionLoading] = useState(false);
  const [versionError, setVersionError] = useState(false);

  React.useEffect(() => {
    superAdminService.getModelRouting().then(res => {
      const routings = (res as Record<string, unknown>).routings;
      if (Array.isArray(routings)) {
        const map: Record<string, Record<string, string>> = {};
        for (const r of routings as { plan: string; task_type: string; primary_model: string; fallback_model: string }[]) {
          if (!map[r.plan]) map[r.plan] = {};
          map[r.plan][r.task_type] = r.primary_model;
          map[r.plan][r.task_type + '_fallback'] = r.fallback_model || '';
        }
        setAiRouting(prev => ({
          freeBasic: map['FREE']?.['basic'] || prev.freeBasic,
          freeFallback: map['FREE']?.['basic_fallback'] || prev.freeFallback,
          proBasic: map['PRO']?.['advanced'] || prev.proBasic,
          proFallback: map['PRO']?.['advanced_fallback'] || prev.proFallback,
          timeout: prev.timeout,
          retries: prev.retries,
        }));
      }
    }).catch(() => {});
    superAdminService.getFeatureFlags().then(res => {
      if (Array.isArray(res?.flags)) setFeatureFlags(res.flags);
    }).catch(() => {});
    superAdminService.getAdmins().then(res => {
      const mapped = ((res as unknown as { users?: unknown[] }).users || (res as unknown as { admins?: unknown[] }).admins || []).map((u: unknown) => {
        const user = u as Record<string, unknown>;
        return {
          id: String(user.id || ''),
          name: String(user.display_name || user.name || user.email || '--'),
          email: String(user.email || ''),
          role: String(user.role || 'Admin'),
          joined: String(user.created_at || user.joined || '--'),
        };
      });
      setAdmins(mapped);
    }).catch(() => {});
    superAdminService.getPlanQuotas().then(res => {
      if (res.quotas?.length) setPlanQuotas(res.quotas);
    }).catch(() => {});
    superAdminService.getAnnouncements().then(res => {
      if (Array.isArray(res?.announcements)) setAnnouncements(res.announcements);
    }).catch(() => {});
    setVersionLoading(true);
    superAdminService.getVersionInfo().then(res => {
      setVersionInfo(res);
      setVersionError(false);
    }).catch(() => {
      setVersionError(true);
    }).finally(() => setVersionLoading(false));
  }, []);

  const handleAddAdmin = async () => {
    const email = prompt('請輸入新管理員的 Email:');
    if (!email) return;

    try {
      await superAdminService.adjustRole(email, 'admin');

      // 重新從 API 取得最新管理員列表
      const res = await superAdminService.getAdmins();
      const mapped = ((res as unknown as { users?: unknown[] }).users || (res as unknown as { admins?: unknown[] }).admins || []).map((u: unknown) => {
        const user = u as Record<string, unknown>;
        return {
          id: String(user.id || ''),
          name: String(user.display_name || user.name || user.email || '--'),
          email: String(user.email || ''),
          role: String(user.role || 'Admin'),
          joined: String(user.created_at || user.joined || '--'),
        };
      });
      setAdmins(mapped);
      await logAdminAction(
        AdminAction.CREATE_ADMIN,
        email,
        `新增了管理員帳號: ${email}`
      );
    } catch { alert('新增管理員失敗，請確認 Email 是否正確'); }
  };

  const handleDeleteAdmin = async (id: string, email: string) => {
    if (!confirm(`確定要刪除管理員 ${email} 嗎？`)) return;

    try {
      await superAdminService.adjustRole(email, 'user');
      setAdmins(admins.filter(a => a.id !== id));
      await logAdminAction(
        AdminAction.DELETE_ADMIN,
        id,
        `刪除了管理員帳號: ${email}`
      );
    } catch { alert('刪除管理員失敗'); }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">系統設定</h1>
          <p className="text-slate-500">免改 code 即時調整系統行為參數與權限</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={async () => {
              if (!confirm('確定要重置所有設定為預設值嗎？此操作無法復原。')) return;
              try {
                // Reload from API
                superAdminService.getFeatureFlags().then(res => {
      if (Array.isArray(res?.flags)) setFeatureFlags(res.flags);
    }).catch(() => {});
                setAnnouncementForm({ title: '', content: '', displayMode: 'banner', scheduleDate: '' });
                alert('已重置為預設值，請點擊「儲存所有設定」以套用');
              } catch { alert('重置失敗'); }
            }}
            className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" /> 重置為預設
          </button>
          <button 
            onClick={handleSaveSettings}
            disabled={isSaving}
            className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 disabled:opacity-50"
          >
            {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            儲存所有設定
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar Tabs */}
        <aside className="lg:w-64 shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "w-full flex items-center px-4 py-3 rounded-xl transition-all group",
                  activeTab === tab.id 
                    ? "bg-white text-emerald-600 shadow-sm border border-slate-200" 
                    : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                <tab.icon className={cn("h-5 w-5 shrink-0", activeTab === tab.id ? "text-emerald-500" : "group-hover:text-slate-700")} />
                <span className="ml-3 font-medium text-sm">{tab.name}</span>
                {activeTab === tab.id && <ChevronRight className="ml-auto h-4 w-4" />}
              </button>
            ))}
          </nav>
        </aside>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            {activeTab === 'ai' && (
              <div className="p-8 space-y-8">
                <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-2xl border border-blue-100">
                  <Info className="h-5 w-5 text-blue-500 shrink-0" />
                  <p className="text-sm text-blue-700">AI 模型路由設定將即時影響所有用戶的請求處理路徑。</p>
                </div>

                <div className="grid gap-8">
                  <section>
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Free 用戶路由</h3>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">基本任務模型</label>
                        <select value={aiRouting.freeBasic} onChange={e => setAiRouting(p => ({ ...p, freeBasic: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>gemini-1.5-flash</option>
                          <option>llama-3-8b</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">備援模型 (Fallback)</label>
                        <select value={aiRouting.freeFallback} onChange={e => setAiRouting(p => ({ ...p, freeFallback: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>llama-3-8b</option>
                          <option>gemini-1.5-flash</option>
                        </select>
                      </div>
                    </div>
                  </section>

                  <section>
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Pro / Ultra 用戶路由</h3>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">進階任務模型</label>
                        <select value={aiRouting.proBasic} onChange={e => setAiRouting(p => ({ ...p, proBasic: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>claude-3.5-sonnet</option>
                          <option>gpt-4o</option>
                          <option>gemini-1.5-pro</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">備援模型 (Fallback)</label>
                        <select value={aiRouting.proFallback} onChange={e => setAiRouting(p => ({ ...p, proFallback: e.target.value }))} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>gpt-4o</option>
                          <option>claude-3.5-sonnet</option>
                        </select>
                      </div>
                    </div>
                  </section>

                  <section>
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Fallback 觸發條件</h3>
                    <p className="text-sm text-slate-500">
                      Timeout 和重試次數目前由後端 <code className="px-1.5 py-0.5 bg-slate-100 rounded text-xs">LLMService</code> 控制（預設 timeout 30s / 重試 2 次），
                      未來可透過環境變數 <code className="px-1.5 py-0.5 bg-slate-100 rounded text-xs">LLM_TIMEOUT_SECONDS</code> 調整。
                    </p>
                  </section>
                </div>
              </div>
            )}

            {activeTab === 'plans' && (
              <div className="p-8 space-y-8">
                <h3 className="text-lg font-bold text-slate-900 mb-6">方案限額調整</h3>
                {planQuotas.length === 0 ? (
                  <div className="text-center py-8 text-slate-400 text-sm">尚無方案限額設定，請先於資料庫建立 plan_quotas 資料</div>
                ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">參數</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">FREE</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">PRO</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">PRO_PLUS</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">ULTRA</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {planQuotas.map((row) => (
                        <tr key={row.key}>
                          <td className="py-4 text-sm font-medium text-slate-700">{row.label}</td>
                          <td className="py-4"><input type="number" value={row.free} onChange={e => setPlanQuotas(prev => prev.map(r => r.key === row.key ? { ...r, free: e.target.value } : r))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                          <td className="py-4"><input type="number" value={row.pro} onChange={e => setPlanQuotas(prev => prev.map(r => r.key === row.key ? { ...r, pro: e.target.value } : r))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                          <td className="py-4"><input type="number" value={row.pro_plus} onChange={e => setPlanQuotas(prev => prev.map(r => r.key === row.key ? { ...r, pro_plus: e.target.value } : r))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                          <td className="py-4"><input type="number" value={row.ultra} onChange={e => setPlanQuotas(prev => prev.map(r => r.key === row.key ? { ...r, ultra: e.target.value } : r))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                )}
              </div>
            )}

            {activeTab === 'announcements' && (
              <div className="p-8 space-y-8">
                {/* Announcement Form */}
                <div>
                  <h3 className="text-lg font-bold text-slate-900 mb-6">建立系統公告</h3>
                  <div className="space-y-4 p-6 bg-slate-50 rounded-2xl border border-slate-100">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">公告標題</label>
                      <input
                        type="text"
                        value={announcementForm.title}
                        onChange={(e) => setAnnouncementForm({ ...announcementForm, title: e.target.value })}
                        placeholder="輸入公告標題..."
                        className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">公告內容</label>
                      <textarea
                        value={announcementForm.content}
                        onChange={(e) => setAnnouncementForm({ ...announcementForm, content: e.target.value })}
                        placeholder="輸入公告內容..."
                        rows={4}
                        className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all resize-none"
                      />
                    </div>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">顯示方式</label>
                        <select
                          value={announcementForm.displayMode}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, displayMode: e.target.value })}
                          className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all"
                        >
                          <option value="banner">全站橫幅 (Banner)</option>
                          <option value="notification">站內通知 (Notification)</option>
                          <option value="email">Email 推播</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">排程發布日期</label>
                        <input
                          type="date"
                          value={announcementForm.scheduleDate}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, scheduleDate: e.target.value })}
                          className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end pt-2">
                      <button
                        onClick={async () => {
                          if (!announcementForm.title || !announcementForm.content) { alert('請填寫標題和內容'); return; }
                          try {
                            await superAdminService.createAnnouncement({
                              title: announcementForm.title,
                              content: announcementForm.content,
                              display_mode: announcementForm.displayMode,
                              schedule_date: announcementForm.scheduleDate || undefined,
                            });
                            setAnnouncementForm({ title: '', content: '', displayMode: 'banner', scheduleDate: '' });
                            const res = await superAdminService.getAnnouncements();
                            if (Array.isArray(res?.announcements)) setAnnouncements(res.announcements);
                            alert('公告已建立');
                          } catch { alert('建立公告失敗'); }
                        }}
                        className="px-5 py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2"
                      >
                        <Plus className="h-4 w-4" /> 建立公告
                      </button>
                    </div>
                  </div>
                </div>

                {/* Existing Announcements */}
                <div>
                  <h3 className="text-lg font-bold text-slate-900 mb-4">已建立公告</h3>
                  {announcements.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 text-sm">
                      尚無已建立的公告
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {announcements.map((a) => (
                        <div key={a.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                          <div className="flex justify-between items-start mb-1">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-bold text-slate-900">{a.title}</p>
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 uppercase">{a.display_mode}</span>
                              {(a as unknown as Record<string, unknown>).status === 'inactive' && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-500">已停用</span>
                              )}
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={async () => {
                                  try {
                                    await superAdminService.deactivateAnnouncement(a.id);
                                    const res = await superAdminService.getAnnouncements();
                                    if (Array.isArray(res?.announcements)) setAnnouncements(res.announcements);
                                  } catch { alert('停用失敗'); }
                                }}
                                className="p-1.5 text-slate-400 hover:text-amber-500 hover:bg-amber-50 rounded-lg transition-all"
                                title="停用公告"
                              >
                                <Bell className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={async () => {
                                  if (!confirm(`確定要刪除公告「${a.title}」嗎？`)) return;
                                  try {
                                    await superAdminService.deleteAnnouncement(a.id);
                                    setAnnouncements(prev => prev.filter(x => x.id !== a.id));
                                  } catch { alert('刪除失敗'); }
                                }}
                                className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all"
                                title="刪除公告"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                          <p className="text-xs text-slate-600 mb-1">{a.content}</p>
                          <p className="text-xs text-slate-400">{a.created_at}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'flags' && (
              <div className="p-8 space-y-6">
                <h3 className="text-lg font-bold text-slate-900 mb-6">Feature Flags</h3>
                <div className="space-y-4">
                  {featureFlags.map((flag) => (
                    <div key={flag.id} className="flex items-center justify-between p-6 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-bold text-slate-900">{flag.name}</p>
                          <span className={cn(
                            "text-[10px] font-bold px-1.5 py-0.5 rounded uppercase",
                            flag.enabled ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500"
                          )}>
                            {flag.enabled ? 'ON' : 'OFF'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 font-mono">{flag.id}</p>
                        <p className="text-xs text-slate-500 mt-1">{flag.description}</p>
                      </div>
                      <button
                        onClick={() => toggleFlag(flag.id)}
                        className={cn(
                          "w-12 h-6 rounded-full transition-all relative cursor-pointer",
                          flag.enabled ? "bg-emerald-500" : "bg-slate-300"
                        )}
                      >
                        <div className={cn(
                          "absolute top-1 w-4 h-4 bg-white rounded-full transition-all shadow-sm",
                          flag.enabled ? "right-1" : "left-1"
                        )}></div>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'version' && (
              <div className="p-8 space-y-8">
                <h3 className="text-lg font-bold text-slate-900 mb-6">版本資訊</h3>

                {/* Frontend Info */}
                <section>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Frontend</h4>
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Version</p>
                      <p className="text-lg font-bold text-slate-900">{BUILD_INFO.version}</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Commit</p>
                      <p className="text-lg font-mono font-bold text-slate-900">{BUILD_INFO.commit}</p>
                    </div>
                    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Build Time</p>
                      <p className="text-sm font-bold text-slate-900">{BUILD_INFO.buildTime}</p>
                    </div>
                  </div>
                </section>

                {/* Backend Info */}
                <section>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Backend</h4>
                  {versionLoading ? (
                    <div className="flex items-center gap-3 p-6 rounded-2xl bg-slate-50 border border-slate-100">
                      <Loader2 className="h-5 w-5 text-slate-400 animate-spin" />
                      <span className="text-sm text-slate-500">Loading backend info...</span>
                    </div>
                  ) : versionError ? (
                    <div className="flex items-center gap-3 p-6 rounded-2xl bg-rose-50 border border-rose-100">
                      <XCircle className="h-5 w-5 text-rose-500" />
                      <span className="text-sm text-rose-700">Unable to connect to backend API</span>
                      <button
                        onClick={() => {
                          setVersionLoading(true);
                          setVersionError(false);
                          superAdminService.getVersionInfo().then(res => {
                            setVersionInfo(res);
                          }).catch(() => setVersionError(true)).finally(() => setVersionLoading(false));
                        }}
                        className="ml-auto text-xs font-bold text-rose-600 hover:text-rose-800 transition-colors"
                      >
                        Retry
                      </button>
                    </div>
                  ) : versionInfo ? (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Version</p>
                        <p className="text-lg font-bold text-slate-900">{versionInfo.backend_version}</p>
                      </div>
                      <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Commit</p>
                        <p className="text-lg font-mono font-bold text-slate-900">{versionInfo.backend_commit}</p>
                      </div>
                      <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Python</p>
                        <p className="text-lg font-bold text-slate-900">{versionInfo.python_version}</p>
                      </div>
                      <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Alembic Head</p>
                        <p className="text-lg font-mono font-bold text-slate-900">{versionInfo.alembic_head}</p>
                      </div>
                      <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Environment</p>
                        <span className={cn(
                          "inline-block text-xs font-bold px-2.5 py-1 rounded-lg uppercase tracking-wider mt-1",
                          versionInfo.environment === 'production'
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-amber-100 text-amber-700"
                        )}>
                          {versionInfo.environment}
                        </span>
                      </div>
                      <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Deployed At</p>
                        <p className="text-sm font-bold text-slate-900">{versionInfo.deployed_at}</p>
                      </div>
                    </div>
                  ) : null}
                </section>

                {/* Connection Status */}
                <section>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Connection Status</h4>
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex items-center gap-3">
                      {versionInfo ? (
                        <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" />
                      ) : (
                        <XCircle className="h-5 w-5 text-rose-500 shrink-0" />
                      )}
                      <div>
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Database</p>
                        <p className="text-sm font-bold text-slate-900">{versionInfo ? 'Connected' : 'Unreachable'}</p>
                      </div>
                    </div>
                    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">API URL</p>
                      <p className="text-sm font-mono font-bold text-slate-900 break-all">
                        {typeof window !== 'undefined'
                          ? (process.env.NEXT_PUBLIC_API_URL || '/api/v1')
                          : '/api/v1'}
                      </p>
                    </div>
                  </div>
                </section>
              </div>
            )}

            {activeTab === 'admins' && (
              <div className="p-8 space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-bold text-slate-900">管理員帳號</h3>
                  <button 
                    onClick={handleAddAdmin}
                    className="px-4 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all flex items-center gap-2"
                  >
                    <Plus className="h-4 w-4" /> 新增管理員
                  </button>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50/50 border-b border-slate-100">
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">管理員</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">權限</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">加入日期</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {admins.map((admin) => (
                        <tr key={admin.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold text-xs">
                                {admin.name.charAt(0)}
                              </div>
                              <div>
                                <p className="text-sm font-bold text-slate-900">{admin.name}</p>
                                <p className="text-xs text-slate-500">{admin.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={cn(
                              "text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider",
                              admin.role === 'Super Admin' ? "bg-rose-50 text-rose-600" : "bg-blue-50 text-blue-600"
                            )}>
                              {admin.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-500">{admin.joined}</td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button className="p-2 text-slate-400 hover:text-slate-900 transition-all">
                                <MoreVertical className="h-4 w-4" />
                              </button>
                              <button 
                                onClick={() => handleDeleteAdmin(admin.id, admin.email)}
                                className="p-2 text-slate-400 hover:text-rose-500 transition-all"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
