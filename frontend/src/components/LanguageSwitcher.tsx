'use client';
import { useTranslation } from 'react-i18next';

export default function LanguageSwitcher() {
  const { i18n } = useTranslation('common');

  return (
    <select
      className="bg-transparent border border-white rounded px-1 text-sm"
      value={i18n.language}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
    >
      <option value="en">EN</option>
      <option value="ko">KO</option>
    </select>
  );
}
