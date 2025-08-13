import { render, waitFor, screen, within } from '@testing-library/react'
import { usePathname, useRouter } from 'next/navigation'
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
  useRouter: jest.fn(),
}))
import MonitoringTestPage from '@/app/monitoring/test/page'
import mockData from '../../public/mock-data.json'
const mockedUsePathname = usePathname as jest.Mock
const mockedUseRouter = useRouter as jest.Mock

jest.mock('@/components/DashboardLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({ json: () => Promise.resolve(mockData) })
  ) as jest.Mock
  mockedUsePathname.mockReturnValue('/monitoring/test')
  mockedUseRouter.mockReturnValue({
    replace: jest.fn(),
    push: jest.fn(),
  })
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: () => ({
      matches: false,
      media: '',
      onchange: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }),
  })
})

afterEach(() => {
  ;(global.fetch as jest.Mock).mockRestore()
  mockedUsePathname.mockReset()
  mockedUseRouter.mockReset()
})

describe('Monitoring test page', () => {
  it('renders charts when mock data is loaded', async () => {
    render(<MonitoringTestPage />)

    const title = await screen.findByText('Anomaly Count (total)')
    const card = title.closest('div')!

    await waitFor(() => {
      expect(within(card).queryByText('No data')).not.toBeInTheDocument()
    })

    // Ensure charts replaced placeholder content
    await waitFor(() => {
      expect(screen.queryAllByText('No data').length).toBeLessThan(7)
    })
  })
})
