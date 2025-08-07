'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import SummaryCard from '@/components/SummaryCard'
import useWebSocket from '@/hooks/useWebSocket'
import { useRequireRole } from '@/hooks/useRequireRole'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from '@/lib/dynamicRecharts'

interface DeviceData {
  time: number
  value: number
}

interface DeviceInfo {
  id: string
  name: string
  type: string
  status: string
  location: string
  lastMaintenance: string
  nextMaintenance: string
}

export default function DeviceDetailPage() {
  useRequireRole(['Admin', 'Engineer', 'Viewer'])
  const params = useParams()
  const id = params?.id as string || 'unknown'

  // WebSocket 연결
  const socketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL
    ? `${process.env.NEXT_PUBLIC_WEBSOCKET_URL}/devices/${id}`
    : `ws://localhost:8080/devices/${id}`
  
  const { data: realtimeData, status } = useWebSocket<DeviceData>(socketUrl, { autoReconnect: true })

  // 장비 정보 조회
  const { data: deviceInfo } = useQuery<DeviceInfo>({
    queryKey: ['device', id],
    queryFn: () =>
      fetch(`/api/devices/${id}`).then((res) => res.json() as Promise<DeviceInfo>),
    staleTime: 30000,
  })

  // 실시간 데이터 처리
  const processedData = realtimeData?.map((d) => ({
    time: d.time,
    vibration: d.value,
    temperature: d.value + 5,
    current: d.value * 0.8,
  })) || []

  const hasAnomaly = realtimeData != null && realtimeData[realtimeData.length - 1]?.value > 50

  return (
    <DashboardLayout>
      {status === 'connecting' && (
        <div className="bg-blue-100 text-blue-800 p-2 rounded-md mb-2">
          Connecting to device...
        </div>
      )}
      {status === 'error' && (
        <div className="bg-red-100 text-red-800 p-2 rounded-md mb-2">
          Connection error. Retrying...
        </div>
      )}

      {/* 장비 정보 */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <SummaryCard label="Device ID" value={deviceInfo?.id || id} />
        <SummaryCard label="Status" value={deviceInfo?.status || 'Unknown'} />
        <SummaryCard label="Type" value={deviceInfo?.type || 'Unknown'} />
        <SummaryCard label="Location" value={deviceInfo?.location || 'Unknown'} />
      </div>

      {/* 센서 데이터 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Vibration Sensor" danger={hasAnomaly}>
          {processedData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={processedData}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Vibration', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="vibration"
                  stroke={hasAnomaly ? '#dc2626' : 'rgb(var(--chart-a))'}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Temperature Sensor">
          {processedData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={processedData}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Temperature', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Current Sensor">
          {processedData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={processedData}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Time', position: 'insideBottomRight' }}
                />
                <YAxis
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                  label={{ value: 'Current', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="current"
                  stroke="var(--color-accent)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="All Sensors">
          {processedData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={processedData}>
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
                <Legend />
                <Line
                  type="monotone"
                  dataKey="vibration"
                  stroke="rgb(var(--chart-a))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="current"
                  stroke="var(--color-accent)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* 유지보수 정보 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        <ChartCard title="Maintenance History">
          <div className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Last Maintenance:</span>
                <span>{deviceInfo?.lastMaintenance || 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span>Next Maintenance:</span>
                <span>{deviceInfo?.nextMaintenance || 'Unknown'}</span>
              </div>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Device Status">
          <div className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Status:</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  deviceInfo?.status === 'active' ? 'bg-green-100 text-green-800' :
                  deviceInfo?.status === 'maintenance' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {deviceInfo?.status || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Type:</span>
                <span>{deviceInfo?.type || 'Unknown'}</span>
              </div>
            </div>
          </div>
        </ChartCard>
      </div>
    </DashboardLayout>
  )
}
