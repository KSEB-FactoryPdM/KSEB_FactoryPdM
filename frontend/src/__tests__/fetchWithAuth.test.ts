import { fetchWithAuth } from '@/lib/api'

// Mock fetch
global.fetch = jest.fn()

describe('fetchWithAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('adds authorization header', async () => {
    const mockResponse = { ok: true, json: () => Promise.resolve({ data: 'test' }) }
    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'abc123'),
      },
      writable: true,
    })

    await fetchWithAuth('/api/test')

    const calls = (global.fetch as jest.Mock).mock.calls
    expect(calls.length).toBe(1)
    expect(calls[0][0]).toBe('/api/test')
    expect(calls[0][1].headers).toEqual({
      'Authorization': 'Bearer abc123',
    })
  })

  it('handles missing token', async () => {
    const mockResponse = { ok: true, json: () => Promise.resolve({ data: 'test' }) }
    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    // Mock localStorage with no token
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => null),
      },
      writable: true,
    })

    await fetchWithAuth('/api/test')

    const calls = (global.fetch as jest.Mock).mock.calls
    expect(calls.length).toBe(1)
    expect(calls[0][0]).toBe('/api/test')
    expect(calls[0][1].headers).toEqual({})
  })
})
