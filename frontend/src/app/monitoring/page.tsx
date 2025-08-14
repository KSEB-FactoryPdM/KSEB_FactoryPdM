'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import SummaryCard from '@/components/SummaryCard'
import { TimeRangeSelector, EquipmentFilter, SensorFilter } from '@/components/filters'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, CSSProperties } from 'react'
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
import { useTranslation } from 'react-i18next'


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
  // Replace size-bucket signals with explicit sensors
  current?: number
  vibration?: number
}
type MyType = Array<MyPoint>

import type { Machine } from '@/components/filters/EquipmentFilter'

interface Anomaly { id: number; status: string }
interface EventItem {
  id: number
  time: string
  device: string
  type: string
  severity: 'low' | 'medium' | 'high' | string
}
interface MaintenanceItem {
  id: number
  equipmentId: string
  scheduledDate: string
  status: string
}

/** CSS 변수 안전 폴백 */
function useThemeColors() {
  const [colors, setColors] = useState({
    accent: '#3b82f6',
    danger: '#dc2626',
    text: '#334155',
    a: '#16a34a',
    zone: '#8b5cf6',
    ptr: '#0ea5e9',
    soa: '#f59e0b',
    srv: '#10b981',
    txt: '#ef4444',
  })
  useEffect(() => {
    const root = document.documentElement
    const read = (name: string, fallback: string) => {
      const v = getComputedStyle(root).getPropertyValue(name).trim()
      return v ? (v.includes(' ') ? `rgb(${v})` : v) : fallback
    }
    setColors({
      accent: read('--color-accent', '#3b82f6'),
      danger: read('--color-danger', '#dc2626'),
      text: read('--color-text-primary', '#334155'),
      a: read('--chart-a', '#16a34a'),
      zone: read('--chart-zone', '#8b5cf6'),
      ptr: read('--chart-ptr', '#0ea5e9'),
      soa: read('--chart-soa', '#f59e0b'),
      srv: read('--chart-srv', '#10b981'),
      txt: read('--chart-txt', '#ef4444'),
    })
  }, [])
  return colors
}

const nf = new Intl.NumberFormat('ko-KR')
const formatNum = (n: number | null | undefined, fallback = '-') =>
  typeof n === 'number' && isFinite(n) ? nf.format(n) : fallback

const fmtTimeShort = (sec: number, rangeKey: '1h' | '24h' | '7d') => {
  const d = new Date(sec * 1000)
  if (rangeKey === '1h' || rangeKey === '24h') {
    return new Intl.DateTimeFormat('ko-KR', { hour12: false, hour: '2-digit', minute: '2-digit' }).format(d)
  }
  return new Intl.DateTimeFormat('ko-KR', {
    month: '2-digit', day: '2-digit', hour12: false, hour: '2-digit', minute: '2-digit',
  }).format(d)
}
const fmtDate = (iso: string | undefined) => {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(d)
}
const hasField = (list: MyType | null | undefined, key: keyof MyPoint) =>
  !!list?.length && typeof list[list.length - 1]?.[key] === 'number'

function downloadCSV(rows: Record<string, any>[], filename = 'monitoring.csv') {
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

  /** 가독성 보장 변수: 요약 카드 등에서 rgb(var(--color-text-primary))를 확실히 표시 */
  const pageVars: CSSProperties = {
    ['--color-text-primary' as any]: '15 23 42', // slate-900
  }

  // WebSocket
  const socketUrl =
    (typeof localStorage !== 'undefined' && localStorage.getItem('socketUrl')) ||
    process.env.NEXT_PUBLIC_WEBSOCKET_URL ||
    'ws://localhost:8080'
  const { data, status } = useWebSocket<MyType>(socketUrl, { autoReconnect: true })

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
  const { data: events } = useQuery<EventItem[]>({
    queryKey: ['alertEvents'],
    queryFn: () => fetch('/mock-alerts.json').then((r) => r.json() as Promise<EventItem[]>),
    staleTime: 30000, gcTime: 300000,
  })
  const { data: maintenance } = useQuery<MaintenanceItem[]>({
    queryKey: ['maintenance'],
    queryFn: () => fetch('/mock-maintenance.json').then((r) => r.json() as Promise<MaintenanceItem[]>),
    staleTime: 30000, gcTime: 300000,
  })

  // 필터
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h')
  const [power, setPower] = useState('')
  const [selectedEquipment, setSelectedEquipment] = useState('')
  const [sensor, setSensor] = useState<'all' | keyof MyPoint>('all')

  // 파생 값
  const latestTs = (snap && snap.length && snap[snap.length - 1]?.time) || 0
  const hasAnomaly = !!(snap && snap.length && snap[snap.length - 1]?.total > 0)
  const rangeSec: Record<'1h' | '24h' | '7d', number> = { '1h': 3600, '24h': 86400, '7d': 604800 }
  const filteredData = useMemo(() => {
    if (!snap || !snap.length) return []
    const from = latestTs - rangeSec[timeRange]
    return snap.filter((d) => d.time >= from)
  }, [snap, latestTs, timeRange])

  const equipmentCount = machines?.length ?? 0
  const activeAlerts = anomalies?.filter((a) => a.status === 'open').length ?? 0
  const predictedToday = snap?.[snap.length - 1]?.total ?? 0
  const latestRul = snap?.[snap.length - 1]?.rul ?? 0
  const upcomingMaintenance = useMemo(() => {
    if (!maintenance?.length) return '-'
    const pending = maintenance.filter((m) => m.status === 'pending')
    if (!pending.length) return '-'
    pending.sort((a, b) => a.scheduledDate.localeCompare(b.scheduledDate))
    return fmtDate(pending[0].scheduledDate)
  }, [maintenance])

  const filteredEvents = useMemo(() => {
    if (!events?.length) return []
    return events.filter((e) => (selectedEquipment ? e.device === selectedEquipment : true))
  }, [events, selectedEquipment])

  const onExportCSV = useCallback(() => {
    if (!filteredData.length) return
    downloadCSV(
      filteredData.map((d) => ({
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

  const colors = useThemeColors()
  const xTick = (v: number) => fmtTimeShort(v, timeRange)
  const tooltipLabel = (v: any) => {
    const sec = typeof v === 'number' ? v : Number(v)
    if (!isFinite(sec)) return String(v)
    const d = new Date(sec * 1000)
    return new Intl.DateTimeFormat('ko-KR', {
      hour12: false, year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    }).format(d)
  }
  const axisStyle = { fill: colors.text, fontSize: 12 }
  const isConnecting = status === 'connecting'
  const isError = status === 'error'

  return (
    <DashboardLayout>
      {/* 전역 텍스트 가시성 보장 */}
      <div style={pageVars}>
        {/* 헤더 + 제어 */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{t('title')}</h1>
            <p className="text-sm text-slate-600">{t('subtitle')}</p>
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

        {/* 요약 카드: 강제 고대비 적용 */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-5 [&_*]:text-slate-900">
          <SummaryCard label={t('summary.totalEquipment')} value={formatNum(equipmentCount, '0')} />
          <SummaryCard label={t('summary.activeAlerts')} value={formatNum(activeAlerts, '0')} />
          <SummaryCard label={t('summary.todaysPredicted')} value={formatNum(predictedToday, '0')} />
          <SummaryCard label={t('summary.latestRul')} value={formatNum(latestRul, '0')} />
          <SummaryCard label={t('summary.nextMaintenance')} value={upcomingMaintenance} />
        </div>

        {/* 최근 이벤트: 내부 세로 스크롤/thead sticky 전부 제거 → 페이지 스크롤과 완전 동기화 */}
        <ChartCard title={t('recentEvents')}>
          {!events?.length ? (
            <div className="h-[220px] flex items-center justify-center text-slate-500">
              {t('noEvents')}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="w-full table-fixed text-sm">
                {/* 👍 컬럼 고정폭으로 헤더/바디 완전 정렬 */}
                <colgroup>
                  <col style={{ width: '28%' }} />
                  <col style={{ width: '24%' }} />
                  <col style={{ width: '28%' }} />
                  <col style={{ width: '20%' }} />
                </colgroup>
                <thead className="bg-slate-50 text-left text-slate-700">
                  <tr className="whitespace-nowrap">
                    <th className="py-2 px-3 font-medium">{t('table.time')}</th>
                    <th className="py-2 px-3 font-medium">{t('table.device')}</th>
                    <th className="py-2 px-3 font-medium">{t('table.sensor')}</th>
                    <th className="py-2 px-3 font-medium">{t('table.severity')}</th>
                  </tr>
                </thead>
                <tbody className="text-slate-900">
                  {filteredEvents.map((e) => (
                    <tr key={e.id} className="border-t border-slate-100 align-middle">
                      <td className="py-2 px-3">{e.time}</td>
                      <td className="py-2 px-3">{e.device}</td>
                      <td className="py-2 px-3">{e.type}</td>
                      <td className="py-2 px-3">
                        <span
                          className={[
                            'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1',
                            e.severity === 'high'
                              ? 'bg-red-50 text-red-700 ring-red-200'
                              : e.severity === 'medium'
                              ? 'bg-amber-50 text-amber-700 ring-amber-200'
                              : 'bg-slate-50 text-slate-600 ring-slate-200',
                          ].join(' ')}
                        >
                          {e.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </ChartCard>

        {/* 필터 */}
        <div className="mb-2 flex flex-wrap items-center gap-2">
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

        {/* 차트들 */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {(['A', 'AAAA', 'PTR', 'SOA', 'SRV', 'TXT'] as (keyof MyPoint)[]).some((k) => hasField(filteredData, k)) && (
            <ChartCard title={t('charts.anomalyByType')}>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={filteredData} syncId="rt" margin={{ left: 12, right: 12, top: 8, bottom: 8 }}>
                  <XAxis dataKey="time" tick={axisStyle} tickFormatter={xTick} />
                  <YAxis tick={axisStyle} width={48} allowDecimals={false} />
                  <Tooltip labelFormatter={tooltipLabel} />
                  <Legend />
                  <Line type="monotone" dataKey="A" stroke={colors.a} dot={false} />
                  <Line type="monotone" dataKey="AAAA" stroke={colors.accent} dot={false} />
                  <Line type="monotone" dataKey="PTR" stroke={colors.ptr} dot={false} />
                  <Line type="monotone" dataKey="SOA" stroke={colors.soa} dot={false} />
                  <Line type="monotone" dataKey="SRV" stroke={colors.srv} dot={false} />
                  <Line type="monotone" dataKey="TXT" stroke={colors.txt} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {(['zone1', 'zone2', 'zone3'] as (keyof MyPoint)[]).some((k) => hasField(filteredData, k)) && (
            <ChartCard title={t('charts.anomalyByZone')}>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={filteredData} syncId="rt" margin={{ left: 12, right: 12, top: 8, bottom: 8 }}>
                  <XAxis dataKey="time" tick={axisStyle} tickFormatter={xTick} />
                  <YAxis tick={axisStyle} width={48} allowDecimals={false} />
                  <Tooltip labelFormatter={tooltipLabel} />
                  <Legend />
                  <Line type="monotone" dataKey="zone1" stroke={colors.zone} dot={false} />
                  <Line type="monotone" dataKey="zone2" stroke={colors.ptr} dot={false} />
                  <Line type="monotone" dataKey="zone3" stroke={colors.a} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {hasField(filteredData, 'rul') && (
            <ChartCard title={t('charts.predictionRul')}>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={filteredData} syncId="rt" margin={{ left: 12, right: 12, top: 8, bottom: 8 }}>
                  <XAxis dataKey="time" tick={axisStyle} tickFormatter={xTick} />
                  <YAxis tick={axisStyle} width={48} />
                  <Tooltip labelFormatter={tooltipLabel} formatter={(v: any) => [formatNum(Number(v)), 'RUL']} />
                  <Line type="monotone" dataKey="rul" stroke={colors.ptr} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
          {(hasField(filteredData, 'current') || hasField(filteredData, 'vibration')) && (
            <ChartCard title={t('charts.sensorData')}>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={filteredData} syncId="rt" margin={{ left: 12, right: 12, top: 8, bottom: 8 }}>
                  <XAxis dataKey="time" tick={axisStyle} tickFormatter={xTick} />
                  <YAxis tick={axisStyle} width={48} />
                  <Tooltip labelFormatter={tooltipLabel} />
                  <Legend />
                  <Line type="monotone" dataKey="current" stroke={colors.a} dot={false} />
                  <Line type="monotone" dataKey="vibration" stroke={colors.ptr} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {sensor !== 'all' && hasField(filteredData, sensor) && (
            <ChartCard title={t('charts.realTimeSelected')} danger={hasAnomaly}>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={filteredData} syncId="rt" margin={{ left: 12, right: 12, top: 8, bottom: 8 }}>
                  <XAxis dataKey="time" tick={axisStyle} tickFormatter={xTick} />
                  <YAxis tick={axisStyle} width={48} />
                  <Tooltip labelFormatter={tooltipLabel} formatter={(v: any) => [formatNum(Number(v)), String(sensor)]} />
                  <Line type="monotone" dataKey={sensor as string} stroke={hasAnomaly ? colors.danger : colors.a} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>

        {machines && (
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {machines
              .filter(
                (m) => (!power || m.power === power) && (!selectedEquipment || m.id === selectedEquipment),
              )
              .flatMap((m) => {
                const sensors = sensor === 'all' ? (['current', 'vibration'] as (keyof MyPoint)[]) : [sensor]
                return sensors.map((s) => (
                  <ChartCard key={`${m.id}-${m.power}-${s}`} title={`${m.id} (${m.power}) - ${t('charts.' + s)}`}>
                    {!filteredData.length ? (
                      <div className="h-[160px] flex items-center justify-center text-slate-500">
                        {t('charts.noData')}
                      </div>
                    ) : (
                      <div className="h-[160px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart
                            data={filteredData}
                            syncId="rt"
                            margin={{ left: 12, right: 12, top: 8, bottom: 8 }}
                          >
                            <XAxis dataKey="time" tick={axisStyle} tickFormatter={xTick} />
                            <YAxis tick={axisStyle} width={48} />
                            <Tooltip labelFormatter={tooltipLabel} />
                            <Line
                              type="monotone"
                              dataKey={s as string}
                              stroke={s === 'current' ? colors.a : colors.ptr}
                              dot={false}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}
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
