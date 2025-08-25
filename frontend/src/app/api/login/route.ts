import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const { username, password } = await req.json()
    if (!username || !password) {
      return NextResponse.json({ error: 'missing credentials' }, { status: 400 })
    }
    const base = (process.env.BACKEND_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')
    const url = `${base}/auth/login`
    console.log('[api/login] request ->', { base, url })
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    if (!res.ok) {
      const cloneText = await res.clone().text().catch(() => '')
      console.error('[api/login] backend non-OK', { status: res.status, body: cloneText })
      const { error, status } = await extractError(res)
      return NextResponse.json({ error }, { status })
    }
    const json = await res.json() as { access_token: string, token_type: string, expires_in: number }
    return NextResponse.json({ token: json.access_token, token_type: json.token_type, expires_in: json.expires_in })
  } catch (e) {
    const msg = (e as any)?.message || 'login failed'
    console.error('[api/login] fetch error', msg)
    return NextResponse.json({ error: `login failed: ${msg}` }, { status: 502 })
  }
}

async function extractError(res: Response): Promise<{ error: string, status: number }> {
  try {
    const raw = await res.clone().text()
    let parsed: any = null
    try { parsed = JSON.parse(raw) } catch {}
    if (parsed?.detail) {
      if (Array.isArray(parsed.detail)) {
        const msgs = parsed.detail.map((d: any) => d?.msg || (typeof d === 'string' ? d : '')).filter(Boolean)
        if (msgs.length) return { error: msgs.join('; '), status: res.status }
      } else if (typeof parsed.detail === 'string') {
        return { error: parsed.detail, status: res.status }
      } else {
        return { error: JSON.stringify(parsed.detail), status: res.status }
      }
    }
    if (typeof parsed?.error === 'string') return { error: parsed.error, status: res.status }
    if (typeof parsed?.message === 'string') return { error: parsed.message, status: res.status }
    if (raw) return { error: raw, status: res.status }
  } catch {}
  return { error: 'login failed', status: res.status }
}


