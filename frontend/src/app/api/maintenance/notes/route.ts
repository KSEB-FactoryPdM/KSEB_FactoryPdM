import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

interface MaintenanceLog {
  id: number
  equipmentId: string
  status: string
  description: string
  timestamp: string
}

const dataFile = path.join(process.cwd(), 'data', 'maintenanceLogs.json')

async function readLogs(): Promise<MaintenanceLog[]> {
  try {
    const data = await fs.readFile(dataFile, 'utf-8')
    return JSON.parse(data) as MaintenanceLog[]
  } catch {
    return []
  }
}

async function writeLogs(logs: MaintenanceLog[]) {
  await fs.writeFile(dataFile, JSON.stringify(logs, null, 2))
}

export async function GET() {
  const logs = await readLogs()
  return NextResponse.json(logs)
}

export async function POST(req: NextRequest) {
  const { equipmentId, status, description } = await req.json()
  const logs = await readLogs()
  const newLog: MaintenanceLog = {
    id: Date.now(),
    equipmentId,
    status,
    description,
    timestamp: new Date().toISOString(),
  }
  logs.push(newLog)
  await writeLogs(logs)
  return NextResponse.json(newLog, { status: 201 })
}
