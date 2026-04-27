/**
 * @file 路由 `/super-admin/prompt-templates/[templateId]` — Prompt 範本詳情頁（靜態匯出 stub）。
 *
 * 因 `output: 'export'` 限制，以 `generateStaticParams` 產出 `detail` stub，
 * 並由 Firebase rewrite 將任意 templateId 指向該 stub；UI 在 `client.tsx`。
 */
import PromptTemplateDetailPage from './client';

/** 靜態匯出 stub 參數，產出單一 detail 頁面檔。 */
export function generateStaticParams() {
  return [{ templateId: 'detail' }];
}

/** 靜態匯出包裝：渲染 client.tsx 內的 prompt 範本詳情頁。 */
export default function Page() {
  return <PromptTemplateDetailPage />;
}
