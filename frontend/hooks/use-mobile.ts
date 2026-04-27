/**
 * @file 行動裝置偵測 hook。以 `window.matchMedia` 訂閱 viewport 寬度，
 * 提供 SSR 安全的布林值供 UI 切換 mobile / desktop 排版。
 */
import * as React from "react"

/** 視為行動裝置的最大寬度（含）以下；單位 px。 */
const MOBILE_BREAKPOINT = 768

/**
 * 偵測當前 viewport 是否屬於行動裝置寬度（< 768px）。
 *
 * 內部以 `matchMedia` 訂閱寬度變化，並在 unmount 時自動移除 listener。
 * 初始 SSR 階段尚未掛載時回傳 `false`，避免 hydration mismatch。
 *
 * @returns `true` 表示當前為行動裝置寬度；否則 `false`。
 *
 * @example
 * const isMobile = useIsMobile();
 * return isMobile ? <MobileNav /> : <DesktopNav />;
 */
export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return !!isMobile
}
