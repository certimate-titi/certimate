/**
 * @file 共同備考夥伴 banner——展示同科目其他學員的鼓勵性訊息。
 */
'use client';

import { useEffect, useState } from 'react';
import { Users } from 'lucide-react';
import { communityService, type CommunityBanner } from '@/lib/api/services';

/**
 * 共同備考夥伴 banner。
 *
 * 從 `communityService.getDashboard()` 取出 `banner` 訊息渲染；無資料時不顯示。
 */
export default function StudyBuddyBanner() {
  const [banner, setBanner] = useState<CommunityBanner | null>(null);

  useEffect(() => {
    communityService
      .getDashboard()
      .then(res => setBanner(res?.banner ?? null))
      .catch(() => setBanner(null));
  }, []);

  if (!banner) return null;

  return (
    <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border-b border-violet-200 px-4 py-3">
      <div className="container mx-auto max-w-6xl flex items-center gap-3">
        <Users className="w-5 h-5 text-violet-600" />
        <span className="text-sm font-bold text-violet-900">共同備考夥伴</span>
        <span className="text-sm text-violet-800">{banner.message}</span>
      </div>
    </div>
  );
}
