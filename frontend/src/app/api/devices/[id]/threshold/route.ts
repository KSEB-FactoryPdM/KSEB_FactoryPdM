import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const { threshold } = await req.json()
  return NextResponse.json({ threshold })
}
