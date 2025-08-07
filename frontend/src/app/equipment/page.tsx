'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { EquipmentFilter } from '@/components/filters'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import type { Machine } from '@/components/filters/EquipmentFilter'
import { useRequireRole } from '@/hooks/useRequireRole'
import { useTranslation } from 'react-i18next'

export default function EquipmentPage() {
  useRequireRole('Admin')
  const { t } = useTranslation('common')
  const { data: machines } = useQuery<Machine[]>({
    queryKey: ['machines'],
    queryFn: () => fetch('/machines.json').then((res) => res.json() as Promise<Machine[]>),
    staleTime: 30000,
    gcTime: 300000,
  })

  const [power, setPower] = useState('')
  const [device, setDevice] = useState('')

  const filtered = useMemo(
    () =>
      machines?.filter(
        (m) => (!power || m.power === power) && (!device || m.id === device)
      ) ?? [],
    [machines, power, device]
  )

  return (
    <DashboardLayout>
      <ChartCard title="Equipment List">
        <div className="mb-2">
          <EquipmentFilter
            machines={machines ?? []}
            power={power}
            device={device}
            onPowerChange={setPower}
            onDeviceChange={setDevice}
          />
        </div>
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">kW</th>
              <th className="py-2">ID</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((eq) => (
              <tr key={eq.id} className="border-t">
                <td className="py-2">{eq.power}</td>
                <td className="py-2">{eq.id}</td>
                <td className="py-2">
                  {eq.statuses.map((s) => t(`status.${s}`)).join(', ')}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td className="py-2" colSpan={3}>
                  No equipment
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </ChartCard>
    </DashboardLayout>
  )
}
