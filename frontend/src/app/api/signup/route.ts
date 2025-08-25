import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  // 요청 본문 파싱(안전)
  let payload: unknown = null
  try {
    const raw = await req.text()
    payload = raw ? JSON.parse(raw) : {}
  } catch {
    return NextResponse.json({ error: 'invalid json body' }, { status: 400 })
  }

  const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null
  const { username, email, password } = isRecord(payload) ? payload : ({} as Record<string, unknown>)
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
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'backend request failed'
    console.error('[api/signup] fetch error', msg)
    return NextResponse.json({ error: `signup failed: ${msg}` }, { status: 502 })
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
  return { error: 'signup failed', status: res.status }
}


