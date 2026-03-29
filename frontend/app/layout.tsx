import type {Metadata} from 'next';
import { Inter } from 'next/font/google';
import './globals.css'; // Global styles
import NavbarWrapper from '@/components/NavbarWrapper';
import { AuthProvider } from '@/lib/auth-context';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: 'TiTi | AI 賦能證照考試平台',
  description: 'AI 賦能證照考試平台，打破單向學習',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en" className={`${inter.variable} font-sans`}>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased flex flex-col" suppressHydrationWarning>
        <AuthProvider>
          <NavbarWrapper />
          <main className="flex-1 flex flex-col">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
