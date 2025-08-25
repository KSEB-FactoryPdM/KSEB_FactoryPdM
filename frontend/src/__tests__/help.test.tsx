import type { ReactNode } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import HelpPage from '@/app/help/page'

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

describe('Help page', () => {
  it('filters FAQ items based on search', () => {
    render(<HelpPage />)
    expect(
      screen.getByText('실시간 모니터링이 연결되지 않아요.')
    ).toBeInTheDocument()
    const input = screen.getByPlaceholderText(
      '검색: 예) WebSocket, 계정, 임계값'
    )
    fireEvent.change(input, { target: { value: '계정' } })
    expect(screen.getByText('계정을 복구하려면?')).toBeInTheDocument()
    expect(
      screen.queryByText('실시간 모니터링이 연결되지 않아요.')
    ).not.toBeInTheDocument()
  })
})

