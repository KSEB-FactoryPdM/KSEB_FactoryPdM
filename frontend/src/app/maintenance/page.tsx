'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { EquipmentFilter } from '@/components/filters'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import type { Machine } from '@/components/filters/EquipmentFilter'
import { useRequireRole } from '@/hooks/useRequireRole'
import { useTranslation } from 'react-i18next'

export default function MaintenancePage() {
  useRequireRole(['Admin', 'Engineer'])
  const { t } = useTranslation('common')
  const { data: machines } = useQuery<Machine[]>({
    queryKey: ['machines'],
    queryFn: () => fetch('/machines.json').then((res) => res.json() as Promise<Machine[]>),
    staleTime: 30000,
    gcTime: 300000,
  })

  const [power, setPower] = useState('')
  const [device, setDevice] = useState('')

  const abnormal = useMemo(() => {
    return (
      machines?.map((m) => ({
        ...m,
        abnormal: m.statuses.filter((s) => s !== 'normal'),
      })) ?? []
    )
  }, [machines])

  const filtered = abnormal.filter(
    (m) => (!power || m.power === power) && (!device || m.id === device)
  )

  return (
    <DashboardLayout>
      <ChartCard title="Maintenance">
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
              <th className="py-2">Equipment</th>
              <th className="py-2">Abnormal</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <tr key={m.id} className="border-t">
                <td className="py-2">{m.power}</td>
                <td className="py-2">{m.id}</td>
                <td className="py-2">
                  {m.abnormal.length > 0
                    ? m.abnormal.map((s) => t(`status.${s}`)).join(', ')
                    : '-'}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td className="py-2" colSpan={3}>
                  No data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </ChartCard>
    </DashboardLayout>
  )
}
