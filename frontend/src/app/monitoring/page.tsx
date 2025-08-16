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

// 고정 범위(초)
const RANGE_SECONDS: Readonly<Record<'1h' | '24h' | '7d', number>> = {
  '1h': 3600,
  '24h': 86400,
  '7d': 604800,
}

// Grafana 설정 상수들
const GRAFANA_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_GRAFANA_BASE_URL || 'http://localhost:3001',
  orgId: process.env.NEXT_PUBLIC_GRAFANA_ORG_ID || '1',
  dashboardId: process.env.NEXT_PUBLIC_GRAFANA_DASHBOARD_ID || '63548124-8a50-4d38-b594-b21591792224',
  panelIds: {
    current: process.env.NEXT_PUBLIC_GRAFANA_PANEL_CURRENT_ID || '1',
    vibration: process.env.NEXT_PUBLIC_GRAFANA_PANEL_VIBRATION_ID || '2'
  }
}

// Grafana 컴포넌트들
const GrafanaPanel = ({ 
  sensor, 
  deviceId, 
  timeRange = '5m' 
}: { 
  sensor: 'current' | 'vibration'
  deviceId: string
  timeRange?: '1h' | '24h' | '7d' | '5m'
}) => {
  const { baseUrl, orgId, dashboardId, panelIds } = GRAFANA_CONFIG
  const panelId = panelIds[sensor]
  
  const timeParams = {
    '1h': { from: 'now-1h', to: 'now' },
    '24h': { from: 'now-24h', to: 'now' },
    '7d': { from: 'now-7d', to: 'now' },
    '5m': { from: 'now-5m', to: 'now' }
  }[timeRange] || { from: 'now-5m', to: 'now' }

  // iframe URL 생성
  const iframeUrl = `${baseUrl}/d-solo/${dashboardId}/b2ee4e4?` + 
    new URLSearchParams({
      orgId,
      'var-device': deviceId,
      panelId,
      from: timeParams.from,
      to: timeParams.to,
      timezone: 'browser',
      refresh: '5s',
      '__feature.dashboardSceneSolo': 'true'
 }).toString()

  return (
    <div className="h-[300px] w-full border rounded-lg overflow-hidden">
      <iframe
        src={iframeUrl}
        width="100%"
        height="100%"
        frameBorder="0"
        title={`${deviceId} - ${sensor}`}
        style={{ border: 'none' }}
      />
    </div>
  )
}

// Note: GrafanaDashboard 컴포넌트는 현재 사용되지 않으므로 제거하여 린트 오류 방지

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
  // 차트 제거로 hasAnomaly 미사용
  const filteredData = useMemo(() => {
    if (!snap || !snap.length) return []
    const from = latestTs - RANGE_SECONDS[timeRange]
    return snap.filter((d) => d.time >= from)
  }, [snap, latestTs, timeRange])

  const equipmentCount = machines?.length ?? 0
  const activeAlerts = anomalies?.filter((a) => a.status === 'open').length ?? 0
  const predictedToday = snap?.[snap.length - 1]?.total ?? 0
  const latestRul = snap?.[snap.length - 1]?.rul ?? 0
  const upcomingMaintenance = useMemo(() => {
    if (!maintenance?.length) return '-'
    const pending = maintenance.filter((m: MaintenanceItem) => m.status === 'pending')
    if (!pending.length) return '-'
    pending.sort((a: MaintenanceItem, b: MaintenanceItem) => a.scheduledDate.localeCompare(b.scheduledDate))
    return fmtDate(pending[0].scheduledDate)
  }, [maintenance])

  const filteredEvents = useMemo(() => {
    if (!events?.length) return []
    return events.filter((e: EventItem) => (selectedEquipment ? e.device === selectedEquipment : true))
  }, [events, selectedEquipment])

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
        <ChartCard title={t('recentEvents')}>
          {!events?.length ? (
            <div className="h-[220px] flex items-center justify-center text-slate-500">
              {t('noEvents')}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="w-full table-fixed text-sm">
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



        {/* 장비별 Grafana 패널들 */}
        {machines && (
          <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {[...machines]
              .sort((a, b) => (a.id === 'L-CAHU-01S' ? -1 : b.id === 'L-CAHU-01S' ? 1 : 0))
              .filter(
                (m) => (!power || m.power === power) && (!selectedEquipment || m.id === selectedEquipment),
              )
              .flatMap((m: Machine) => {
                const sensors = sensor === 'all' ? (['current', 'vibration'] as const) : [sensor as 'current' | 'vibration']
                                 return sensors.map((s) => (
                   <ChartCard key={`${m.id}-${m.power}-${s}`} title={`${m.id} (${m.power}) - ${t('charts.' + s)}`}>
                     <GrafanaPanel sensor={s} deviceId={m.id} timeRange="5m" />
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