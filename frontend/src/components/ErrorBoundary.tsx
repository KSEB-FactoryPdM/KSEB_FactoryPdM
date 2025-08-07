'use client'
import { Component, ReactNode } from 'react'
import { withTranslation, WithTranslation } from 'react-i18next'

interface Props extends WithTranslation {
  children: ReactNode
}
interface State {
  hasError: boolean
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false })
  }

  render() {
    if (this.state.hasError) {
      const { t } = this.props
      return (
        <div className="flex flex-col items-center justify-center h-screen gap-4 p-4">
          <p>{t('errorBoundary.message', 'An error occurred')}</p>
          <button onClick={this.handleRetry} className="bg-primary text-white px-4 py-2 rounded">
            {t('errorBoundary.retry', 'Retry')}
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default withTranslation('common')(ErrorBoundary)
