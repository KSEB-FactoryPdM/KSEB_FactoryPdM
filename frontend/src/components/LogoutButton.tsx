'use client'
import { useRouter } from 'next/navigation'
import { useTranslation } from 'react-i18next'

export default function LogoutButton() {
  const router = useRouter()
  const { t } = useTranslation('common')
  function handleClick() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
    router.push('/login')
  }
  return (
    <button onClick={handleClick} className="text-sm">
      {t('nav.logout')}
    </button>
  )
}
