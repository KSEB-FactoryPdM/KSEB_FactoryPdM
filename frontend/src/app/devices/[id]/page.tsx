'use client'
import { useParams } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchWithAuth } from '@/lib/api'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from '@/lib/dynamicRecharts'

import useWebSocket from '@/hooks/useWebSocket'
import { useState } from 'react'

interface AnomalyRow {
  id: number
  equipmentId: string
  type: string
  timestamp: string
  status: string
}

interface MaintenanceRow {
  id: number
  equipmentId: string
  scheduledDate: string
  status: string
}

interface ActionLog {
  id: number
  action: string
  user: string
  time: string
  result: string
}

interface DeviceDetail {
  id: string
  name: string
  model: string
  location: string
  lastInspection: string
  threshold: number
  history: { time: number; value: number }[]
}

export default function DeviceDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params?.id ?? ''
  const queryClient = useQueryClient()
  // Device detail comes from static mock JSON. Cache briefly to reduce network
  // calls without holding stale data for too long.
  const { data } = useQuery<DeviceDetail>({
    queryKey: ['device', id],
    queryFn: () => fetch(`/devices/${id}.json`).then(r => r.json()),
    staleTime: 30000,
    gcTime: 300000,
  })

  const { data: anomalies = [] } = useQuery<AnomalyRow[]>({
    queryKey: ['anomalies', id],
    queryFn: () => fetch('/mock-anomalies.json').then(r => r.json()),
    staleTime: 30000,
    gcTime: 300000,
  })

  const { data: maintenance = [] } = useQuery<MaintenanceRow[]>({
    queryKey: ['maintenance', id],
    queryFn: () => fetch('/mock-maintenance.json').then(r => r.json()),
    staleTime: 30000,
    gcTime: 300000,
  })

  const { data: actions = [] } = useQuery<ActionLog[]>({
    queryKey: ['actions', id],
    queryFn: () => fetch('/mock-actions.json').then(r => r.json()),
    staleTime: 30000,
    gcTime: 300000,
  })

  const [threshold, setThreshold] = useState<number | undefined>(undefined)

  const mutation = useMutation({
    mutationFn: async (value: number) => {
      await fetchWithAuth(`/api/devices/${id}/threshold`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threshold: value })
      })
      return value
    },
    onSuccess: val => {
      queryClient.setQueryData<DeviceDetail>(['device', id], old =>
        old ? { ...old, threshold: val } : old
      )
    }
  })

  const handleAcknowledge = () =>
    fetchWithAuth(`/api/devices/${id}/acknowledge`, { method: 'POST' })

  const handleStop = () =>
    fetchWithAuth(`/api/devices/${id}/stop`, { method: 'POST' })

  const handleRequestMaintenance = () =>
    fetchWithAuth(`/api/devices/${id}/maintenance-request`, { method: 'POST' })

  const { data: realtime } = useWebSocket<{ time: number; value: number }[]>(
    process.env.NEXT_PUBLIC_WEBSOCKET_URL
      ? `${process.env.NEXT_PUBLIC_WEBSOCKET_URL}/devices/${id}`
      : undefined,
    { autoReconnect: true }
  )

  const history = data?.history.map(h => ({
    time: h.time,
    vibration: h.value,
    temperature: h.value + 5,
  })) ?? []

  const realtimeData = (realtime ?? []).map(d => ({
    time: d.time,
    vibration: d.value,
    temperature: d.value + 5,
  }))

  const filteredAnomalies = anomalies.filter(a => a.equipmentId === id)
  const filteredMaintenance = maintenance.filter(m => m.equipmentId === id)
  const actionHistory = actions

  const downloadLog = (rows: unknown[], filename: string) => {
    const blob = new Blob([JSON.stringify(rows, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <DashboardLayout>
      <ChartCard title="Equipment Info">
        <table className="w-full text-sm">
          <tbody>
            <tr>
              <td className="py-1 font-medium">ID</td>
              <td className="py-1">{data?.id}</td>
            </tr>
            <tr>
              <td className="py-1 font-medium">Model</td>
              <td className="py-1">{data?.model}</td>
            </tr>
            <tr>
              <td className="py-1 font-medium">Location</td>
              <td className="py-1">{data?.location}</td>
            </tr>
            <tr>
              <td className="py-1 font-medium">Last Inspection</td>
              <td className="py-1">{data?.lastInspection}</td>
            </tr>
          </tbody>
        </table>
      </ChartCard>
      <ChartCard title={`Device ${id}`}>
        <div className="mb-4 space-y-2">
          <div>
            <label className="block text-sm mb-1">Threshold</label>
            <input
              type="number"
              className="border px-2 py-1 rounded text-sm"
              value={threshold ?? data?.threshold ?? 0}
              onChange={e => setThreshold(Number(e.target.value))}
            />
            <button
              className="ml-2 px-2 py-1 border rounded text-sm"
              onClick={() => {
                if (threshold != null) mutation.mutate(threshold)
              }}
            >Save</button>
          </div>
          <div className="space-x-2">
            <button className="px-2 py-1 border rounded text-sm" onClick={handleAcknowledge}>
              Acknowledge Alert
            </button>
            <button className="px-2 py-1 border rounded text-sm" onClick={handleStop}>
              Remote Stop
            </button>
            <button className="px-2 py-1 border rounded text-sm" onClick={handleRequestMaintenance}>
              Request Maintenance
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium mb-1 text-sm">History</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={history} syncId="sensorSync">
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="vibration"
                  stroke="var(--color-accent)"
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="temperature"
                  stroke="#f97316"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div>
            <h3 className="font-medium mb-1 text-sm">Real-Time</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={realtimeData} syncId="sensorSync">
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="vibration"
                  stroke="var(--color-accent)"
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="temperature"
                  stroke="#f97316"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </ChartCard>

      <ChartCard title="Anomaly History">
        <div className="mb-2 text-right">
          <button
            className="px-2 py-1 border rounded text-sm"
            onClick={() => downloadLog(filteredAnomalies, `anomalies-${id}.json`)}
          >
            Download
          </button>
        </div>
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-1">Time</th>
              <th className="py-1">Type</th>
              <th className="py-1">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredAnomalies.map(a => (
              <tr key={a.id} className="border-t">
                <td className="py-1">{a.timestamp}</td>
                <td className="py-1">{a.type}</td>
                <td className="py-1">{a.status}</td>
              </tr>
            ))}
            {filteredAnomalies.length === 0 && (
              <tr>
                <td className="py-1" colSpan={3}>No anomalies</td>
              </tr>
            )}
          </tbody>
        </table>
      </ChartCard>

      <ChartCard title="Action History">
        <div className="mb-2 text-right">
          <button
            className="px-2 py-1 border rounded text-sm"
            onClick={() => downloadLog(actionHistory, `actions-${id}.json`)}
          >
            Download
          </button>
        </div>
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-1">Time</th>
              <th className="py-1">Action</th>
              <th className="py-1">User</th>
              <th className="py-1">Result</th>
            </tr>
          </thead>
          <tbody>
            {actionHistory.map(a => (
              <tr key={a.id} className="border-t">
                <td className="py-1">{a.time}</td>
                <td className="py-1">{a.action}</td>
                <td className="py-1">{a.user}</td>
                <td className="py-1">{a.result}</td>
              </tr>
            ))}
            {actionHistory.length === 0 && (
              <tr>
                <td className="py-1" colSpan={4}>No actions</td>
              </tr>
            )}
          </tbody>
        </table>
      </ChartCard>

      <ChartCard title="Maintenance Log">
        <div className="mb-2 text-right">
          <button
            className="px-2 py-1 border rounded text-sm"
            onClick={() => downloadLog(filteredMaintenance, `maintenance-${id}.json`)}
          >
            Download
          </button>
        </div>
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-1">Date</th>
              <th className="py-1">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredMaintenance.map(m => (
              <tr key={m.id} className="border-t">
                <td className="py-1">{m.scheduledDate}</td>
                <td className="py-1">{m.status}</td>
              </tr>
            ))}
            {filteredMaintenance.length === 0 && (
              <tr>
                <td className="py-1" colSpan={2}>No logs</td>
              </tr>
            )}
          </tbody>
        </table>
      </ChartCard>
    </DashboardLayout>
  )
}
