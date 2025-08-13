'use client'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

export default function FontSizeSelector() {
  const { t } = useTranslation('common')
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>(() => {
    if (typeof window === 'undefined') return 'medium'
    return (localStorage.getItem('fontSize') as 'small' | 'medium' | 'large') || 'medium'
  })

  useEffect(() => {
    const root = window.document.documentElement
    const sizeMap = { small: '14px', medium: '16px', large: '18px' }
    root.style.setProperty('--base-font-size', sizeMap[fontSize])
    localStorage.setItem('fontSize', fontSize)
  }, [fontSize])

  return (
    <select
      value={fontSize}
      onChange={e => setFontSize(e.target.value as 'small' | 'medium' | 'large')}
      aria-label={t('header.fontSize')}
      className="bg-input-bg rounded p-1 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
    >
      <option value="small">A-</option>
      <option value="medium">A</option>
      <option value="large">A+</option>
    </select>
  )
}
