'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { anomalyLog } from '@/mockData'
import { useRequireRole } from '@/hooks/useRequireRole'

export default function AnomaliesPage() {
  useRequireRole(['Admin', 'Engineer'])
  return (
    <DashboardLayout>
      <ChartCard title="Recent Anomalies">
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">Time</th>
              <th className="py-2">Description</th>
              <th className="py-2">Severity</th>
            </tr>
          </thead>
          <tbody>
            {anomalyLog.map((row) => (
              <tr key={row.id} className="border-t">
                <td className="py-2">{row.time}</td>
                <td className="py-2">{row.description}</td>
                <td className="py-2">{row.severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ChartCard>
    </DashboardLayout>
  )
}
