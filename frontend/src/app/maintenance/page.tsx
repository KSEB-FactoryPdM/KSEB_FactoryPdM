'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { EquipmentFilter } from '@/components/filters'
import { useQuery, useMutation } from '@tanstack/react-query'
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

  interface MaintenanceLog {
    id: number
    equipmentId: string
    status: string
    description: string
    timestamp: string
  }

  const { data: logs = [], refetch } = useQuery<MaintenanceLog[]>({
    queryKey: ['maintenanceLogs'],
    queryFn: () => fetch('/api/maintenance/notes').then((r) => r.json() as Promise<MaintenanceLog[]>),
  })

  const mutation = useMutation({
    mutationFn: (newLog: Omit<MaintenanceLog, 'id' | 'timestamp'>) =>
      fetch('/api/maintenance/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newLog),
      }).then((r) => r.json()),
    onSuccess: () => refetch(),
  })

  const [showModal, setShowModal] = useState(false)
  const [noteEquipment, setNoteEquipment] = useState('')
  const [noteStatus, setNoteStatus] = useState('pending')
  const [noteDesc, setNoteDesc] = useState('')

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

  const handleSave = () => {
    mutation.mutate({
      equipmentId: noteEquipment,
      status: noteStatus,
      description: noteDesc,
    })
    setShowModal(false)
    setNoteEquipment('')
    setNoteStatus('pending')
    setNoteDesc('')
  }

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <ChartCard title="Maintenance Notes">
          <div className="mb-2 text-right">
            <button
              className="px-3 py-1 rounded bg-gray-200 text-gray-800 hover:bg-gray-300"
              onClick={() => setShowModal(true)}
            >
              Add Note
            </button>
          </div>
          <table className="w-full text-sm">
            <thead className="text-left">
              <tr>
                <th className="py-2">Equipment</th>
                <th className="py-2">Status</th>
                <th className="py-2">Description</th>
                <th className="py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-t">
                  <td className="py-2">{log.equipmentId}</td>
                  <td className="py-2">{log.status}</td>
                  <td className="py-2">{log.description}</td>
                  <td className="py-2">{new Date(log.timestamp).toLocaleString()}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td className="py-2" colSpan={4}>
                    No notes
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </ChartCard>

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
      </div>

      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setShowModal(false)}
        >
          <div
            className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-heading">Add Maintenance Note</h3>
            <div className="space-y-3">
              <select
                className="w-full rounded border p-2"
                value={noteEquipment}
                onChange={(e) => setNoteEquipment(e.target.value)}
              >
                <option value="">Select equipment</option>
                {machines?.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.id}
                  </option>
                ))}
              </select>
              <select
                className="w-full rounded border p-2"
                value={noteStatus}
                onChange={(e) => setNoteStatus(e.target.value)}
              >
                <option value="pending">Needs Fix</option>
                <option value="resolved">Resolved</option>
              </select>
              <textarea
                className="w-full rounded border p-2"
                rows={3}
                value={noteDesc}
                onChange={(e) => setNoteDesc(e.target.value)}
              />
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                className="rounded bg-gray-100 px-4 py-1 hover:bg-gray-200"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button
                className="rounded bg-gray-200 px-4 py-1 text-gray-800 hover:bg-gray-300 disabled:opacity-50"

                onClick={handleSave}
                disabled={!noteEquipment || !noteDesc}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
