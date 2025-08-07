'use client'

import { useState, useMemo } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { alertList, AlertItem } from '@/mockData'
import { EquipmentFilter } from '@/components/filters'
import type { Machine } from '@/components/filters/EquipmentFilter'
import { useQuery } from '@tanstack/react-query'
import AlertDetailsModal from '@/components/AlertDetailsModal'
import { error } from '@/lib/logger'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState(alertList)
  const [selected, setSelected] = useState<AlertItem | null>(null)
  const [power, setPower] = useState('')
  const [equipment, setEquipment] = useState('')
  const [severity, setSeverity] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const { data: machines } = useQuery<Machine[]>({
    queryKey: ['machines'],
    queryFn: () => fetch('/machines.json').then((res) => res.json() as Promise<Machine[]>),
    staleTime: 30000,
    gcTime: 300000,
  })
  const severityOptions = useMemo(
    () => Array.from(new Set(alerts.map((a) => a.severity))),
    [alerts]
  )

  const updateStatus = async (ids: number[], status: string) => {
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/alerts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
          })
        )
      )
    } catch (err) {
      error('Failed to update status', err)
    }
    setAlerts((prev) =>
      prev.map((a) => (ids.includes(a.id) ? { ...a, status } : a))
    )
  }

  const changeStatus = (id: number, status: string) => {
    updateStatus([id], status)
  }

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      if (power && a.power !== power) return false
      if (equipment && a.device !== equipment) return false
      if (severity && a.severity !== severity) return false
      if (statusFilter && a.status !== statusFilter) return false
      const date = new Date(a.time)
      if (startDate && date < new Date(startDate)) return false
      if (endDate && date > new Date(endDate)) return false
      return true
    })
  }, [alerts, power, equipment, severity, statusFilter, startDate, endDate])

  return (
    <DashboardLayout>
      <ChartCard title="Alerts">
        <div className="flex flex-wrap gap-2 mb-2">
          <EquipmentFilter
            machines={machines ?? []}
            power={power}
            device={equipment}
            onPowerChange={setPower}
            onDeviceChange={setEquipment}
          />
          <select
            className="border rounded px-2 py-1"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="">All Severity</option>
            {severityOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="border rounded px-2 py-1"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <input
            type="date"
            className="border rounded px-2 py-1"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
          <select
            className="border rounded px-2 py-1"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="new">new</option>
            <option value="acknowledged">acknowledged</option>
            <option value="cleared">cleared</option>
          </select>
        </div>
        {selectedIds.length > 0 && (
          <div className="mb-2 space-x-2">
            <button
              className="px-2 py-1 bg-blue-600 text-white rounded"
              onClick={() => {
                updateStatus(selectedIds, 'acknowledged')
                setSelectedIds([])
              }}
            >
              Acknowledge Selected
            </button>
            <button
              className="px-2 py-1 bg-red-600 text-white rounded"
              onClick={() => {
                updateStatus(selectedIds, 'cleared')
                setSelectedIds([])
              }}
            >
              Clear Selected
            </button>
          </div>
        )}
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">
                <input
                  type="checkbox"
                  checked={
                    filteredAlerts.length > 0 &&
                    filteredAlerts.every((a) => selectedIds.includes(a.id))
                  }
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedIds(filteredAlerts.map((a) => a.id))
                    } else {
                      setSelectedIds([])
                    }
                  }}
                />
              </th>
              <th className="py-2">Time</th>
              <th className="py-2">kW</th>
              <th className="py-2">Device</th>
              <th className="py-2">Type</th>
              <th className="py-2">Severity</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.map((a) => (
              <tr key={a.id} className="border-t">
                <td className="py-2">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(a.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedIds((prev) => [...prev, a.id])
                      } else {
                        setSelectedIds((prev) => prev.filter((id) => id !== a.id))
                      }
                    }}
                  />
                </td>
                <td className="py-2">{a.time}</td>
                <td className="py-2">{a.power}</td>
                <td className="py-2">{a.device}</td>
                <td className="py-2">{a.type}</td>
                <td className="py-2">{a.severity}</td>
                <td className="py-2 space-x-2">
                  <button
                    className="text-blue-600 underline"
                    onClick={() => changeStatus(a.id, 'acknowledged')}
                  >
                    Acknowledge
                  </button>
                  <button
                    className="text-red-600 underline"
                    onClick={() => changeStatus(a.id, 'cleared')}
                  >
                    Clear
                  </button>
                  <button
                    className="text-primary underline"
                    onClick={() => setSelected(a)}
                  >
                    Details
                  </button>
                </td>
              </tr>
            ))}
            {filteredAlerts.length === 0 && (
              <tr>
                <td className="py-2" colSpan={6}>
                  No alerts
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </ChartCard>
      {selected && (
        <AlertDetailsModal alert={selected} onClose={() => setSelected(null)} />
      )}
    </DashboardLayout>
  )
}
