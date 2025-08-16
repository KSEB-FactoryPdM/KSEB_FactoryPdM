import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: jest.fn() }),
}))
import AnomaliesPage from '@/app/anomalies/page'
import EquipmentPage from '@/app/equipment/page'
import MaintenancePage from '@/app/maintenance/page'
import AlertsPage from '@/app/alerts/page'

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

describe('Static pages', () => {
  const mockMachines = [
    { power: '11kW', id: 'L-CAHU-01R', statuses: ['normal'] },
  ]

  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve({ json: () => Promise.resolve(mockMachines) })
    ) as jest.Mock
  })

  afterEach(() => {
    ;(global.fetch as jest.Mock).mockRestore()
  })
  it('renders anomalies page shell', async () => {
    const client = new QueryClient()
    render(
      <QueryClientProvider client={client}>
        <AnomaliesPage />
      </QueryClientProvider>
    )
    // 제목 번역 키 사용: 안정적인 셀렉터
    expect(await screen.findByText('Anomalies')).toBeInTheDocument()
  })
  const renderWithClient = (ui: ReactNode) => {
    const queryClient = new QueryClient()
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    )
  }

  it('renders equipment data', async () => {
    renderWithClient(<EquipmentPage />)
    await screen.findAllByText('L-CAHU-01R')
  })

  it('renders maintenance data', async () => {
    renderWithClient(<MaintenancePage />)
    await screen.findAllByText('L-CAHU-01R')
  })

  it('renders alerts data', async () => {
    renderWithClient(<AlertsPage />)
    await screen.findAllByText('L-CAHU-01R')
  })
 
})
