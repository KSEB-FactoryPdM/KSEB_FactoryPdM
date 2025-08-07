'use client'
import { useEffect, useState } from 'react'
import { AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline'
import { useTranslation } from 'react-i18next'

export default function HighContrastToggle() {
  const { t } = useTranslation('common')
  const [mounted, setMounted] = useState(false)
  const [enabled, setEnabled] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('highContrast') === 'true'
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    const root = window.document.documentElement
    if (enabled) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
    localStorage.setItem('highContrast', String(enabled))
  }, [enabled, mounted])

  if (!mounted) return null

  return (
    <button
      type="button"
      onClick={() => setEnabled(!enabled)}
      className="p-1 rounded hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-accent"
      aria-label={enabled ? t('header.disableHighContrast') : t('header.enableHighContrast')}
    >
      <AdjustmentsHorizontalIcon className="w-6 h-6" />
    </button>
  )
}
