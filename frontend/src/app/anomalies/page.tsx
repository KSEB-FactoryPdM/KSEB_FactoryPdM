'use client'

import { useEffect, useMemo, useState, type ChangeEvent } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { useRequireRole } from '@/hooks/useRequireRole'
import { useQuery } from '@tanstack/react-query'
import { EquipmentFilter, DateRange, FilterToolbar } from '@/components/filters'
import type { Machine } from '@/components/filters/EquipmentFilter'
import EmptyState from '@/components/EmptyState'
import { useTranslation } from 'react-i18next'
import { error } from '@/lib/logger'
import AnomalyDetailsModal from '@/components/AnomalyDetailsModal'

type Anomaly = { id: string; equipmentId: string; type: string; timestamp: string; status: string; description?: string; severity?: string }

function StatusBadge({ status }: { status: string }) {
  const color = status === 'resolved' ? 'bg-green-100 text-green-800 border-green-200' : 'bg-red-100 text-red-800 border-red-200'
  return <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium border rounded ${color}`}>{status}</span>
}

export default function AnomaliesPage() {
  useRequireRole(['Admin', 'Engineer'])
  const { t } = useTranslation('common')

  const [power, setPower] = useState('')
  const [equipment, setEquipment] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [range, setRange] = useState<'1h' | '24h' | '7d' | 'custom'>('24h')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [sortBy, setSortBy] = useState<'timestamp' | 'equipment' | 'type' | 'status'>('timestamp')
  const [sortAsc, setSortAsc] = useState(false)
  const [selected, setSelected] = useState<Anomaly | null>(null)

  const { data: machines } = useQuery<Machine[]>({
    queryKey: ['machines'],
    queryFn: () => fetch('/machines.json').then((res) => res.json() as Promise<Machine[]>),
    staleTime: 30000,
    gcTime: 300000,
  })

  // Backend REST Base
  const backendBase = (process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000/api/v1')

  type AnomalyEvent = { event_time: string; device_id: string; is_anomaly: boolean; confidence?: number; scores?: unknown; thresholds?: unknown; modalities?: unknown }
  type AnomalyResp = { events: AnomalyEvent[]; total: number; page: number; size: number }
  const { data: anomalies, isLoading } = useQuery<Anomaly[]>({
    queryKey: ['anomalies', equipment, range, startDate, endDate],
    queryFn: async () => {
      try {
        const now = Date.now()
        const delta = range === '1h' ? 3_600_000 : range === '24h' ? 86_400_000 : range === '7d' ? 604_800_000 : 86_400_000
        const startIso = range === 'custom' && startDate ? new Date(startDate).toISOString() : new Date(now - delta).toISOString()
        const endIso = range === 'custom' && endDate ? new Date(endDate).toISOString() : new Date(now).toISOString()
        const params = new URLSearchParams({ page: '1', size: '200', start_time: startIso, end_time: endIso })
        if (equipment) params.set('device_id', equipment)
        const url = `${backendBase}/anomalies/events?${params.toString()}`
        const res = await fetch(url)
        if (!res.ok) throw new Error('failed to load anomalies')
        const json = (await res.json()) as AnomalyResp
        const mapped: Anomaly[] = (json.events || [])
          .filter((e) => e.is_anomaly)
          .map((e) => {
            const c = typeof e.confidence === 'number' ? e.confidence : NaN
            const sev = !Number.isFinite(c) ? 'low' : c > 0.8 ? 'high' : c > 0.6 ? 'medium' : 'low'
            return {
              id: `${e.device_id}-${e.event_time}`,
              timestamp: e.event_time,
              equipmentId: e.device_id,
              type: 'anomaly',
              status: 'open',
              severity: sev,
              description: '',
            }
          })
        return mapped
      } catch (e) {
        error('Failed to fetch anomalies', e)
        return []
      }
    },
    refetchInterval: 4000,
    staleTime: 3000,
    gcTime: 300000,
  })

  const typeOptions = useMemo(
    () => Array.from(new Set((anomalies ?? []).map((a: Anomaly) => a.type))).sort(),
    [anomalies],
  )

  const filtered = useMemo(() => {
    const items = (anomalies ?? []).filter((a: Anomaly) => {
      if (equipment && a.equipmentId !== equipment) return false
      if (typeFilter && a.type !== typeFilter) return false
      if (statusFilter && a.status !== statusFilter) return false
      const ts = new Date(a.timestamp)
      const now = new Date()
      let startBound: Date | null = null
      let endBound: Date | null = null
      if (range === '1h') startBound = new Date(now.getTime() - 1 * 60 * 60 * 1000)
      else if (range === '24h') startBound = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      else if (range === '7d') startBound = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      else if (range === 'custom') {
        if (startDate) startBound = new Date(startDate)
        if (endDate) endBound = new Date(endDate)
      }
      if (startBound && ts < startBound) return false
      if (endBound && ts > endBound) return false
      if (search) {
        const hay = `${a.equipmentId} ${a.type} ${a.status}`.toLowerCase()
        if (!hay.includes(search.toLowerCase())) return false
      }
      return true
    })
    const sorted = [...items].sort((a: Anomaly, b: Anomaly) => {
      let va: string | number = ''
      let vb: string | number = ''
      if (sortBy === 'timestamp') {
        va = new Date(a.timestamp).getTime()
        vb = new Date(b.timestamp).getTime()
      } else if (sortBy === 'equipment') {
        va = a.equipmentId
        vb = b.equipmentId
      } else if (sortBy === 'type') {
        va = a.type
        vb = b.type
      } else {
        va = a.status
        vb = b.status
      }
      if (va < vb) return sortAsc ? -1 : 1
      if (va > vb) return sortAsc ? 1 : -1
      return 0
    })
    return sorted
  }, [anomalies, equipment, typeFilter, statusFilter, startDate, endDate, search, range, sortBy, sortAsc])

  const toggleSort = (key: typeof sortBy) => {
    if (sortBy === key) {
      setSortAsc((v) => !v)
    } else {
      setSortBy(key)
      setSortAsc(true)
    }
  }

  const SortHeader = ({ label, keyName }: { label: string; keyName: typeof sortBy }) => (
    <button
      className="inline-flex items-center gap-1 text-left"
      onClick={() => toggleSort(keyName)}
      title={t('anomalies.sort')}
    >
      <span>{label}</span>
      {sortBy === keyName && (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="text-neutral-400">
          {sortAsc ? (
            <path d="M7 14l5-5 5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          ) : (
            <path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          )}
        </svg>
      )}
    </button>
  )

  const resetFilters = () => {
    setPower('')
    setEquipment('')
    setTypeFilter('')
    setStatusFilter('')
    setSearch('')
    setRange('24h')
    setStartDate('')
    setEndDate('')
  }

  const exportCsv = () => {
    const headers = ['id', 'timestamp', 'equipmentId', 'type', 'status']
    const lines = [headers.join(','), ...filtered.map((a) => [a.id, a.timestamp, a.equipmentId, a.type, a.status].join(','))]
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'anomalies.csv'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  useEffect(() => {
    // No-op; kept to mirror equipment change behavior if needed later
  }, [power])

  return (
    <DashboardLayout>
      <ChartCard title={t('anomalies.title')}>
        <FilterToolbar className="mb-3">
          <select
            className="border rounded px-2 py-1"
            value={range}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setRange(e.target.value as typeof range)}
            aria-label={t('anomalies.filters.range')}
          >
            <option value="1h">1h</option>
            <option value="24h">24h</option>
            <option value="7d">7d</option>
            <option value="custom">Custom</option>
          </select>
          <EquipmentFilter
            machines={machines ?? []}
            power={power}
            device={equipment}
            onPowerChange={setPower}
            onDeviceChange={setEquipment}
          />
          <select
            className="border rounded px-2 py-1"
            value={typeFilter}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setTypeFilter(e.target.value)}
            aria-label={t('anomalies.filters.type')}
          >
            <option value="">{t('anomalies.allTypes')}</option>
            {typeOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
          <select
            className="border rounded px-2 py-1"
            value={statusFilter}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
            aria-label={t('anomalies.filters.status')}
          >
            <option value="">{t('anomalies.allStatus')}</option>
            <option value="open">{t('anomalies.status.open')}</option>
            <option value="resolved">{t('anomalies.status.resolved')}</option>
          </select>
          {range === 'custom' && (
            <DateRange
              start={startDate}
              end={endDate}
              onStart={setStartDate}
              onEnd={setEndDate}
              startLabel={t('anomalies.filters.startDate')}
              endLabel={t('anomalies.filters.endDate')}
            />
          )}
          <input
            type="search"
            className="border rounded px-3 py-1 flex-1 min-w-[160px]"
            placeholder={t('anomalies.search')}
            value={search}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          />
          <button className="px-3 py-1 text-sm bg-neutral-100 rounded border" onClick={resetFilters}>
            {t('anomalies.reset')}
          </button>
          <div className="grow" />
          <button className="px-3 py-1 text-sm bg-primary text-white rounded" onClick={exportCsv}>
            {t('anomalies.exportCsv')}
          </button>
        </FilterToolbar>
        {isLoading ? (
          <div className="text-sm text-neutral-500">{t('anomalies.loading')}</div>
        ) : filtered.length === 0 ? (
          <EmptyState title={t('anomalies.noAnomalies')} description={t('anomalies.tryFilters')} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left select-none">
                <tr>
                  <th className="py-2 cursor-pointer select-none">
                    <SortHeader label={t('anomalies.headers.time')} keyName={'timestamp'} />
                  </th>
                  <th className="py-2 cursor-pointer select-none">
                    <SortHeader label={t('anomalies.headers.equipment')} keyName={'equipment'} />
                  </th>
                  <th className="py-2 cursor-pointer select-none">
                    <SortHeader label={t('anomalies.headers.type')} keyName={'type'} />
                  </th>
                  <th className="py-2 cursor-pointer select-none">
                    <SortHeader label={t('anomalies.headers.status')} keyName={'status'} />
                  </th>
                  <th className="py-2">{t('anomalies.headers.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((a) => (
                  <tr key={a.id} className="border-t hover:bg-neutral-50">
                    <td className="py-2">{new Date(a.timestamp).toLocaleString()}</td>
                    <td className="py-2">{a.equipmentId}</td>
                    <td className="py-2 capitalize">{a.type}</td>
                    <td className="py-2"><StatusBadge status={a.status} /></td>
                    <td className="py-2">
                      <button className="text-primary underline" onClick={() => setSelected(a)}>{t('anomalies.buttons.details')}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ChartCard>
      {selected && (
        <AnomalyDetailsModal anomaly={selected} onClose={() => setSelected(null)} />
      )}
    </DashboardLayout>
  )
}
