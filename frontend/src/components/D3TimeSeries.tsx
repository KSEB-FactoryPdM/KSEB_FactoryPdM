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
        .attr('stroke-width', 1.5) // 선 두께 증가로 간격 넓히기
        .attr('d', line)
        .style('stroke-linecap', 'round')
        .style('stroke-linejoin', 'round')

      // Single-series legend with stats
      const last = prepared.series.length ? prepared.series[prepared.series.length - 1].value : NaN
      const avg = prepared.series.length ? d3.mean(prepared.series, d => d.value) ?? NaN : NaN
      const fmt = d3.format('.3f')
      const text = `vibration (avg ${Number.isFinite(avg) ? fmt(avg) : '-'}, last ${Number.isFinite(last) ? fmt(last) : '-'})`

      // 텍스트 크기 측정을 위한 임시 텍스트 요소
      const tempText = svg.append('text')
        .attr('x', 0).attr('y', 0)
        .attr('fill', '#e2e8f0')
        .attr('font-size', 12)
        .attr('font-weight', '500')
        .text(text)
        .style('visibility', 'hidden')

      const textBBox = (tempText.node() as SVGTextElement).getBBox()
      const textWidth = textBBox.width
      const textHeight = textBBox.height
      tempText.remove()

      // 동적으로 범례 크기 계산
      const legendWidth = textWidth + 36 // 좌우 패딩 + 색상 박스 여백
      const legendHeight = Math.max(textHeight + 12, 28)
      const legendX = margin.left + 16 // 왼쪽으로 이동
      const legendY = margin.top + 6 // 추가 6px 위쪽으로 이동

      const legend = svg.append('g').attr('transform', `translate(${legendX}, ${legendY})`).style('pointer-events', 'none')

      // 범례 배경에 그라디언트 효과
      const gradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', 'legendGradient')
        .attr('x1', '0%').attr('y1', '0%')
        .attr('x2', '0%').attr('y2', '100%')

      gradient.append('stop').attr('offset', '0%').attr('stop-color', '#1e293b').attr('stop-opacity', 0.95)
      gradient.append('stop').attr('offset', '100%').attr('stop-color', '#0f172a').attr('stop-opacity', 0.95)

      legend.append('rect')
        .attr('width', legendWidth)
        .attr('height', legendHeight)
        .attr('fill', 'url(#legendGradient)')
        .attr('opacity', 0.95)
        .attr('rx', 8)
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 1)
        .attr('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))')

      // 색상 인디케이터 (더 부드러운 원형)
      legend.append('circle')
        .attr('cx', 16)
        .attr('cy', 14) // 상단 여백 제거
        .attr('r', 6)
        .attr('fill', color)
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 1)
        .attr('opacity', 0.9)

      legend.append('text')
        .attr('x', 32)
        .attr('y', 14 + textHeight / 3) // 상단 여백 제거
        .attr('fill', '#f1f5f9')
        .attr('font-size', 12)
        .attr('font-weight', '500')
        .attr('font-family', 'Inter, -apple-system, BlinkMacSystemFont, sans-serif')
        .text(text)
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

      const fmt = d3.format('.3f')
      const lines = prepared.seriesByKey.map(s => {
        const last = s.values.length ? s.values[s.values.length - 1].value : NaN
        const avg = s.values.length ? d3.mean(s.values, d => d.value) ?? NaN : NaN
        return `${s.key} (avg ${Number.isFinite(avg) ? fmt(avg) : '-'}, last ${Number.isFinite(last) ? fmt(last) : '-'})`
      })

      // 각 텍스트 라인의 너비 측정
      const textWidths: number[] = []
      const textHeight = 12
      const tempTexts = lines.map(line => {
        const tempText = svg.append('text')
          .attr('x', 0).attr('y', 0)
          .attr('fill', '#e2e8f0')
          .attr('font-size', 12)
          .attr('font-weight', '500')
          .text(line)
          .style('visibility', 'hidden')
        const bbox = (tempText.node() as SVGTextElement).getBBox()
        textWidths.push(bbox.width)
        return tempText
      })

      // 임시 텍스트 요소들 제거
      tempTexts.forEach(t => t.remove())

      // 최대 텍스트 너비 계산
      const maxTextWidth = Math.max(...textWidths)
      const itemHeight = 24
      const legendWidth = maxTextWidth + 48 // 좌우 패딩 + 색상 원 여백
      const legendHeight = prepared.seriesByKey.length * itemHeight + 20
      const legendX = margin.left + 16 // 왼쪽으로 이동
      const legendY = margin.top + 6 // 추가 6px 위쪽으로 이동

      const legend = svg.append('g').attr('transform', `translate(${legendX}, ${legendY})`).style('pointer-events', 'none')

      // 범례 배경에 그라디언트 효과
      const multiGradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', 'multiLegendGradient')
        .attr('x1', '0%').attr('y1', '0%')
        .attr('x2', '0%').attr('y2', '100%')

      multiGradient.append('stop').attr('offset', '0%').attr('stop-color', '#1e293b').attr('stop-opacity', 0.95)
      multiGradient.append('stop').attr('offset', '100%').attr('stop-color', '#0f172a').attr('stop-opacity', 0.95)

      legend.append('rect')
        .attr('width', legendWidth)
        .attr('height', legendHeight)
        .attr('fill', 'url(#multiLegendGradient)')
        .attr('opacity', 0.95)
        .attr('rx', 10)
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 1)
        .attr('filter', 'drop-shadow(0 4px 6px rgba(0,0,0,0.4))')

      prepared.seriesByKey.forEach((s, i) => {
        const c = getColor(s.key)
        const y = 10 + i * itemHeight + itemHeight / 2 // 상단 여백 제거

        // 색상 인디케이터 (원형)
        legend.append('circle')
          .attr('cx', 18)
          .attr('cy', y)
          .attr('r', 6)
          .attr('fill', c)
          .attr('stroke', '#ffffff')
          .attr('stroke-width', 2)
          .attr('opacity', 0.9)

        legend.append('text')
          .attr('x', 36)
          .attr('y', y + textHeight / 3)
          .attr('fill', '#f1f5f9')
          .attr('font-size', 12)
          .attr('font-weight', '500')
          .attr('font-family', 'Inter, -apple-system, BlinkMacSystemFont, sans-serif')
          .text(lines[i])
      })
    }
  }, [prepared, width, height, margin.left, margin.top, innerHeight, innerWidth, color, yLabel, multi, xTickSeconds, xTickCount, domainPaddingSeconds, xDomainSeconds])

  return (
    <div className="w-full overflow-hidden rounded-lg" style={{ background: '#0f172a' }}>
      <svg ref={ref} />
    </div>
  )
}


