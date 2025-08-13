'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

export default function LoginPage() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(
    () => username.trim().length > 0 && password.trim().length > 0 && !submitting,
    [username, password, submitting]
  );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canSubmit) return;
    setError('');
    setSubmitting(true);
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        const { token } = await res.json();
        localStorage.setItem('token', token);
        router.push('/monitoring');
      } else {
        const { error: msg } = await res.json();
        setError(msg ?? t('login.failed'));
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(t('login.failed'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md px-6">
        <Card className="relative z-10 border border-gray-200 bg-white shadow-[0_12px_40px_rgba(0,0,0,0.08)]">
          <CardContent className="relative px-8 py-10 text-black opacity-100">
            {/* Clear in-card title and subtitle */}
            <div className="mb-6 text-center">
              <h1 className="text-2xl font-semibold tracking-tight text-black opacity-100">
                {t('login.title', 'Login')}
              </h1>
              <p className="mt-2 text-sm text-gray-700">
                {t('login.subtitle', '계정으로 로그인하여 대시보드에 접속하세요.')}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <Label htmlFor="username" className="text-gray-800">
                  {t('login.username')}
                </Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder={t('login.usernamePlaceholder', '아이디 또는 이메일')}
                  autoComplete="username"
                  className="mt-1 bg-white focus:bg-white"
                />
              </div>

              <div>
                <Label htmlFor="password" className="text-gray-800">
                  {t('login.password')}
                </Label>
                <div className="relative mt-1">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder={t('login.passwordPlaceholder', '비밀번호')}
                    autoComplete="current-password"
                    className="pr-10 bg-white focus:bg-white"
                  />
                  <button
                    type="button"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPassword((s) => !s)}
                    className="absolute inset-y-0 right-2 my-auto h-8 w-8 rounded-md text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-accent"
                  >
                    {showPassword ? (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
                        <path d="M3 3l18 18" />
                        <path d="M10.58 10.58a2 2 0 102.83 2.83" />
                        <path d="M16.88 16.88A10.94 10.94 0 0112 18c-5 0-9.27-3.11-11-7 1-2.18 2.62-3.99 4.55-5.2" />
                        <path d="M9.88 5.12A10.94 10.94 0 0112 5c5 0 9.27 3.11 11 7-.58 1.26-1.38 2.4-2.35 3.38" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
                        <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <p role="alert" aria-live="polite" className="text-sm text-red-600">
                  {error}
                </p>
              )}

              <Button
                type="submit"
                disabled={!canSubmit}
                className="mt-2 w-full text-base py-3 !bg-[#1A1F71] !text-white !opacity-100 !border !border-[#1A1F71] hover:!bg-[#005F73] focus:!ring-2 focus:!ring-accent disabled:!opacity-100"
                aria-label={t('login.button', '로그인')}
              >
                {submitting ? (
                  <span className="inline-flex items-center justify-center gap-2">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                      <path d="M22 12a10 10 0 00-10-10" />
                    </svg>
                    {t('login.button', '로그인')}
                  </span>
                ) : (
                  t('login.button', '로그인')
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
        {/* Secondary meta */}
        <p className="mt-6 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} KSEB Factory PdM
        </p>
      </div>
    </div>
  );
}
