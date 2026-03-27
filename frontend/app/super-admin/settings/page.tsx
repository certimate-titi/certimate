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
  MoreVertical
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { logAdminAction, AdminAction } from '@/firebase';

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
  ];

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await logAdminAction(
        AdminAction.UPDATE_SETTINGS,
        activeTab,
        `更新了 ${tabs.find(t => t.id === activeTab)?.name} 的系統設定`
      );
      
      alert('設定已儲存並記錄至審計日誌');
    } catch (error) {
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  const [featureFlags, setFeatureFlags] = useState([
    { id: 'enable_notion_sync', name: 'Notion 同步功能', description: '是否開放 Notion 同步功能', enabled: true },
    { id: 'enable_socratic_tutor_v2', name: '新版 AI 教練', description: '蘇格拉底式引導 V2', enabled: false },
    { id: 'enable_b2b_dashboard', name: 'B2B 管理後台', description: '機構管理員專屬介面', enabled: true },
    { id: 'enable_weekly_report', name: '每週學習報告', description: '每週自動寄送學習進度報告至用戶信箱', enabled: false },
  ]);

  const toggleFlag = (flagId: string) => {
    setFeatureFlags(prev => prev.map(f => f.id === flagId ? { ...f, enabled: !f.enabled } : f));
  };

  const [announcementForm, setAnnouncementForm] = useState({
    title: '',
    content: '',
    displayMode: 'banner',
    scheduleDate: '',
  });

  const [admins, setAdmins] = useState([
    { id: 'adm_1', name: '系統管理員', email: 'admin@certimate.com', role: 'Super Admin', joined: '2025-12-01' },
    { id: 'adm_2', name: '營運專員', email: 'ops@certimate.com', role: 'Admin', joined: '2026-01-10' },
  ]);

  const handleAddAdmin = async () => {
    const email = prompt('請輸入新管理員的 Email:');
    if (!email) return;

    const newAdmin = {
      id: `adm_${Date.now()}`,
      name: '新管理員',
      email,
      role: 'Admin',
      joined: new Date().toISOString().split('T')[0]
    };

    setAdmins([...admins, newAdmin]);
    await logAdminAction(
      AdminAction.CREATE_ADMIN,
      newAdmin.id,
      `新增了管理員帳號: ${email}`
    );
  };

  const handleDeleteAdmin = async (id: string, email: string) => {
    if (!confirm(`確定要刪除管理員 ${email} 嗎？`)) return;

    setAdmins(admins.filter(a => a.id !== id));
    await logAdminAction(
      AdminAction.DELETE_ADMIN,
      id,
      `刪除了管理員帳號: ${email}`
    );
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">系統設定</h1>
          <p className="text-slate-500">免改 code 即時調整系統行為參數與權限</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center gap-2">
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
                        <select className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>gemini-1.5-flash</option>
                          <option>llama-3-8b</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">備援模型 (Fallback)</label>
                        <select className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
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
                        <select className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>claude-3.5-sonnet</option>
                          <option>gpt-4o</option>
                          <option>gemini-1.5-pro</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">備援模型 (Fallback)</label>
                        <select className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                          <option>gpt-4o</option>
                          <option>claude-3.5-sonnet</option>
                        </select>
                      </div>
                    </div>
                  </section>

                  <section>
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Fallback 觸發條件</h3>
                    <div className="flex items-center gap-4">
                      <div className="flex-1 space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Timeout 閾值 (ms)</label>
                        <input type="number" defaultValue={3000} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all" />
                      </div>
                      <div className="flex-1 space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">重試次數</label>
                        <input type="number" defaultValue={2} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all" />
                      </div>
                    </div>
                  </section>
                </div>
              </div>
            )}

            {activeTab === 'plans' && (
              <div className="p-8 space-y-8">
                <h3 className="text-lg font-bold text-slate-900 mb-6">方案限額調整</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">參數</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Free</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Pro</th>
                        <th className="py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Ultra</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {[
                        { label: '每月上傳文件數', free: 5, pro: 50, ultra: '無限' },
                        { label: '每月考試生成次數', free: 3, pro: 30, ultra: '無限' },
                        { label: 'AI 問答次數/日', free: 10, pro: 100, ultra: '無限' },
                        { label: 'Vision OCR 頁數/月', free: 5, pro: 100, ultra: 500 },
                        { label: '單檔大小上限 (MB)', free: 10, pro: 50, ultra: 200 },
                      ].map((row) => (
                        <tr key={row.label}>
                          <td className="py-4 text-sm font-medium text-slate-700">{row.label}</td>
                          <td className="py-4"><input type="text" defaultValue={row.free} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                          <td className="py-4"><input type="text" defaultValue={row.pro} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                          <td className="py-4"><input type="text" defaultValue={row.ultra} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
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
                      <button className="px-5 py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2">
                        <Plus className="h-4 w-4" /> 建立公告
                      </button>
                    </div>
                  </div>
                </div>

                {/* Existing Announcements */}
                <div>
                  <h3 className="text-lg font-bold text-slate-900 mb-4">已建立公告</h3>
                  <div className="space-y-4">
                    {[
                      { title: '系統維護預告', type: '維護', status: '排程中', date: '2026-03-20' },
                      { title: '新功能：AI 教練 V2 上線', type: '功能', status: '發布中', date: '2026-03-15' },
                      { title: '緊急修復：OCR 辨識問題', type: '警告', status: '已結束', date: '2026-03-12' },
                    ].map((ann) => (
                      <div key={ann.title} className="flex items-center justify-between p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className={cn(
                            "h-10 w-10 rounded-xl flex items-center justify-center",
                            ann.type === '維護' && "bg-blue-50 text-blue-600",
                            ann.type === '功能' && "bg-emerald-50 text-emerald-600",
                            ann.type === '警告' && "bg-rose-50 text-rose-600"
                          )}>
                            <Bell className="h-5 w-5" />
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-900">{ann.title}</p>
                            <p className="text-xs text-slate-500">{ann.type} • {ann.date}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-xs font-medium text-slate-500">{ann.status}</span>
                          <button className="p-2 text-slate-400 hover:text-rose-500 transition-all">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
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
