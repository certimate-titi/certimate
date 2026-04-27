/**
 * @file Navbar 包裝元件——根據當前路徑決定是否渲染主 Navbar。
 */
'use client';

import { usePathname } from 'next/navigation';
import Navbar from './Navbar';

/**
 * Navbar 路徑感知包裝。
 *
 * 在 `/onboarding` 與 `/exam/workspace` 路徑隱藏 Navbar，其餘頁面正常顯示。
 */
export default function NavbarWrapper() {
  const pathname = usePathname();
  if (pathname === '/onboarding' || pathname === '/exam/workspace') return null;
  return <Navbar />;
}
