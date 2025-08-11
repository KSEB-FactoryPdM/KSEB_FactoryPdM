'use client';
import Image from 'next/image';
import { BellIcon, UserCircleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useEffect, useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import ThemeToggle from './ThemeToggle';
import LanguageSwitcher from './LanguageSwitcher';
import LogoutButton from './LogoutButton';
import HighContrastToggle from './HighContrastToggle';
import FontSizeSelector from './FontSizeSelector';

import { useTranslation } from 'react-i18next';


export default function Header() {
  const { t } = useTranslation('common');

  const role = useAuthStore((s) => s.role);
  const [username, setUsername] = useState('');
  const [dateTime, setDateTime] = useState<string>(
    new Date().toLocaleString()
  );
  const [unread, setUnread] = useState<number>(0);
  const [search, setSearch] = useState('');
  const router = useRouter();
  const [isPrimaryLight, setIsPrimaryLight] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setDateTime(new Date().toLocaleString());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function updateTextColor() {
      const raw = getComputedStyle(document.documentElement)
        .getPropertyValue('--color-primary')
        .trim();
      const [r, g, b] = raw.split(' ').map(Number);
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      setIsPrimaryLight(brightness > 180);
    }
    updateTextColor();
    const observer = new MutationObserver(updateTextColor);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'style'],
    });
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    mql.addEventListener('change', updateTextColor);
    return () => {
      observer.disconnect();
      mql.removeEventListener('change', updateTextColor);
    };
  }, []);

  useEffect(() => {
    async function fetchUnread() {
      try {
        const res = await fetch('/api/alerts?status=new');
        if (!res.ok) return;
        const data = await res.json();
        const count = Array.isArray(data) ? data.length : data?.count ?? 0;
        setUnread(count);
      } catch (err) {
        console.error('Failed to fetch unread alerts', err);
      }
    }
    fetchUnread();
    const id = setInterval(fetchUnread, 30000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('username');
      if (stored) {
        setUsername(stored);
        return;
      }
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.username) setUsername(payload.username);
        } catch (err) {
          console.error('Failed to parse token', err);
        }
      }
    }
  }, []);

  return (
    <header
      className={`h-16 flex items-center bg-primary px-4 ${isPrimaryLight ? 'text-black' : 'text-white'}`}
    >
      <div className="flex items-center gap-2">
        <Image src="/logo.svg" alt="Factory PMS logo" width={32} height={32} />
        <span className="text-[1.25rem] font-bold font-heading">
          {t('header.title')}
        </span>
      </div>
      <div className="flex-1 px-4">
        <form
          className="relative w-full"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            if (search.trim()) {
              router.push(`/search?query=${encodeURIComponent(search.trim())}`);
            }
          }}
        >
          <MagnifyingGlassIcon
            className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-text-primary"
            aria-hidden="true"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('header.searchPlaceholder')}
            aria-label={t('header.searchPlaceholder')}
            className="w-full bg-input-bg rounded-md py-2 pl-10 text-sm text-black placeholder:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-hover focus:ring-offset-2"
          />
        </form>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm" aria-label={t('header.datetime', { datetime: dateTime })}>
          {t('header.datetime', { datetime: dateTime })}
        </span>
        <span className="text-sm" aria-label={t('header.userInfo', { username, role })}>
          {t('header.userInfo', { username, role })}
        </span>
        <LanguageSwitcher />
        <div className="relative">
          <BellIcon className="w-6 h-6" aria-label={t('header.notifications')} />
          {unread > 0 && (
            <>
              <span className="sr-only">
                {t('header.unreadAlerts', { count: unread })}
              </span>
              <span className="absolute -top-1 -right-1 bg-red-600 text-white rounded-full text-[10px] px-1">
                {unread}
              </span>
            </>
          )}
        </div>
        <UserCircleIcon className="w-8 h-8" aria-label={t('header.user')} />
        <ThemeToggle />
        <HighContrastToggle />
        <FontSizeSelector />
        <LogoutButton />
      </div>
    </header>
  );
}
