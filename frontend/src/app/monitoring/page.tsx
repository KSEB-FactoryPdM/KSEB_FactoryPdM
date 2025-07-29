// 실시간 모니터링 페이지
'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import SummaryCard from '@/components/SummaryCard'
import { TimeRangeSelector, EquipmentFilter, SensorFilter } from '@/components/filters'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
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
import { useRequireRole } from '@/hooks/useRequireRole'

type MyType = Array<{
  time: number
  total: number
  A: number
  AAAA: number
  PTR: number
  SOA: number
  SRV: number
  TXT: number
  zone1: number
  zone2: number
  zone3: number
  rul: number
  size50: number
  size90: number
  size99: number
}>

interface Equipment {
  id: string
  name: string
  status: string
}

interface Anomaly {
  id: number
  status: string
}

interface EventItem {
  id: number
  time: string
  device: string
  type: string
  severity: string
}

interface MaintenanceItem {
  id: number
  equipmentId: string
  scheduledDate: string
  status: string
}

export default function MonitoringPage() {
  useRequireRole(['Admin', 'Engineer', 'Viewer'])
  // 환경변수 NEXT_PUBLIC_WEBSOCKET_URL 사용, 없으면 로컬로 폴백
  const socketUrl =
    (typeof localStorage !== 'undefined' && localStorage.getItem('socketUrl')) ||
    process.env.NEXT_PUBLIC_WEBSOCKET_URL ||
    'ws://localhost:8080'
  // 자동 재연결 옵션 추가
  const { data, status } = useWebSocket<MyType>(socketUrl, { autoReconnect: true })
  const hasAnomaly =
    data != null && data[data.length - 1]?.total != null && data[data.length - 1]!.total > 0

  // Fetch static mock lists with short caching to reduce network traffic.
  const { data: equipment } = useQuery<Equipment[]>({
    queryKey: ['equipment'],
    queryFn: () =>
      fetch('/mock-equipment.json').then((res) => res.json() as Promise<Equipment[]>),
    staleTime: 30000,
    gcTime: 300000,
  })
  const { data: anomalies } = useQuery<Anomaly[]>({
    queryKey: ['anomalies'],
    queryFn: () =>
      fetch('/mock-anomalies.json').then((res) => res.json() as Promise<Anomaly[]>),
    staleTime: 30000,
    gcTime: 300000,
  })
  const { data: events } = useQuery<EventItem[]>({
    queryKey: ['alertEvents'],
    queryFn: () =>
      fetch('/mock-alerts.json').then((res) => res.json() as Promise<EventItem[]>),
    staleTime: 30000,
    gcTime: 300000,
  })
  const { data: maintenance } = useQuery<MaintenanceItem[]>({
    queryKey: ['maintenance'],
    queryFn: () =>
      fetch('/mock-maintenance.json').then((res) => res.json() as Promise<MaintenanceItem[]>),
    staleTime: 30000,
    gcTime: 300000,
  })

  const [timeRange, setTimeRange] = useState('24h')
  const [selectedEquipment, setSelectedEquipment] = useState('')
  const [sensor, setSensor] = useState('size50')

  const filteredData = useMemo(() => {
    if (!data) return null
    const latest = data[data.length - 1]?.time ?? 0
    const map: Record<string, number> = { '1h': 3600, '24h': 86400, '7d': 604800 }
    const range = map[timeRange] ?? 0
    return data.filter((d) => d.time >= latest - range)
  }, [data, timeRange])

  const equipmentCount = equipment?.length ?? 0
  const activeAlerts = anomalies?.filter((a) => a.status === 'open').length ?? 0
  const predictedToday = data?.[data.length - 1]?.total ?? 0
  const latestRul = data?.[data.length - 1]?.rul ?? 0
  const upcomingMaintenance = useMemo(() => {
    if (!maintenance) return '-'
    const pending = maintenance.filter((m) => m.status === 'pending')
    if (pending.length === 0) return '-'
    return pending.sort((a, b) =>
      a.scheduledDate.localeCompare(b.scheduledDate)
    )[0].scheduledDate
  }, [maintenance])

  return (
    <DashboardLayout>
      {/* Version Card */}
        <div className="bg-white rounded-lg shadow-md p-4 h-20 flex items-center justify-center">
          <div className="text-center w-full">
            <h3 className="text-[1.25rem] font-medium font-heading">
              System Version
            </h3>
            <div className="text-[3rem] font-bold">v1.7.0</div>
          </div>
        </div>

      {status === 'connecting' && (
        <div className="bg-blue-100 text-blue-800 p-2 rounded-md mb-2">
          Connecting to server...
        </div>
      )}
      {status === 'error' && (
        <div className="bg-red-100 text-red-800 p-2 rounded-md mb-2">
          Connection error. Retrying...
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        <SummaryCard label="Total Equipment" value={equipmentCount} />
        <SummaryCard label="Active Alerts" value={activeAlerts} />
        <SummaryCard label="Today's Predicted" value={predictedToday} />
        <SummaryCard label="Latest RUL" value={latestRul} />
        <SummaryCard label="Next Maintenance" value={upcomingMaintenance} />
      </div>

      {/* Recent Anomaly Events */}
      <ChartCard title="Recent Anomaly Events">
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">Time</th>
              <th className="py-2">Device</th>
              <th className="py-2">Sensor</th>
              <th className="py-2">Severity</th>
            </tr>
          </thead>
          <tbody>
            {events?.map((e) => (
              <tr key={e.id} className="border-t">
                <td className="py-2">{e.time}</td>
                <td className="py-2">{e.device}</td>
                <td className="py-2">{e.type}</td>
                <td className="py-2">{e.severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ChartCard>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
        <EquipmentFilter
          options={equipment?.map((e) => e.id) ?? []}
          value={selectedEquipment}
          onChange={setSelectedEquipment}
        />
        <SensorFilter
          options={[
            'size50',
            'size90',
            'size99',
            'rul',
            'A',
            'AAAA',
            'PTR',
            'SOA',
            'SRV',
            'TXT',
          ]}
          value={sensor}
          onChange={setSensor}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 1. Anomaly Count (total) */}
        <ChartCard title="Anomaly Count (total)" danger={hasAnomaly}>
          {data == null ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={filteredData ?? data}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  domain={[0, 1.5]}
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[0, 1.5]}
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="total"
                  stroke={hasAnomaly ? '#dc2626' : 'var(--color-accent)'}
                  dot={false}
                />
                <Tooltip />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 2. Anomaly Count (by type) */}
        <ChartCard title="Anomaly Count (by type)">
          {data == null ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={filteredData ?? data}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="A"
                  stroke="rgb(var(--chart-a))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="AAAA"
                  stroke="var(--color-accent)"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="PTR"
                  stroke="rgb(var(--chart-ptr))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="SOA"
                  stroke="rgb(var(--chart-soa))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="SRV"
                  stroke="rgb(var(--chart-srv))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="TXT"
                  stroke="rgb(var(--chart-txt))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 3. Anomaly Count (by zone) */}
        <ChartCard title="Anomaly Count (by zone)">
          {data == null ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={filteredData ?? data}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="zone1"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="zone2"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="zone3"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 4. Prediction (Remaining Useful Life) */}
        <ChartCard title="Prediction (Remaining Useful Life)">
          {data == null ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={filteredData ?? data}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'RUL', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="rul"
                  stroke="rgb(var(--chart-ptr))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 5. Sensor Data (size, temperature) */}
        <ChartCard title="Sensor Data (size, temperature)">
          {data == null ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={filteredData ?? data}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Value', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="size50"
                  stroke="rgb(var(--chart-a))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="size90"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="size99"
                  stroke="var(--color-accent)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 6. Sensor Data (size, vibration) */}
        <ChartCard title="Sensor Data (size, vibration)">
          <div className="h-[200px] flex items-center justify-center text-text-primary">
            No data
          </div>
        </ChartCard>

        {/* 7. Real-Time Signal */}
        <ChartCard title="Real-Time Signal" danger={hasAnomaly}>
          {data == null ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={filteredData ?? data}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Signal', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey={sensor}
                  stroke={hasAnomaly ? '#dc2626' : 'rgb(var(--chart-a))'}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </DashboardLayout>
  )
}
