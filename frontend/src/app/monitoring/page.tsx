'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import SummaryCard from '@/components/SummaryCard'
import { TimeRangeSelector, EquipmentFilter, SensorFilter } from '@/components/filters'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, CSSProperties } from 'react'
import useWebSocket from '@/hooks/useWebSocket'
import { useRequireRole } from '@/hooks/useRequireRole'
import { useTranslation } from 'react-i18next'
import { InformationCircleIcon } from '@heroicons/react/24/outline'
import DeviceSensorPanel from '@/components/DeviceSensorPanel'

type MyPoint = {
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
  current?: number
  vibration?: number
}
type MyType = Array<MyPoint>

import type { Machine } from '@/components/filters/EquipmentFilter'

interface Anomaly { id: number; equipmentId: string; type: string; status: string }
 

// 고정 범위(초)
const RANGE_SECONDS: Readonly<Record<'1h' | '24h' | '7d', number>> = {
  '1h': 3600,
  '24h': 86400,
  '7d': 604800,
}

// Grafana 관련 코드는 제거되었습니다

// useThemeColors 제거 (차트 제거로 미사용)

const nf = new Intl.NumberFormat('ko-KR')
const formatNum = (n: number | null | undefined, fallback = '-') =>
  typeof n === 'number' && isFinite(n) ? nf.format(n) : fallback

// fmtTimeShort 제거 (차트 제거로 미사용)

const fmtDate = (iso: string | undefined) => {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(d)
}

// 차트 렌더를 제거하여 필드 존재 체크 유틸은 더 이상 사용하지 않음

function downloadCSV(rows: Record<string, unknown>[], filename = 'monitoring.csv') {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const csv =
    [headers.join(','), ...rows.map((r) => headers.map((h) => JSON.stringify(r[h] ?? '')).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function MonitoringPage() {
  useRequireRole(['Admin', 'Engineer', 'Viewer'])

  const { t } = useTranslation('common', { keyPrefix: 'monitoring' })

  /** 가독성 보장 변수 */
  const pageVars: CSSProperties = {
    ['--color-text-primary' as string]: '15 23 42', // slate-900
  }

  // WebSocket
  const envWs = process.env.NEXT_PUBLIC_WEBSOCKET_URL
  const wsStream = envWs
    ? (envWs.endsWith('/stream') ? envWs : `${envWs.replace(/\/$/, '')}/stream`)
    : undefined
  const socketUrl =
    (typeof localStorage !== 'undefined' && localStorage.getItem('socketUrl')) ||
    wsStream ||
    'ws://localhost:8000/api/v1/ws/stream'
  const { data, status } = useWebSocket<MyType>(socketUrl, { autoReconnect: true })

  // Backend REST Base
  const backendBase = (process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000/api/v1')

  // 실시간 일시정지 스냅샷
  const [paused, setPaused] = useState(false)
  const [snap, setSnap] = useState<MyType | null>(null)
  useEffect(() => { if (!paused && data) setSnap(data) }, [data, paused])

  // 정적 목록
  const { data: machines } = useQuery<Machine[]>({
    queryKey: ['machines'],
    queryFn: () => fetch('/machines.json').then((r) => r.json() as Promise<Machine[]>),
    staleTime: 30000, gcTime: 300000,
  })
  const { data: anomalies } = useQuery<Anomaly[]>({
    queryKey: ['anomalies'],
    queryFn: () => fetch('/mock-anomalies.json').then((r) => r.json() as Promise<Anomaly[]>),
    staleTime: 30000, gcTime: 300000,
  })
  

  // 필터
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h')
  const [power, setPower] = useState('')
  const [selectedEquipment, setSelectedEquipment] = useState('')
  const [sensor, setSensor] = useState<'all' | keyof MyPoint>('all')
  // 강조 지속 시간 관리용 타이머(1초)
  const [nowMs, setNowMs] = useState<number>(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNowMs(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  // 실제 모델 추론 결과에서 이상만 조회 (필터 선언 이후)
  type AnomalyEvent = { event_time: string; device_id: string; is_anomaly: boolean; confidence?: number; scores?: unknown; thresholds?: unknown; modalities?: unknown }
  type AnomalyResp = { events: AnomalyEvent[]; total: number; page: number; size: number }
  const { data: anomaliesFromModel } = useQuery<AnomalyResp>({
    queryKey: ['anomalyEvents', selectedEquipment, timeRange],
    queryFn: async () => {
      const now = Date.now()
      const delta = timeRange === '1h' ? 3_600_000 : timeRange === '24h' ? 86_400_000 : 7 * 86_400_000
      const start = new Date(now - delta).toISOString()
      const end = new Date(now).toISOString()
      const params = new URLSearchParams({ page: '1', size: '50', start_time: start, end_time: end })
      if (selectedEquipment) params.set('device_id', selectedEquipment)
      const url = `${backendBase}/anomalies/events?${params.toString()}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('failed to load anomaly events')
      return res.json() as Promise<AnomalyResp>
    },
    refetchInterval: 5000,
    staleTime: 4000,
  })

  // 파생 값
  const latestTs = (snap && snap.length && snap[snap.length - 1]?.time) || 0
  const filteredData = useMemo(() => {
    if (!snap || !snap.length) return []
    const from = latestTs - RANGE_SECONDS[timeRange]
    return snap.filter((d) => d.time >= from)
  }, [snap, latestTs, timeRange])

  // (과거 목업 기반 오픈 이상 맵은 사용하지 않음)

  // 장비 표시용: 동일 기기명(전력 무시)으로 통일된 목록
  const deviceIds = useMemo(() => {
    if (!machines) return [] as string[]
    const filtered = machines.filter((m) => (!power || m.power === power) && (!selectedEquipment || m.id === selectedEquipment))
    return Array.from(new Set(filtered.map((m) => m.id)))
  }, [machines, power, selectedEquipment])

  // 장비별 전력 목록 맵
  const devicePowersMap = useMemo(() => {
    const map = new Map<string, string[]>()
    for (const m of machines ?? []) {
      const arr = map.get(m.id) ?? []
      if (!arr.includes(m.power)) arr.push(m.power)
      map.set(m.id, arr)
    }
    return map
  }, [machines])

  // RUL-lite 퍼센트 맵 (장비 단위, 여러 전력 중 최소값 보수 적용)
  const [rulLiteMap, setRulLiteMap] = useState<Map<string, number>>(new Map())
  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setInterval> | null = null

    const fetchRulLite = async () => {
      try {
        const entries = await Promise.all(
          deviceIds.map(async (id) => {
            const powersRaw = devicePowersMap.get(id) ?? []
            // serve-ml MQTT 추론 갱신은 power 키로 'auto'를 사용할 수 있으므로 함께 조회
            const powers = Array.from(new Set([...powersRaw, 'auto']))
            if (!powers.length) return [id, NaN] as const
            const results = await Promise.all(
              powers.map(async (p) => {
                try {
                  const url = `${backendBase}/rul/status?equipment_id=${encodeURIComponent(id)}&power=${encodeURIComponent(p)}`
                  const res = await fetch(url)
                  if (!res.ok) return NaN
                  const json = (await res.json()) as { rul_pct?: number }
                  const v = typeof json?.rul_pct === 'number' ? json.rul_pct : NaN
                  return v
                } catch {
                  return NaN
                }
              })
            )
            const valid = results.filter((v) => typeof v === 'number' && isFinite(v)) as number[]
            const minPct = valid.length ? Math.min(...valid) : NaN
            return [id, minPct] as const
          })
        )
        if (cancelled) return
        setRulLiteMap(new Map(entries))
      } catch {
        if (cancelled) return
        setRulLiteMap(new Map())
      }
    }

    // 최초 1회 즉시 갱신 후, 주기 폴링(2초)
    fetchRulLite()
    timer = setInterval(fetchRulLite, 2000)

    return () => {
      cancelled = true
      if (timer) clearInterval(timer)
    }
  }, [backendBase, deviceIds, devicePowersMap])

  const equipmentCount = machines?.length ?? 0
  const activeAlerts = anomalies?.filter((a) => a.status === 'open').length ?? 0
  const predictedToday = snap?.[snap.length - 1]?.total ?? 0
  const latestRul = snap?.[snap.length - 1]?.rul ?? 0
  const upcomingMaintenance = useMemo(() => fmtDate('2025-08-28T00:00:00Z'), [])

  const filteredEvents = useMemo(() => {
    const rows = anomaliesFromModel?.events ?? []
    const anomaliesOnly = rows.filter((e) => e.is_anomaly)
    anomaliesOnly.sort((a, b) => b.event_time.localeCompare(a.event_time))
    return anomaliesOnly
  }, [anomaliesFromModel])

  // 최근(예: 10초 이내) 이상 발생 장비만 강조
  const recentAnomalyDeviceIds = useMemo(() => {
    const HIGHLIGHT_MS = 10_000
    const set = new Set<string>()
    for (const e of filteredEvents) {
      const ts = new Date(e.event_time).getTime()
      if (Number.isFinite(ts) && nowMs - ts <= HIGHLIGHT_MS) set.add(e.device_id)
    }
    return set
  }, [filteredEvents, nowMs])

  const onExportCSV = useCallback(() => {
    if (!filteredData.length) return
    downloadCSV(
      filteredData.map((d: MyPoint) => ({
        time: new Date(d.time * 1000).toISOString(),
        total: d.total,
        A: d.A, AAAA: d.AAAA, PTR: d.PTR, SOA: d.SOA, SRV: d.SRV, TXT: d.TXT,
        zone1: d.zone1, zone2: d.zone2, zone3: d.zone3,
        rul: d.rul,
        current: d.current,
        vibration: d.vibration,
      })),
      `monitoring_${timeRange}.csv`,
    )
  }, [filteredData, timeRange])

  // 차트 제거로 색상 팔레트는 더 이상 사용하지 않음
  // 차트 유틸 제거 (xTick, tooltipLabel, axisStyle)
  const isConnecting = status === 'connecting'
  const isError = status === 'error'

  return (
    <DashboardLayout>
      <div style={pageVars}>
        {/* 헤더 + 제어 */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-900">{t('title')}</h1>
            <InformationCircleIcon className="h-5 w-5 text-slate-400" title={t('subtitle')} />
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${
                isError
                  ? 'bg-red-50 text-red-700 ring-red-200'
                  : isConnecting
                  ? 'bg-amber-50 text-amber-700 ring-amber-200'
                  : 'bg-emerald-50 text-emerald-700 ring-emerald-200'
              }`}
              aria-live="polite"
            >
              {isConnecting ? t('connecting') : isError ? t('error') : t('connected')}
            </span>

            <button
              type="button"
              onClick={() => setPaused((p) => !p)}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 active:bg-slate-100"
              aria-pressed={paused}
              title={paused ? t('resumeTitle') : t('pauseTitle')}
            >
              {paused ? t('resume') : t('pause')}
            </button>

            <button
              type="button"
              onClick={onExportCSV}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 active:bg-slate-100"
              disabled={!filteredData.length}
              title={t('exportTitle')}
            >
              {t('exportCsv')}
            </button>
          </div>
        </div>

        {/* 요약 카드 */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-5 [&_*]:text-slate-900">
          <SummaryCard label={t('summary.totalEquipment')} value={formatNum(equipmentCount, '0')} />
          <SummaryCard label={t('summary.activeAlerts')} value={formatNum(activeAlerts, '0')} />
          <SummaryCard label={t('summary.todaysPredicted')} value={formatNum(predictedToday, '0')} />
          <SummaryCard label={t('summary.latestRul')} value={formatNum(latestRul, '0')} />
          <SummaryCard label={t('summary.nextMaintenance')} value={upcomingMaintenance} />
        </div>



        {/* 최근 이벤트 */}
        <div className="relative z-0 mb-8 pointer-events-none">
        <ChartCard title={t('recentEvents')} hoverable={false}>
          {!filteredEvents.length ? (
            <div className="h-[220px] flex items-center justify-center text-slate-500">
              {t('noEvents')}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border border-slate-200 pointer-events-auto">
              <div className="max-h-[240px] overflow-y-auto pointer-events-auto">
                <table className="w-full table-fixed text-sm">
                  <colgroup>
                    <col style={{ width: '34%' }} />
                    <col style={{ width: '28%' }} />
                    <col style={{ width: '22%' }} />
                    <col style={{ width: '16%' }} />
                  </colgroup>
                  <thead className="bg-slate-50 text-left text-slate-700 sticky top-0">
                    <tr className="whitespace-nowrap">
                      <th className="py-2 px-3 font-medium">{t('table.time')}</th>
                      <th className="py-2 px-3 font-medium">{t('table.device')}</th>
                      <th className="py-2 px-3 font-medium">Confidence</th>
                      <th className="py-2 px-3 font-medium">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-900">
                    {filteredEvents.map((e, idx) => {
                      const c = typeof e.confidence === 'number' ? e.confidence : NaN
                      const sev = !isFinite(c) ? 'low' : c > 0.8 ? 'high' : c > 0.6 ? 'medium' : 'low'
                      return (
                        <tr key={`${e.device_id}-${e.event_time}-${idx}`} className="border-t border-slate-100 align-middle">
                          <td className="py-2 px-3">{new Date(e.event_time).toLocaleString('ko-KR')}</td>
                          <td className="py-2 px-3">{e.device_id}</td>
                          <td className="py-2 px-3">{isFinite(c) ? c.toFixed(2) : '-'}</td>
                          <td className="py-2 px-3">
                            <span
                              className={[
                                'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1',
                                sev === 'high'
                                  ? 'bg-red-50 text-red-700 ring-red-200'
                                  : sev === 'medium'
                                  ? 'bg-amber-50 text-amber-700 ring-amber-200'
                                  : 'bg-slate-50 text-slate-600 ring-slate-200',
                              ].join(' ')}
                            >
                              {sev}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </ChartCard>
        </div>

        {/* 필터 */}
        <div className="relative z-50 mb-2 flex flex-wrap items-center gap-2 pointer-events-auto">
          <TimeRangeSelector value={timeRange} onChange={(v: string) => setTimeRange(v as '1h' | '24h' | '7d')} />
          <EquipmentFilter
            machines={machines ?? []}
            power={power}
            device={selectedEquipment}
            onPowerChange={(v: string) => setPower(v)}
            onDeviceChange={(v: string) => setSelectedEquipment(v)}
          />
          <SensorFilter
            options={[
              { value: 'all', label: t('filters.allSensors') },
              { value: 'current', label: t('charts.current') },
              { value: 'vibration', label: t('charts.vibration') },
            ]}
            value={sensor}
            onChange={(v) => setSensor(v as 'all' | keyof MyPoint)}
          />
        </div>

        {/* 활성 필터 배지 */}
        <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-700 ring-1 ring-slate-200">
            {t('activeFilters.period')}: {timeRange}
          </span>
          {selectedEquipment && (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-700 ring-1 ring-slate-200">
              {t('activeFilters.equipment')}: {selectedEquipment}
            </span>
          )}
          {power && (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-700 ring-1 ring-slate-200">
              {t('activeFilters.power')}: {power}
            </span>
          )}
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-700 ring-1 ring-slate-200">
            {t('activeFilters.sensor')}: {sensor === 'all' ? t('filters.allSensors') : t('charts.' + sensor)}
          </span>
        </div>



        {/* 장비별 시계열 패널들 (D3) */}
        {machines && (
          <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {deviceIds
              .sort((a, b) => (a === 'L-CAHU-01S' ? -1 : b === 'L-CAHU-01S' ? 1 : 0))
              .flatMap((devId: string) => {
                const sensors = sensor === 'all' ? (['current', 'vibration'] as const) : [sensor as 'current' | 'vibration']
                const rulPct = rulLiteMap.get(devId)
                const rulLabel = typeof rulPct === 'number' && isFinite(rulPct) ? `${Math.round(rulPct)}%` : '-'
                return sensors.map((s) => (
                  <ChartCard
                    key={`${devId}-${s}`}
                    title={`${devId} - ${t('charts.' + s)} (RUL ${rulLabel})`}
                    danger={recentAnomalyDeviceIds.has(devId)}
                  >
                    <DeviceSensorPanel sensor={s} deviceId={devId} range="5m" />
                  </ChartCard>
                ))
              })}
          </div>
        )}

        {/* 연결 상태 안내 */}
        {isConnecting && (
          <div className="mt-4 rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-800 ring-1 ring-blue-200">
            {t('connectingNotice')}
          </div>
        )}
        {isError && (
          <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800 ring-1 ring-red-200">
            {t('errorNotice')}
          </div>
        )}

      </div>
    </DashboardLayout>
  )
}