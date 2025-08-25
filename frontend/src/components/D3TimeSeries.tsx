'use client'

import { useCallback, useEffect, useMemo, useRef } from 'react'
import * as d3 from 'd3'

export type D3Point = { time: number; value: number; metric?: string }

export interface D3TimeSeriesProps {
  data: D3Point[]
  height?: number
  yLabel?: string
  color?: string
  multi?: boolean
  xTickSeconds?: number
  xTickCount?: number
  domainPaddingSeconds?: number
  resampleSeconds?: number
  xDomainSeconds?: [number, number]
}

function groupByMetric(points: D3Point[]): Record<string, D3Point[]> {
  const groups: Record<string, D3Point[]> = {}
  for (const p of points) {
    const k = p.metric || 'value'
    if (!groups[k]) groups[k] = []
    groups[k].push(p)
  }
  for (const k of Object.keys(groups)) {
    groups[k].sort((a, b) => a.time - b.time)
  }
  return groups
}

export default function D3TimeSeries({ data, height = 300, yLabel = '', color = '#A78BFA', multi = false, xTickSeconds = 3, xTickCount = 3, domainPaddingSeconds = 1, resampleSeconds = 1, xDomainSeconds }: D3TimeSeriesProps) {
  const ref = useRef<SVGSVGElement | null>(null)
  const clipIdRef = useRef<string>(`clip-${Math.random().toString(36).slice(2)}`)

  const margin = { top: 8, right: 168, bottom: 40, left: 50 }
  const width = 800
  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom

  const resample = useCallback((series: { time: Date; value: number }[]): { time: Date; value: number }[] => {
    if (!series.length || resampleSeconds <= 0) return series
    const bucketMs = resampleSeconds * 1000
    const map = new Map<number, { sum: number; count: number }>()
    for (const p of series) {
      const k = Math.floor(p.time.getTime() / bucketMs) * bucketMs
      const cur = map.get(k) || { sum: 0, count: 0 }
      cur.sum += p.value
      cur.count += 1
      map.set(k, cur)
    }
    const result: { time: Date; value: number }[] = []
    for (const [k, agg] of map) {
      result.push({ time: new Date(k), value: agg.sum / Math.max(1, agg.count) })
    }
    result.sort((a, b) => a.time.getTime() - b.time.getTime())
    return result
  }, [resampleSeconds])

  const prepared = useMemo(() => {
    if (!multi) {
      const seriesRaw = (data || []).map(d => ({ time: new Date(d.time * 1000), value: d.value }))
      const series = resample(seriesRaw)
      return { kind: 'single' as const, series }
    } else {
      const grouped = groupByMetric(data || [])
      const keys = Object.keys(grouped)
      const seriesByKey = keys.map(k => ({ key: k, values: resample(grouped[k].map(d => ({ time: new Date(d.time * 1000), value: d.value }))) }))
      return { kind: 'multi' as const, seriesByKey }
    }
  }, [data, multi, resample])

  // 그래프 하단 한 줄로 표시할 정보 준비
  const footerItems = useMemo(() => {
    const items: { key: string; color: string; label: string }[] = []
    const fmt = d3.format('.3f')
    if (!multi && prepared.kind === 'single') {
      const series = prepared.series
      const last = series.length ? series[series.length - 1].value : NaN
      const avg = series.length ? (d3.mean(series, d => d.value) ?? NaN) : NaN
      const label = `${yLabel || 'value'} (avg ${Number.isFinite(avg) ? fmt(avg) : '-'}, last ${Number.isFinite(last) ? fmt(last) : '-'})`
      items.push({ key: 'single', color, label })
    } else if (multi && prepared.kind === 'multi') {
      const keys = prepared.seriesByKey.map(s => s.key)
      const palette = d3.scaleOrdinal<string, string>()
        .domain(keys)
        .range(['#F87171', '#34D399', '#60A5FA', '#A78BFA', '#FBBF24', '#22D3EE'])
      const fixed: Record<string, string> = { x: '#F87171', y: '#34D399', z: '#60A5FA' }
      const getColor = (k: string) => fixed[k] || palette(k)
      for (const s of prepared.seriesByKey) {
        const last = s.values.length ? s.values[s.values.length - 1].value : NaN
        const avg = s.values.length ? (d3.mean(s.values, d => d.value) ?? NaN) : NaN
        const label = `${s.key} (avg ${Number.isFinite(avg) ? fmt(avg) : '-'}, last ${Number.isFinite(last) ? fmt(last) : '-'})`
        items.push({ key: s.key, color: getColor(s.key), label })
      }
    }
    return items
  }, [prepared, multi, color, yLabel])

  useEffect(() => {
    const svg = d3.select(ref.current)
    svg.selectAll('*').remove()
    svg.attr('width', width).attr('height', height)
    
    // Dark background
    svg.append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', '#0f172a')

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    const allPoints = (!multi
      ? (prepared.kind === 'single' ? prepared.series : [])
      : (prepared.kind === 'multi' ? prepared.seriesByKey.flatMap(s => s.values) : [])
    ) as { time: Date; value: number }[]

    if (!allPoints.length) return

    const extent = d3.extent(allPoints, d => d.time) as [Date, Date]
    // Domain 우선순위: 외부에서 고정 윈도우 제공(xDomainSeconds) > 데이터 기반 extent ± padding
    const padMs = (domainPaddingSeconds ?? 0) * 1000
    const domainFromData: [Date, Date] = [
      new Date(extent[0].getTime() - padMs / 2),
      new Date(extent[1].getTime() + padMs / 2),
    ]
    const domainFromProp: [Date, Date] | null = (Array.isArray(xDomainSeconds) && xDomainSeconds.length === 2 &&
      Number.isFinite(xDomainSeconds[0]) && Number.isFinite(xDomainSeconds[1]))
      ? [new Date(xDomainSeconds[0] * 1000), new Date(xDomainSeconds[1] * 1000)]
      : null
    const x = d3.scaleTime()
      .domain(domainFromProp ?? domainFromData)
      .range([0, innerWidth])

    const y = d3.scaleLinear()
      .domain(d3.extent(allPoints, d => d.value) as [number, number])
      .nice()
      .range([innerHeight, 0])

    const domainSec = (+(x.domain()[1] as Date) - +(x.domain()[0] as Date)) / 1000
    const fmt = domainSec <= 60 ? d3.timeFormat('%H:%M:%S') : (domainSec >= 86400 ? d3.timeFormat('%m-%d %H:%M') : d3.timeFormat('%H:%M'))
    const xAxis = d3.axisBottom<Date>(x).tickFormat(fmt)
    if (xTickSeconds && xTickSeconds > 0) {
      const interval = d3.timeSecond.every(xTickSeconds)
      if (interval) xAxis.ticks(interval)
    } else if (typeof xTickCount === 'number') {
      xAxis.ticks(xTickCount)
    }
    const yAxis = d3.axisLeft<number>(y).ticks(5)

    const ax = g.append('g').attr('transform', `translate(0,${innerHeight})`).call(xAxis)
    const ay = g.append('g').call(yAxis)
    ax.selectAll('text').attr('fill', '#cbd5e1')
    ax.selectAll('line,path').attr('stroke', '#334155')
    ay.selectAll('text').attr('fill', '#cbd5e1')
    ay.selectAll('line,path').attr('stroke', '#334155')

    if (yLabel) {
      g.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('x', -innerHeight / 2)
        .attr('y', -margin.left + 12)
        .attr('text-anchor', 'middle')
        .attr('fill', '#cbd5e1')
        .attr('font-size', 11)
        .text(yLabel)
    }

    // Clip path to avoid drawing over axes area
    svg.append('defs')
      .append('clipPath')
      .attr('id', clipIdRef.current)
      .append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', innerWidth)
      .attr('height', innerHeight)

    const plot = g.append('g').attr('clip-path', `url(#${clipIdRef.current})`)

    const line = d3.line<{ time: Date; value: number }>()
      .x(d => x(d.time))
      .y(d => y(d.value))
      .defined(d => Number.isFinite(d.value))
      .curve(d3.curveMonotoneX)

    if (!multi && prepared.kind === 'single') {
      plot.append('path')
        .datum(prepared.series)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('d', line)
        .style('stroke-linecap', 'round')
        .style('stroke-linejoin', 'round')
    } else if (multi && prepared.kind === 'multi') {
      const keys = prepared.seriesByKey.map(s => s.key)
      const palette = d3.scaleOrdinal<string, string>()
        .domain(keys)
        .range(['#F87171', '#34D399', '#60A5FA', '#A78BFA', '#FBBF24', '#22D3EE'])
      const fixed: Record<string, string> = { x: '#F87171', y: '#34D399', z: '#60A5FA' }
      const getColor = (k: string) => fixed[k] || palette(k)

      for (const s of prepared.seriesByKey) {
        plot.append('path')
          .datum(s.values)
          .attr('fill', 'none')
          .attr('stroke', getColor(s.key))
          .attr('stroke-width', 1.5)
          .attr('d', line)
          .style('stroke-linecap', 'round')
          .style('stroke-linejoin', 'round')
      }
    }
  }, [prepared, width, height, margin.left, margin.top, innerHeight, innerWidth, color, yLabel, multi, xTickSeconds, xTickCount, domainPaddingSeconds, xDomainSeconds])

  return (
    <div className="w-full overflow-hidden rounded-lg" style={{ background: '#0f172a' }}>
      <svg ref={ref} />
      <div className="px-3 py-2 text-[11px] sm:text-xs text-slate-200 border-t border-slate-700 flex items-center gap-4 overflow-x-auto whitespace-nowrap">
        {footerItems.length ? (
          footerItems.map(item => (
            <div key={item.key} className="inline-flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span>{item.label}</span>
            </div>
          ))
        ) : (
          <span className="text-slate-400">-</span>
        )}
      </div>
    </div>
  )
}


