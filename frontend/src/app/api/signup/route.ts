import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  // 요청 본문 파싱(안전)
  let payload: any = null
  try {
    const raw = await req.text()
    payload = raw ? JSON.parse(raw) : {}
  } catch {
    return NextResponse.json({ error: 'invalid json body' }, { status: 400 })
  }

  const { username, email, password } = payload || {}
  if (!username || !email || !password) {
    return NextResponse.json({ error: 'missing fields' }, { status: 400 })
  }

  // 백엔드 베이스 URL 결정(서버용 우선)
  const baseRaw = process.env.BACKEND_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_BASE_URL || 'http://localhost:8000/api/v1'
  const base = baseRaw.replace(/\/$/, '')

  const url = `${base}/auth/register`
  try {
    console.log('[api/signup] request ->', { base, url })
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    })
    if (!res.ok) {
      const cloneText = await res.clone().text().catch(() => '')
      console.error('[api/signup] backend non-OK', { status: res.status, body: cloneText })
      const { error, status } = await extractError(res)
      return NextResponse.json({ error }, { status })
    }
    return NextResponse.json({ ok: true })
  } catch (err: any) {
    const msg = typeof err?.message === 'string' ? err.message : 'backend request failed'
    console.error('[api/signup] fetch error', msg)
    return NextResponse.json({ error: `signup failed: ${msg}` }, { status: 502 })
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
  return { error: 'signup failed', status: res.status }
}


