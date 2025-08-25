'use client';

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import DashboardLayout from '@/components/DashboardLayout';
import ThemeToggle from '@/components/ThemeToggle';
import HighContrastToggle from '@/components/HighContrastToggle';
import FontSizeSelector from '@/components/FontSizeSelector';
import pkg from '../../../package.json';

// light-weight ui primitives available in this repo
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// icons (lucide-react already installed in your project)
import {
  UserCircle2,
  Bell,
  ShieldCheck,
  SlidersHorizontal,
  Wrench,
  Info,
  Search as SearchIcon,
  KeyRound,
  Copy as CopyIcon,
  XCircle,
  CheckCircle2,
  type LucideIcon
} from 'lucide-react';

type Section =
  | 'profile'
  | 'notifications'
  | 'security'
  | 'preferences'
  | 'advanced'
  | 'about';

export default function SettingsPage() {
  const { t } = useTranslation('common');

  // ---------------------------
  // Section meta (with icons)
  // ---------------------------
  const sections = useMemo(
    () => [
      { id: 'profile', label: t('settings.sections.profile'), icon: UserCircle2 },
      { id: 'notifications', label: t('settings.sections.notifications'), icon: Bell },
      { id: 'security', label: t('settings.sections.security'), icon: ShieldCheck },
      { id: 'preferences', label: t('settings.sections.preferences'), icon: SlidersHorizontal },
      { id: 'advanced', label: t('settings.sections.advanced'), icon: Wrench },
      { id: 'about', label: t('settings.sections.about'), icon: Info },
    ],
    [t]
  ) as { id: Section; label: string; icon: LucideIcon }[];

  const [active, setActive] = useState<Section>('profile');

  // search jumps to section by label match
  const [search, setSearch] = useState('');
  useEffect(() => {
    if (!search) return;
    const match = sections.find((s) =>
      (s.label ?? '').toLowerCase().includes(search.toLowerCase())
    );
    if (match) setActive(match.id);
  }, [search, sections]);

  // ---------------------------
  // State
  // ---------------------------
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

  // derive dirty-state to enable/disable Save
  const [initialSnapshot, setInitialSnapshot] = useState<string>('');
  const snapshot = JSON.stringify({
    profile: { name, email, password },
    notifications,
    frequency,
    twoFactor,
    sessions,
    language,
    beta,
    apiKey,
  });
  const dirty = snapshot !== initialSnapshot;

  // ---------------------------
  // Load from localStorage once
  // ---------------------------
  useEffect(() => {
    try {
      const profile = localStorage.getItem('profile');
      if (profile) {
        const p = JSON.parse(profile);
        setName(p?.name ?? '');
        setEmail(p?.email ?? '');
        setPassword(p?.password ?? '');
      }
    } catch {}

    try {
      const notif = localStorage.getItem('notifications');
      if (notif) setNotifications(JSON.parse(notif));
    } catch {}

    const freq = localStorage.getItem('notificationFrequency') as
      | 'daily'
      | 'weekly'
      | 'monthly'
      | null;
    if (freq) setFrequency(freq);

    const two = localStorage.getItem('twoFactor');
    if (two) {
      try { setTwoFactor(JSON.parse(two)); } catch {}
    }

    const sess = localStorage.getItem('sessions');
    if (sess) {
      try { setSessions(JSON.parse(sess)); } catch {}
    } else {
      setSessions(['Chrome on Windows']);
    }

    const lang = localStorage.getItem('language') as 'en' | 'ko' | null;
    if (lang) setLanguage(lang);

    const betaStored = localStorage.getItem('beta');
    if (betaStored) {
      try { setBeta(JSON.parse(betaStored)); } catch {}
    }

    const storedKey = localStorage.getItem('apiKey');
    if (storedKey) setApiKey(storedKey);
    else setApiKey(Math.random().toString(36).slice(2, 10));
  }, []);

  // take initial snapshot after first render with loaded values
  useEffect(() => {
    // Only set a baseline snapshot when we actually have some data (first mount)
    if (!initialSnapshot) setInitialSnapshot(snapshot);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snapshot]);

  // ---------------------------
  // Actions (keep behavior)
  // ---------------------------
  const saveSettings = () => {
    localStorage.setItem('profile', JSON.stringify({ name, email, password }));
    localStorage.setItem('notifications', JSON.stringify(notifications));
    localStorage.setItem('notificationFrequency', frequency);
    localStorage.setItem('twoFactor', JSON.stringify(twoFactor));
    localStorage.setItem('sessions', JSON.stringify(sessions));
    localStorage.setItem('language', language);
    localStorage.setItem('beta', JSON.stringify(beta));
    localStorage.setItem('apiKey', apiKey);

    setInitialSnapshot(snapshot);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
    setApiKey(Math.random().toString(36).slice(2, 10));
  };

  const regenerateApiKey = () => {
    const key = Math.random().toString(36).slice(2, 10);
    setApiKey(key);
  };

  const logoutSession = (idx: number) => {
    setSessions(sessions.filter((_, i) => i !== idx));
  };

  const copyApiKey = async () => {
    try {
      await navigator.clipboard?.writeText(apiKey);
      setSaved(true);
      setTimeout(() => setSaved(false), 1200);
    } catch {}
  };

  // ---------------------------
  // UI
  // ---------------------------
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto w-full p-6">
        {/* Page header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold leading-tight">
              {t('settings.title', { defaultValue: 'Settings' })}
            </h1>
            <p className="text-sm text-gray-500">
              {t('settings.subtitle', {
                defaultValue: 'Manage your account, notifications, security and preferences.',
              })}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              className="border border-blue-500 bg-transparent text-blue-500 hover:bg-blue-50"
              onClick={resetSettings}
              type="button"
            >
              {t('settings.reset')}
            </Button>
            <Button
              onClick={saveSettings}
              type="button"
              disabled={!dirty}
              className={!dirty ? 'opacity-50 cursor-not-allowed' : ''}
            >
              {t('settings.save')}
            </Button>
          </div>
        </div>

        {/* success banner */}
        {saved && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-700">
            <CheckCircle2 className="h-4 w-4" />
            <span>{t('settings.saved', { defaultValue: 'Saved.' })}</span>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* Left: sticky nav */}
          <aside className="col-span-12 md:col-span-4 lg:col-span-3">
            <div className="sticky top-6 space-y-3">
              <div className="relative">
                <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder={t('settings.search', { defaultValue: 'Search settings…' }) as string}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
                {search && (
                  <button
                    type="button"
                    onClick={() => setSearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    aria-label="Clear"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                )}
              </div>

              <nav className="rounded-2xl border border-gray-200 bg-white p-2 shadow-sm">
                {sections.map(({ id, label, icon: Icon }) => {
                  const isActive = active === id;
                  return (
                    <button
                      key={id}
                      type="button"
                      onClick={() => setActive(id)}
                      className={[
                        'w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm',
                        isActive
                          ? 'bg-blue-500 text-white'
                          : 'hover:bg-gray-50 text-gray-700',
                      ].join(' ')}
                    >
                      <Icon className="h-4 w-4" />
                      <span className="truncate">{label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* Right: content */}
          <section className="col-span-12 md:col-span-8 lg:col-span-9 space-y-6">
            {active === 'profile' && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('settings.sections.profile')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name" className="text-[#6B6B6E]">
                        {t('settings.profile.name')}
                      </Label>
                      <Input
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder={t('settings.profile.name') as string}
                      />
                    </div>
                    <div>
                      <Label htmlFor="email" className="text-[#6B6B6E]">
                        {t('settings.profile.email')}
                      </Label>
                      <Input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="name@company.com"
                        autoComplete="email"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor="password" className="text-[#6B6B6E]">
                        {t('settings.profile.password')}
                      </Label>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        autoComplete="new-password"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        {t('settings.profile.password_hint', {
                          defaultValue: 'Use 8+ characters with a mix of letters and numbers.',
                        })}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {active === 'notifications' && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('settings.sections.notifications')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div className="text-sm">
                        <div className="font-medium">{t('settings.notifications.email')}</div>
                        <div className="text-gray-500">
                          {t('settings.notifications.email_desc', { defaultValue: 'Receive alerts by email.' })}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={notifications.email}
                        onChange={(e) => setNotifications({ ...notifications, email: e.target.checked })}
                      />
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div className="text-sm">
                        <div className="font-medium">{t('settings.notifications.sms')}</div>
                        <div className="text-gray-500">
                          {t('settings.notifications.sms_desc', { defaultValue: 'Receive SMS updates.' })}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={notifications.sms}
                        onChange={(e) => setNotifications({ ...notifications, sms: e.target.checked })}
                      />
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div className="text-sm">
                        <div className="font-medium">{t('settings.notifications.push')}</div>
                        <div className="text-gray-500">
                          {t('settings.notifications.push_desc', { defaultValue: 'Show push notifications.' })}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={notifications.push}
                        onChange={(e) => setNotifications({ ...notifications, push: e.target.checked })}
                      />
                    </div>

                    <div>
                      <Label htmlFor="frequency" className="text-[#6B6B6E]">
                        {t('settings.notifications.frequency')}
                      </Label>
                      <select
                        id="frequency"
                        value={frequency}
                        onChange={(e) => setFrequency(e.target.value as 'daily' | 'weekly' | 'monthly')}
                        className="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2"
                      >
                        <option value="daily">{t('settings.notifications.daily', { defaultValue: 'Daily' })}</option>
                        <option value="weekly">{t('settings.notifications.weekly', { defaultValue: 'Weekly' })}</option>
                        <option value="monthly">{t('settings.notifications.monthly', { defaultValue: 'Monthly' })}</option>
                      </select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {active === 'security' && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('settings.sections.security')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div className="text-sm">
                        <div className="font-medium">{t('settings.security.twoFactor')}</div>
                        <div className="text-gray-500">
                          {t('settings.security.twoFactor_desc', { defaultValue: 'Add an extra layer of security to your account.' })}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={twoFactor}
                        onChange={(e) => setTwoFactor(e.target.checked)}
                      />
                    </div>

                    <div>
                      <div className="mb-2 text-sm font-medium">{t('settings.security.sessions')}</div>
                      <ul className="space-y-2">
                        {sessions.map((s, i) => (
                          <li key={s} className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2">
                            <span className="truncate">{s}</span>
                            <Button
                              type="button"
                              className="bg-white text-red-600 border border-red-200 hover:bg-red-50"
                              onClick={() => logoutSession(i)}
                            >
                              {t('settings.security.logout')}
                            </Button>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Button type="button">{t('settings.security.download')}</Button>
                      <Button type="button">{t('settings.security.delete')}</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {active === 'preferences' && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('settings.sections.preferences')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center gap-4">
                      <ThemeToggle />
                      <HighContrastToggle />
                      <FontSizeSelector />
                    </div>

                    <div>
                      <Label htmlFor="language" className="text-[#6B6B6E]">
                        {t('settings.preferences.language')}
                      </Label>
                      <select
                        id="language"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value as 'en' | 'ko')}
                        className="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2"
                      >
                        <option value="en">English</option>
                        <option value="ko">한국어</option>
                      </select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {active === 'advanced' && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('settings.sections.advanced')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div className="text-sm">
                        <div className="font-medium">{t('settings.advanced.beta')}</div>
                        <div className="text-gray-500">
                          {t('settings.advanced.beta_desc', { defaultValue: 'Try experimental features.' })}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={beta}
                        onChange={(e) => setBeta(e.target.checked)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="apiKey" className="text-[#6B6B6E] flex items-center gap-2">
                        <KeyRound className="h-4 w-4" />
                        {t('settings.advanced.apiKey')}
                      </Label>
                      <div className="mt-1 flex gap-2">
                        <Input id="apiKey" value={apiKey} readOnly className="flex-1" />
                        <Button
                          type="button"
                          className="bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 flex items-center gap-1"
                          onClick={copyApiKey}
                          title={t('settings.advanced.copy', { defaultValue: 'Copy' }) as string}
                        >
                          <CopyIcon className="h-4 w-4" />
                          {t('settings.advanced.copy', { defaultValue: 'Copy' })}
                        </Button>
                        <Button type="button" onClick={regenerateApiKey}>
                          {t('settings.advanced.regenerate')}
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {active === 'about' && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('settings.sections.about')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-gray-700">
                    {t('settings.about.version')} {pkg.version}
                  </div>
                </CardContent>
              </Card>
            )}
          </section>
        </div>
      </div>
    </DashboardLayout>
  );
}

