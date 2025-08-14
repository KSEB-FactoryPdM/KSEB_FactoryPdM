import type { ReactNode } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import HelpPage from '@/app/help/page'

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

jest.mock('@/components/ChartCard', () => ({
  __esModule: true,
  default: ({ title, children }: { title: string; children: ReactNode }) => (
    <div>
      <h3>{title}</h3>
      {children}
    </div>
  ),
}))

describe('Help page', () => {
  it('filters FAQ items based on search', () => {
    render(<HelpPage />)
    expect(screen.getByText('How do I reset my password?')).toBeInTheDocument()
    const input = screen.getByPlaceholderText('Search the FAQ...')
    fireEvent.change(input, { target: { value: 'contact' } })
    expect(screen.getByText('How do I contact support?')).toBeInTheDocument()
    expect(
      screen.queryByText('How do I reset my password?')
    ).not.toBeInTheDocument()
  })
})

