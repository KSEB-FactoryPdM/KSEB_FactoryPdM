import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: jest.fn() }),
}))
jest.mock('jspdf', () => {
  return function MockJsPdf() {
    return { text: jest.fn(), save: jest.fn() }
  }
})
import AnomaliesPage from '@/app/anomalies/page'
import EquipmentPage from '@/app/equipment/page'
import MaintenancePage from '@/app/maintenance/page'
import ReportsPage from '@/app/reports/page'
import AlertsPage from '@/app/alerts/page'

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

describe('Static pages', () => {
  it('renders anomalies data', () => {
    render(<AnomaliesPage />)
    expect(screen.getByText('High vibration detected')).toBeInTheDocument()
  })

  it('renders equipment data', () => {
    render(<EquipmentPage />)
    expect(screen.getByText('Compressor #3')).toBeInTheDocument()
  })

  it('renders maintenance data', () => {
    render(<MaintenancePage />)
    expect(screen.getByText('Replace filters')).toBeInTheDocument()
  })

  it('renders alerts data', () => {
    render(<AlertsPage />)
    expect(screen.getAllByText('Motor #5')[0]).toBeInTheDocument()
  })

  it('renders report chart', () => {
    render(<ReportsPage />)
    expect(screen.getByText('Summary Report')).toBeInTheDocument()
  })
})
