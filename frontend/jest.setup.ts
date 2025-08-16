// RTL 매처
import '@testing-library/jest-dom'

// i18next 초기화 (클라이언트 전용 가드 포함)
import './src/i18n'

// ResizeObserver mock (Recharts ResponsiveContainer 등)
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error jsdom window typing
window.ResizeObserver = window.ResizeObserver || ResizeObserverMock

// matchMedia mock
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// 기본 fetch 목 (필요 시 테스트 내에서 override)
const originalFetch = global.fetch
global.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === 'string' ? input : String(input)
  // public 정적 목 파일에 대한 간단한 핸들링
  if (url.startsWith('/mock-') || url.startsWith('/machines.json') || url.startsWith('/mock-')) {
    // jsdom에서는 상대 경로 fetch가 동작하지 않으므로 간단히 빈 배열/객체 반환
    return new Response(JSON.stringify([]), { status: 200 }) as any
  }
  return originalFetch ? originalFetch(input as any, init) : (new Response('{}', { status: 200 }) as any)
}
