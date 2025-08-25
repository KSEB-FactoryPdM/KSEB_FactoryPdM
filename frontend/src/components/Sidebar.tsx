'use client';

import Link from 'next/link';
import type { Route } from 'next';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  HomeIcon,
  ExclamationCircleIcon,
  CogIcon,
  ClipboardDocumentListIcon,
  ArrowLeftOnRectangleIcon,
  QuestionMarkCircleIcon,
  ExclamationTriangleIcon,
  Cog8ToothIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
} from '@heroicons/react/24/outline';

import { Phone } from 'lucide-react';


const navItems = [
  { href: '/monitoring' as Route, label: 'nav.dashboard', icon: HomeIcon },
  { href: '/anomalies' as Route, label: 'nav.anomalies', icon: ExclamationCircleIcon },
  { href: '/alerts' as Route, label: 'nav.alerts', icon: ExclamationTriangleIcon },
  { href: '/maintenance' as Route, label: 'nav.maintenance', icon: CogIcon },
  { href: '/equipment' as Route, label: 'nav.equipment', icon: ClipboardDocumentListIcon },
  { href: '/fts' as Route, label: 'nav.call', icon: Phone },
  { href: '/settings' as Route, label: 'nav.settings', icon: Cog8ToothIcon },
  { href: '/help' as Route, label: 'nav.help', icon: QuestionMarkCircleIcon },

];

export default function Sidebar() {
  const pathname = usePathname() ?? '';
  const router = useRouter();
  const itemRefs = useRef<(HTMLAnchorElement | null)[]>([]);
  const { t } = useTranslation('common');
  const [collapsed, setCollapsed] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    const currentIndex = itemRefs.current.findIndex(el => el === document.activeElement);
    const delta = e.key === 'ArrowDown' ? 1 : -1;
    const nextIndex = (currentIndex + delta + itemRefs.current.length) % itemRefs.current.length;
    itemRefs.current[nextIndex]?.focus();
  };

  return (
    <aside
      className={`flex flex-col ${collapsed ? 'w-20' : 'w-60'} bg-black text-white shadow-lg h-screen`}
      role="navigation"
      aria-label={t('nav.sidebarLabel')}
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {/* Logo / Brand */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-800">
        <div className="flex items-center">
          <Image src="/logo.svg" alt="Factory PdM" width={32} height={32} />
          {!collapsed && (
            <span className="ml-2 text-xl font-bold select-none">Factory PdM</span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          aria-label="Toggle sidebar"
          className="p-1 rounded hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-accent"
        >
          {collapsed ? (
            <ChevronRightIcon className="w-5 h-5" />
          ) : (
            <ChevronLeftIcon className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className={`flex-1 overflow-y-auto ${collapsed ? 'px-1' : 'px-2'} py-4 space-y-1`}>
        {navItems.map(({ href, label, icon: Icon }, index) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              ref={el => {
                itemRefs.current[index] = el;
              }}
              className={`group flex items-center gap-3 h-12 px-3 rounded-lg text-sm transition focus:outline-none focus:ring-2 focus:ring-accent ${
                active ? 'bg-gray-800 font-semibold' : 'hover:bg-gray-800'
              }`}
              aria-current={active ? 'page' : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
              <span className={`${collapsed ? 'hidden' : 'flex-1'}`}>{t(label)}</span>
              {active && <span className="h-2 w-2 bg-accent rounded-full" />}
            </Link>
          );
        })}
      </nav>

      {/* Logout Button */}
      <div className="px-4 py-4 border-t border-gray-800">
        <motion.button
          onClick={() => {
            if (typeof window !== 'undefined') {
              localStorage.removeItem('token');
              localStorage.removeItem('username');
              // Optionally show confirmation toast
              window.alert('Logged out');
            }
            router.push('/login');
          }}
          className="group w-full flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-400"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <ArrowLeftOnRectangleIcon className="w-5 h-5" aria-hidden="true" />
          {!collapsed && <span>{t('nav.logout')}</span>}
        </motion.button>
      </div>
    </aside>
);
}
