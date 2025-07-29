'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { maintenanceSchedule } from '@/mockData'
import { useRequireRole } from '@/hooks/useRequireRole'

export default function MaintenancePage() {
  useRequireRole(['Admin', 'Engineer'])
  return (
    <DashboardLayout>
      <ChartCard title="Upcoming Maintenance">
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">Task</th>
              <th className="py-2">Due Date</th>
            </tr>
          </thead>
          <tbody>
            {maintenanceSchedule.map((m) => (
              <tr key={m.id} className="border-t">
                <td className="py-2">{m.task}</td>
                <td className="py-2">{m.dueDate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ChartCard>
    </DashboardLayout>
  )
}
