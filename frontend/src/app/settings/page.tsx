'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import DashboardLayout from '@/components/DashboardLayout';
import HighContrastToggle from '@/components/HighContrastToggle';
import FontSizeSelector from '@/components/FontSizeSelector';
import pkg from '../../../package.json';

type Section =
  | 'profile'
  | 'notifications'
  | 'security'
  | 'preferences'
  | 'advanced'
  | 'about';

export default function SettingsPage() {
  const { t } = useTranslation('common');
  const sections = [
    { id: 'profile', label: t('settings.sections.profile') },
    { id: 'notifications', label: t('settings.sections.notifications') },
    { id: 'security', label: t('settings.sections.security') },
    { id: 'preferences', label: t('settings.sections.preferences') },
    { id: 'advanced', label: t('settings.sections.advanced') },
    { id: 'about', label: t('settings.sections.about') },
  ];

  const [active, setActive] = useState<Section>('profile');
  const [search, setSearch] = useState('');
  useEffect(() => {
    if (search) {
      const match = sections.find((s) =>
        s.label.toLowerCase().includes(search.toLowerCase())
      );
      if (match) setActive(match.id as Section);
    }
  }, [search]);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [notifications, setNotifications] = useState({
    email: false,
    sms: false,
    push: false,
  });
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [twoFactor, setTwoFactor] = useState(false);
  const [sessions, setSessions] = useState<string[]>([]);
  const [language, setLanguage] = useState<'en' | 'ko'>('en');
  const [beta, setBeta] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const profile = localStorage.getItem('profile');
    if (profile) {
      try {
        const p = JSON.parse(profile);
        setName(p.name || '');
        setEmail(p.email || '');
        setPassword(p.password || '');
      } catch {}
    }
    const notif = localStorage.getItem('notifications');
    if (notif) {
      try {
        setNotifications(JSON.parse(notif));
      } catch {}
    }
    const freq = localStorage.getItem('notificationFrequency');
    if (freq === 'daily' || freq === 'weekly' || freq === 'monthly') {
      setFrequency(freq);
    }
    const two = localStorage.getItem('twoFactor');
    if (two) setTwoFactor(JSON.parse(two));
    const sess = localStorage.getItem('sessions');
    if (sess) {
      try {
        setSessions(JSON.parse(sess));
      } catch {}
    } else {
      setSessions(['Chrome on Windows']);
    }
    const lang = localStorage.getItem('language') as 'en' | 'ko' | null;
    if (lang) setLanguage(lang);
    const betaStored = localStorage.getItem('beta');
    if (betaStored) setBeta(JSON.parse(betaStored));
    const storedKey = localStorage.getItem('apiKey');
    if (storedKey) setApiKey(storedKey);
    else setApiKey(Math.random().toString(36).slice(2, 10));
  }, []);

  const saveSettings = () => {
    localStorage.setItem('profile', JSON.stringify({ name, email, password }));
    localStorage.setItem('notifications', JSON.stringify(notifications));
    localStorage.setItem('notificationFrequency', frequency);
    localStorage.setItem('twoFactor', JSON.stringify(twoFactor));
    localStorage.setItem('sessions', JSON.stringify(sessions));
    localStorage.setItem('language', language);
    localStorage.setItem('beta', JSON.stringify(beta));
    localStorage.setItem('apiKey', apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const regenerateApiKey = () => {
    const key = Math.random().toString(36).slice(2, 10);
    setApiKey(key);
  };

  const resetSettings = () => {
    setName('');
    setEmail('');
    setPassword('');
    setNotifications({ email: false, sms: false, push: false });
    setFrequency('daily');
    setTwoFactor(false);
    setSessions(['Chrome on Windows']);
    setLanguage('en');
    setBeta(false);
    const key = Math.random().toString(36).slice(2, 10);
    setApiKey(key);
    localStorage.removeItem('profile');
    localStorage.removeItem('notifications');
    localStorage.removeItem('notificationFrequency');
    localStorage.removeItem('twoFactor');
    localStorage.removeItem('sessions');
    localStorage.removeItem('language');
    localStorage.removeItem('beta');
    localStorage.removeItem('apiKey');
    setSaved(false);
  };
  const logoutSession = (idx: number) => {
    setSessions(sessions.filter((_, i) => i !== idx));
  };

  return (
    <DashboardLayout>
      <div className="md:flex gap-6">
        <aside className="md:w-1/4 mb-4 md:mb-0 md:pr-4 md:border-r md:border-[#D1D1D1]">
          <input
            className="w-full p-2 mb-4 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
            placeholder={t('settings.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <ul className="divide-y divide-[#D1D1D1]">
            {sections.map((sec) => (
              <li key={sec.id}>
                <button
                  onClick={() => setActive(sec.id as Section)}
                  className={`w-full text-left p-2 ${
                    active === sec.id
                      ? 'bg-[#F7F7F7] text-primary font-semibold'
                      : 'text-[#1C1C1E] hover:bg-[#F7F7F7]'
                  }`}
                >
                  {sec.label}
                </button>
              </li>
            ))}
          </ul>
        </aside>
        <div className="flex-1 space-y-6">
          {saved && <p className="text-green-600">{t('settings.saved')}</p>}

          {active === 'profile' && (
            <section className="divide-y divide-[#D1D1D1]">
              <div className="py-4 first:pt-0">
                <label htmlFor="name" className="block text-sm text-[#6B6B6E]">
                  {t('settings.profile.name')}
                </label>
                <input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t('settings.profile.name')}
                  className="w-full p-2 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
                />
              </div>
              <div className="py-4">
                <label htmlFor="email" className="block text-sm text-[#6B6B6E]">
                  {t('settings.profile.email')}
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('settings.profile.email')}
                  className="w-full p-2 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
                />
              </div>
              <div className="py-4">
                <label htmlFor="password" className="block text-sm text-[#6B6B6E]">
                  {t('settings.profile.password')}
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('settings.profile.password')}
                  className="w-full p-2 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
                />
              </div>
              <div className="py-4">
                <span className="block text-sm text-[#6B6B6E]">
                  {t('settings.profile.sns')}
                </span>
                <div className="flex gap-2 mt-1">
                  <button className="px-3 py-1 bg-primary text-white rounded">
                    {t('settings.profile.link')}
                  </button>
                  <button className="px-3 py-1 bg-primary text-white rounded">
                    {t('settings.profile.unlink')}
                  </button>
                </div>
              </div>
            </section>
          )}

          {active === 'notifications' && (
            <section className="divide-y divide-[#D1D1D1]">
              <div className="flex items-center gap-2 py-4 first:pt-0">
                <input
                  type="checkbox"
                  checked={notifications.email}
                  onChange={(e) =>
                    setNotifications({ ...notifications, email: e.target.checked })
                  }
                />
                <span>{t('settings.notifications.email')}</span>
              </div>
              <div className="flex items-center gap-2 py-4">
                <input
                  type="checkbox"
                  checked={notifications.sms}
                  onChange={(e) =>
                    setNotifications({ ...notifications, sms: e.target.checked })
                  }
                />
                <span>{t('settings.notifications.sms')}</span>
              </div>
              <div className="flex items-center gap-2 py-4">
                <input
                  type="checkbox"
                  checked={notifications.push}
                  onChange={(e) =>
                    setNotifications({ ...notifications, push: e.target.checked })
                  }
                />
                <span>{t('settings.notifications.push')}</span>
              </div>
              <div className="py-4">
                <label htmlFor="frequency" className="block text-sm text-[#6B6B6E]">
                  {t('settings.notifications.frequency')}
                </label>
                <select
                  id="frequency"
                  value={frequency}
                  onChange={(e) =>
                    setFrequency(e.target.value as 'daily' | 'weekly' | 'monthly')
                  }
                  className="w-full p-2 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
                >
                  <option value="daily">{t('settings.notifications.daily')}</option>
                  <option value="weekly">{t('settings.notifications.weekly')}</option>
                  <option value="monthly">{t('settings.notifications.monthly')}</option>
                </select>
              </div>
            </section>
          )}

          {active === 'security' && (
            <section className="divide-y divide-[#D1D1D1]">
              <div className="flex items-center gap-2 py-4 first:pt-0">
                <input
                  type="checkbox"
                  checked={twoFactor}
                  onChange={(e) => setTwoFactor(e.target.checked)}
                />
                <span>{t('settings.security.twoFactor')}</span>
              </div>
              <div className="py-4">
                <p className="text-sm text-[#6B6B6E]">
                  {t('settings.security.sessions')}
                </p>
                <ul className="mt-2 space-y-1">
                  {sessions.map((s, i) => (
                    <li
                      key={s}
                      className="flex justify-between items-center bg-[#F7F7F7] p-2 rounded"
                    >
                      <span>{s}</span>
                      <button
                        onClick={() => logoutSession(i)}
                        className="text-sm text-primary"
                      >
                        {t('settings.security.logout')}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex gap-2 py-4">
                <button className="px-3 py-1 bg-primary text-white rounded">
                  {t('settings.security.download')}
                </button>
                <button className="px-3 py-1 bg-primary text-white rounded">
                  {t('settings.security.delete')}
                </button>
              </div>
            </section>
          )}

          {active === 'preferences' && (
            <section className="divide-y divide-[#D1D1D1]">
              <div className="flex items-center gap-2 py-4 first:pt-0">
                <HighContrastToggle />
                <FontSizeSelector />
              </div>
              <div className="py-4">
                <label htmlFor="language" className="block text-sm text-[#6B6B6E]">
                  {t('settings.preferences.language')}
                </label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as 'en' | 'ko')}
                  className="w-full p-2 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
                >
                  <option value="en">English</option>
                  <option value="ko">한국어</option>
                </select>
              </div>
            </section>
          )}

          {active === 'advanced' && (
            <section className="divide-y divide-[#D1D1D1]">
              <div className="flex items-center gap-2 py-4 first:pt-0">
                <input
                  type="checkbox"
                  checked={beta}
                  onChange={(e) => setBeta(e.target.checked)}
                />
                <span>{t('settings.advanced.beta')}</span>
              </div>
              <div className="py-4">
                <label htmlFor="apiKey" className="block text-sm text-[#6B6B6E]">
                  {t('settings.advanced.apiKey')}
                </label>
                <div className="flex gap-2">
                  <input
                    id="apiKey"
                    value={apiKey}
                    readOnly
                    className="flex-1 p-2 rounded border border-[#D1D1D1] bg-[#F7F7F7]"
                  />
                  <button
                    onClick={regenerateApiKey}
                    className="px-3 py-1 bg-primary text-white rounded"
                  >
                    {t('settings.advanced.regenerate')}
                  </button>
                </div>
              </div>
            </section>
          )}

          {active === 'about' && (
            <section className="py-4 border-t border-b border-[#D1D1D1]">
              <p>
                {t('settings.about.version')} {pkg.version}
              </p>
            </section>
          )}

          <div className="flex gap-2">
            <button
              onClick={resetSettings}
              className="px-4 py-2 border border-primary text-primary rounded"
              type="button"
            >
              {t('settings.reset')}
            </button>
            <button
              onClick={saveSettings}
              className="px-4 py-2 bg-primary text-white rounded"
              type="button"
            >
              {t('settings.save')}
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

