/**
 * @file 路由 `/` — 應用程式根 layout。
 *
 * 套用全域字型（Inter）、全域樣式、Google OAuth Wrapper、
 * 認證狀態 Provider、全站 Navbar，並提供 `<main>` 容器給所有子路由。
 */
import type {Metadata, Viewport} from 'next';
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

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  // 不鎖縮放（accessibility 原則）；保留橋接讓 iOS 不會自動放大表單
  themeColor: '#10b981',
};

/**
 * 應用程式根 layout。
 *
 * 包覆所有子路由並提供認證、Google OAuth、全站導覽列等全域 context。
 */
export default function RootLayout({children}: {children: React.ReactNode}) {
  // Dark mode: 在 SSR/SSG 靜態匯出環境中，透過 inline script 在 hydration 前套用 .dark class
  // 避免 FOUC (Flash of Unstyled Content)
  const darkModeScript = `
    (function(){
      try {
        if(localStorage.getItem('certimate_dark_mode')==='true'){
          document.documentElement.classList.add('dark');
        }
      } catch(e){}
    })();
  `;

  return (
    <html lang="en" className={`${inter.variable} font-sans`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: darkModeScript }} />
      </head>
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
