/**
 * 前端建置版本資訊。
 *
 * `NEXT_PUBLIC_BUILD_COMMIT` 與 `NEXT_PUBLIC_BUILD_TIME`
 * 由 CI（GitHub Actions）在 build 時注入；本地開發回退為 `'dev'`。
 */

/**
 * 前端版本元資料；通常顯示於 footer / about 頁。
 *
 * @property version - 語意化版本號（手動維護於本檔案）
 * @property commit - Git commit short hash；CI 注入，否則 `'dev'`
 * @property buildTime - ISO 時間字串；CI 注入，否則 `'dev'`
 */
export const BUILD_INFO = {
  version: '0.3.1',
  commit: process.env.NEXT_PUBLIC_BUILD_COMMIT || 'dev',
  buildTime: process.env.NEXT_PUBLIC_BUILD_TIME || 'dev',
};
