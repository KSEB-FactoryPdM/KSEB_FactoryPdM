import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../public/locales/en/common.json';
import ko from '../public/locales/ko/common.json';
import config from '../next-i18next.config.mjs';

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    resources: {
      en: { common: en },
      ko: { common: ko },
    },
    lng: config.i18n.defaultLocale,
    fallbackLng: config.i18n.defaultLocale,
    interpolation: { escapeValue: false },
  });
}

export default i18n;
