'use client';

/**
 * @file CoachQuotaBanner — 顯示本月剩餘蘇格拉底對話次數
 *
 * 僅在 FREE 方案或配額不足時顯示警示；PRO_PLUS+ 不顯示。
 */

import Link from 'next/link';

interface CoachQuotaBannerProps {
  /** 本月已用次數 */
  used: number;
  /** 本月總配額（-1 = 無上限） */
  quota: number;
  /** 是否為配額已滿錯誤（402 回傳） */
  isBlocked?: boolean;
}

export default function CoachQuotaBanner({ used, quota, isBlocked = false }: CoachQuotaBannerProps) {
  if (quota === -1) return null; // 無上限方案不顯示

  const remaining = Math.max(0, quota - used);

  if (isBlocked) {
    return (
      <div className="mx-3 my-2 p-3 rounded-lg bg-amber-50 border border-amber-200 text-center">
        <p className="text-xs font-semibold text-amber-700 mb-1">本月蘇格拉底對話配額已滿</p>
        <p className="text-[11px] text-amber-600 mb-2">
          已使用 {used} / {quota} 次。升級方案解鎖更多次數。
        </p>
        <Link
          href="/account"
          className="inline-flex items-center gap-1 px-3 py-1 bg-violet-500 text-white rounded-lg text-[11px] font-bold hover:bg-violet-600 transition-colors"
        >
          升級方案
        </Link>
      </div>
    );
  }

  if (remaining <= 2) {
    return (
      <div className="mx-3 my-1 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-between">
        <span className="text-[11px] text-amber-700">
          本月蘇格拉底對話剩 <strong>{remaining}</strong> / {quota} 次
        </span>
        <Link href="/account" className="text-[10px] text-violet-600 font-semibold hover:text-violet-700">
          升級
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-3 my-1 px-3 py-1 rounded-lg bg-violet-50 border border-violet-100 flex items-center justify-between">
      <span className="text-[11px] text-violet-600">
        本月剩 {remaining} / {quota} 次蘇格拉底對話
      </span>
    </div>
  );
}
