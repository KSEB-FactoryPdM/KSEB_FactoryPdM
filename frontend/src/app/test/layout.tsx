import React from 'react';
import { Noto_Sans_KR, Roboto } from 'next/font/google';
import MockSidebar from '@/components/Sidebar';
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

export default function TestLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body
        className={`${notoSans.variable} ${roboto.variable} antialiased bg-white flex h-screen`}
      >
        <MockSidebar />

        <main className="flex-1 overflow-auto p-6">
          <div className="mb-6 px-4 py-2 bg-yellow-50 border-l-4 border-yellow-400 text-yellow-700 rounded">
            <strong>테스트 환경:</strong> 모킹 데이터로만 그래프를 렌더링합니다.
          </div>
          {children}
        </main>
      </body>
    </html>
  );
}
