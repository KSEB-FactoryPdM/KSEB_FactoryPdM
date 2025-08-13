// src/app/layout.tsx

import type { Metadata } from 'next';
import { Noto_Sans_KR, Roboto } from 'next/font/google';
import QueryProvider from '@/components/QueryProvider';
import Sidebar from '@/components/Sidebar';
import I18nProvider from '@/components/I18nProvider';
import LanguageListener from '@/components/LanguageListener';
import './globals.css';

const notoSans = Noto_Sans_KR({
  weight: ['400', '700'],
  subsets: ['latin'],
  variable: '--font-noto-sans',
});

const roboto = Roboto({
  weight: ['400', '500', '700'],
  subsets: ['latin'],
  variable: '--font-roboto',
});

export const metadata: Metadata = {
  title: 'Factory PdM Monitoring Dashboard',
  description: 'Real-time dashboard for predictive maintenance data',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body
        className={`${notoSans.variable} ${roboto.variable} antialiased bg-gray-100`}
      >
        <I18nProvider>
          <LanguageListener />
          <QueryProvider>
            <div className="flex h-screen">
              <Sidebar />
              <main className="flex-1 overflow-auto p-6">
                {children}
              </main>
            </div>
          </QueryProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
