'use client'

import { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { AlertItem } from '@/mockData'
import { EquipmentFilter, DateRange, FilterToolbar } from '@/components/filters'
import type { Machine } from '@/components/filters/EquipmentFilter'
import { useQuery } from '@tanstack/react-query'
import AlertDetailsModal from '@/components/AlertDetailsModal'
import { error } from '@/lib/logger'
import { useTranslation } from 'react-i18next'
import EmptyState from '@/components/EmptyState'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [selected, setSelected] = useState<AlertItem | null>(null)
  const [power, setPower] = useState('')
  const [equipment, setEquipment] = useState('')
  const [severity, setSeverity] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const { t } = useTranslation('common')

  const { data: machines } = useQuery<Machine[]>({
    queryKey: ['machines'],
    queryFn: () => fetch('/machines.json').then((res) => res.json() as Promise<Machine[]>),
    staleTime: 30000,
    gcTime: 300000,
  })

  // Backend REST Base
  const backendBase = (process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000/api/v1')

  // 최근 N초 내 발생한 anomaly를 주기적으로 조회하여 일시 경보로 표시
  type AnomalyEvent = { event_time: string; device_id: string; is_anomaly: boolean; confidence?: number }
  type AnomalyResp = { events: AnomalyEvent[]; total: number; page: number; size: number }
  const EPHEMERAL_WINDOW_SEC = 20
  const { data: recentAnomalies } = useQuery<AnomalyResp>({
    queryKey: ['alerts-recent', equipment, severity],
    queryFn: async () => {
      try {
        const now = Date.now()
        const startIso = new Date(now - EPHEMERAL_WINDOW_SEC * 1000).toISOString()
        const endIso = new Date(now).toISOString()
        const params = new URLSearchParams({ page: '1', size: '100', start_time: startIso, end_time: endIso })
        if (equipment) params.set('device_id', equipment)
        const url = `${backendBase}/anomalies/events?${params.toString()}`
        const res = await fetch(url)
        if (!res.ok) throw new Error('failed to load recent anomalies')
        return res.json() as Promise<AnomalyResp>
      } catch (e) {
        error('Failed to fetch recent anomalies', e)
        return { events: [], total: 0, page: 1, size: 0 }
      }
    },
    refetchInterval: 2000,
    staleTime: 1500,
  })

  // 이벤트를 AlertItem으로 매핑하여 일시 목록으로 반영
  useEffect(() => {
    const rows = recentAnomalies?.events ?? []
    const items: AlertItem[] = rows
      .filter((e) => e.is_anomaly)
      .map((e, idx) => {
        const c = typeof e.confidence === 'number' ? e.confidence : NaN
        const sev = !Number.isFinite(c) ? 'Low' : c > 0.8 ? 'Critical' : c > 0.6 ? 'High' : 'Medium'
        return {
          id: Date.parse(e.event_time) + idx,
          time: new Date(e.event_time).toLocaleString('ko-KR'),
          power: '-',
          device: e.device_id,
          type: 'Anomaly',
          severity: sev,
          status: 'new',
          cause: '',
          snapshot: '',
        }
      })
    // 최신순 정렬
    items.sort((a, b) => b.id - a.id)
    setAlerts(items)
  }, [recentAnomalies])
  const severityOptions = useMemo(
    () => Array.from(new Set(alerts.map((a) => a.severity))),
    [alerts]
  )

  const updateStatus = async (ids: number[], status: string) => {
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/alerts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
          })
        )
      )
    } catch (err) {
      error('Failed to update status', err)
    }
    setAlerts((prev) =>
      prev.map((a) => (ids.includes(a.id) ? { ...a, status } : a))
    )
  }

  const changeStatus = (id: number, status: string) => {
    updateStatus([id], status)
  }

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      if (power && a.power !== power) return false
      if (equipment && a.device !== equipment) return false
      if (severity && a.severity !== severity) return false
      if (statusFilter && a.status !== statusFilter) return false
      const date = new Date(a.time)
      if (startDate && date < new Date(startDate)) return false
      if (endDate && date > new Date(endDate)) return false
      return true
    })
  }, [alerts, power, equipment, severity, statusFilter, startDate, endDate])

  return (
    <DashboardLayout>
      <ChartCard title={t('alerts.title')}>
        <FilterToolbar className="mb-2">
          <EquipmentFilter
            machines={machines ?? []}
            power={power}
            device={equipment}
            onPowerChange={setPower}
            onDeviceChange={setEquipment}
          />
          <select
            className="border rounded px-2 py-1"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            aria-label={t('alerts.filters.severity')}
          >
            <option value="">{t('alerts.allSeverity')}</option>
            {severityOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
          <DateRange
            start={startDate}
            end={endDate}
            onStart={setStartDate}
            onEnd={setEndDate}
            startLabel={t('alerts.filters.startDate')}
            endLabel={t('alerts.filters.endDate')}
          />
          <select
            className="border rounded px-2 py-1"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label={t('alerts.filters.status')}
          >
            <option value="">{t('alerts.allStatus')}</option>
            <option value="new">{t('alerts.status.new')}</option>
            <option value="acknowledged">{t('alerts.status.acknowledged')}</option>
            <option value="cleared">{t('alerts.status.cleared')}</option>
          </select>
        </FilterToolbar>
        {selectedIds.length > 0 && (
          <div className="mb-2 space-x-2">
            <button
              className="px-2 py-1 bg-blue-600 text-white rounded"
              onClick={() => {
                updateStatus(selectedIds, 'acknowledged')
                setSelectedIds([])
              }}
            >
              {t('alerts.acknowledgeSelected')}
            </button>
            <button
              className="px-2 py-1 bg-red-600 text-white rounded"
              onClick={() => {
                updateStatus(selectedIds, 'cleared')
                setSelectedIds([])
              }}
            >
              {t('alerts.clearSelected')}
            </button>
          </div>
        )}
        {filteredAlerts.length === 0 ? (
          <EmptyState
            title={t('alerts.noAlerts')}
            description={t('filters.equipment') + ' / ' + t('alerts.filters.severity')}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left">
                <tr>
                  <th className="py-2">
                    <input
                      type="checkbox"
                      checked={
                        filteredAlerts.length > 0 &&
                        filteredAlerts.every((a) => selectedIds.includes(a.id))
                      }
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedIds(filteredAlerts.map((a) => a.id))
                        } else {
                          setSelectedIds([])
                        }
                      }}
                    />
                  </th>
                  <th className="py-2">{t('alerts.headers.time')}</th>
                  <th className="py-2">{t('alerts.headers.kw')}</th>
                  <th className="py-2">{t('alerts.headers.device')}</th>
                  <th className="py-2">{t('alerts.headers.type')}</th>
                  <th className="py-2">{t('alerts.headers.severity')}</th>
                  <th className="py-2">{t('alerts.headers.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((a) => (
                  <tr key={a.id} className="border-t">
                    <td className="py-2">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(a.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedIds((prev) => [...prev, a.id])
                          } else {
                            setSelectedIds((prev) => prev.filter((id) => id !== a.id))
                          }
                        }}
                      />
                    </td>
                    <td className="py-2">{a.time}</td>
                    <td className="py-2">{a.power}</td>
                    <td className="py-2">{a.device}</td>
                    <td className="py-2">{a.type}</td>
                    <td className="py-2">{a.severity}</td>
                    <td className="py-2 space-x-2">
                      <button
                        className="text-blue-600 underline"
                        onClick={() => changeStatus(a.id, 'acknowledged')}
                      >
                        {t('alerts.buttons.acknowledge')}
                      </button>
                      <button
                        className="text-red-600 underline"
                        onClick={() => changeStatus(a.id, 'cleared')}
                      >
                        {t('alerts.buttons.clear')}
                      </button>
                      <button
                        className="text-primary underline"
                        onClick={() => setSelected(a)}
                      >
                        {t('alerts.buttons.details')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ChartCard>
      {selected && (
        <AlertDetailsModal alert={selected} onClose={() => setSelected(null)} />
      )}
    </DashboardLayout>
  )
}
