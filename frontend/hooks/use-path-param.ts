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

export function useResourceIdFromPath(): string {
  return usePathParam(/\/resources\/([^/]+)\/(parsed|candidates)/);
}
