'use client';

import { useState, useEffect } from 'react';
import { X, Bell, AlertTriangle, Wrench, Sparkles, Info } from 'lucide-react';
import { announcementService } from '@/lib/api/services';

interface Announcement {
  id: string;
  title: string;
  content: string;
  type: string;
  display_mode: string;
}

const typeConfig: Record<string, { icon: typeof Info; bg: string; border: string; text: string; iconColor: string }> = {
  info: { icon: Info, bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', iconColor: 'text-blue-500' },
  warning: { icon: AlertTriangle, bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800', iconColor: 'text-amber-500' },
  maintenance: { icon: Wrench, bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', iconColor: 'text-orange-500' },
  feature: { icon: Sparkles, bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-800', iconColor: 'text-emerald-500' },
};

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
