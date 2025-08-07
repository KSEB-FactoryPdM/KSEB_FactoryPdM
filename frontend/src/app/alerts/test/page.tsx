'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { AlertItem } from '@/mockData'
import { error } from '@/lib/logger'

export default function AlertsTestPage() {
  const [data, setData] = useState<AlertItem[] | null>(null)

  useEffect(() => {
    fetch('/mock-alerts.json')
      .then((res) => res.json())
      .then((json: AlertItem[]) => setData(json))
      .catch((err) => error('Failed to load mock data:', err))
  }, [])

  return (
    <DashboardLayout>
      <div className="bg-white rounded-lg shadow-md p-4">
        <h1 className="text-xl font-heading mb-2">Alerts Test Page</h1>
        {data ? (
          <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
        ) : (
          <div>Loading...</div>
        )}
      </div>
    </DashboardLayout>
  )
}
