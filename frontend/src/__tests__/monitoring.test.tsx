// import type { ReactNode } from 'react'
// import { render, screen, waitFor, within } from '@testing-library/react'
// import { useRouter } from 'next/navigation'
// import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
// import WS from 'jest-websocket-mock'

// // Layout, Router 목
// jest.mock('@/components/DashboardLayout', () => ({
//   __esModule: true,
//   default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
// }))
// jest.mock('next/navigation', () => ({
//   useRouter: jest.fn(),
// }))
// const mockedUseRouter = useRouter as jest.Mock

// describe('MonitoringPage', () => {
//   // 원본 fetch 저장(복원용)
//   const originalFetch = global.fetch
//   let fetchMock: jest.Mock

//   // env 주입 후 모듈 캐시 초기화 + 동적 import로 페이지 로드
//   const importPageAfterEnv = async () => {
//     jest.resetModules()
//     const mod = await import('@/app/monitoring/page')
//     return mod.default
//   }

//   beforeEach(() => {
//     // Router 목
//     mockedUseRouter.mockReturnValue({
//       replace: jest.fn(),
//       push: jest.fn(),
//     })

//     // 토큰 준비
//     localStorage.setItem('token', 'abc123')

//     // fetch 목
//     fetchMock = jest.fn().mockResolvedValue({
//       json: async () => [],
//     })
//     // @ts-expect-error: 테스트에서 fetch를 목으로 교체
//     global.fetch = fetchMock
//   })

//   afterEach(() => {
//     // fetch 원복 + 각종 정리
//     global.fetch = originalFetch
//     localStorage.clear()
//     WS.clean()
//     mockedUseRouter.mockReset()
//     jest.clearAllMocks()
//   })

//   it('updates charts when messages arrive', async () => {
//     // 1) 서버 먼저 띄우고
//     const server = new WS('ws://localhost:1234')

//     // 2) env를 모듈 로드 전에 주입
//     process.env.NEXT_PUBLIC_WEBSOCKET_URL = 'ws://localhost:1234'

//     // 3) 동적 import로 페이지 로드
//     const MonitoringPage = await importPageAfterEnv()

//     const queryClient = new QueryClient()
//     render(
//       <QueryClientProvider client={queryClient}>
//         <MonitoringPage />
//       </QueryClientProvider>
//     )

//     await server.connected

//     // 초기 상태
//     const title = await screen.findByText('Anomaly Count (total)')
//     const card = title.closest('div')!
//     expect(within(card).getByText(/No data|데이터 없음/)).toBeInTheDocument()

//     const rulCard = screen.getByText('Latest RUL').closest('div')!

//     // 웹소켓 메시지 전송
//     server.send(
//       JSON.stringify([
//         {
//           time: 1,
//           total: 1,
//           A: 0,
//           AAAA: 0,
//           PTR: 0,
//           SOA: 0,
//           SRV: 0,
//           TXT: 0,
//           zone1: 0,
//           zone2: 0,
//           zone3: 0,
//           rul: 5,
//           size50: 0,
//           size90: 0,
//           size99: 0,
//         },
//       ])
//     )

//     // 데이터 반영 확인
//     await waitFor(() => {
//       expect(within(card).queryByText(/No data|데이터 없음/)).not.toBeInTheDocument()
//     })
//     await waitFor(() => {
//       expect(within(rulCard).getByText('5')).toBeInTheDocument()
//     })

//     server.close()
//   })

//   it('fetches mock equipment and anomaly data', async () => {
//     // 페이지가 WebSocket을 초기화한다면, 연결 에러를 피하려고 서버를 켜 둡니다.
//     const server = new WS('ws://localhost:1234')
//     process.env.NEXT_PUBLIC_WEBSOCKET_URL = 'ws://localhost:1234'
//     const MonitoringPage = await importPageAfterEnv()

//     const queryClient = new QueryClient()
//     render(
//       <QueryClientProvider client={queryClient}>
//         <MonitoringPage />
//       </QueryClientProvider>
//     )

//     await server.connected

//     // fetch 호출 4회 및 엔드포인트 검증
//     await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4))
//     const urls = fetchMock.mock.calls.map(args => String(args[0]))
//     expect(urls).toEqual(
//       expect.arrayContaining([
//         '/machines.json',
//         '/mock-anomalies.json',
//         '/mock-alerts.json',
//         '/mock-maintenance.json',
//       ])
//     )

//     server.close()
//   })
// })
