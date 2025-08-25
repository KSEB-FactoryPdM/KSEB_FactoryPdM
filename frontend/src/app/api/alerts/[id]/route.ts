import { NextRequest, NextResponse } from 'next/server'

// Using `any` here keeps the handler simple while avoiding TypeScript
// issues with Next.js route context typing.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function PUT(req: NextRequest, context: any) {
  await req.json()
  return NextResponse.json({ ok: true, id: context.params.id })
}
