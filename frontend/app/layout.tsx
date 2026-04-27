/**
 * @file 路由 `/` — 應用程式根 layout。
 *
 * 套用全域字型（Inter）、全域樣式、Google OAuth Wrapper、
 * 認證狀態 Provider、全站 Navbar，並提供 `<main>` 容器給所有子路由。
 */
import type {Metadata} from 'next';
import { Inter } from 'next/font/google';
import './globals.css'; // Global styles
import NavbarWrapper from '@/components/NavbarWrapper';
import { AuthProvider } from '@/lib/auth-context';
import { GoogleOAuthWrapper } from '@/lib/google-oauth-wrapper';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: 'TiTi | AI 賦能證照考試平台',
  description: 'AI 賦能證照考試平台，打破單向學習',
};

/**
 * 應用程式根 layout。
 *
 * 包覆所有子路由並提供認證、Google OAuth、全站導覽列等全域 context。
 */
export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en" className={`${inter.variable} font-sans`}>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased flex flex-col" suppressHydrationWarning>
        <GoogleOAuthWrapper>
          <AuthProvider>
            <NavbarWrapper />
            <main className="flex-1 flex flex-col">
              {children}
            </main>
          </AuthProvider>
        </GoogleOAuthWrapper>
      </body>
    </html>
  );
}
