import type { ReactNode } from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import MonitoringPage from '@/app/monitoring/page'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import WS from 'jest-websocket-mock'

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))
const mockedUseRouter = useRouter as jest.Mock

describe('MonitoringPage', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'abc123')
    global.fetch = jest.fn(() =>
      Promise.resolve({ json: () => Promise.resolve([]) })
    ) as jest.Mock
    mockedUseRouter.mockReturnValue({
      replace: jest.fn(),
      push: jest.fn(),
    })
  })

  afterEach(() => {
    ;(global.fetch as jest.Mock).mockRestore()
    localStorage.clear()
    WS.clean()
    mockedUseRouter.mockReset()
  })

  it('updates charts when messages arrive', async () => {
    const server = new WS('ws://localhost:1234')
    process.env.NEXT_PUBLIC_WEBSOCKET_URL = 'ws://localhost:1234'

    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MonitoringPage />
      </QueryClientProvider>
    )

    await server.connected

    const title = await screen.findByText('Anomaly Count (total)')
    const card = title.closest('div')!

    expect(within(card).getByText('No data')).toBeInTheDocument()

    const rulCard = screen.getByText('Latest RUL').closest('div')!
    server.send(
      JSON.stringify([
        {
          time: 1,
          total: 1,
          A: 0,
          AAAA: 0,
          PTR: 0,
          SOA: 0,
          SRV: 0,
          TXT: 0,
          zone1: 0,
          zone2: 0,
          zone3: 0,
          rul: 5,
          size50: 0,
          size90: 0,
          size99: 0,
        },
      ])
    )

    await waitFor(() => {
      expect(within(card).queryByText('No data')).not.toBeInTheDocument()
    })
    await waitFor(() => {
      expect(within(rulCard).getByText('5')).toBeInTheDocument()
    })
  })

  it('fetches mock equipment and anomaly data', async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MonitoringPage />
      </QueryClientProvider>
    )

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(4))
    const calls = (global.fetch as jest.Mock).mock.calls
    expect(calls).toEqual(
      expect.arrayContaining([
        ['/mock-equipment.json'],
        ['/mock-anomalies.json'],
        ['/mock-alerts.json'],
        ['/mock-maintenance.json'],
      ])
    )
  })
})
