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

      <div className="mt-4">
        <ChartCard title="Maintenance Notes">
          <div className="mb-2 text-right">
            <button
              className="px-2 py-1 bg-primary text-white rounded"
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
      </div>

      {showModal && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-white rounded-md p-4 w-80"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-heading mb-2">Add Maintenance Note</h3>
            <select
              className="border p-1 mb-2 w-full"
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
              className="border p-1 mb-2 w-full"
              value={noteStatus}
              onChange={(e) => setNoteStatus(e.target.value)}
            >
              <option value="pending">Needs Fix</option>
              <option value="resolved">Resolved</option>
            </select>
            <textarea
              className="border p-1 mb-2 w-full"
              rows={3}
              value={noteDesc}
              onChange={(e) => setNoteDesc(e.target.value)}
            />
            <div className="flex justify-end space-x-2">
              <button
                className="px-3 py-1 border rounded"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button
                className="px-3 py-1 bg-primary text-white rounded"
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
