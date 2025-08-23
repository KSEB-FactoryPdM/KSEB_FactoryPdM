'use client'

import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import D3TimeSeries, { type D3Point } from './D3TimeSeries'

type SensorKind = 'current' | 'vibration'

export default function DeviceSensorPanel({
  deviceId,
  sensor,
  range = '5m',
  height = 300,
}: {
  deviceId: string
  sensor: SensorKind
  range?: '5m' | '1h' | '24h' | '7d'
  height?: number
}) {
  const backendBase = (process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000/api/v1')

  type ApiRow = { time: string; device_id: string; sensor_type: string; value: number; unit?: string; created_at?: string }
  type ApiResp = { data: ApiRow[] }

  const queryKey = ['sensor-series', deviceId, sensor, range]

  const { data } = useQuery<ApiResp>({
    queryKey,
    queryFn: async () => {
      const now = Date.now()
      const delta = range === '1h' ? 3_600_000 : range === '24h' ? 86_400_000 : range === '7d' ? 7 * 86_400_000 : 300_000
      const fromIso = new Date(now - delta).toISOString()
      const toIso = new Date(now).toISOString()
      const url = sensor === 'vibration'
        ? `${backendBase}/sensors/data/${encodeURIComponent(deviceId)}?sensor_type=vibe&start_time=${encodeURIComponent(fromIso)}&end_time=${encodeURIComponent(toIso)}&limit=1000`
        : `${backendBase}/sensors/data/${encodeURIComponent(deviceId)}?start_time=${encodeURIComponent(fromIso)}&end_time=${encodeURIComponent(toIso)}&limit=2000`
      const res = await fetch(url)
      if (!res.ok) throw new Error('failed to load series')
      return res.json() as Promise<ApiResp>
    },
    refetchInterval: 3000,
    staleTime: 2500,
  })

  // 고정 윈도우용 현재 시각(초) 갱신
  const [nowSec, setNowSec] = useState<number>(() => Math.floor(Date.now() / 1000))
  useEffect(() => {
    const id = setInterval(() => setNowSec(Math.floor(Date.now() / 1000)), 1000)
    return () => clearInterval(id)
  }, [])

  const xDomainSeconds: [number, number] = useMemo(() => {
    const deltaSec = range === '1h' ? 3600 : range === '24h' ? 86_400 : range === '7d' ? 604_800 : 300
    return [nowSec - deltaSec, nowSec]
  }, [nowSec, range])

  const points: D3Point[] = useMemo(() => {
    const rows = data?.data ?? []
    if (!rows.length) return []
    if (sensor === 'vibration') {
      return rows
        .map(r => ({ time: Math.floor(new Date(r.time).getTime() / 1000), value: r.value, metric: 'vibration' }))
        .sort((a, b) => a.time - b.time)
    }
    const wanted = new Set(['x', 'y', 'z'])
    const pts = rows
      .filter(r => wanted.has(r.sensor_type))
      .map(r => ({ time: Math.floor(new Date(r.time).getTime() / 1000), value: r.value, metric: r.sensor_type }))
    pts.sort((a, b) => a.time - b.time)
    return pts
  }, [data, sensor])

  const yLabel = sensor === 'vibration' ? '진동' : '전류 (A)'
  const multi = sensor === 'current'
  const color = sensor === 'vibration' ? '#8b5cf6' : '#6366F1'

  // 범위별 x축 눈금 간격(초): 5m=30s, 1h=5m, 24h=1h, 7d=12h
  const xTickSeconds = useMemo(() => {
    switch (range) {
      case '1h':
        return 300
      case '24h':
        return 3600
      case '7d':
        return 43200
      default:
        return 30
    }
  }, [range])

  return (
    <D3TimeSeries
      data={points}
      height={height}
      yLabel={yLabel}
      color={color}
      multi={multi}
      xTickSeconds={xTickSeconds}
      xTickCount={undefined as unknown as number}
      domainPaddingSeconds={0}
      resampleSeconds={0}
      xDomainSeconds={xDomainSeconds}
    />
  )
}


