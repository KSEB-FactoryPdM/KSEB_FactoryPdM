'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { equipmentList } from '@/mockData'
import { useRequireRole } from '@/hooks/useRequireRole'

export default function EquipmentPage() {
  useRequireRole('Admin')
  return (
    <DashboardLayout>
      <ChartCard title="Equipment List">
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">ID</th>
              <th className="py-2">Name</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {equipmentList.map((eq) => (
              <tr key={eq.id} className="border-t">
                <td className="py-2">{eq.id}</td>
                <td className="py-2">{eq.name}</td>
                <td className="py-2">{eq.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ChartCard>
    </DashboardLayout>
  )
}
