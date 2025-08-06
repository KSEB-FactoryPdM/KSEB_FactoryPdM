'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { error } from '@/lib/logger'

interface Equipment {
  id: string
  name: string
  status: string
}

export default function EquipmentTestPage() {
  const [data, setData] = useState<Equipment[] | null>(null)

  useEffect(() => {
    fetch('/mock-equipment.json')
      .then((res) => res.json())
      .then((json: Equipment[]) => setData(json))
      .catch((err) => error('Failed to load mock data:', err))
  }, [])

  return (
    <DashboardLayout>
      <div className="bg-white rounded-lg shadow-md p-4">
        <h1 className="text-xl font-heading mb-2">Equipment Test Page</h1>
        {data ? (
          <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
        ) : (
          <div>Loading...</div>
        )}
      </div>
    </DashboardLayout>
  )
}
