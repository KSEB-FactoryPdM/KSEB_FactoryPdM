import type { NextApiRequest, NextApiResponse } from 'next'
// @ts-expect-error no types for compiled package
import jwt from 'jsonwebtoken'
import '../../../sentry.server.config'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const { username, password } = req.body as {
    username?: string
    password?: string
  }

  if (username === 'admin' && password === 'password') {
    const secret = process.env.JWT_SECRET || 'secret'
    const token = jwt.sign({ username }, secret, { expiresIn: '1h' })
    return res.status(200).json({ token })
  }

  return res.status(401).json({ error: 'Invalid credentials' })
}
