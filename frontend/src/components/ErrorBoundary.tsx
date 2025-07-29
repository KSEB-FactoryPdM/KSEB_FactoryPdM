'use client'
import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
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
      return (
        <div className="flex flex-col items-center justify-center h-screen gap-4 p-4">
          <p>문제가 발생했습니다</p>
          <button onClick={this.handleRetry} className="bg-primary text-white px-4 py-2 rounded">
            다시 시도
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
