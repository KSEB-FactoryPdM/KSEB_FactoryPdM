// src/app/layout.tsx

import type { Metadata } from 'next';
import QueryProvider from '@/components/QueryProvider';
import Sidebar from '@/components/Sidebar';
import I18nProvider from '@/components/I18nProvider';
import LanguageListener from '@/components/LanguageListener';
import './globals.css';

// Preload fonts locally to avoid network fetch during build
import '@fontsource/noto-sans-kr/400.css';
import '@fontsource/noto-sans-kr/700.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';

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
      <body className="antialiased bg-gray-100">
        <I18nProvider>
          <LanguageListener />
          <QueryProvider>
            <fieldset disabled className="flex h-screen border-0 p-0 m-0">
              <Sidebar />
              <main className="flex-1 overflow-auto p-6">
                {children}
              </main>
            </fieldset>
          </QueryProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
