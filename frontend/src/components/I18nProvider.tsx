'use client';
import { ReactNode, useEffect, useState } from 'react';
import { I18nextProvider } from 'react-i18next';

export default function I18nProvider({ children }: { children: ReactNode }) {
  const [i18n, setI18n] = useState<unknown>(null);

  useEffect(() => {
    // 클라이언트 사이드에서만 i18n 로드
    import('../i18n').then((module) => {
      setI18n(module.default);
    });
  }, []);

  if (!i18n) {
    return <div>Loading...</div>;
  }

  return <I18nextProvider i18n={i18n as unknown as any}>{children}</I18nextProvider>;
}
