import { useTranslation } from 'react-i18next'
import pkg from '../../package.json'

export default function Footer() {
  const { t } = useTranslation('common')
  const year = new Date().getFullYear()
  const version = pkg.version

  return (
    <footer className="text-center text-xs text-gray-500 py-4 border-t mt-auto">
      <p>{t('footer.version', { version })}</p>
      <p>{t('footer.contact', { year })}</p>
    </footer>
  )
}
