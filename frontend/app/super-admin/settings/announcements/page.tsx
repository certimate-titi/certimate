'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Bell } from 'lucide-react';
import { superAdminService } from '@/lib/api/services';

export default function AnnouncementsPage() {
  const [announcementForm, setAnnouncementForm] = useState({ title: '', content: '', displayMode: 'banner', scheduleDate: '' });
  const [announcements, setAnnouncements] = useState<{ id: string; title: string; content: string; display_mode: string; created_at: string; status?: string }[]>([]);

  useEffect(() => {
    superAdminService.getAnnouncements().then(res => {
      if (Array.isArray(res?.announcements)) setAnnouncements(res.announcements);
    }).catch(() => {});
  }, []);

  const handleCreate = async () => {
    if (!announcementForm.title || !announcementForm.content) { alert('請填寫標題和內容'); return; }
    try {
      await superAdminService.createAnnouncement({
        title: announcementForm.title, content: announcementForm.content,
        display_mode: announcementForm.displayMode, schedule_date: announcementForm.scheduleDate || undefined,
      });
      setAnnouncementForm({ title: '', content: '', displayMode: 'banner', scheduleDate: '' });
      const res = await superAdminService.getAnnouncements();
      if (Array.isArray(res?.announcements)) setAnnouncements(res.announcements);
      alert('公告已建立');
    } catch { alert('建立公告失敗'); }
  };

  return (
    <div className="p-8 space-y-8">
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-6">建立系統公告</h3>
        <div className="space-y-4 p-6 bg-slate-50 rounded-2xl border border-slate-100">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">公告標題</label>
            <input type="text" value={announcementForm.title} onChange={e => setAnnouncementForm({ ...announcementForm, title: e.target.value })} placeholder="輸入公告標題..." className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">公告內容</label>
            <textarea value={announcementForm.content} onChange={e => setAnnouncementForm({ ...announcementForm, content: e.target.value })} placeholder="輸入公告內容..." rows={4} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all resize-none" />
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">顯示方式</label>
              <select value={announcementForm.displayMode} onChange={e => setAnnouncementForm({ ...announcementForm, displayMode: e.target.value })} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all">
                <option value="banner">全站橫幅 (Banner)</option>
                <option value="notification">站內通知 (Notification)</option>
                <option value="email">Email 推播</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">排程發布日期</label>
              <input type="date" value={announcementForm.scheduleDate} onChange={e => setAnnouncementForm({ ...announcementForm, scheduleDate: e.target.value })} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-emerald-500 transition-all" />
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <button onClick={handleCreate} className="px-5 py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2">
              <Plus className="h-4 w-4" /> 建立公告
            </button>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4">已建立公告</h3>
        {announcements.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">尚無已建立的公告</div>
        ) : (
          <div className="space-y-3">
            {announcements.map((a) => (
              <div key={a.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <div className="flex justify-between items-start mb-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-bold text-slate-900">{a.title}</p>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 uppercase">{a.display_mode}</span>
                    {a.status === 'inactive' && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-500">已停用</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={async () => { try { await superAdminService.deactivateAnnouncement(a.id); const res = await superAdminService.getAnnouncements(); if (Array.isArray(res?.announcements)) setAnnouncements(res.announcements); } catch { alert('停用失敗'); } }} className="p-1.5 text-slate-400 hover:text-amber-500 hover:bg-amber-50 rounded-lg transition-all" title="停用公告">
                      <Bell className="h-3.5 w-3.5" />
                    </button>
                    <button onClick={async () => { if (!confirm(`確定要刪除公告「${a.title}」嗎？`)) return; try { await superAdminService.deleteAnnouncement(a.id); setAnnouncements(prev => prev.filter(x => x.id !== a.id)); } catch { alert('刪除失敗'); } }} className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all" title="刪除公告">
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
  );
}
