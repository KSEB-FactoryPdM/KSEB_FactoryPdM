'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Route } from 'next';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

export default function SignupPage() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(
    () =>
      username.trim().length > 0 &&
      email.trim().length > 0 &&
      password.trim().length > 0 &&
      confirm.trim().length > 0 &&
      password === confirm &&
      !submitting,
    [username, email, password, confirm, submitting]
  );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canSubmit) return;
    setError('');
    setSubmitting(true);
    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });
      if (res.ok) {
        router.push('/login' as Route);
      } else {
        const { error: msg } = await res.json();
        setError(msg ?? t('signup.failed'));
      }
    } catch (err) {
      console.error('Signup error:', err);
      setError(t('signup.failed'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md px-6">
        <Card className="relative z-10 border border-gray-200 bg-white shadow-[0_12px_40px_rgba(0,0,0,0.08)]">
          <CardContent className="relative px-8 py-10 text-black opacity-100">
            <div className="mb-6 text-center">
              <h1 className="text-2xl font-semibold tracking-tight text-black opacity-100">
                {t('signup.title', 'Sign Up')}
              </h1>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <Label htmlFor="username" className="text-gray-800">
                  {t('signup.username')}
                </Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder={t('signup.username')}
                  autoComplete="username"
                  className="mt-1 bg-white focus:bg-white"
                />
              </div>

              <div>
                <Label htmlFor="email" className="text-gray-800">
                  {t('signup.email')}
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder={t('signup.email')}
                  autoComplete="email"
                  className="mt-1 bg-white focus:bg-white"
                />
              </div>

              <div>
                <Label htmlFor="password" className="text-gray-800">
                  {t('signup.password')}
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder={t('signup.password')}
                  autoComplete="new-password"
                  className="mt-1 bg-white focus:bg-white"
                />
              </div>

              <div>
                <Label htmlFor="confirm" className="text-gray-800">
                  {t('signup.confirmPassword')}
                </Label>
                <Input
                  id="confirm"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  placeholder={t('signup.confirmPassword')}
                  autoComplete="new-password"
                  className="mt-1 bg-white focus:bg-white"
                />
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
                aria-label={t('signup.button', 'Sign Up')}
              >
                {submitting ? (
                  <span className="inline-flex items-center justify-center gap-2">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                      <path d="M22 12a10 10 0 00-10-10" />
                    </svg>
                    {t('signup.button', 'Sign Up')}
                  </span>
                ) : (
                  t('signup.button', 'Sign Up')
                )}
              </Button>

              <p className="mt-4 text-center text-sm text-gray-600">
                {t('signup.loginPrompt', 'Already have an account?')}{' '}
                <a href="/login" className="text-blue-600 hover:underline">
                  {t('signup.loginLink', 'Login')}
                </a>
              </p>
            </form>
          </CardContent>
        </Card>
        <p className="mt-6 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} KSEB Factory PdM
        </p>
      </div>
    </div>
  );
}

