import { renderHook, act, waitFor } from '@testing-library/react'

jest.setTimeout(10000)
import WS from 'jest-websocket-mock'
import useWebSocket from '@/hooks/useWebSocket'

jest.setTimeout(10000)

afterEach(() => {
  WS.clean()
})

jest.setTimeout(10000)

describe('useWebSocket', () => {
  it('parses incoming JSON messages', async () => {
    const server = new WS('ws://localhost:1234')
    const { result } = renderHook(() =>
      useWebSocket<{ a: number }[]>('ws://localhost:1234')
    )

    await server.connected
    act(() => {
      server.send(JSON.stringify([{ a: 1 }]))
    })

    await waitFor(() => expect(result.current.data).toEqual([{ a: 1 }]))
  })

  it.skip('reconnects after the socket closes', async () => {
    jest.useFakeTimers()

    const server = new WS('ws://localhost:5678')
    const { result } = renderHook(() =>
      useWebSocket('ws://localhost:5678', { autoReconnect: true, initialDelay: 100 })
    )

    await server.connected
    server.close()
    new WS('ws://localhost:5678')
    act(() => {
      jest.advanceTimersByTime(100)
    })
    await waitFor(() => expect(result.current.status).toBe('connected'))
    jest.useRealTimers()
  }, 10000)
})
