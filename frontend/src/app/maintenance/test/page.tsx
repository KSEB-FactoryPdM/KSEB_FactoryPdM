'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { error } from '@/lib/logger'

interface Maintenance {
  id: number
  equipmentId: string
  scheduledDate: string
  status: string
}

export default function MaintenanceTestPage() {
  const [data, setData] = useState<Maintenance[] | null>(null)

  useEffect(() => {
    fetch('/mock-maintenance.json')
      .then((res) => res.json())
      .then((json: Maintenance[]) => setData(json))
      .catch((err) => error('Failed to load mock data:', err))
  }, [])

  return (
    <DashboardLayout>
      <div className="bg-white rounded-lg shadow-md p-4">
        <h1 className="text-xl font-heading mb-2">Maintenance Test Page</h1>
        {data ? (
          <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
        ) : (
          <div>Loading...</div>
        )}
      </div>
    </DashboardLayout>
  )
}
