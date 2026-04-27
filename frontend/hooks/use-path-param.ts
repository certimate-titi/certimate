/**
 * @file 動態路由 param 解析 hook。專為 Next.js 靜態匯出 + Firebase rewrite
 * 場景設計，繞過 `useParams()` 在 stub 路由下回傳字面值的限制。
 */
'use client';

import { useEffect, useState } from 'react';

/**
 * 從 window.location.pathname 以 regex 解析動態路由 param。
 *
 * 為何不用 Next.js useParams？
 * 靜態匯出 (`output: 'export'`) 搭配 Firebase rewrites：`generateStaticParams()` 產出單一 stub 檔，
 * 所有實際 UUID 請求都被 rewrite 到該 stub 的 index.html，`useParams()` 只會讀到 stub 的字面值
 * （例如 "detail"），而非 URL 中的真實 ID。
 *
 * @param pattern - 必須包含一組捕獲（capture group），第 1 組為要回傳的 param。
 * @returns 解析到的 param；尚未掛載或無 match 時為空字串。
 *
 * @example
 * const resourceId = usePathParam(/\/resources\/([^/]+)\/parsed/);
 */
export function usePathParam(pattern: RegExp): string {
  const [value, setValue] = useState('');
  useEffect(() => {
    const m = window.location.pathname.match(pattern);
    if (m && m[1]) setValue(m[1]);
  }, [pattern]);
  return value;
}

/**
 * 從 `/resources/:id/parsed` 或 `/resources/:id/candidates` 路徑取出 resource UUID。
 *
 * `usePathParam` 的便利包裝；專供資源詳情子頁使用。
 *
 * @returns 資源 UUID；尚未掛載或路徑不符時為空字串。
 *
 * @example
 * const resourceId = useResourceIdFromPath();
 */
export function useResourceIdFromPath(): string {
  return usePathParam(/\/resources\/([^/]+)\/(parsed|candidates)/);
}
