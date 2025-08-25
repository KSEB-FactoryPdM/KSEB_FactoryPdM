'use client';
import { useTranslation } from 'react-i18next';

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation('common');

  return (
    <select
      aria-label={t('header.language')}
      className="bg-transparent border border-white rounded px-1 text-sm"
      value={i18n.language}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
    >
      <option value="en">English</option>
      <option value="ko">한국어</option>
    </select>
  );
}
