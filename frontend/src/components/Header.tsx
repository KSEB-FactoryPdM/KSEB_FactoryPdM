'use client';
import {
  BellIcon,
  UserCircleIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useEffect, useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import LanguageSwitcher from './LanguageSwitcher';
import LogoutButton from './LogoutButton';
import { useTranslation } from 'react-i18next';

/** 현재 i18n 언어(예: 'ko', 'en-US', 'ja')에 맞춰 날짜/시간을 포맷 */
function formatDateTime(d: Date, locale: string) {
  const month = new Intl.DateTimeFormat(locale, { month: 'long' }).format(d);
  const day = new Intl.DateTimeFormat(locale, { day: 'numeric' }).format(d);
  const weekday = new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(d);

  // 언어별로 자연스러운 표기: ko는 "8월 11일(월)", 그 외는 "August 11 (Mon)"
  const isKo = locale.startsWith('ko');
  const dateText = isKo ? `${month} ${day} (${weekday})` : `${month} ${day} (${weekday})`;

  const timeText = new Intl.DateTimeFormat(locale, {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(d);

  const fullLabel = new Intl.DateTimeFormat(locale, {
    dateStyle: 'full',
    timeStyle: 'medium',
  }).format(d);

  return { dateText, timeText, fullLabel };
}

export default function Header() {
  const { t, i18n } = useTranslation('common');

  const role = useAuthStore((s) => s.role);
  const [username, setUsername] = useState('');
  const [now, setNow] = useState<Date>(new Date());
  const [unread, setUnread] = useState<number>(0);
  const [search, setSearch] = useState('');
  const router = useRouter();

  // i18n에서 현재 적용된 언어(해결된 언어 우선)
  const locale = (i18n as any)?.resolvedLanguage || i18n.language || 'en';

  // 시간(1초마다 업데이트)
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // 알림 미읽음 수
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

  // 사용자명 로딩
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

  const { dateText, timeText, fullLabel } = formatDateTime(now, locale);

  return (
    <header
      role="banner"
      className="
        sticky top-0 z-40
        h-16 flex items-center
        px-4
        bg-white/90 backdrop-blur
        border-b border-neutral-200
        text-neutral-900
      "
    >
      {/* 좌측: 검색창 — 우측 섹션과 충분한 간격 확보 */}
      <div className="flex-1 max-w-xl md:max-w-2xl lg:max-w-3xl pr-2 md:pr-4 mr-6 md:mr-10">
        <form
          className="relative w-full"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            if (search.trim()) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              router.push(`/search?query=${encodeURIComponent(search.trim())}` as any);
            }
          }}
        >
          <MagnifyingGlassIcon
            className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500 pointer-events-none"
            aria-hidden="true"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('header.searchPlaceholder')}
            aria-label={t('header.searchPlaceholder')}
            className="
              w-full
              bg-neutral-50 border border-neutral-200
              rounded-md py-2 pl-10 pr-9
              text-sm text-neutral-900 placeholder:text-neutral-500
              outline-none
              transition
              focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 focus:ring-offset-white
              hover:border-neutral-300
              shadow-[0_0_0_0_rgba(0,0,0,0)]
              focus:shadow-[0_8px_24px_-16px_rgba(0,0,0,0.25)]
            "
          />
          {/* 검색어 지우기 버튼 (입력 시만 표시) */}
          {search && (
            <button
              type="button"
              onClick={() => setSearch('')}
              aria-label={t('header.clearSearch', { defaultValue: '검색어 지우기' })}
              className="
                absolute right-2 top-1/2 -translate-y-1/2
                inline-flex items-center justify-center
                w-6 h-6 rounded
                text-neutral-500 hover:text-neutral-800
                hover:bg-neutral-200/60
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400
                transition
              "
              title={t('header.clearSearch', { defaultValue: '검색어 지우기' })}
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>

      {/* 우측: 시간 칩 + 상태/유틸 */}
      <div className="flex items-center gap-4 lg:gap-5">
        {/* 느낌 있는 시간 칩: 언어별 요일 자동 변경, 숫자 탭룰러, 은은한 그라데이션 */}
        <time
          dateTime={now.toISOString()}
          title={fullLabel}
          aria-label={t('header.datetime', { datetime: fullLabel })}
          className="
            hidden md:inline-flex items-center
            rounded-full border px-3 py-1 text-xs font-medium
            font-mono tabular-nums tracking-tight
            bg-gradient-to-b from-neutral-100 to-neutral-50
            border-neutral-200 text-neutral-700
            shadow-[inset_0_1px_0_0_rgba(255,255,255,0.7)]
          "
        >
          {dateText}
          <span className="mx-1 text-neutral-400">·</span>
          {timeText}
        </time>

        {/* 가느다란 구분선 */}
        <div className="hidden md:block h-5 w-px bg-neutral-300/60" aria-hidden="true" />

        {/* 사용자 정보(중소형 화면에서는 공간 절약) */}
        <span
          className="hidden sm:inline text-sm text-neutral-700"
          aria-label={t('header.userInfo', { username, role })}
          title={t('header.userInfo', { username, role })}
        >
          {t('header.userInfo', { username, role })}
        </span>

        {/* 언어 변경도 툴팁/포커스 스타일로 상호작용 명확화 */}
        <div
          className="
            rounded-md -m-1 p-1 transition
            hover:bg-neutral-100
            focus-within:bg-neutral-100
            focus-within:ring-2 focus-within:ring-neutral-300
          "
          title={t('header.changeLanguage', { defaultValue: '언어 변경' })}
        >
          <LanguageSwitcher />
        </div>

        {/* 알림 아이콘: 호버/포커스 피드백 + 뱃지 */}
        <button
          type="button"
          className="
            relative rounded-md p-1 -m-1
            hover:bg-neutral-100
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400
            transition
          "
          aria-label={t('header.notifications')}
          title={t('header.notifications')}
          // TODO: onClick에 알림 패널 열기 연동 가능
        >
          <BellIcon className="w-6 h-6 text-current" />
          {unread > 0 && (
            <>
              <span className="sr-only">
                {t('header.unreadAlerts', { count: unread })}
              </span>
              <span
                className="
                  absolute -top-0.5 -right-0.5
                  bg-red-600 text-white rounded-full
                  text-[10px] leading-none px-1 py-[2px]
                  shadow
                  animate-[pulse_2s_infinite]
                "
              >
                {unread}
              </span>
            </>
          )}
        </button>

        {/* 사용자 아이콘 */}
        <div
          className="
            rounded-md p-1 -m-1
            hover:bg-neutral-100
            focus-within:bg-neutral-100
            focus-within:ring-2 focus-within:ring-neutral-300
            transition
          "
          title={t('header.user')}
        >
          <UserCircleIcon className="w-8 h-8 text-current" aria-label={t('header.user')} />
        </div>

        {/* 로그아웃: 호버/포커스 시 배경/테두리/살짝 확대 */}
        <div
          className="
            group rounded-md -m-1 p-1
            transition-all duration-200
            hover:bg-neutral-100 hover:ring-1 hover:ring-neutral-300
            focus-within:bg-neutral-100 focus-within:ring-2 focus-within:ring-neutral-400
            active:scale-[0.98]
          "
          title={t('header.logout', { defaultValue: '로그아웃' })}
        >
          {/* LogoutButton이 자체 버튼을 렌더한다고 가정.
              외곽 래퍼에 호버/포커스 스타일을 주어 시각 변화 제공 */}
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}
