import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SearchPage from '@/app/search/page'
import type { ReactNode } from 'react'

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

jest.mock('@/components/DeviceSensorPanel', () => ({
  __esModule: true,
  default: () => <div data-testid="graph">graph</div>,
}))

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams([["query", "L-DEF"]]),
}))

const mockDevices = [
  { id: 'L-DEF-01', name: 'Line Device', type: 'Motor', status: 'Active' },
  { id: 'B-123', name: 'Boiler', type: 'Boiler', status: 'Idle' },
]

describe('SearchPage', () => {
  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve({ json: () => Promise.resolve(mockDevices) })
    ) as jest.Mock
  })

  afterEach(() => {
    ;(global.fetch as jest.Mock).mockRestore()
  })

  it('filters devices by query and shows matching results', async () => {
    const client = new QueryClient()
    render(
      <QueryClientProvider client={client}>
        <SearchPage />
      </QueryClientProvider>
    )
    expect(await screen.findByText('Line Device')).toBeInTheDocument()
    expect(screen.queryByText('Boiler')).not.toBeInTheDocument()
  })
})

