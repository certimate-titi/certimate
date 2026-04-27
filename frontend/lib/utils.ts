/**
 * 通用工具函式集合（CSS class 合併等）。
 */

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * 合併多個 Tailwind / CSS class names。
 *
 * 透過 clsx 處理條件式 class 後，再以 tailwind-merge
 * 解決 Tailwind utility class 衝突（後者覆蓋前者）。
 *
 * @param inputs - 要合併的 class 表達式（字串、陣列、物件、布林等）
 * @returns 去重並解衝突後的 class 字串
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
