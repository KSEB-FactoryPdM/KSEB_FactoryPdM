// src/app/layout.tsx

import type { Metadata } from 'next';
import QueryProvider from '@/components/QueryProvider';
import Sidebar from '@/components/Sidebar';
import I18nProvider from '@/components/I18nProvider';
import LanguageListener from '@/components/LanguageListener';
import './globals.css';

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
