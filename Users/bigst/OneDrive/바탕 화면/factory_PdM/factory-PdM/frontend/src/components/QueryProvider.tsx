// src/components/QueryProvider.tsx
'use client';

import React, { ReactNode, useMemo } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePathname } from 'next/navigation';

interface QueryProviderProps {
  children: ReactNode;
}

export default function QueryProvider({ children }: QueryProviderProps) {
  // Next.js 13+ 에서는 usePathname() 가 null 을 반환할 수 있으니 기본값 '' 처리
  const pathname = usePathname() ?? '';
  const useMock = pathname.includes('/test');

  const client = useMemo(() => {
    return new QueryClient({
      defaultOptions: {
        queries: {
          queryFn: async ({ queryKey }) => {
            // queryKey[0] 을 endpoint 이름으로 사용
            const key = queryKey[0] as string;

            // 테스트 모드이면 public/ 아래 있는 mock-*.json 을 읽어옴
            // - monitoring 호출 시 파일명이 mock-data.json 이므로 별도 처리
            // - 그 외는 mock-<key>.json
            const fileName =
              key === 'monitoring' ? 'data' : key;

            const url = useMock
              ? `/mock-${fileName}.json`
              : `/api/${key}`;

            const res = await fetch(url);
            if (!res.ok) {
              throw new Error(`Fetch failed: ${url}`);
            }
            return res.json();
          },
          staleTime: 5 * 60 * 1000, // 5분
        },
      },
    });
  }, [useMock]);

  return (
    <QueryClientProvider client={client}>
      {children}
    </QueryClientProvider>
  );
}
