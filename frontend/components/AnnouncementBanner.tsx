/**
 * @file 全站系統公告 banner 元件——載入並顯示 display_mode='banner' 的公告。
 */
'use client';

import { useState, useEffect } from 'react';
import { X, Bell, AlertTriangle, Wrench, Sparkles, Info } from 'lucide-react';
import { announcementService } from '@/lib/api/services';

/**
 * 後端公告 API 回應的單一公告結構（snake_case）。
 */
interface Announcement {
  /** 公告 ID */
  id: string;
  /** 公告標題 */
  title: string;
  /** 公告內文 */
  content: string;
  /** 類型：info / warning / maintenance / feature */
  type: string;
  /** 顯示模式：banner / modal / toast 等 */
  display_mode: string;
}

const typeConfig: Record<string, { icon: typeof Info; bg: string; border: string; text: string; iconColor: string }> = {
  info: { icon: Info, bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', iconColor: 'text-blue-500' },
  warning: { icon: AlertTriangle, bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800', iconColor: 'text-amber-500' },
  maintenance: { icon: Wrench, bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', iconColor: 'text-orange-500' },
  feature: { icon: Sparkles, bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-800', iconColor: 'text-emerald-500' },
};

/**
 * 系統公告 banner。
 *
 * 進站時呼叫 `announcementService.getActive()` 取得公告，僅渲染 banner 模式項目；
 * 使用者可逐則關閉，關閉狀態僅保留於 component state（不持久化）。
 */
export default function AnnouncementBanner() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  useEffect(() => {
    announcementService.getActive().then(res => {
      if (Array.isArray(res?.announcements)) {
        // Only show banner-type announcements
        setAnnouncements(res.announcements.filter(a => a.display_mode === 'banner'));
      }
    }).catch(() => {});
  }, []);

  const visible = announcements.filter(a => !dismissed.has(a.id));
  if (visible.length === 0) return null;

  return (
    <div className="space-y-2 mb-4">
      {visible.map(ann => {
        const config = typeConfig[ann.type] || typeConfig.info;
        const Icon = config.icon;
        return (
          <div
            key={ann.id}
            className={`${config.bg} ${config.border} border rounded-xl px-4 py-3 flex items-start gap-3`}
          >
            <Icon className={`h-5 w-5 ${config.iconColor} shrink-0 mt-0.5`} />
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-bold ${config.text}`}>{ann.title}</p>
              <p className={`text-xs ${config.text} opacity-80 mt-0.5`}>{ann.content}</p>
            </div>
            <button
              onClick={() => setDismissed(prev => new Set(prev).add(ann.id))}
              className={`p-1 ${config.text} opacity-50 hover:opacity-100 transition-opacity shrink-0`}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
