import { fetchWithAuth } from '@/lib/api'

beforeEach(() => {
  global.fetch = jest.fn(() => Promise.resolve({})) as jest.Mock
})

afterEach(() => {
  ;(global.fetch as jest.Mock).mockRestore()
  localStorage.clear()
})

describe('fetchWithAuth', () => {
  it('adds Authorization header from localStorage', async () => {
    localStorage.setItem('token', 'abc123')
    await fetchWithAuth('/api/test')
    const headers = (global.fetch as jest.Mock).mock.calls[0][1]?.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer abc123')
  })
})
