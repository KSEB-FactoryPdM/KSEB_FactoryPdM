'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { error } from '@/lib/logger'

interface Anomaly {
  id: number
  equipmentId: string
  type: string
  timestamp: string
  status: string
}

export default function AnomaliesTestPage() {
  const [data, setData] = useState<Anomaly[] | null>(null)

  useEffect(() => {
    fetch('/mock-anomalies.json')
      .then((res) => res.json())
      .then((json: Anomaly[]) => setData(json))
      .catch((err) => error('Failed to load mock data:', err))
  }, [])

  return (
    <DashboardLayout>
      <div className="bg-white rounded-lg shadow-md p-4">
        <h1 className="text-xl font-heading mb-2">Anomalies Test Page</h1>
        {data ? (
          <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
        ) : (
          <div>Loading...</div>
        )}
      </div>
    </DashboardLayout>
  )
}
