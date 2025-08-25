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
    const msg = e instanceof Error ? e.message : 'login failed'
    console.error('[api/login] fetch error', msg)
    return NextResponse.json({ error: `login failed: ${msg}` }, { status: 502 })
  }
}

async function extractError(res: Response): Promise<{ error: string, status: number }> {
  try {
    const raw = await res.clone().text()
    let parsed: unknown = null
    try { parsed = JSON.parse(raw) } catch {}

    const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null

    if (isRecord(parsed) && 'detail' in parsed) {
      const detail = (parsed as { detail?: unknown }).detail
      if (Array.isArray(detail)) {
        const msgs = detail
          .map((d) => {
            if (typeof d === 'string') return d
            if (typeof d === 'object' && d !== null && typeof (d as { msg?: unknown }).msg === 'string') {
              return (d as { msg?: string }).msg as string
            }
            return ''
          })
          .filter((s): s is string => Boolean(s))
        if (msgs.length) return { error: msgs.join('; '), status: res.status }
      } else if (typeof detail === 'string') {
        return { error: detail, status: res.status }
      } else if (isRecord(detail)) {
        return { error: JSON.stringify(detail), status: res.status }
      }
    }

    if (isRecord(parsed) && typeof parsed.error === 'string') return { error: parsed.error, status: res.status }
    if (isRecord(parsed) && typeof parsed.message === 'string') return { error: parsed.message, status: res.status }
    if (raw) return { error: raw, status: res.status }
  } catch {}
  return { error: 'login failed', status: res.status }
}


